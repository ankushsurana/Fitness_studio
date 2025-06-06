from datetime import datetime
from typing import Dict, List
import pytz
import logging

from app.config.settings import get_settings
from app.utils.exceptions import InvalidTimezoneError

logger = logging.getLogger(__name__)
settings = get_settings()

class TimezoneService:
    
    def __init__(self):
        self.default_timezone = settings.DEFAULT_TIMEZONE
        self.valid_timezones = settings.VALID_TIMEZONES
    
    def convert_class_datetime(self, datetime_ist: datetime, target_timezone: str) -> str:
        try:
            if target_timezone == "IST" or target_timezone == self.default_timezone:
                return datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
            
            if not self.is_valid_timezone(target_timezone):
                raise InvalidTimezoneError(target_timezone, self.get_valid_timezones())
            
            converted_dt = settings.convert_timezone(datetime_ist, self.default_timezone, target_timezone)
            return converted_dt.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.error(f"Error converting datetime to {target_timezone}: {str(e)}")
            return datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
    
    def convert_multiple_datetimes(self, datetimes_ist: List[datetime], target_timezone: str) -> List[str]:
        return [self.convert_class_datetime(dt, target_timezone) for dt in datetimes_ist]
    
    def parse_datetime_with_timezone(self, datetime_str: str, source_timezone: str) -> datetime:
        try:
            dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            
            # If source timezone is IST, return as is
            if source_timezone == "IST" or source_timezone == self.default_timezone:
                return dt
            
            # Convert from source timezone to default timezone
            return settings.convert_timezone(dt, source_timezone, self.default_timezone)
            
        except ValueError as e:
            logger.error(f"Error parsing datetime string: {datetime_str}")
            raise ValueError(f"Invalid datetime format: {datetime_str}")
        except Exception as e:
            logger.error(f"Error converting datetime from {source_timezone} to {self.default_timezone}: {str(e)}")
            raise
    
    def get_timezone_offset(self, timezone_name: str) -> str:
        try:
            if timezone_name == "IST":
                timezone_name = self.default_timezone
            
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            offset = now.strftime('%z')
            
            if offset:
                return f"{offset[:3]}:{offset[3:]}"
            return "+00:00"
            
        except Exception as e:
            logger.error(f"Error getting timezone offset for {timezone_name}: {str(e)}")
            return "+00:00"
    
    def get_timezone_info(self, timezone_name: str) -> Dict[str, str]:
        try:
            if timezone_name == "IST":
                timezone_name = self.default_timezone
            
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            
            return {
                "timezone": timezone_name,
                "display_name": timezone_name.replace('_', ' '),
                "offset": self.get_timezone_offset(timezone_name),
                "current_time": now.strftime('%Y-%m-%d %H:%M:%S'),
                "is_dst": bool(now.dst())
            }
            
        except Exception as e:
            logger.error(f"Error getting timezone info for {timezone_name}: {str(e)}")
            return {
                "timezone": timezone_name,
                "display_name": timezone_name,
                "offset": "+00:00",
                "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "is_dst": False
            }
    
    def is_valid_timezone(self, timezone_name: str) -> bool:
        if timezone_name == "IST":
            return True
        
        try:
            pytz.timezone(timezone_name)
            return timezone_name in self.valid_timezones
        except pytz.UnknownTimeZoneError:
            return False
    
    def get_valid_timezones(self) -> List[str]:
        return ["IST"] + self.valid_timezones