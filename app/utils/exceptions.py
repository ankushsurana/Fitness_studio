
from typing import Optional, Dict, Any

class BookingError(Exception):
    """Base exception for booking-related errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BookingError):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ClassNotFoundError(BookingError):
    """Exception when class is not found"""
    
    def __init__(self, class_id: int):
        super().__init__(
            message=f"Class with ID {class_id} not found",
            status_code=404,
            error_code="CLASS_NOT_FOUND",
            details={"class_id": class_id}
        )


class DuplicateBookingError(BookingError):
    """Exception when trying to book the same class twice"""
    
    def __init__(self, class_id: int, client_email: str):
        super().__init__(
            message=f"Client {client_email} has already booked this class",
            status_code=409,
            error_code="DUPLICATE_BOOKING",
            details={
                "class_id": class_id,
                "client_email": client_email
            }
        )


class PastClassBookingError(BookingError):
    """Exception when trying to book a past class"""
    
    def __init__(self, class_id: int, class_name: str, class_datetime: str):
        super().__init__(
            message=f"Cannot book past class '{class_name}' scheduled for {class_datetime}",
            status_code=400,
            error_code="PAST_CLASS_BOOKING",
            details={
                "class_id": class_id,
                "class_name": class_name,
                "class_datetime": class_datetime
            }
        )


class BookingNotFoundError(BookingError):
    """Exception when booking is not found"""
    
    def __init__(self, booking_id: Optional[int] = None, client_email: Optional[str] = None):
        if booking_id:
            message = f"Booking with ID {booking_id} not found"
            details = {"booking_id": booking_id}
        elif client_email:
            message = f"No bookings found for email {client_email}"
            details = {"client_email": client_email}
        else:
            message = "Booking not found"
            details = {}
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="BOOKING_NOT_FOUND",
            details=details
        )


class InvalidTimezoneError(ValidationError):
    """Exception for invalid timezone"""
    
    def __init__(self, timezone: str, valid_timezones: list):
        super().__init__(
            message=f"Invalid timezone '{timezone}'. Valid timezones: {', '.join(valid_timezones)}",
            details={
                "provided_timezone": timezone,
                "valid_timezones": valid_timezones
            }
        )


class DatabaseError(BookingError):
    """Exception for database-related errors"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=500,
            error_code="DATABASE_ERROR",
            details={"operation": operation} if operation else {}
        )
