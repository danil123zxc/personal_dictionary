# Project Structure

This document describes the reorganized structure of the Personal Dictionary application.

## 📁 Directory Structure

```
personal_dictionary/
├── src/                          # Main source code
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── nodes.py             # LangGraph workflow nodes
│   │   └── prompts.py           # AI prompts
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── database.py          # Database configuration
│   │   ├── redis_client.py      # Redis client wrapper
│   │   └── redis_dependency.py  # FastAPI Redis dependency
│   ├── config/                   # Configuration
│   │   ├── __init__.py
│   │   └── settings.py          # Application settings
│   ├── models/                   # Data models and schemas
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   └── crud_schemas.py      # CRUD operation schemas
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication service
│   │   ├── crud.py              # Database operations
│   │   └── generate.py          # AI generation service
│   └── utils/                    # Utility functions
│       └── __init__.py
├── scripts/                      # Utility scripts
│   ├── __init__.py
│   └── test_redis.py            # Redis testing script
├── examples/                     # Example code
│   ├── __init__.py
│   └── example_usage.py         # Usage examples
├── docs/                         # Documentation
│   └── PROJECT_STRUCTURE.md     # This file
├── tests/                        # Test files
│   ├── conftest.py
│   ├── test_crud.py
│   └── README.md
├── db/                          # Database files
│   └── init/
├── alembic/                     # Database migrations
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── compose.yaml                 # Docker services
├── Dockerfile                   # Application container
└── README.md                    # Project documentation
```

## 🏗️ Architecture Overview

### **API Layer (`src/api/`)**
- **FastAPI application** with all endpoints
- **LangGraph workflow nodes** for AI processing
- **AI prompts** for language generation

### **Core (`src/core/`)**
- **Database configuration** and connection management
- **Redis client** with connection pooling and error handling
- **FastAPI dependencies** for dependency injection

### **Configuration (`src/config/`)**
- **Centralized settings** using Pydantic BaseSettings
- **Environment variable management**
- **Type-safe configuration** with validation

### **Models (`src/models/`)**
- **SQLAlchemy models** for database tables
- **Pydantic schemas** for API requests/responses
- **CRUD schemas** for database operations

### **Services (`src/services/`)**
- **Authentication service** with JWT tokens
- **Database operations** (CRUD)
- **AI generation service** for translations, definitions, etc.

### **Scripts (`scripts/`)**
- **Utility scripts** for testing and maintenance
- **Redis testing** and validation

### **Examples (`examples/`)**
- **Usage examples** and demonstrations
- **Code samples** for common operations

## 🔄 Migration Guide

### **Old Structure → New Structure**

| Old Path | New Path | Description |
|----------|----------|-------------|
| `app/main.py` | `src/api/main.py` | FastAPI application |
| `app/models.py` | `src/models/models.py` | Database models |
| `app/schemas.py` | `src/models/schemas.py` | Pydantic schemas |
| `app/crud_schemas.py` | `src/models/crud_schemas.py` | CRUD schemas |
| `app/crud.py` | `src/services/crud.py` | Database operations |
| `app/auth.py` | `src/services/auth.py` | Authentication |
| `app/generate.py` | `src/services/generate.py` | AI generation |
| `app/database.py` | `src/core/database.py` | Database config |
| `app/redis_client.py` | `src/core/redis_client.py` | Redis client |
| `app/redis_dependency.py` | `src/core/redis_dependency.py` | Redis dependency |
| `app/nodes.py` | `src/api/nodes.py` | Workflow nodes |
| `app/prompts.py` | `src/api/prompts.py` | AI prompts |

### **Import Updates**

All import statements have been updated to use the new structure:

```python
# Old imports
from app.models import User
from app.crud import get_user
from app.database import get_db

# New imports
from src.models.models import User
from src.services.crud import get_user
from src.core.database import get_db
```

## 🚀 Running the Application

### **Development**
```bash
# Run with the new structure
python main.py
```

### **Docker**
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### **Testing**
```bash
# Run tests
pytest tests/

# Test Redis
python scripts/test_redis.py
```

## 📝 Benefits of New Structure

1. **Better Organization**: Clear separation of concerns
2. **Scalability**: Easy to add new modules and features
3. **Maintainability**: Related code is grouped together
4. **Testability**: Easier to test individual components
5. **Configuration**: Centralized settings management
6. **Documentation**: Clear structure for documentation

## 🔧 Configuration

The application now uses a centralized configuration system:

```python
from src.config.settings import settings

# Access configuration
database_url = settings.DATABASE_URL
redis_url = settings.REDIS_URL
secret_key = settings.SECRET_KEY
```

## 📚 Next Steps

1. **Update remaining imports** in any files that haven't been migrated
2. **Add type hints** throughout the codebase
3. **Create comprehensive tests** for each module
4. **Add API documentation** using FastAPI's built-in features
5. **Implement logging** configuration
6. **Add monitoring** and health checks
