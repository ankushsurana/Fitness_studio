from datetime import datetime
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from typing import List, Optional, Dict, Any
import logging
from app.models.entities import Booking
from app.models.database import get_db_connection
from app.utils.exceptions import DatabaseError, DuplicateBookingError
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class BookingRepository:
    def __init__(self):
        self.db = get_db_connection()
        self.collection = self.db['bookings']

    def create_booking(self, booking: Booking) -> Booking:
        try:
            # Check if class_id is already an ObjectId or string
            if not ObjectId.is_valid(booking.class_id):
                class_object_id = ObjectId(booking.class_id)
            
            class_object_id = booking.class_id
                
            doc = {
                "class_id": class_object_id,
                "client_name": booking.client_name.strip(),
                "client_email": booking.client_email.strip(),
                "booking_time": booking.booking_time or datetime.utcnow(),
                "status": booking.status,
                "created_at": booking.created_at or datetime.utcnow(),
            }
            result = self.collection.insert_one(doc)
            booking.id = str(result.inserted_id)
            return booking
        except DuplicateKeyError:
            raise DuplicateBookingError(booking.class_id, booking.client_email)
        except PyMongoError as e:
            logger.error(f"MongoDB error creating booking: {str(e)}")
            raise DatabaseError(f"Failed to create booking: {str(e)}", "create_booking")
    
    def get_booking_by_id(self, booking_id: str) -> Optional[Booking]:
        try:
            if not ObjectId.is_valid(booking_id):
                return None
            
            pipeline = [
                {'$match': {'_id': ObjectId(booking_id)}},
                {
                    '$lookup': {
                        'from': 'classes',
                        'localField': 'class_id',
                        'foreignField': '_id',
                        'as': 'class_info'
                    }
                },
                {'$unwind': {'path': '$class_info', 'preserveNullAndEmptyArrays': True}}
            ]
            result = list(self.collection.aggregate(pipeline))
            if not result:
                return None
            return self._doc_to_entity(result[0])
        except PyMongoError as e:
            logger.error(f"Database error retrieving booking {booking_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve booking: {str(e)}", "get_booking_by_id")
    
    def get_bookings_by_email(self, client_email: str, include_cancelled: bool = False) -> List[Booking]:
        try:
            query = {"client_email": client_email.lower()}
            if not include_cancelled:
                query["status"] = {"$ne": "cancelled"}
            
            pipeline = [
                {'$match': query},
                {
                    '$lookup': {
                        'from': 'classes',
                        'localField': 'class_id',
                        'foreignField': '_id',
                        'as': 'class_info'
                    }
                },
                {'$unwind': {'path': '$class_info', 'preserveNullAndEmptyArrays': True}}
            ]
            
            bookings = [self._doc_to_entity(doc) for doc in self.collection.aggregate(pipeline)]
            logger.info(f"Retrieved {len(bookings)} bookings for {client_email}")
            return bookings
        except PyMongoError as e:
            logger.error(f"MongoDB error retrieving bookings by email: {str(e)}")
            raise DatabaseError(f"Failed to retrieve bookings: {str(e)}", "get_bookings_by_email")
    
    def get_bookings_by_class(self, class_id: str) -> List[Booking]:
        try:
            if not ObjectId.is_valid(class_id):
                return []
            
            pipeline = [
                {'$match': {'class_id': ObjectId(class_id), 'status': 'confirmed'}},
                {
                    '$lookup': {
                        'from': 'classes',
                        'localField': 'class_id',
                        'foreignField': '_id',
                        'as': 'class_info'
                    }
                },
                {'$unwind': {'path': '$class_info', 'preserveNullAndEmptyArrays': True}}
            ]
            
            bookings = [self._doc_to_entity(doc) for doc in self.collection.aggregate(pipeline)]
            logger.info(f"Retrieved {len(bookings)} bookings for class {class_id}")
            return bookings
        except PyMongoError as e:
            logger.error(f"MongoDB error retrieving bookings by class: {str(e)}")
            raise DatabaseError(f"Failed to retrieve class bookings: {str(e)}", "get_bookings_by_class")

    def cancel_booking(self, booking_id: str) -> bool:
        try:
            if not ObjectId.is_valid(booking_id):
                return False
            result = self.collection.update_one(
                {'_id': ObjectId(booking_id), 'status': 'confirmed'},
                {'$set': {'status': 'cancelled'}}
            )
            if result.matched_count == 0:
                return False
            logger.info(f"Cancelled booking: {booking_id}")
            return True
        except PyMongoError as e:
            logger.error(f"Database error cancelling booking: {str(e)}")
            raise DatabaseError(f"Failed to cancel booking: {str(e)}", "cancel_booking")
    
    def get_booking_count_by_class(self, class_id: str) -> int:
        try:
            if not ObjectId.is_valid(class_id):
                return 0
            
            count = self.collection.count_documents({
                'class_id': ObjectId(class_id),
                'status': 'confirmed'
            })
            return count
        except PyMongoError as e:
            logger.error(f"Database error getting booking count: {str(e)}")
            raise DatabaseError(f"Failed to get booking count: {str(e)}", "get_booking_count_by_class")
    
    def check_duplicate_booking(self, class_id: str, client_email: str) -> bool:
        try:
            if not ObjectId.is_valid(class_id):
                return False
            existing = self.collection.find_one({
                'class_id': ObjectId(class_id),
                'client_email': client_email.lower(),
                'status': 'confirmed'
            })
            
            return existing is not None
        except PyMongoError as e:
            logger.error(f"Database error checking duplicate booking: {str(e)}")
            raise DatabaseError(f"Failed to check duplicate booking: {str(e)}", "check_duplicate_booking")
    
    def get_all_bookings(self, limit: int = 100, offset: int = 0) -> List[Booking]:
        try:
            pipeline = [
                {
                    '$lookup': {
                        'from': 'classes',
                        'localField': 'class_id',
                        'foreignField': '_id',
                        'as': 'class_info'
                    }
                },
                {'$unwind': {'path': '$class_info', 'preserveNullAndEmptyArrays': True}},
                {'$sort': {'created_at': -1}}
            ]
            
            if limit != -1:
                pipeline.extend([
                    {'$skip': offset},
                    {'$limit': limit}
                ])
            
            cursor = self.collection.aggregate(pipeline)
            bookings = [self._doc_to_entity(doc) for doc in cursor]
            
            logger.info(f"Retrieved {len(bookings)} bookings (limit: {limit}, offset: {offset})")
            return bookings
        except PyMongoError as e:
            logger.error(f"Database error retrieving all bookings: {str(e)}")
            raise DatabaseError(f"Failed to retrieve bookings: {str(e)}", "get_all_bookings")
    
    def _doc_to_entity(self, doc: Dict[str, Any]) -> Booking:
        class_info = doc.get('class_info', {})
        return Booking(
            id=str(doc['_id']),
            class_id=str(doc['class_id']),
            client_name=doc['client_name'],
            client_email=doc['client_email'],
            booking_time=doc['booking_time'],
            status=doc['status'],
            created_at=doc.get('created_at'),
            class_name=class_info.get('name'),
            class_datetime_ist=class_info.get('datetime_ist'),
            instructor=class_info.get('instructor')
        )