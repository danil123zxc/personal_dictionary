from typing import List, Optional, Dict, Tuple, Any, Union, Set, Annotated
import json
from app.prompts import *
from fastapi import FastAPI, HTTPException, Query, Body, Depends, status
from app.generate import generate_translation, generate_definition, generate_examples, language_codes, codes_language, llm
from app.database import Base, engine, get_db
from app.models import *
from app.schemas import TranslationRead as SchemaTranslationRead, ExamplesRead as SchemaExamplesRead, DefinitionRead as SchemaDefinitionRead, TranslationResponse, TranslationInput, ExamplesInput, DefinitionInput
from sqlalchemy.orm import Session, selectinload
from app.crud_schemas import (
    WordBase, WordRead, DictionaryBase, DictionaryRead, TranslationBase, TranslationRead, DefinitionBase, DefinitionRead,
    ExampleBase, ExampleRead, TextBase, TextRead, LearningProfileBase, LearningProfileRead, 
    UserBase, UserUpdate, Token, UserCreate, UserRead, LanguageBase, LanguageRead)
from fastapi.security import OAuth2PasswordRequestForm
import os
from app import auth
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from app.embeddings import embed

# Initialize FastAPI application with metadata for Swagger documentation
app = FastAPI(
    title="Personal Dictionary API",
    description="A comprehensive API for managing personal dictionaries and language learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Type alias for database session dependency
db_dependency = Annotated[Session, Depends(get_db)]

# -----------------------------------------------------------------------------
# Authentication & User Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: db_dependency) -> UserRead:
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
    # Normalize email to lowercase for consistency
    email_norm = payload.email.strip().lower()
    
    # Check if user with the same username or email already exists
    existing_user = db.query(User).filter(
        (User.username == payload.username) |
        (User.email == email_norm)
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")
    
    # Create new user with hashed password
    db_user = User(
        username=payload.username, 
        full_name=payload.full_name, 
        email=email_norm, 
        password=auth.get_password_hash(payload.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
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
    # Authenticate user credentials
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password", 
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Generate JWT access token with expiration
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},  # Store user ID as string in JWT
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

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
def get_user_info(db: db_dependency, 
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
    # Build query based on provided parameters
    if user_id and username:
        # Both parameters provided - both must match
        user = db.query(User).filter(
            (User.username == username) & (User.id == user_id)
        ).first()
    elif user_id:
        # Search by user ID only
        user = db.query(User).filter(User.id == user_id).first()
    elif username:
        # Search by username only
        user = db.query(User).filter(User.username == username).first()
    else:
        # No search criteria provided
        raise HTTPException(status_code=400, detail="Must provide either user_id or username")

    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return user

@app.put("/update_user/me", response_model=UserRead)
def update_current_user(
    current_user: Annotated[User, Depends(auth.get_current_active_user)], 
    db: db_dependency,
    payload: UserUpdate
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
    # Guard: check if there are any fields to update
    if (payload.username is None and payload.full_name is None and 
        payload.email is None and payload.disabled is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # Check username uniqueness (only if username is being changed)
    if payload.username and payload.username != current_user.username:
        exists = db.query(User).filter(User.username == payload.username).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    # Check email uniqueness (only if email is being changed)
    if payload.email and payload.email != current_user.email:
        exists = db.query(User).filter(User.email == payload.email).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # Apply changes to user object
    if payload.username is not None:
        current_user.username = payload.username
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.email is not None:
        current_user.email = payload.email
    if payload.disabled is not None:
        current_user.disabled = payload.disabled

    # Persist changes to database
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    # Return safe public model (without password)
    return UserRead.model_validate(current_user)

@app.delete("/user_delete/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: db_dependency,
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
    if not hard:
        # Soft delete (idempotent) - just mark as disabled
        if not current_user.disabled:
            current_user.disabled = True
            db.add(current_user)
            db.commit()
        return  # 204 No Content

    # Hard delete (may fail if FK cascades aren't configured)
    try:
        db.delete(current_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hard delete failed: related records exist. Enable cascade or remove dependents first.",
        )

# -----------------------------------------------------------------------------
# Language Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_language", response_model=LanguageRead, status_code=status.HTTP_201_CREATED)
def create_language(language: LanguageBase, db: db_dependency) -> LanguageRead:
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
    # Map language name to ISO code using predefined mapping
    code = language_codes.get(language.name)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid language"
        )
    
    # Check if language already exists (by name or code)
    existing_language = (
        db.query(Language)
        .filter(
            (Language.name == language.name) | (Language.code == code)
        )
        .first()
    )

    if existing_language:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Language already exists"
        )
    
    # Create new language entry
    db_language = Language(name=language.name, code=code)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)

    return LanguageRead.model_validate(db_language, from_attributes=True)

# -----------------------------------------------------------------------------
# Learning Profile Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_learning_profile", response_model=LearningProfileRead, status_code=status.HTTP_201_CREATED)
def create_learning_profile(
    db: db_dependency,
    learning_profile: LearningProfileBase, 
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
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
    # Check if profile already exists for this user with same language pair
    learning_profile_db = (
        db.query(LearningProfile)
        .filter(
            (LearningProfile.user_id == current_user.id) &
            (LearningProfile.primary_language_id == learning_profile.primary_language_id) &
            (LearningProfile.foreign_language_id == learning_profile.foreign_language_id)
        )
        .first()
    )
    if learning_profile_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists"
        )

    # Create new learning profile
    created_lp = LearningProfile(
        user_id=current_user.id, 
        primary_language_id=learning_profile.primary_language_id,
        foreign_language_id=learning_profile.foreign_language_id,
        is_active=learning_profile.is_active,
    )

    db.add(created_lp)
    db.commit()
    db.refresh(created_lp)

    return LearningProfileRead.model_validate(created_lp, from_attributes=True)

# -----------------------------------------------------------------------------
# Word Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_word", response_model=WordRead, status_code=status.HTTP_201_CREATED)
def create_word(word: WordBase, db: db_dependency) -> WordRead:
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
    # Validate that the referenced language exists
    language = db.query(Language).filter(Language.id == word.language_id).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language doesn't exist"
        )

    # Check if word already exists for this language
    exists = (
        db.query(Word)
        .filter(
            (Word.lemma == word.lemma) &
            (Word.language_id == word.language_id)
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Word already exists"
        )
    
    # Generate vector embeddings for semantic search
    embedding_doc = embed(word.lemma)
    embedding = embedding_doc[0].metadata.get('embedding')  # Get actual vector
    embedding_model = embedding_doc[0].metadata.get('model')  # Get model name

    # Create new word with embeddings
    db_word = Word(
        lemma=word.lemma, 
        language_id=language.id, 
        embedding=embedding, 
        embedding_model=embedding_model
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)

    return WordRead.model_validate(db_word, from_attributes=True)

# -----------------------------------------------------------------------------
# Dictionary Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_in_dictionary", response_model=DictionaryRead, status_code=status.HTTP_201_CREATED)
def create_in_dictionary(
    dictionary: DictionaryBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: db_dependency,
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
    # Ensure the learning profile belongs to the current user
    lp = (
        db.query(LearningProfile)
        .filter(
            (LearningProfile.id == dictionary.learning_profile_id)
            & (LearningProfile.user_id == current_user.id)
        )
        .first()
    )
    if lp is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: profile doesn't belong to you"
        )

    # Check if word already exists in this learning profile's dictionary
    exists = (
        db.query(Dictionary)
        .filter(
            (Dictionary.learning_profile_id == dictionary.learning_profile_id)
            & (Dictionary.word_id == dictionary.word_id)
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This word already exists in your dictionary"
        )

    # Create new dictionary entry
    create_dictionary = Dictionary(**dictionary.model_dump())
    db.add(create_dictionary)
    db.commit()
    db.refresh(create_dictionary)
    return DictionaryRead.model_validate(create_dictionary, from_attributes=True)

# -----------------------------------------------------------------------------
# Translation Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/create_translation", response_model=TranslationRead, status_code=status.HTTP_201_CREATED)
def create_translation(
    translation: TranslationBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: db_dependency,
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
    # Validate that the language exists
    lang = db.query(Language).filter(Language.id == translation.language_id).first()
    if lang is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )

    # Validate dictionary entry exists and belongs to current user
    dic = (
        db.query(Dictionary)
        .options(selectinload(Dictionary.learning_profile))  # Eager load learning profile
        .filter(Dictionary.id == translation.dictionary_id)
        .first()
    )
    if dic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dictionary entry not found"
        )
    if dic.learning_profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: dictionary entry doesn't belong to you"
        )

    # Create translation entry
    row = Translation(
        dictionary_id=translation.dictionary_id,
        language_id=translation.language_id,
        translation=translation.translation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return TranslationRead.model_validate(row, from_attributes=True)

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
    # Get the user's active learning profile
    learning_profile = (
        db.query(LearningProfile)
        .filter(
            LearningProfile.user_id == current_user.id,
            LearningProfile.is_active == True
        )
        .first()
    )

    if not learning_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active learning profile found for current user."
        )

    # Create new Text instance
    new_text = Text(
        text=text.text,
        dictionary_id=text.dictionary_id,  # Can be None if not provided
        learning_profile_id=learning_profile.id
    )

    # Add and commit with error handling
    db.add(new_text)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create text: {str(e)}"
        )
    db.refresh(new_text)

    return TextRead.model_validate(new_text, from_attributes=True)

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

