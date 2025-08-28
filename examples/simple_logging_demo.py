#!/usr/bin/env python3
"""
Simple Logging Demonstration

This script demonstrates how Python logging works without requiring
the full application dependencies.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

def setup_simple_logging(log_level="INFO", log_file=None):
    """Setup basic logging configuration."""
    
    # Convert string level to logging constant
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
    
    # Create handlers list
    handlers = [console_handler]
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True
    )

def demonstrate_logging():
    """Demonstrate various logging features."""
    
    print("=== Python Logging Demonstration ===\n")
    
    # Setup logging
    setup_simple_logging(log_level="DEBUG", log_file="logs/simple_demo.log")
    
    # Get loggers for different components
    main_logger = logging.getLogger(__name__)
    user_logger = logging.getLogger("user_actions")
    db_logger = logging.getLogger("database")
    api_logger = logging.getLogger("api")
    
    # 1. Basic logging levels
    print("1. Basic Logging Levels:")
    main_logger.debug("Debug: Detailed information for debugging")
    main_logger.info("Info: General information about program execution")
    main_logger.warning("Warning: Something unexpected happened")
    main_logger.error("Error: Something went wrong")
    main_logger.critical("Critical: Program may not be able to continue")
    print()
    
    # 2. Structured logging with context
    print("2. Structured Logging:")
    user_logger.info("User login successful", extra={
        "user_id": 123,
        "username": "john_doe",
        "ip_address": "192.168.1.100"
    })
    
    user_logger.info("User performed action", extra={
        "user_id": 123,
        "action": "create_word",
        "word": "hello",
        "language": "English"
    })
    print()
    
    # 3. Database operations logging
    print("3. Database Operations:")
    db_logger.info("Database connection established", extra={
        "database": "postgresql",
        "host": "localhost",
        "port": 5432
    })
    
    db_logger.info("Query executed", extra={
        "query": "SELECT * FROM words WHERE language_id = 1",
        "execution_time": 0.045,
        "rows_returned": 15
    })
    print()
    
    # 4. API request logging
    print("4. API Request Logging:")
    api_logger.info("API request received", extra={
        "method": "POST",
        "endpoint": "/translate",
        "client_ip": "192.168.1.100"
    })
    
    api_logger.info("API response sent", extra={
        "method": "POST",
        "endpoint": "/translate",
        "status_code": 200,
        "response_time": 1.234
    })
    print()
    
    # 5. Error logging with exceptions
    print("5. Error Logging:")
    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        main_logger.error("Division by zero error", extra={
            "operation": "division",
            "dividend": 10,
            "divisor": 0
        })
        main_logger.exception("Exception details:")
    
    try:
        # Simulate a database error
        raise ConnectionError("Database connection failed")
    except ConnectionError as e:
        db_logger.error("Database connection failed", extra={
            "database_url": "postgresql://localhost:5432/db",
            "retry_count": 3
        })
        db_logger.exception("Database error details:")
    print()
    
    # 6. Performance logging
    print("6. Performance Logging:")
    import time
    
    start_time = time.time()
    # Simulate some work
    time.sleep(0.1)
    end_time = time.time()
    
    api_logger.info("Operation completed", extra={
        "operation": "word_translation",
        "execution_time": end_time - start_time,
        "words_processed": 5
    })
    print()
    
    # 7. Conditional logging
    print("7. Conditional Logging:")
    debug_mode = True
    
    if debug_mode:
        main_logger.debug("Debug mode is enabled - showing detailed information")
        main_logger.debug("Processing word: 'hello'", extra={
            "word": "hello",
            "language": "English",
            "embedding_model": "sentence-transformers"
        })
    
    print("=== Logging Demonstration Complete ===")
    print("Check the logs/simple_demo.log file to see the logged messages!")

def show_log_levels():
    """Show what each log level means."""
    print("=== Log Levels Explained ===\n")
    
    levels = [
        ("DEBUG", "Detailed information for diagnosing problems"),
        ("INFO", "General information about program execution"),
        ("WARNING", "Something unexpected happened, but the program can continue"),
        ("ERROR", "A more serious problem occurred"),
        ("CRITICAL", "A critical problem that may prevent the program from running")
    ]
    
    for level, description in levels:
        print(f"{level:8} - {description}")
    
    print("\nLog levels are hierarchical:")
    print("DEBUG < INFO < WARNING < ERROR < CRITICAL")
    print("Setting a level will show that level and all levels above it.")

def show_logging_best_practices():
    """Show logging best practices."""
    print("\n=== Logging Best Practices ===\n")
    
    practices = [
        "Use descriptive log messages that explain what happened",
        "Include relevant context using the 'extra' parameter",
        "Use appropriate log levels (don't log everything as ERROR)",
        "Log exceptions with logger.exception() to include stack traces",
        "Use structured logging for machine-readable logs",
        "Configure log rotation to prevent log files from growing too large",
        "Set different log levels for different environments (DEBUG for dev, INFO for prod)",
        "Don't log sensitive information like passwords or API keys",
        "Use consistent log formats across your application",
        "Consider using log aggregation tools for production environments"
    ]
    
    for i, practice in enumerate(practices, 1):
        print(f"{i:2}. {practice}")

def show_logger_usage():
    """Show how to use loggers in your code."""
    print("\n=== How to Use Loggers in Your Code ===\n")
    
    print("1. Import logging and get a logger:")
    print("   import logging")
    print("   logger = logging.getLogger(__name__)")
    print()
    
    print("2. Use different log levels:")
    print("   logger.debug('Debug information')")
    print("   logger.info('General information')")
    print("   logger.warning('Warning message')")
    print("   logger.error('Error message')")
    print("   logger.critical('Critical error')")
    print()
    
    print("3. Log with context:")
    print("   logger.info('User action', extra={")
    print("       'user_id': 123,")
    print("       'action': 'login',")
    print("       'ip_address': '192.168.1.1'")
    print("   })")
    print()
    
    print("4. Log exceptions:")
    print("   try:")
    print("       # Some code that might fail")
    print("       pass")
    print("   except Exception as e:")
    print("       logger.exception('An error occurred')")
    print()

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    show_log_levels()
    show_logging_best_practices()
    show_logger_usage()
    print("\n" + "="*50 + "\n")
    demonstrate_logging()
