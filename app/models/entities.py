from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FitnessClass:
    id: Optional[str] = None
    name: str = ""
    instructor: str = ""
    datetime_ist: datetime = None
    duration_minutes: int = 0
    total_slots: int = 0
    available_slots: int = 0
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.total_slots < 1:
            raise ValueError("Total slots must be at least 1")
        
        if self.available_slots < 0:
            raise ValueError("Available slots cannot be negative")
        
        if self.available_slots > self.total_slots:
            raise ValueError("Available slots cannot exceed total slots")
        
        if self.duration_minutes < 15:
            raise ValueError("Class duration must be at least 15 minutes")
    
    @property
    def is_full(self) -> bool:
        return self.available_slots == 0
    
    @property
    def booking_percentage(self) -> float:
        if self.total_slots == 0:
            return 0.0
        return ((self.total_slots - self.available_slots) / self.total_slots) * 100
    
    def can_book(self, slots_needed: int = 1) -> bool:
        return self.available_slots >= slots_needed
    
    def book_slot(self, slots: int = 1) -> bool:
        if not self.can_book(slots):
            return False
        
        self.available_slots -= slots
        return True
    
    def cancel_slot(self, slots: int = 1) -> bool:
        if self.available_slots + slots > self.total_slots:
            return False
        
        self.available_slots += slots
        return True


@dataclass
class Booking:
    id: Optional[str] = None
    class_id: Optional[str] = None
    client_name: str = ""
    client_email: str = ""
    booking_time: datetime = None
    class_name: Optional[str] = None
    class_datetime_ist: Optional[datetime] = None
    instructor: Optional[str] = None
    created_at: Optional[datetime] = None
    status: str = "confirmed"
    
    def __post_init__(self):
        valid_statuses = ["confirmed", "cancelled", "pending"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if not self.client_name or not self.client_name.strip():
            raise ValueError("Client name cannot be empty")
        
        if not self.client_email or not self.client_email.strip():
            raise ValueError("Client email cannot be empty")
    
    @property
    def is_active(self) -> bool:
        return self.status == "confirmed"
    
    def cancel(self) -> bool:
        if self.status == "confirmed":
            self.status = "cancelled"
            return True
        return False
    
    def confirm(self) -> bool:
        if self.status == "pending":
            self.status = "confirmed"
            return True
        return False