from pymongo import MongoClient
from pymongo.database import Database
from contextlib import contextmanager
from datetime import datetime
import logging
import threading
from typing import Generator

from app.config.settings import get_settings
from app.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)
settings = get_settings()

_local = threading.local()

# def get_db_connection() -> Database:
    # if not hasattr(_local, 'client'):
        # _local.client = MongoClient(settings.MONGO_URL)
        # _local.db = _local.client[settings.MONGO_DB_NAME]
    # return _local.db

def get_db_connection() -> Database:
    if not hasattr(_local, 'client'):
        try:
            _local.client = MongoClient(settings.MONGO_URL, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
            _local.client.admin.command('ping')  # Test the connection
            _local.db = _local.client[settings.MONGO_DB_NAME]
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise DatabaseError("Failed to establish database connection")
    return _local.db

def get_db() -> Generator[Database, None, None]:
    db = get_db_connection()
    try:
        yield db
    finally:
        pass  

@contextmanager
def get_db_transaction():
    db = get_db_connection()
    session = _local.client.start_session()
    try:
        with session.start_transaction():
            yield db
            session.commit_transaction()
    except Exception as e:
        logger.error(f"Database transaction failed: {str(e)}")
        session.abort_transaction()
        raise
    finally:
        session.end_session()

def init_db():
    db = get_db_connection()
    
    try:
        if 'classes' not in db.list_collection_names():
            db.create_collection('classes')
        
        if 'bookings' not in db.list_collection_names():
            db.create_collection('bookings')
        
        classes_collection = db['classes']
        bookings_collection = db['bookings']
        
        classes_collection.create_index("datetime_ist")
        classes_collection.create_index("instructor")
        
        bookings_collection.create_index("client_email")
        bookings_collection.create_index("class_id")
        bookings_collection.create_index([("class_id", 1), ("client_email", 1)], unique=True)
        
        _insert_sample_data(db)
        logger.info("MongoDB database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

def _insert_sample_data(db: Database):
    classes_collection = db['classes']
    
    if classes_collection.count_documents({}) == 0:
        sample_classes = [
            {
                'name': 'Morning Yoga',
                'instructor': 'Sarah Johnson',
                'datetime_ist': datetime(2025, 6, 5, 7, 0, 0),
                'duration_minutes': 60,
                'total_slots': 20,
                'available_slots': 20,
                'description': 'Start your day with peaceful yoga session',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'High-Intensity HIIT',
                'instructor': 'Mark Davis',
                'datetime_ist': datetime(2025, 6, 5, 18, 0, 0),
                'duration_minutes': 45,
                'total_slots': 15,
                'available_slots': 15,
                'description': 'Intense cardio and strength training',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'Zumba Dance Fitness',
                'instructor': 'Maria Rodriguez',
                'datetime_ist': datetime(2025, 6, 6, 19, 0, 0),
                'duration_minutes': 60,
                'total_slots': 25,
                'available_slots': 25,
                'description': 'Fun Latin-inspired dance workout',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'Evening Yoga',
                'instructor': 'Sarah Johnson',
                'datetime_ist': datetime(2025, 6, 6, 20, 0, 0),
                'duration_minutes': 75,
                'total_slots': 18,
                'available_slots': 18,
                'description': 'Relaxing yoga session to end your day',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'Power HIIT',
                'instructor': 'Mike Thompson',
                'datetime_ist': datetime(2025, 6, 7, 6, 30, 0),
                'duration_minutes': 45,
                'total_slots': 12,
                'available_slots': 12,
                'description': 'Early morning high-intensity workout',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'Beginner Yoga',
                'instructor': 'Lisa Wang',
                'datetime_ist': datetime(2025, 6, 7, 10, 0, 0),
                'duration_minutes': 60,
                'total_slots': 20,
                'available_slots': 20,
                'description': 'Perfect for yoga beginners',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        classes_collection.insert_many(sample_classes)
        logger.info(f"Inserted {len(sample_classes)} sample classes")

def close_db_connections():
    if hasattr(_local, 'client'):
        _local.client.close()
        delattr(_local, 'client')
        delattr(_local, 'db')
        logger.info("MongoDB connections closed")