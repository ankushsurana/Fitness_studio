from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.testclient import TestClient
import pytest

app = FastAPI()

# Pydantic models
class Booking(BaseModel):
    id: int
    name: str
    email: str
    room_type: str
    check_in: str
    check_out: str

# In-memory "database"
bookings_db = [
    Booking(id=1, name="John Doe", email="john.doe@example.com", room_type="single", check_in="2023-10-01", check_out="2023-10-05")
]

# FastAPI routes
@app.post("/api/book")
async def book_room(booking: Booking):
    bookings_db.append(booking)
    return {"message": "Booking successful", "booking_id": booking.id}

@app.get("/api/bookings")
async def get_bookings(email: Optional[str] = None):
    if email:
        return [booking for booking in bookings_db if booking.email == email]
    return bookings_db

# Test client
client = TestClient(app)

# Tests
def test_book_class_missing_fields():
    response = client.post("/api/book", json={})
    assert response.status_code == 422

def test_get_bookings_invalid_email():
    response = client.get("/api/bookings?email=notanemail")
    assert response.status_code in (400, 422)
