
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.api.classes import router as classes_router
from app.api.bookings import router as bookings_router
from app.models.database import init_db, get_db
from app.utils.exceptions import BookingError, ValidationError
from app.utils.logger import setup_logging
from app.config.settings import get_settings

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fitness Studio Booking API...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    logger.info("Shutting down Fitness Studio Booking API...")

app = FastAPI(
    title="Fitness Studio Booking API",
    description="A comprehensive API for managing fitness class bookings",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BookingError)
async def booking_error_handler(request: Request, exc: BookingError):
    """Handle booking-related errors"""
    logger.warning(f"Booking error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Booking Error",
            "message": exc.message,
            "error_code": exc.error_code
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

app.include_router(classes_router, prefix="/api", tags=["Classes"])
app.include_router(bookings_router, prefix="/api", tags=["Bookings"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Fitness Studio Booking API",
        "version": "1.0.0",
        "endpoints": {
            "classes": "/api/classes - Get all available classes",
            "book": "/api/book - Book a class",
            "bookings": "/api/bookings - Get bookings by email"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = next(get_db())
        db.command('ismaster')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": settings.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

