from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime
import logging

from app.models.schemas import ClassResponse
from app.repositories.class_repository import ClassRepository
from app.utils.exceptions import (
    ValidationError, ClassNotFoundError, DatabaseError,
)
from app.utils.validators import TimezoneValidator, PaginationValidator
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["classes"])  


def get_class_repository() -> ClassRepository:
    return ClassRepository()

@router.get("/classes", response_model=List[ClassResponse])
async def get_classes(
    include_past: bool = Query(False),
    instructor: Optional[str] = Query(None),
    timezone: str = Query("IST"),
    class_repo: ClassRepository = Depends(get_class_repository)
):
    try:
        if instructor:
            classes = class_repo.get_classes_by_instructor(instructor)
        else:
            classes = class_repo.get_all_classes(include_past=include_past)
        
        response_classes = []
        for fitness_class in classes:
            class_data = {
                "id": str(fitness_class.id),
                "name": fitness_class.name,
                "instructor": fitness_class.instructor,
                "datetime_ist": fitness_class.datetime_ist.isoformat(),
                "duration_minutes": fitness_class.duration_minutes,
                "total_slots": fitness_class.total_slots,
                "available_slots": fitness_class.available_slots,
                "description": fitness_class.description
            }
            
            if timezone != "IST":
                try:
                    local_time = settings.convert_timezone(
                        fitness_class.datetime_ist, "IST", timezone
                    )
                    class_data["datetime_local"] = local_time.isoformat()
                except Exception as e:
                    logger.warning(f"Timezone conversion failed: {str(e)}")
                    class_data["datetime_local"] = fitness_class.datetime_ist.isoformat()
            else:
                class_data["datetime_local"] = fitness_class.datetime_ist.isoformat()
                
            response_classes.append(ClassResponse(**class_data))
            
        return response_classes
    except Exception as e:
        logger.error(f"Failed to get classes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve classes")


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class_by_id(
    class_id: str,
    timezone: str = Query("IST", description="Timezone for datetime display"),
    class_repo: ClassRepository = Depends(get_class_repository)
):
    try:
        if hasattr(TimezoneValidator, 'validate'):
            timezone = TimezoneValidator.validate(timezone)
        
        fitness_class = class_repo.get_class_by_id(class_id)
        if not fitness_class:
            raise ClassNotFoundError(class_id)
        
        class_data = {
            "id": str(fitness_class.id),
            "name": fitness_class.name,
            "instructor": fitness_class.instructor,
            "datetime_ist": fitness_class.datetime_ist.isoformat(),
            "duration_minutes": fitness_class.duration_minutes,
            "total_slots": fitness_class.total_slots,
            "available_slots": fitness_class.available_slots,
            "description": fitness_class.description
        }
        
        if timezone != "IST":
            try:
                local_time = settings.convert_timezone(
                    fitness_class.datetime_ist, "IST", timezone
                )
                class_data["datetime_local"] = local_time.isoformat()
            except Exception as e:
                logger.warning(f"Timezone conversion failed: {str(e)}")
                class_data["datetime_local"] = fitness_class.datetime_ist.isoformat()
        else:
            class_data["datetime_local"] = fitness_class.datetime_ist.isoformat()
        
        logger.info(f"Retrieved class {class_id} in timezone {timezone}")
        return ClassResponse(**class_data)
        
    except ClassNotFoundError as e:
        logger.warning(f"Class not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving class: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/classes/upcoming", response_model=List[ClassResponse])
async def get_upcoming_classes(
    timezone: str = Query("IST", description="Timezone for datetime display"),
    class_repo: ClassRepository = Depends(get_class_repository)
):
    try:    
        classes = class_repo.get_upcoming_classes()
        
        response_classes = []
        for fitness_class in classes:
            class_data = {
                "id": str(fitness_class.id),
                "name": fitness_class.name,
                "instructor": fitness_class.instructor,
                "datetime_ist": fitness_class.datetime_ist.isoformat(),
                "duration_minutes": fitness_class.duration_minutes,
                "total_slots": fitness_class.total_slots,
                "available_slots": fitness_class.available_slots,
                "description": fitness_class.description
            }
            response_classes.append(ClassResponse(**class_data))
        logger.info(f"Retrieved {len(response_classes)} upcoming classes in timezone {timezone}")
        return response_classes
    except Exception as e:
        logger.error(f"Failed to get upcoming classes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve upcoming classes")

@router.get("/health")
async def health_check():
    """Health check endpoint for classes API"""
    try:
        class_repo = ClassRepository()
        classes = class_repo.get_all_classes(include_past=True)
        
        return {
            "status": "healthy",
            "service": "classes",
            "timestamp": datetime.now().isoformat(),
            "timezone": "IST",
            "total_classes": len(classes)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")