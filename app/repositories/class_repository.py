from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from app.models.entities import FitnessClass
from app.models.database import get_db_connection
from app.utils.exceptions import DatabaseError, ClassNotFoundError
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ClassRepository:
    
    def __init__(self):
        self.db = get_db_connection()
        self.collection = self.db['classes']
    
    def get_all_classes(self, include_past: bool = False) -> List[FitnessClass]:
        try:
            query = {}
            if not include_past:
                now_ist = settings.now("IST")
                query['datetime_ist'] = {'$gt': now_ist}
            
            cursor = self.collection.find(query).sort('datetime_ist', 1)
            
            classes = []
            for doc in cursor:
                fitness_class = self._doc_to_entity(doc)
                classes.append(fitness_class)
            
            logger.info(f"Retrieved {len(classes)} classes from database")
            return classes
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving classes: {str(e)}")
            raise DatabaseError(f"Failed to retrieve classes: {str(e)}", "get_all_classes")
    
    def get_class_by_id(self, class_id: str) -> Optional[FitnessClass]:
        try:
            if not ObjectId.is_valid(class_id):
                return None
                
            doc = self.collection.find_one({'_id': ObjectId(class_id)})
            
            if not doc:
                return None
            
            return self._doc_to_entity(doc)
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving class {class_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve class: {str(e)}", "get_class_by_id")
    
    def create_class(self, fitness_class: FitnessClass) -> FitnessClass:
        try:
            doc = {
                'name': fitness_class.name,
                'instructor': fitness_class.instructor,
                'datetime_ist': fitness_class.datetime_ist,
                'duration_minutes': fitness_class.duration_minutes,
                'total_slots': fitness_class.total_slots,
                'available_slots': fitness_class.available_slots,
                'description': fitness_class.description,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = self.collection.insert_one(doc)
            fitness_class.id = str(result.inserted_id)
            
            logger.info(f"Created new class: {fitness_class.name} (ID: {fitness_class.id})")
            return fitness_class
                
        except PyMongoError as e:
            logger.error(f"Database error creating class: {str(e)}")
            raise DatabaseError(f"Failed to create class: {str(e)}", "create_class")
    
    def update_class_slots(self, class_id: str, available_slots: int) -> bool:
        try:
            if not ObjectId.is_valid(class_id):
                raise ClassNotFoundError(class_id)
            
            result = self.collection.update_one(
                {'_id': ObjectId(class_id)},
                {
                    '$set': {
                        'available_slots': available_slots,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                raise ClassNotFoundError(class_id)
            
            logger.info(f"Updated class {class_id} slots to {available_slots}")
            return True
                
        except ClassNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(f"Database error updating class slots: {str(e)}")
            raise DatabaseError(f"Failed to update class slots: {str(e)}", "update_class_slots")
    
    def delete_class(self, class_id: str) -> bool:
        try:
            if not ObjectId.is_valid(class_id):
                raise ClassNotFoundError(class_id)
            
            result = self.collection.delete_one({'_id': ObjectId(class_id)})
            
            if result.deleted_count == 0:
                raise ClassNotFoundError(class_id)
            
            logger.info(f"Deleted class with ID: {class_id}")
            return True
                
        except ClassNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(f"Database error deleting class: {str(e)}")
            raise DatabaseError(f"Failed to delete class: {str(e)}", "delete_class")

    def get_classes_by_instructor(self, instructor: str) -> List[FitnessClass]:
        try:
            cursor = self.collection.find(
                {'instructor': instructor}
            ).sort('datetime_ist', 1)
            
            classes = [self._doc_to_entity(doc) for doc in cursor]
            
            logger.info(f"Retrieved {len(classes)} classes for instructor: {instructor}")
            return classes
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving classes by instructor: {str(e)}")
            raise DatabaseError(f"Failed to retrieve classes by instructor: {str(e)}", "get_classes_by_instructor")
    
    def get_upcoming_classes(self, hours_ahead: int = 24) -> List[FitnessClass]:
        try:
            now = settings.now("IST")
            future_time = now + timedelta(hours=hours_ahead)
            
            cursor = self.collection.find({
                'datetime_ist': {
                    '$gte': now,
                    '$lte': future_time
                }
            }).sort('datetime_ist', 1)
            
            classes = [self._doc_to_entity(doc) for doc in cursor]
            
            logger.info(f"Retrieved {len(classes)} upcoming classes")
            return classes
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving upcoming classes: {str(e)}")
            raise DatabaseError(f"Failed to retrieve upcoming classes: {str(e)}", "get_upcoming_classes")
    
    def _doc_to_entity(self, doc: Dict[str, Any]) -> FitnessClass:
        return FitnessClass(
            id=str(doc.get('_id', doc.get('id'))),
            name=doc['name'],
            instructor=doc['instructor'],
            datetime_ist=doc['datetime_ist'],
            duration_minutes=doc['duration_minutes'],
            total_slots=doc['total_slots'],
            available_slots=doc['available_slots'],
            description=doc.get('description'),
            created_at=doc.get('created_at'),
            updated_at=doc.get('updated_at')
        )

    def get_class_id_by_name(self, name: str) -> Optional[str]:
        try:
            doc = self.collection.find_one({"name": name})
            if doc:
                return str(doc.get('_id'))
            return None
        except PyMongoError as e:
            logger.error(f"MongoDB error retrieving class id by name: {str(e)}")
            raise DatabaseError(f"Failed to retrieve class id by name: {str(e)}", "get_class_id_by_name")