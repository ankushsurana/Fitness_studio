from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from bson import ObjectId

from app.models.entities import Booking
from app.repositories.booking_repository import BookingRepository
from app.repositories.class_repository import ClassRepository
from app.utils.exceptions import (
    BookingNotFoundError,
    DatabaseError, 
    DuplicateBookingError, 
    ClassNotFoundError,
    ValidationError,
)
from app.utils.validators import BookingValidator
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class BookingService:
    def __init__(self):
        self.booking_repo = BookingRepository()
        self.class_repo = ClassRepository()
    
    def create_booking(self, class_id: str, client_name: str, client_email: str) -> Booking:
        try:
            if not ObjectId.is_valid(class_id):
                raise ValidationError("Invalid class ID format")
                
            fitness_class = self.class_repo.get_class_by_id(class_id)
            if not fitness_class:
                raise ClassNotFoundError(class_id)
            
            if fitness_class.available_slots <= 0:
                raise ValidationError("No available slots for this class")
                
            if self.booking_repo.check_duplicate_booking(class_id, client_email):
                raise DuplicateBookingError(class_id, client_email)
                
            booking = Booking(
                class_id=class_id,
                client_name=client_name,
                client_email=client_email,
                booking_time=datetime.utcnow(),
                status='confirmed',
                class_name=fitness_class.name,
                class_datetime_ist=fitness_class.datetime_ist,
                instructor=fitness_class.instructor
            )
            
            created_booking = self.booking_repo.create_booking(booking)
            
            new_slots = fitness_class.available_slots - 1
            if not self.class_repo.update_class_slots(class_id, new_slots):
                raise DatabaseError("Failed to update class slots")
                
            return created_booking
            
        except Exception as e:
            logger.error(f"Failed to create booking: {str(e)}")
            raise
    
    def get_bookings_by_email(
        self, 
        client_email: str, 
        include_cancelled: bool = False
    ) -> List[Booking]:
        logger.info(f"Retrieving bookings for {client_email}")
        
        if not client_email or not client_email.strip():
            raise ValidationError("Email address is required")
        
        normalized_email = client_email.strip().lower()
        bookings = self.booking_repo.get_bookings_by_email(
            normalized_email, 
            include_cancelled
        )
        logger.info(f"Found {len(bookings)} bookings for {client_email}")
        return bookings
    
    def get_booking_by_id(self, booking_id: str) -> Optional[Booking]:
        logger.info(f"Retrieving booking {booking_id}")
        return self.booking_repo.get_booking_by_id(booking_id)

    def cancel_booking(self, booking_id: str) -> bool:
        logger.info(f"Cancelling booking {booking_id}")
        
        booking = self.booking_repo.get_booking_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id=booking_id)
        success = self.booking_repo.cancel_booking(booking_id)
        if success:
            fitness_class = self.class_repo.get_class_by_id(booking.class_id)
            if fitness_class:
                new_available_slots = fitness_class.available_slots + 1
                self.class_repo.update_class_slots(booking.class_id, new_available_slots)
            
            logger.info(f"Successfully cancelled booking {booking_id}")
        
        return success
    
    def get_bookings_by_class(self, class_id: str) -> List[Booking]:
        logger.info(f"Retrieving bookings for class {class_id}")
        
        fitness_class = self.class_repo.get_class_by_id(class_id)
        if not fitness_class:
            raise ClassNotFoundError(class_id)
        return self.booking_repo.get_bookings_by_class(class_id)
    
    def get_booking_stats(self) -> Dict[str, Any]:
        logger.info("Retrieving booking statistics")
        
        all_bookings = self.booking_repo.get_all_bookings(limit=-1)
        
        total_bookings = len(all_bookings)
        confirmed_bookings = sum(1 for b in all_bookings if b.status == 'confirmed')
        cancelled_bookings = sum(1 for b in all_bookings if b.status == 'cancelled')
        pending_bookings = sum(1 for b in all_bookings if b.status == 'pending')
        unique_clients = len(set(b.client_email for b in all_bookings))
        
        return {
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'pending_bookings': pending_bookings,
            'unique_clients': unique_clients,
            'confirmation_rate': (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0,
            'cancellation_rate': (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
        }