from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List
import re

class ClassResponse(BaseModel):
    id: str
    name: str
    instructor: str
    datetime_local: str = Field(..., description="Class date/time in requested timezone")
    datetime_ist: str = Field(..., description="Class date/time in IST")
    duration_minutes: int
    total_slots: int
    available_slots: int
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class ClassListResponse(BaseModel):
    classes: List[ClassResponse]
    total_count: int
    timezone: str = Field(default="IST", description="Timezone for datetime_local field")


class BookingRequest(BaseModel):
    class_id: str = Field(..., description="ID of the class to book")
    client_name: str = Field(..., min_length=2, max_length=100, description="Client's full name")
    client_email: EmailStr = Field(..., description="Client's email address")
    
    @validator('client_name')
    def validate_client_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Client name cannot be empty')
        
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v.strip()):
            raise ValueError('Client name contains invalid characters')
        
        return v.strip().title()

class BookingResponse(BaseModel):
    id: str
    class_id: str
    class_name: str
    class_datetime_local: str
    class_datetime_ist: str
    instructor: str
    client_name: str
    client_email: str
    booking_time: str
    status: str
    
    class Config:
        from_attributes = True

class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
    total_count: int
    client_email: str
    timezone: str = Field(default="IST")

class BookingSuccessResponse(BaseModel):
    message: str
    booking_id: str
    class_name: str
    class_datetime_local: str
    remaining_slots: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str

class TimezoneRequest(BaseModel):
    timezone: str = Field(default="IST", description="Target timezone (e.g., 'UTC', 'US/Pacific', 'IST')")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        valid_timezones = [
            'UTC', 'IST', 'US/Pacific', 'US/Eastern', 'US/Central', 'US/Mountain',
            'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai',
            'Australia/Sydney', 'America/New_York', 'America/Los_Angeles'
        ]
        
        if v not in valid_timezones:
            raise ValueError(f'Timezone must be one of: {", ".join(valid_timezones)}')
        
        return v

class ClassListRequest(TimezoneRequest):
    include_past: bool = Field(default=False, description="Include past classes")

class BookingListRequest(BaseModel):
    client_email: EmailStr = Field(..., description="Client's email address")
    timezone: str = Field(default="IST", description="Target timezone for datetime fields")
    include_cancelled: bool = Field(default=False, description="Include cancelled bookings")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        valid_timezones = [
            'UTC', 'IST', 'US/Pacific', 'US/Eastern', 'US/Central', 'US/Mountain',
            'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai',
            'Australia/Sydney', 'America/New_York', 'America/Los_Angeles'
        ]
        
        if v not in valid_timezones:
            raise ValueError(f'Timezone must be one of: {", ".join(valid_timezones)}')
        
        return v

class ClassCreate(BaseModel):
    name: str
    instructor: str
    datetime_ist: str
    duration_minutes: int
    total_slots: int
    description: Optional[str] = None

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    instructor: Optional[str] = None
    datetime_ist: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_slots: Optional[int] = None
    available_slots: Optional[int] = None
    description: Optional[str] = None