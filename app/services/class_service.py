from typing import List, Optional, Dict, Any
import logging

from app.models.entities import FitnessClass
from app.repositories.class_repository import ClassRepository
from app.repositories.booking_repository import BookingRepository
from app.utils.exceptions import ClassNotFoundError, ValidationError
from app.utils.validators import ClassValidator, DateTimeValidator
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ClassService:
    
    def __init__(self):
        self.class_repo = ClassRepository()
        self.booking_repo = BookingRepository()
    
    def get_all_classes(
        self,
        include_past: bool = False
    ) -> List[FitnessClass]:
        logger.info(f"Retrieving all classes (include_past: {include_past})")
        
        classes = self.class_repo.get_all_classes(include_past)
        
        logger.info(f"Retrieved {len(classes)} classes")
        return classes
    
    def get_class_by_id(self, class_id: int) -> Optional[FitnessClass]:
        logger.info(f"Retrieving class {class_id}")
        
        if class_id <= 0:
            raise ValidationError("Class ID must be a positive integer")
        
        fitness_class = self.class_repo.get_class_by_id(class_id)
        
        return fitness_class
    
    def get_upcoming_classes(
        self, 
        hours_ahead: int = 24
    ) -> List[FitnessClass]:
        logger.info(f"Retrieving upcoming classes for next {hours_ahead} hours")
        
        if hours_ahead <= 0:
            raise ValidationError("Hours ahead must be positive")
        
        classes = self.class_repo.get_upcoming_classes(hours_ahead)
        
        logger.info(f"Retrieved {len(classes)} upcoming classes")
        return classes
    
    def create_class(
        self,
        class_id: int,
        name: str,
        instructor: str,
        datetime_str: str,
        duration_minutes: int,
        total_slots: int,
        description: Optional[str] = None,
        timezone: str = "IST"
    ) -> FitnessClass:
        logger.info(f"Creating new class: {name} by {instructor}")
        
        parsed_datetime = DateTimeValidator.parse_datetime_string(datetime_str, timezone)
        
        if timezone != "IST":
            datetime_ist = settings.convert_timezone(parsed_datetime, timezone, "IST")
        else:
            datetime_ist = parsed_datetime
        
        validated_data = ClassValidator.validate_class_data(
            name=name,
            instructor=instructor,
            datetime_ist=datetime_ist,
            duration_minutes=duration_minutes,
            total_slots=total_slots,
            description=description
        )
        
        fitness_class = FitnessClass(
            id=None,
            class_id=class_id,
            name=validated_data['name'],
            instructor=validated_data['instructor'],
            datetime_ist=validated_data['datetime_ist'],
            duration_minutes=validated_data['duration_minutes'],
            total_slots=validated_data['total_slots'],
            available_slots=validated_data['total_slots'],
            description=validated_data['description']
        )
        
        created_class = self.class_repo.create_class(fitness_class)
        
        logger.info(f"Successfully created class {created_class.id}")
        return created_class
    
    def get_classes_by_instructor(
        self, 
        instructor: str
    ) -> List[FitnessClass]:
        logger.info(f"Retrieving classes for instructor: {instructor}")
        
        if not instructor or not instructor.strip():
            raise ValidationError("Instructor name is required")
        
        classes = self.class_repo.get_classes_by_instructor(instructor.strip())
        
        logger.info(f"Retrieved {len(classes)} classes for instructor {instructor}")
        return classes
    
    def update_class_slots(self, class_id: int, available_slots: int) -> bool:
        logger.info(f"Updating class {class_id} slots to {available_slots}")
        
        if class_id <= 0:
            raise ValidationError("Class ID must be a positive integer")
        
        if available_slots < 0:
            raise ValidationError("Available slots cannot be negative")
        
        fitness_class = self.class_repo.get_class_by_id(class_id)
        if not fitness_class:
            raise ClassNotFoundError(class_id)
        
        if available_slots > fitness_class.total_slots:
            raise ValidationError("Available slots cannot exceed total slots")
        
        return self.class_repo.update_class_slots(class_id, available_slots)
    
    def delete_class(self, class_id: int) -> bool:
        logger.info(f"Attempting to delete class {class_id}")
        
        if class_id <= 0:
            raise ValidationError("Class ID must be a positive integer")
        
        fitness_class = self.class_repo.get_class_by_id(class_id)
        if not fitness_class:
            raise ClassNotFoundError(class_id)
        
        booking_count = self.booking_repo.get_booking_count_by_class(class_id)
        if booking_count > 0:
            raise ValidationError(f"Cannot delete class with {booking_count} confirmed bookings")
        
        success = self.class_repo.delete_class(class_id)
        
        if success:
            logger.info(f"Successfully deleted class {class_id}")
        
        return success
    
    def get_class_with_booking_info(
        self,
        class_id: int
    ) -> Dict[str, Any]:
        logger.info(f"Retrieving class {class_id} with booking info")
        
        fitness_class = self.get_class_by_id(class_id)
        if not fitness_class:
            raise ClassNotFoundError(class_id)
        
        bookings = self.booking_repo.get_bookings_by_class(class_id)
        booking_count = len(bookings)
        
        return {
            'class': fitness_class,
            'booking_count': booking_count,
            'bookings': bookings,
            'is_full': fitness_class.is_full,
            'booking_percentage': fitness_class.booking_percentage
        }
    
    def get_class_stats(self) -> Dict[str, Any]:
        logger.info("Retrieving class statistics")
        
        all_classes = self.class_repo.get_all_classes(include_past=True)
        
        total_classes = len(all_classes)
        total_capacity = sum(c.total_slots for c in all_classes)
        total_booked = sum(c.total_slots - c.available_slots for c in all_classes)
        fully_booked_classes = sum(1 for c in all_classes if c.is_full)
        
        upcoming_classes = self.class_repo.get_all_classes(include_past=False)
        upcoming_count = len(upcoming_classes)
        
        return {
            'total_classes': total_classes,
            'upcoming_classes': upcoming_count,
            'total_capacity': total_capacity,
            'total_booked': total_booked,
            'available_slots': total_capacity - total_booked,
            'fully_booked_classes': fully_booked_classes,
            'utilization_rate': (total_booked / total_capacity * 100) if total_capacity > 0 else 0,
            'full_booking_rate': (fully_booked_classes / total_classes * 100) if total_classes > 0 else 0
        }
    
    def get_available_classes(self) -> List[FitnessClass]:
        logger.info("Retrieving classes with available slots")
        
        all_classes = self.get_all_classes(include_past=False)
        available_classes = [c for c in all_classes if c.available_slots > 0]
        
        logger.info(f"Found {len(available_classes)} classes with available slots")
        return available_classes