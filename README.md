# Fitness Studio Booking API

A robust FastAPI backend for managing fitness class schedules and bookings, using MongoDB Atlas for persistent storage.

## Features
- **View Classes:** List all upcoming fitness classes (Yoga, Zumba, HIIT, etc.) with instructor, time, and available slots.
- **Book a Class:** Clients can book a spot in a class by providing class ID, name, and email. Slot availability is validated.
- **View Bookings:** Retrieve all bookings for a specific client email.
- **Timezone Support:** All class times are stored in IST; API supports conversion to other timezones.
- **Input Validation:** Strong validation for emails, names, and booking logic.
- **Error Handling:** Custom exceptions for overbooking, invalid input, and business rules.
- **Logging:** Structured logging for all major operations.
- **Unit Tests:** Basic tests for endpoints and services.

## Tech Stack
- **Python 3.11+**
- **FastAPI**
- **MongoDB Atlas** (via `pymongo`)
- **Pydantic** for data validation
- **Uvicorn** for ASGI server

## API Endpoints

### Classes
- `GET /api/classes` — List all (upcoming) classes
- `GET /api/classes/{class_id}` — Get details for a specific class
- `GET /api/classes/upcoming` — List classes in the next 24 hours

### Bookings
- `POST /api/book` — Book a class (requires `class_id`, `client_name`, `client_email`)
- `GET /api/bookings?email=...` — List all bookings for a client
- `GET /api/bookings/{booking_id}` — Get booking details
- `DELETE /api/bookings/{booking_id}` — Cancel a booking

## Quickstart

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd Fictional_Fitness_Studio
```

### 2. Install dependencies
```sh
pip install -r requirements.txt
```

### 3. Configure Environment
- Copy `.env` and set your MongoDB Atlas connection string (`MONGO_URL`) and database name (`MONGO_DB_NAME`).

### 4. Run the API
```sh
python run.py
```
- The API will be available at [http://localhost:8000](http://localhost:8000)
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Example Booking Request
```json
POST /api/book
{
  "class_id": "<MongoDB_Class_ObjectId>",
  "client_name": "John Doe",
  "client_email": "john@example.com"
}
```

## Project Structure
```
app/
  api/           # FastAPI endpoints
  models/        # Pydantic and business entities
  repositories/  # MongoDB data access
  services/      # Business logic
  utils/         # Validation, logging, exceptions
  config/        # Settings and environment
run.py           # Application entry point
requirements.txt # Dependencies
.env             # Environment variables (not committed)
```