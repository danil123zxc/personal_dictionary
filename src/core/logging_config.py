import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from src.config.settings import settings

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configure logging for the application.
    
    This function sets up a comprehensive logging configuration that includes:
    - Console logging with colored output
    - File logging with rotation (optional)
    - Structured log format with timestamps
    - Different log levels for different components
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    
    # Create file handler if log_file is specified
    handlers = [console_handler]
    
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set specific log levels for external libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)

# Example usage and demonstration
if __name__ == "__main__":
    # Setup logging
    setup_logging(
        log_level="DEBUG",
        log_file="logs/app.log"
    )
    
    # Get loggers for different components
    logger = get_logger(__name__)
    redis_logger = get_logger("redis_client")
    db_logger = get_logger("database")
    api_logger = get_logger("api")
    
    # Demonstrate different log levels
    logger.debug("This is a debug message - detailed information for debugging")
    logger.info("This is an info message - general information about program execution")
    logger.warning("This is a warning message - something unexpected happened")
    logger.error("This is an error message - something went wrong")
    logger.critical("This is a critical message - program may not be able to continue")
    
    # Demonstrate structured logging
    logger.info("User action", extra={
        "user_id": 123,
        "action": "login",
        "ip_address": "192.168.1.1"
    })
    
    # Demonstrate exception logging
    try:
        1 / 0
    except Exception as e:
        logger.exception("An error occurred during calculation")
