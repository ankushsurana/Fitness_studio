import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from email_validator import validate_email, EmailNotValidError
from bson import ObjectId

from app.utils.exceptions import ValidationError
from app.config.settings import get_settings

settings = get_settings()


class EmailValidator:
    
    @staticmethod
    def validate(email: str) -> str:
        if not email or not email.strip():
            raise ValidationError("Email address is required")
        
        try:
            validation = validate_email(email.strip())
            return validation.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email format: {str(e)}")
    
    @staticmethod
    def is_valid(email: str) -> bool:
        try:
            EmailValidator.validate(email)
            return True
        except ValidationError:
            return False


class NameValidator:
    
    NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-'\.]+$")
    MIN_LENGTH = 2
    MAX_LENGTH = 100
    
    @staticmethod
    def validate(name: str) -> str:
        if not name or not name.strip():
            raise ValidationError("Name is required")
        
        name = name.strip()
        
        if len(name) < NameValidator.MIN_LENGTH:
            raise ValidationError(f"Name must be at least {NameValidator.MIN_LENGTH} characters long")
        
        if len(name) > NameValidator.MAX_LENGTH:
            raise ValidationError(f"Name must not exceed {NameValidator.MAX_LENGTH} characters")
        
        if not NameValidator.NAME_PATTERN.match(name):
            raise ValidationError("Name contains invalid characters. Only letters, spaces, hyphens, apostrophes, and dots are allowed")
        
        if '  ' in name or '--' in name or "''" in name:
            raise ValidationError("Name contains consecutive spaces or special characters")
        
        return ' '.join(word.capitalize() for word in name.split())
    
    @staticmethod
    def is_valid(name: str) -> bool:
        try:
            NameValidator.validate(name)
            return True
        except ValidationError:
            return False


class DateTimeValidator:
    
    @staticmethod
    def validate_future_datetime(dt: datetime, min_advance_hours: int = None) -> None:
        if min_advance_hours is None:
            min_advance_hours = settings.BOOKING_ADVANCE_HOURS
        
        now = settings.now("IST")
        min_datetime = now + timedelta(hours=min_advance_hours)
        
        if dt <= now:
            raise ValidationError(f"DateTime must be in the future (current time: {now.strftime('%Y-%m-%d %H:%M:%S')} IST)")
        
        if dt < min_datetime:
            raise ValidationError(f"Booking must be made at least {min_advance_hours} hour(s) in advance")
    
    @staticmethod
    def validate_business_hours(dt: datetime, timezone_name: str = "IST") -> None:
        if not settings.is_business_hours(dt, timezone_name):
            local_dt = settings.convert_timezone(dt, "IST", timezone_name)
            raise ValidationError(f"Class time {local_dt.strftime('%H:%M')} is outside business hours (6 AM - 10 PM)")
    
    @staticmethod
    def parse_datetime_string(dt_str: str, timezone_name: str = "IST") -> datetime:
        if not dt_str or not dt_str.strip():
            raise ValidationError("DateTime string is required")
        
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
        ]
        
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str.strip(), fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            raise ValidationError(f"Invalid datetime format: {dt_str}. Expected format: YYYY-MM-DD HH:MM:SS")
        
        return dt


class ClassValidator:
    
    @staticmethod
    def validate_class_data(
        name: str,
        instructor: str,
        datetime_ist: datetime,
        duration_minutes: int,
        total_slots: int,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        errors = {}
        
        try:
            name = NameValidator.validate(name)
        except ValidationError as e:
            errors['name'] = str(e)
        
        try:
            instructor = NameValidator.validate(instructor)
        except ValidationError as e:
            errors['instructor'] = str(e)
        
        try:
            DateTimeValidator.validate_future_datetime(datetime_ist)
            DateTimeValidator.validate_business_hours(datetime_ist)
        except ValidationError as e:
            errors['datetime'] = str(e)
        
        if duration_minutes < settings.MIN_CLASS_DURATION:
            errors['duration'] = f"Class duration must be at least {settings.MIN_CLASS_DURATION} minutes"
        elif duration_minutes > settings.MAX_CLASS_DURATION:
            errors['duration'] = f"Class duration must not exceed {settings.MAX_CLASS_DURATION} minutes"
        
        if total_slots < 1:
            errors['total_slots'] = "Total slots must be at least 1"
        elif total_slots > settings.MAX_CLASS_CAPACITY:
            errors['total_slots'] = f"Total slots must not exceed {settings.MAX_CLASS_CAPACITY}"
        
        if description and len(description.strip()) > 500:
            errors['description'] = "Description must not exceed 500 characters"
        
        if errors:
            raise ValidationError("Class validation failed", details=errors)
        
        return {
            'name': name,
            'instructor': instructor,
            'datetime_ist': datetime_ist,
            'duration_minutes': duration_minutes,
            'total_slots': total_slots,
            'description': description.strip() if description else None
        }


class BookingValidator:
    
    @staticmethod
    def validate_booking_request(
        class_id: str,
        client_name: str,
        client_email: str
    ) -> Dict[str, Any]:
        errors = {}

        # Accept string ObjectId for MongoDB
        if not class_id or not ObjectId.is_valid(str(class_id)):
            errors['class_id'] = "Class ID must be a valid MongoDB ObjectId string"

        try:
            client_name = NameValidator.validate(client_name)
        except ValidationError as e:
            errors['client_name'] = str(e)

        try:
            client_email = EmailValidator.validate(client_email)
        except ValidationError as e:
            errors['client_email'] = str(e)

        if errors:
            raise ValidationError("Booking validation failed", details=errors)

        return {
            'class_id': class_id,
            'client_name': client_name,
            'client_email': client_email
        }


class TimezoneValidator:
    
    @staticmethod
    def validate(timezone_name: str) -> str:
        if not timezone_name or not timezone_name.strip():
            raise ValidationError("Timezone is required")
        
        timezone_name = timezone_name.strip()
        
        if not settings.is_valid_timezone(timezone_name):
            valid_timezones = settings.get_valid_timezones()
            raise ValidationError(
                f"Invalid timezone '{timezone_name}'. Valid timezones: {', '.join(valid_timezones)}",
                details={'valid_timezones': valid_timezones}
            )
        
        return timezone_name
    
    @staticmethod
    def is_valid(timezone_name: str) -> bool:
        try:
            TimezoneValidator.validate(timezone_name)
            return True
        except ValidationError:
            return False


class PaginationValidator:
    
    MAX_LIMIT = 100
    DEFAULT_LIMIT = 20
    
    @staticmethod
    def validate_pagination(page: int = 1, limit: int = DEFAULT_LIMIT) -> Dict[str, int]:
        errors = {}
        
        if not isinstance(page, int) or page < 1:
            errors['page'] = "Page must be a positive integer"
        
        if not isinstance(limit, int) or limit < 1:
            errors['limit'] = "Limit must be a positive integer"
        elif limit > PaginationValidator.MAX_LIMIT:
            errors['limit'] = f"Limit must not exceed {PaginationValidator.MAX_LIMIT}"
        
        if errors:
            raise ValidationError("Pagination validation failed", details=errors)
        
        return {
            'page': page,
            'limit': limit,
            'offset': (page - 1) * limit
        }

    @staticmethod
    def validate_limit_offset(limit: int, offset: int) -> Dict[str, int]:
        errors = {}

        if not isinstance(limit, int) or limit < 1:
            errors['limit'] = "Limit must be a positive integer"
        elif limit > PaginationValidator.MAX_LIMIT:
            errors['limit'] = f"Limit must not exceed {PaginationValidator.MAX_LIMIT}"

        if not isinstance(offset, int) or offset < 0:
            errors['offset'] = "Offset must be a non-negative integer"

        if errors:
            raise ValidationError("Pagination validation failed", details=errors)

        return {
            'limit': limit,
            'offset': offset
        }