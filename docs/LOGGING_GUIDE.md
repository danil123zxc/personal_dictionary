# Logging Guide

This guide explains how logging works in the Personal Dictionary application and how to use it effectively.

## Table of Contents

1. [What is Logging?](#what-is-logging)
2. [Log Levels](#log-levels)
3. [How Logging Works in This Application](#how-logging-works-in-this-application)
4. [Using Loggers in Your Code](#using-loggers-in-your-code)
5. [Configuration](#configuration)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

## What is Logging?

Logging is a way to record information about what your application is doing. It's like keeping a diary of your application's activities. Logging helps you:

- **Debug problems** - See what happened when something goes wrong
- **Monitor performance** - Track how long operations take
- **Audit user actions** - Record what users are doing
- **Understand system behavior** - See the flow of your application

## Log Levels

Python logging has 5 levels, from least to most severe:

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed information for debugging | "Processing word 'hello' with embedding model 'sentence-transformers'"
| **INFO** | General information about program execution | "User 'john_doe' logged in successfully"
| **WARNING** | Something unexpected happened, but the program can continue | "Database connection slow, retrying..."
| **ERROR** | A more serious problem occurred | "Failed to connect to Redis server"
| **CRITICAL** | A critical problem that may prevent the program from running | "Database connection lost, cannot continue"

**Important**: Log levels are hierarchical. If you set the level to `INFO`, you'll see INFO, WARNING, ERROR, and CRITICAL messages, but not DEBUG messages.

## How Logging Works in This Application

### 1. Configuration Setup

The application uses a centralized logging configuration in `src/core/logging_config.py`:

```python
from src.core.logging_config import setup_logging, get_logger

# Setup logging at application startup
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT
)
```

### 2. Logger Creation

Each module gets its own logger:

```python
# In any module
from src.core.logging_config import get_logger

logger = get_logger(__name__)  # __name__ is the module name
```

### 3. Log Output

Logs are written to:
- **Console** (stdout) - for immediate viewing
- **File** (optional) - for persistent storage with rotation

## Using Loggers in Your Code

### Basic Usage

```python
import logging
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("User logged in")
logger.warning("Database connection slow")
logger.error("Failed to save data")
```

### Logging with Context

```python
# Log with additional context
logger.info("User action completed", extra={
    "user_id": 123,
    "action": "create_word",
    "word": "hello",
    "language": "English"
})
```

### Logging Exceptions

```python
try:
    # Some code that might fail
    result = database.save(data)
except Exception as e:
    logger.exception("Failed to save data")  # Includes stack trace
    # OR
    logger.error("Failed to save data", extra={
        "error_type": type(e).__name__,
        "data_id": data.id
    })
```

### Performance Logging

```python
import time

start_time = time.time()
# ... do some work ...
end_time = time.time()

logger.info("Operation completed", extra={
    "operation": "word_translation",
    "execution_time": end_time - start_time,
    "words_processed": 5
})
```

## Configuration

### Environment Variables

You can configure logging through environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Log file path (optional)
export LOG_FILE=logs/app.log

# Log file size limit (default: 10MB)
export LOG_MAX_BYTES=10485760

# Number of backup files (default: 5)
export LOG_BACKUP_COUNT=5
```

### Settings File

The configuration is defined in `src/config/settings.py`:

```python
class Settings(BaseSettings):
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    LOG_MAX_BYTES: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_BYTES")
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
```

## Best Practices

### 1. Use Descriptive Messages

```python
# Good
logger.info("User 'john_doe' created new word 'hello' in English")

# Bad
logger.info("Created word")
```

### 2. Include Relevant Context

```python
# Good
logger.info("Database query executed", extra={
    "query": "SELECT * FROM words WHERE language_id = 1",
    "execution_time": 0.045,
    "rows_returned": 15
})

# Bad
logger.info("Query done")
```

### 3. Use Appropriate Log Levels

```python
# DEBUG - Detailed debugging information
logger.debug("Processing word with embedding model", extra={
    "word": "hello",
    "model": "sentence-transformers",
    "embedding_dim": 384
})

# INFO - General information
logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})

# WARNING - Something unexpected but not critical
logger.warning("Database connection slow", extra={"response_time": 2.5})

# ERROR - Something went wrong
logger.error("Failed to save word", extra={"word": "hello", "error": str(e)})

# CRITICAL - Application may not be able to continue
logger.critical("Database connection lost", extra={"retry_count": 5})
```

### 4. Don't Log Sensitive Information

```python
# Good
logger.info("User authenticated", extra={"user_id": 123})

# Bad - Never log passwords, API keys, etc.
logger.info("User authenticated", extra={"password": "secret123"})
```

### 5. Use Structured Logging

```python
# Good - Machine-readable format
logger.info("API request", extra={
    "method": "POST",
    "endpoint": "/translate",
    "status_code": 200,
    "response_time": 1.234,
    "user_id": 123
})
```

## Examples

### Database Operations

```python
def create_word(db: Session, word: WordBase) -> WordRead:
    logger.info("Creating new word", extra={
        "word": word.lemma,
        "language_id": word.language_id
    })
    
    try:
        # ... create word logic ...
        logger.info("Word created successfully", extra={
            "word_id": word_db.id,
            "word": word.lemma
        })
        return WordRead.model_validate(word_db, from_attributes=True)
    except Exception as e:
        logger.error("Failed to create word", extra={
            "word": word.lemma,
            "error": str(e)
        })
        raise
```

### API Endpoints

```python
@app.post("/translate")
def translate_text(text: TranslationInput):
    logger.info("Translation request received", extra={
        "text_length": len(text.text),
        "src_language": text.src_language,
        "tgt_language": text.tgt_language
    })
    
    start_time = time.time()
    result = generate_translation(text.text, text.src_language, text.tgt_language)
    end_time = time.time()
    
    logger.info("Translation completed", extra={
        "execution_time": end_time - start_time,
        "words_translated": len(result.words)
    })
    
    return result
```

### Error Handling

```python
def connect_to_redis():
    try:
        redis_client = RedisClient()
        logger.info("Redis connection established")
        return redis_client
    except ConnectionError as e:
        logger.error("Failed to connect to Redis", extra={
            "redis_url": settings.REDIS_URL,
            "error": str(e)
        })
        raise
    except Exception as e:
        logger.exception("Unexpected error connecting to Redis")
        raise
```

## Troubleshooting

### Common Issues

1. **No logs appearing**
   - Check if logging is configured
   - Verify log level is set correctly
   - Ensure logger is created properly

2. **Too many logs**
   - Increase log level (e.g., from DEBUG to INFO)
   - Reduce logging in production

3. **Log files too large**
   - Enable log rotation
   - Reduce log level
   - Clean up old log files

4. **Missing context**
   - Use `extra` parameter for additional information
   - Include relevant IDs and metadata

### Debugging Logging Issues

```python
# Check if logging is working
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")

# Check logger configuration
print(f"Logger level: {logger.level}")
print(f"Logger handlers: {logger.handlers}")
```

### Testing Logging

```python
import logging
from unittest.mock import patch

def test_logging():
    with patch('logging.Logger.info') as mock_info:
        logger.info("Test message")
        mock_info.assert_called_once_with("Test message")
```

## Running the Logging Demo

To see logging in action, run the demonstration script:

```bash
python3 examples/simple_logging_demo.py
```

This will show you:
- Different log levels
- Structured logging
- Error logging
- Performance logging
- Best practices

The demo creates a log file at `logs/simple_demo.log` that you can examine to see the formatted output.

## Integration with Your Application

The logging system is already integrated into your application:

1. **FastAPI startup** - Logs application initialization
2. **Redis client** - Logs connection status and errors
3. **Database operations** - Can be added to CRUD functions
4. **API endpoints** - Can be added to track requests and responses

To add logging to new components, simply:

```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Then use logger.info(), logger.error(), etc.
```

This ensures consistent logging across your entire application!
