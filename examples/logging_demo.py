#!/usr/bin/env python3
"""
Logging Demonstration Script

This script demonstrates how logging works in Python applications.
It shows different log levels, structured logging, and error handling.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging_config import setup_logging, get_logger
from src.config.settings import settings

def demonstrate_logging():
    """Demonstrate various logging features."""
    
    # Setup logging
    setup_logging(
        log_level="DEBUG",
        log_file="logs/demo.log"
    )
    
    # Get loggers for different components
    main_logger = get_logger(__name__)
    user_logger = get_logger("user_actions")
    db_logger = get_logger("database")
    api_logger = get_logger("api")
    
    print("=== Logging Demonstration ===\n")
    
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
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
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
        "client_ip": "192.168.1.100",
        "user_agent": "curl/7.68.0"
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
    
    # 8. Log filtering by level
    print("8. Log Level Filtering:")
    # These will only show if log level is DEBUG
    main_logger.debug("This debug message will only appear if log level is DEBUG or lower")
    main_logger.debug("Another debug message with context", extra={
        "component": "word_processor",
        "stage": "embedding_generation"
    })
    print()
    
    print("=== Logging Demonstration Complete ===")
    print("Check the logs/demo.log file to see the logged messages!")

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

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    show_log_levels()
    show_logging_best_practices()
    print("\n" + "="*50 + "\n")
    demonstrate_logging()
