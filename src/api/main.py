from typing import List, Optional, Dict, Tuple, Any, Union, Set, Annotated
import json
from src.api.prompts import *
from fastapi import FastAPI, HTTPException, Query, Body, Depends, status
from src.services.generate import generate_translation, generate_definition, generate_examples, language_codes, codes_language, llm, embed
from src.core.database import Base, engine, get_db
from src.models import *
from src.services.crud import get_learning_profile
from src.models.schemas import TranslationRead as SchemaTranslationRead, ExamplesRead as SchemaExamplesRead, DefinitionRead as SchemaDefinitionRead, TranslationResponse, TranslationInput, ExamplesInput, DefinitionInput
from sqlalchemy.orm import Session, selectinload
from src.models.crud_schemas import (
    WordBase, WordRead, DictionaryBase, DictionaryRead, TranslationBase, TranslationRead, DefinitionBase, DefinitionRead,
    ExampleBase, ExampleRead, TextBase, TextRead, LearningProfileBase, LearningProfileRead, 
    UserBase, UserUpdate, Token, UserCreate, UserRead, LanguageBase, LanguageRead)
from fastapi.security import OAuth2PasswordRequestForm
import os
from src.services import auth
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from src.services import crud
from src.core.redis_dependency import get_redis
from src.core.redis_client import RedisClient
from src.core.logging_config import setup_logging, get_logger
from src.config.settings import settings

# Setup logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT
)

# Get logger for this module
logger = get_logger(__name__)

# Initialize FastAPI application with metadata for Swagger documentation
app = FastAPI(
    title="Personal Dictionary API",
    description="A comprehensive API for managing personal dictionaries and language learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

logger.info("FastAPI application initialized")


# -----------------------------------------------------------------------------
# Authentication & User Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """
    Register a new user in the system.
    
    This endpoint creates a new user account with the provided credentials.
    The email is normalized to lowercase, and uniqueness is enforced for both
    username and email addresses.
    
    Args:
        payload (UserCreate): User registration data including username, email, 
                             full name, and password
        db (Session): Database session dependency
        
    Returns:
        UserRead: The created user object (without password)
        
    Raises:
        HTTPException: 409 if username or email already exists
        
    Example:
        POST /register
        {
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }
    """
    return crud.register_user(db, payload)

@app.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)) -> Token:
    """
    Authenticate user and issue JWT access token.
    
    This endpoint implements OAuth2 password grant flow for user authentication.
    Upon successful authentication, it returns a JWT token that can be used
    for subsequent authenticated requests.
    
    Args:
        db (Session): Database session dependency
        form_data (OAuth2PasswordRequestForm): Form data containing username and password
        
    Returns:
        Token: JWT access token with token type
        
    Raises:
        HTTPException: 401 if authentication fails
        
    Example:
        POST /login
        Form data:
        - username: john_doe
        - password: securepassword123
    """
    return crud.login(db, form_data.username, form_data.password)

@app.get("/users/me", response_model=UserRead)
def read_user_me(current_user: Annotated[User, Depends(auth.get_current_active_user)]):
    """
    Get current authenticated user's profile information.
    
    This endpoint returns the profile of the currently authenticated user.
    It requires a valid JWT token in the Authorization header.
    
    Args:
        current_user (User): Current authenticated user (injected by dependency)
        
    Returns:
        UserRead: Current user's profile information
        
    Example:
        GET /users/me
        Authorization: Bearer <jwt_token>
    """
    return UserRead.model_validate(current_user)  

@app.get("/users/", response_model=UserRead)
def get_user_info(db: Session = Depends(get_db), 
                  user_id: Optional[int] = None, 
                  username: Optional[str] = None) -> UserRead:
    """
    Query user information by ID or username.
    
    This endpoint allows querying user information by either user ID or username.
    If both parameters are provided, both must match the same user.
    
    Args:
        db (Session): Database session dependency
        user_id (Optional[int]): User ID to search for
        username (Optional[str]): Username to search for
        
    Returns:
        UserRead: User profile information
        
    Raises:
        HTTPException: 400 if user not found or no search criteria provided
        
    Example:
        GET /users/?user_id=123
        GET /users/?username=john_doe
        GET /users/?user_id=123&username=john_doe
    """
    return crud.get_user_info(db, user_id=user_id, username=username)

@app.put("/update_user/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(auth.get_current_active_user)], 
    db: Session = Depends(get_db)
) -> UserRead:
    """
    Update current user's profile information.
    
    This endpoint allows the authenticated user to update their profile information.
    Only the current user can update their own profile (no user_id in request body).
    Password changes are not handled here - use a dedicated password change endpoint.
    
    Args:
        current_user (User): Current authenticated user (injected by dependency)
        db (Session): Database session dependency
        payload (UserUpdate): Fields to update (username, full_name, email, disabled)
        
    Returns:
        UserRead: Updated user profile information
        
    Raises:
        HTTPException: 400 if no fields to update, 409 if username/email already taken
        
    Example:
        PUT /update_user/me
        {
            "username": "new_username",
            "full_name": "New Full Name",
            "email": "newemail@example.com"
        }
    """
    return crud.update_current_user(db, current_user, payload)

@app.delete("/user_delete/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db),
    hard: bool = Query(
        False,
        description="If true, attempt a hard delete (requires FK cascades). Otherwise performs a soft delete by setting disabled=True."
    ),
) -> None:
    """
    Delete the current authenticated user.
    
    This endpoint provides two deletion modes:
    1. Soft delete (default): Sets disabled=True, keeps account and data (idempotent)
    2. Hard delete (hard=true): Removes the user row from database
    
    Args:
        current_user (User): Current authenticated user (injected by dependency)
        db (Session): Database session dependency
        hard (bool): If True, perform hard delete; if False, perform soft delete
        
    Returns:
        None: 204 No Content on success
        
    Raises:
        HTTPException: 409 if hard delete fails due to dependent records
        
    Example:
        DELETE /user_delete/me
        DELETE /user_delete/me?hard=true
    """
    return crud.delete_current_user(db, current_user, hard)

# -----------------------------------------------------------------------------
# Language Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_language", response_model=LanguageRead, status_code=status.HTTP_201_CREATED)
def create_language(language: LanguageBase, db: Session = Depends(get_db)) -> LanguageRead:
    """
    Create a new language in the system.
    
    This endpoint creates a language entry with the provided name and automatically
    maps it to the appropriate language code using the predefined language_codes mapping.
    
    Args:
        language (LanguageBase): Language information (name and optional code)
        db (Session): Database session dependency
        
    Returns:
        LanguageRead: Created language object
        
    Raises:
        HTTPException: 400 if language name is invalid, 409 if language already exists
        
    Example:
        POST /create_language
        {
            "name": "English"
        }
    """
    return crud.create_language(db, language)

# -----------------------------------------------------------------------------
# Learning Profile Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_learning_profile", response_model=LearningProfileRead, status_code=status.HTTP_201_CREATED)
def create_learning_profile(
    learning_profile: LearningProfileBase, 
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
) -> LearningProfileRead:
    """
    Create a learning profile for the current user.
    
    This endpoint creates a learning profile that defines a language pair for the user.
    Each user can have multiple learning profiles, but the combination of
    (user_id, primary_language_id, foreign_language_id) must be unique.
    
    Args:
        db (Session): Database session dependency
        learning_profile (LearningProfileBase): Learning profile configuration
        current_user (User): Current authenticated user (injected by dependency)
        
    Returns:
        LearningProfileRead: Created learning profile
        
    Raises:
        HTTPException: 409 if profile already exists for this language pair
        
    Example:
        POST /create_learning_profile
        {
            "primary_language_id": 1,
            "foreign_language_id": 2,
            "is_active": true
        }
    """
    return crud.create_learning_profile(db, learning_profile, current_user)

# -----------------------------------------------------------------------------
# Word Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_word", response_model=WordRead, status_code=status.HTTP_201_CREATED)
def create_word(word: WordBase, db: Session = Depends(get_db)) -> WordRead:
    """
    Create a new word in the system.
    
    This endpoint creates a word entry with the provided lemma and language.
    It automatically generates vector embeddings for semantic search capabilities.
    The combination of (lemma, language_id) must be unique.
    
    Args:
        word (WordBase): Word information (lemma and language_id)
        db (Session): Database session dependency
        
    Returns:
        WordRead: Created word object with embeddings
        
    Raises:
        HTTPException: 404 if language doesn't exist, 409 if word already exists
        
    Example:
        POST /create_word
        {
            "lemma": "hello",
            "language_id": 1
        }
    """
    return crud.create_word(db, word)

# -----------------------------------------------------------------------------
# Dictionary Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_in_dictionary", response_model=DictionaryRead, status_code=status.HTTP_201_CREATED)
def create_in_dictionary(
    dictionary: DictionaryBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db),
) -> DictionaryRead:
    """
    Add a word to the user's personal dictionary.
    
    This endpoint adds a word to the user's dictionary for a specific learning profile.
    It ensures that the learning profile belongs to the current user and prevents
    duplicate entries for the same word in the same learning profile.
    
    Args:
        dictionary (DictionaryBase): Dictionary entry information
        current_user (User): Current authenticated user (injected by dependency)
        db (Session): Database session dependency
        
    Returns:
        DictionaryRead: Created dictionary entry
        
    Raises:
        HTTPException: 403 if learning profile doesn't belong to user, 409 if word already in dictionary
        
    Example:
        POST /create_in_dictionary
        {
            "learning_profile_id": 1,
            "word_id": 5,
            "notes": "Important word to remember"
        }
    """
    return crud.create_in_dictionary(db, dictionary, current_user)

# -----------------------------------------------------------------------------
# Translation Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_translation", response_model=TranslationRead, status_code=status.HTTP_201_CREATED)
def create_translation(
    translation: TranslationBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db),
) -> TranslationRead:
    """
    Create a translation for a dictionary entry.
    
    This endpoint creates a translation row that is attached to a dictionary entry.
    It ensures that the dictionary entry belongs to the current user and validates
    that the specified language exists.
    
    Args:
        translation (TranslationBase): Translation information
        current_user (User): Current authenticated user (injected by dependency)
        db (Session): Database session dependency
        
    Returns:
        TranslationRead: Created translation
        
    Raises:
        HTTPException: 404 if language or dictionary entry not found, 403 if dictionary doesn't belong to user
        
    Example:
        POST /create_translation
        {
            "translation": "hola",
            "language_id": 2,
            "dictionary_id": 10
        }
    """
    return crud.create_translation(db, translation, current_user)

# -----------------------------------------------------------------------------
# Text Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_text", response_model=TextRead, status_code=status.HTTP_201_CREATED)
def create_text(
    text: TextBase,
    current_user: Annotated["User", Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
) -> TextRead:
    """
    Create a new text entry for the current authenticated user.
    
    This endpoint creates a new Text object and associates it with the user's
    active LearningProfile. The text can optionally be linked to a dictionary entry.
    
    Args:
        text (TextBase): Text content and optional dictionary_id
        current_user (User): Current authenticated user (injected by dependency)
        db (Session): Database session dependency
        
    Returns:
        TextRead: Created text object
        
    Raises:
        HTTPException: 400 if no active learning profile or database error
        
    Example:
        POST /create_text
        {
            "learning_profile_id": 1,
            "dictionary_id": 5,
            "text": "Hello, how are you today?"
        }
    """
    learning_profile_id = get_learning_profile(db, current_user)
    return crud.create_text(db, text, learning_profile_id)

# -----------------------------------------------------------------------------
# AI-Powered Generation Endpoints
# -----------------------------------------------------------------------------

@app.post("/translate", response_model=SchemaTranslationRead)
def translate_text(text: TranslationInput):
    """
    Generate translations for words in a given text.
    
    This endpoint uses AI to extract content words from the input text and
    generate translations from the source language to the target language.
    
    Args:
        text (TranslationInput): Input text and language pair information
        
    Returns:
        SchemaTranslationRead: Translation results with word mappings
        
    Example:
        POST /translate
        {
            "text": "Hello world",
            "src_language": "English",
            "tgt_language": "Spanish"
        }
    """
    return generate_translation(text.text, text.src_language, text.tgt_language)

@app.post("/definition", response_model=Dict[str, Any])
def definitions(text: DefinitionInput):
    """
    Generate definition for a word in a specified language.
    
    This endpoint uses AI to generate a definition for the given word,
    optionally considering the provided context.
    
    Args:
        text (DefinitionInput): Word, language, and optional context
        
    Returns:
        Dict[str, Any]: Definition results
        
    Example:
        POST /definition
        {
            "word": "hello",
            "language": "English",
            "context": "Hello, how are you?"
        }
    """
    return generate_definition(text.word, text.language, text.context)

@app.post("/examples", response_model=SchemaExamplesRead)
def examples(text: ExamplesInput):
    """
    Generate usage examples for a word in a specified language.
    
    This endpoint uses AI to generate example sentences for the given word,
    optionally using the provided definition as context.
    
    Args:
        text (ExamplesInput): Word, language, number of examples, and optional definition
        
    Returns:
        SchemaExamplesRead: Generated examples
        
    Raises:
        HTTPException: 500 if example generation fails
        
    Example:
        POST /examples
        {
            "word": "hello",
            "language": "English",
            "examples_number": 3,
            "definition": "A greeting"
        }
    """
    try:
        return generate_examples(text.word, text.language, text.examples_number, text.definition)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating examples: {str(e)}")

# -----------------------------------------------------------------------------
# Redis Cache Endpoints
# -----------------------------------------------------------------------------

# Redis dependency

@app.post("/cache/set")
def set_cache_data(
    key: str = Body(..., embed=True),
    value: Any = Body(..., embed=True),
    expiration: Optional[int] = Body(3600, embed=True),  # Default 1 hour
    redis: RedisClient = Depends(get_redis)
):
    """
    Set data in Redis cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expiration: Expiration time in seconds (default: 3600)
        redis: Redis client dependency
        
    Returns:
        Dict: Operation result
    """
    success = redis.set(key, value, ex=expiration)
    return {
        "success": success,
        "key": key,
        "expiration": expiration
    }

@app.get("/cache/get/{key}")
def get_cache_data(
    key: str,
    redis: RedisClient = Depends(get_redis)
):
    """
    Get data from Redis cache.
    
    Args:
        key: Cache key
        redis: Redis client dependency
        
    Returns:
        Any: Cached value or None if not found
    """
    value = redis.get(key)
    return {
        "key": key,
        "value": value,
        "exists": value is not None
    }

@app.delete("/cache/delete/{key}")
def delete_cache_data(
    key: str,
    redis: RedisClient = Depends(get_redis)
):
    """
    Delete data from Redis cache.
    
    Args:
        key: Cache key
        redis: Redis client dependency
        
    Returns:
        Dict: Operation result
    """
    deleted_count = redis.delete(key)
    return {
        "success": deleted_count > 0,
        "key": key,
        "deleted_count": deleted_count
    }

@app.get("/cache/exists/{key}")
def check_cache_exists(
    key: str,
    redis: RedisClient = Depends(get_redis)
):
    """
    Check if a key exists in Redis cache.
    
    Args:
        key: Cache key
        redis: Redis client dependency
        
    Returns:
        Dict: Existence check result
    """
    exists_count = redis.exists(key)
    ttl = redis.ttl(key) if exists_count > 0 else -2
    
    return {
        "key": key,
        "exists": exists_count > 0,
        "ttl": ttl
    }

@app.post("/cache/hash/set")
def set_hash_data(
    hash_name: str = Body(..., embed=True),
    data: Dict[str, Any] = Body(..., embed=True),
    redis: RedisClient = Depends(get_redis)
):
    """
    Set hash data in Redis cache.
    
    Args:
        hash_name: Hash name
        data: Dictionary of field-value pairs
        redis: Redis client dependency
        
    Returns:
        Dict: Operation result
    """
    fields_set = redis.hset(hash_name, data)
    return {
        "success": fields_set > 0,
        "hash_name": hash_name,
        "fields_set": fields_set
    }

@app.get("/cache/hash/get/{hash_name}")
def get_hash_data(
    hash_name: str,
    field: Optional[str] = Query(None),
    redis: RedisClient = Depends(get_redis)
):
    """
    Get hash data from Redis cache.
    
    Args:
        hash_name: Hash name
        field: Specific field to get (optional, gets all if not specified)
        redis: Redis client dependency
        
    Returns:
        Dict: Hash data
    """
    if field:
        value = redis.hget(hash_name, field)
        return {
            "hash_name": hash_name,
            "field": field,
            "value": value,
            "exists": value is not None
        }
    else:
        data = redis.hgetall(hash_name)
        return {
            "hash_name": hash_name,
            "data": data,
            "field_count": len(data)
        }

@app.post("/cache/list/push")
def push_to_list(
    list_name: str = Body(..., embed=True),
    values: List[Any] = Body(..., embed=True),
    redis: RedisClient = Depends(get_redis)
):
    """
    Push values to a Redis list.
    
    Args:
        list_name: List name
        values: Values to push
        redis: Redis client dependency
        
    Returns:
        Dict: Operation result
    """
    pushed_count = redis.lpush(list_name, *values)
    return {
        "success": pushed_count > 0,
        "list_name": list_name,
        "pushed_count": pushed_count
    }

@app.get("/cache/list/get/{list_name}")
def get_list_data(
    list_name: str,
    start: int = Query(0),
    end: int = Query(-1),
    redis: RedisClient = Depends(get_redis)
):
    """
    Get data from a Redis list.
    
    Args:
        list_name: List name
        start: Start index
        end: End index
        redis: Redis client dependency
        
    Returns:
        Dict: List data
    """
    data = redis.lrange(list_name, start, end)
    return {
        "list_name": list_name,
        "data": data,
        "count": len(data),
        "range": f"{start}:{end}"
    }

@app.post("/cache/set/add")
def add_to_set(
    set_name: str = Body(..., embed=True),
    values: List[Any] = Body(..., embed=True),
    redis: RedisClient = Depends(get_redis)
):
    """
    Add values to a Redis set.
    
    Args:
        set_name: Set name
        values: Values to add
        redis: Redis client dependency
        
    Returns:
        Dict: Operation result
    """
    added_count = redis.sadd(set_name, *values)
    return {
        "success": added_count > 0,
        "set_name": set_name,
        "added_count": added_count
    }

@app.get("/cache/set/get/{set_name}")
def get_set_data(
    set_name: str,
    redis: RedisClient = Depends(get_redis)
):
    """
    Get data from a Redis set.
    
    Args:
        set_name: Set name
        redis: Redis client dependency
        
    Returns:
        Dict: Set data
    """
    data = redis.smembers(set_name)
    return {
        "set_name": set_name,
        "data": list(data),
        "count": len(data)
    }

@app.get("/cache/health")
def redis_health_check(redis: RedisClient = Depends(get_redis)):
    """
    Health check for Redis connection.
    
    Args:
        redis: Redis client dependency
        
    Returns:
        Dict: Health status
    """
    try:
        # Test connection by setting and getting a test key
        test_key = "health_check_test"
        test_value = {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
        
        redis.set(test_key, test_value, ex=10)  # Expire in 10 seconds
        retrieved_value = redis.get(test_key)
        redis.delete(test_key)
        
        return {
            "status": "healthy",
            "redis_url": redis.url,
            "test_passed": retrieved_value == test_value
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "redis_url": redis.url
        }

