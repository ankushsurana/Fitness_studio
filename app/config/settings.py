import os
from datetime import datetime
from typing import Optional, List
from functools import lru_cache
import pytz


class Settings:    
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb+srv://ankush:ankush@fitness.ifansw0.mongodb.net/?retryWrites=true&w=majority&appName=Fitness")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "Fitness") # Added database name setting
    
    BOOKING_ADVANCE_HOURS: int = int(os.getenv("BOOKING_ADVANCE_HOURS", "1"))
    MIN_CLASS_DURATION: int = int(os.getenv("MIN_CLASS_DURATION", "15"))
    MAX_CLASS_DURATION: int = int(os.getenv("MAX_CLASS_DURATION", "180"))
    MAX_CLASS_CAPACITY: int = int(os.getenv("MAX_CLASS_CAPACITY", "50"))
    
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"  # IST
    VALID_TIMEZONES: List[str] = [
        'UTC', 'Asia/Kolkata', 'US/Pacific', 'US/Eastern', 'US/Central', 'US/Mountain',
        'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai',
        'Australia/Sydney', 'America/New_York', 'America/Los_Angeles'
    ]
    
    BUSINESS_START_HOUR: int = 6
    BUSINESS_END_HOUR: int = 22
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    def now(self, timezone_name: str = None) -> datetime:
        if timezone_name is None:
            timezone_name = self.DEFAULT_TIMEZONE
        
        if timezone_name == "IST":
            timezone_name = self.DEFAULT_TIMEZONE
        
        tz = pytz.timezone(timezone_name)
        return datetime.now(tz).replace(tzinfo=None)
    
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        if from_tz == "IST":
            from_tz = self.DEFAULT_TIMEZONE
        if to_tz == "IST":
            to_tz = self.DEFAULT_TIMEZONE
        
        from_timezone = pytz.timezone(from_tz)
        to_timezone = pytz.timezone(to_tz)
        
        localized_dt = from_timezone.localize(dt)
        
        converted_dt = localized_dt.astimezone(to_timezone)
        
        return converted_dt.replace(tzinfo=None)
    
    def is_valid_timezone(self, timezone_name: str) -> bool:
        if timezone_name == "IST":
            return True
        return timezone_name in self.VALID_TIMEZONES
    
    def get_valid_timezones(self) -> List[str]:
        return ["IST"] + self.VALID_TIMEZONES
    
    def is_business_hours(self, dt: datetime, timezone_name: str = None) -> bool:
        if timezone_name is None:
            timezone_name = self.DEFAULT_TIMEZONE
        
        if timezone_name != "IST" and timezone_name != self.DEFAULT_TIMEZONE:
            dt = self.convert_timezone(dt, timezone_name, "IST")
        
        hour = dt.hour
        return self.BUSINESS_START_HOUR <= hour < self.BUSINESS_END_HOUR


@lru_cache()
def get_settings() -> Settings:
    return Settings()