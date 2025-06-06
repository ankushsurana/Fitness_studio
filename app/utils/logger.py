import logging
import sys
from datetime import datetime
from typing import Optional
import os

class CustomFormatter(logging.Formatter):
    
    COLORS = {
        'DEBUG': '\033[36m',    
        'INFO': '\033[32m',     
        'WARNING': '\033[33m', 
        'ERROR': '\033[31m',   
        'CRITICAL': '\033[35m', 
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return super().format(record)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', 'N/A')
        return True


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_colors: bool = True
) -> None:    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    if enable_colors and sys.stdout.isatty():
        console_formatter = CustomFormatter(
            fmt='%(timestamp)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s'
        )
    else:
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(console_handler)
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(RequestIdFilter())
        root_logger.addHandler(file_handler)
    
    app_logger = logging.getLogger('app')
    app_logger.setLevel(numeric_level)
    
    logging.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")


class LoggerMixin:    
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)


class LogContext:    
    def __init__(self, **context):
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


class TimedOperation:    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        duration_ms = duration.total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(f"Operation completed: {self.operation_name} ({duration_ms:.2f}ms)")
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name} ({duration_ms:.2f}ms) - {exc_val}"
            )