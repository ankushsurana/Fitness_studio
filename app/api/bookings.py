from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, EmailStr, Field
import logging

from app.services.booking_service import BookingService
from app.utils.exceptions import (
    BookingNotFoundError,
    DuplicateBookingError,
    ClassNotFoundError,
    ValidationError,
    DatabaseError
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bookings"])

class BookingRequest(BaseModel):
    class_id: str = Field(..., description="ID of the class to book")
    client_name: str = Field(..., min_length=2, max_length=100, description="Client's full name")
    client_email: EmailStr = Field(..., description="Client's email address")

class BookingResponse(BaseModel):
    id: str
    class_id: str
    client_name: str
    client_email: str
    booking_time: str
    status: str
    class_name: Optional[str] = None
    class_datetime: Optional[str] = None
    instructor: Optional[str] = None

class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
    total_count: int

class BookingStatsResponse(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    pending_bookings: int
    unique_clients: int
    confirmation_rate: float
    cancellation_rate: float

booking_service = BookingService()

def booking_to_response(booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        class_id=booking.class_id,
        client_name=booking.client_name,
        client_email=booking.client_email,
        booking_time=booking.booking_time.strftime('%Y-%m-%d %H:%M:%S') if booking.booking_time else '',
        status=booking.status,
        class_name=booking.class_name,
        class_datetime=booking.class_datetime_ist.strftime('%Y-%m-%d %H:%M:%S') if booking.class_datetime_ist else None,
        instructor=booking.instructor
    )

@router.post("/book", response_model=BookingResponse)
async def create_booking(booking_request: BookingRequest):
    try:
        logger.info(f"Creating booking request for class {booking_request.class_id}")
        booking = booking_service.create_booking(
            class_id=booking_request.class_id,
            client_name=booking_request.client_name,
            client_email=booking_request.client_email
        )
        
        logger.info(f"Successfully created booking {booking.id}")
        return booking_to_response(booking)
    except ClassNotFoundError as e:
        logger.warning(f"Class not found: {e}")
        raise HTTPException(status_code=404, detail=f"Class with ID {booking_request.class_id} not found")
    
    except DuplicateBookingError as e:
        logger.warning(f"Duplicate booking attempt: {e}")
        raise HTTPException(status_code=409, detail="You already have a booking for this class")
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your booking")
    
    except Exception as e:
        logger.error(f"Unexpected error creating booking: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/bookings", response_model=BookingListResponse)
async def get_bookings(
    email: EmailStr = Query(..., description="Client email address"),
    include_cancelled: bool = Query(False, description="Include cancelled bookings")
):
    try:
        logger.info(f"Retrieving bookings for email: {email}")
        
        bookings = booking_service.get_bookings_by_email(
            client_email=str(email),
            include_cancelled=include_cancelled
        )
        booking_responses = [booking_to_response(booking) for booking in bookings]
        
        logger.info(f"Retrieved {len(booking_responses)} bookings for {email}")
        return BookingListResponse(
            bookings=booking_responses,
            total_count=len(booking_responses)
        )
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving bookings")
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving bookings: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str = Path(..., description="Booking ID")):
    try:
        logger.info(f"Retrieving booking {booking_id}")
        
        booking = booking_service.get_booking_by_id(booking_id)
        
        if not booking:
            logger.warning(f"Booking {booking_id} not found")
            raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")
        
        return booking_to_response(booking)
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the booking")
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving booking: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str = Path(..., description="Booking ID")):
    try:
        logger.info(f"Cancelling booking {booking_id}")
        
        success = booking_service.cancel_booking(booking_id)
        
        if success:
            logger.info(f"Successfully cancelled booking {booking_id}")
            return {"message": f"Booking {booking_id} has been cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel booking")
            
    except BookingNotFoundError as e:
        logger.warning(f"Booking not found: {e}")
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while cancelling the booking")
    
    except Exception as e:
        logger.error(f"Unexpected error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/bookings-stats", response_model=BookingStatsResponse)
async def get_booking_stats():
    try:
        logger.info("Retrieving booking statistics")
        
        stats = booking_service.get_booking_stats()
        
        return BookingStatsResponse(**stats)
        
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving statistics")
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")