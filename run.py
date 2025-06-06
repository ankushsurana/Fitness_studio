
import uvicorn
import logging
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.logger import setup_logging
from app.config.settings import get_settings


def setup_environment():
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        level=settings.LOG_LEVEL,
        log_file=settings.LOG_FILE,
        enable_colors=True
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("FITNESS STUDIO BOOKING API")
    logger.info("=" * 60)
    logger.info(f"Database: {settings.MONGO_URL}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"Business Hours: {settings.BUSINESS_START_HOUR}:00 - {settings.BUSINESS_END_HOUR}:00")
    logger.info(f"Default Timezone: {settings.DEFAULT_TIMEZONE}")
    logger.info(f"Booking Advance Hours: {settings.BOOKING_ADVANCE_HOURS}")
    logger.info("=" * 60)


def main():
    try:
        setup_environment()
        
        host = os.getenv("HOST", "127.0.0.1")
        port = int(os.getenv("PORT", "8000"))
        reload = os.getenv("RELOAD", "true").lower() == "true"
        workers = int(os.getenv("WORKERS", "1"))
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Reload: {reload}, Workers: {workers}")
        
        # Configure uvicorn
        config = {
            "app": "app.main:app",
            "host": host,
            "port": port,
            "reload": reload,
            "log_level": "info",
            "access_log": True,
        }
        
        # Add workers only in production (not with reload)
        if not reload and workers > 1:
            config["workers"] = workers
        
        # Run the server
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Server stopped by user")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()