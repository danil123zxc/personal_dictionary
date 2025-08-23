from typing import List, Optional, Dict, Tuple, Any, Union, Set, Annotated
import json
from app.prompts import *
from fastapi import FastAPI, HTTPException, Query, Body, Depends, status
from app.generate import generate_translation, generate_definition, generate_examples, language_codes, codes_language, llm
from app.database import Base, engine, get_db
from app.models import *
from app.schemas import TranslationRead, ExamplesRead, DefinitionRead, TranslationResponse, TranslationInput, ExamplesInput, DefinitionInput
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

app = FastAPI()

db_dependency = Annotated[Session, Depends(get_db)]

# -----------------------------------------------------------------------------
# Auth & Users
# -----------------------------------------------------------------------------

@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: db_dependency)-> UserRead:
    """
    Register a new user.

    - Normalizes email to lowercase.
    - Checks uniqueness on username/email.
    - Hashes password using auth.get_password_hash.
    """
    #Normalizing email
    email_norm = payload.email.strip().lower()
    #Checking if user with the same username of email already exists
    existing_user = db.query(User).filter(
        (User.username == payload.username) |
        (User.email == email_norm)
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")
    #Adding user to the db
    db_user = User(username=payload.username, 
                   full_name=payload.full_name, 
                   email=email_norm, 
                   password=auth.get_password_hash(payload.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()])-> Token:
    """
    OAuth2 password grant login.
    - Authenticates user by username/password.
    - Issues JWT with `sub` = user.id (string).
    - Make sure `auth.get_current_user` decodes `sub` as user_id.
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Incorrect username or password", 
                            headers={"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},  
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserRead)
def read_user_me(current_user: Annotated[User, Depends(auth.get_current_active_user)]):
    """
    Return the current authenticated user (Pydantic model).
    """
    return UserRead.model_validate(current_user)  

@app.get("/users/", response_model=UserRead)
def get_user_info(db: db_dependency, 
                  user_id: Optional[int]=None, 
                  username: Optional[str]=None)-> UserRead:
    """
    Query a user by id or username. If both provided, both must match the same user.

    Returns:
        404 if not found,
        400 if neither filter is provided.
    """
    if user_id and username:
        user = db.query(User).filter((User.username == username) &
                                       (User.id == user_id)).first()
    elif user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif username:
        user = db.query(User).filter(User.username == username).first()


    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return user

@app.put("/update_user/me", response_model=UserRead)
def update_current_user(current_user: Annotated[User, Depends(auth.get_current_active_user)], 
                        db: db_dependency,
                        payload: UserUpdate)-> UserRead:
    """
    Update current user's profile (partial update).

    Allowed fields:
      - username, full_name, email

    Security:
      - Works only for the authenticated user (no user_id in body).
      - Does not handle password changes (use a dedicated /change_password endpoint).

    Validations:
      - username/email uniqueness across users (409 on conflict).
      - username min length 3 if provided.
    """
    # 0) Guard: nothing to update
    if payload.username is None and payload.full_name is None and payload.email is None and payload.disabled is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # 1) Uniqueness checks (only when field provided and changed)
    if payload.username and payload.username != current_user.username:
        exists = db.query(User).filter(User.username == payload.username).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    if payload.email and payload.email != current_user.email:
        exists = db.query(User).filter(User.email == payload.email).first()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # 2) Apply changes
    if payload.username is not None:
        current_user.username = payload.username
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.email is not None:
        current_user.email = payload.email
    if payload.disabled is not None:
        current_user.disabled = payload.disabled

    # 3) Persist
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    # 4) Return safe public model
    return UserRead.model_validate(current_user)

@app.delete("/user_delete/me",status_code=status.HTTP_204_NO_CONTENT)
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

    Modes
    -----
    - Soft delete (default): set `disabled=True`, keep the account/data (idempotent).
    - Hard delete (`?hard=true`): remove the `users` row. Requires ON DELETE CASCADE (DB) or ORM cascade;
      otherwise returns 409 if dependent rows exist (learning profiles, dictionaries, etc.).
    """
    if not hard:
        # Soft delete (idempotent)
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
# Languages
# -----------------------------------------------------------------------------

@app.post("/create_language", response_model=LanguageRead, status_code=status.HTTP_201_CREATED)
def create_language(language: LanguageBase, db: db_dependency) -> LanguageRead:
    """
    Create a language from its name (and optional code).

    Validations:
      - `language_codes` maps human-readable names to codes; if not found -> 400.
      - Enforces uniqueness on name/code.
    """
    # 1) Map name to code
    code = language_codes.get(language.name)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid language"
        )
    
    # 2) Check uniqueness
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
    
    # 3) Create new language
    db_language = Language(name=language.name, code=code)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)

    return LanguageRead.model_validate(db_language, from_attributes=True)
# -----------------------------------------------------------------------------
# Learning Profiles
# -----------------------------------------------------------------------------

@app.post("/create_learning_profile", response_model=LearningProfileRead, status_code=status.HTTP_201_CREATED)
def create_learning_profile(
    db: db_dependency,
    learning_profile: LearningProfileBase, 
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
) -> LearningProfileRead:
    """
    Create a learning profile for the current user.

    Security:
      - Ignore `user_id` from request body and use `current_user.id`.

    Uniqueness:
      - (user_id, primary_language_id, foreign_language_id) should be unique.
    """

    # 1) Check if profile already exists for this user with same lang pair
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

    # 2) Create new profile
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
# Words
# -----------------------------------------------------------------------------

@app.post("/create_word", response_model=WordRead, status_code=status.HTTP_201_CREATED)
def create_word(
    word: WordBase, 
    db: db_dependency
) -> WordRead:
    """
    Create a Word by (lemma, language_id).

    Validations:
      - The referenced language_id must exist.
      - (lemma, language_id) pair must be unique.
    """

    # 1) Validate language exists
    language = db.query(Language).filter(Language.id == word.language_id).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language doesn't exist"
        )

    # 2) Check duplicates
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

    # 3) Create new word
    db_word = Word(lemma=word.lemma, language_id=language.id)
    db.add(db_word)
    db.commit()
    db.refresh(db_word)

    return WordRead.model_validate(db_word, from_attributes=True)
# -----------------------------------------------------------------------------
# Dictionary
# -----------------------------------------------------------------------------


@app.post("/create_in_dictionary", response_model=DictionaryRead, status_code=status.HTTP_201_CREATED)
def create_in_dictionary(
    dictionary: DictionaryBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: db_dependency,
) -> DictionaryRead:
    """
    Add a word to the user's dictionary for a specific learning_profile.

    Security:
      - Verify the referenced learning_profile belongs to current_user.

    Race-safety:
      - Prefer a UNIQUE constraint on (learning_profile_id, word_id).
      - Handle IntegrityError on commit to avoid TOCTOU races.
    """
    # 1) Ensure LP belongs to current user
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

    # 2) Check if entry already exists
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

    # 3) Create
    create_dictionary = Dictionary(**dictionary.model_dump())
    db.add(create_dictionary)
    db.commit()
    db.refresh(create_dictionary)
    return DictionaryRead.model_validate(create_dictionary, from_attributes=True)

# -----------------------------------------------------------------------------
# Translation
# -----------------------------------------------------------------------------
@app.post("/create_translation", response_model=TranslationRead, status_code=status.HTTP_201_CREATED)
def create_translation(
    translation: TranslationBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
    db: db_dependency,
) -> TranslationRead:
    """
    Create a Translation row attached to a dictionary entry.

    Security:
      - Ensure the dictionary entry belongs to the current user via learning_profile.user_id.

    Validations:
      - language_id must exist
      - dictionary_id must exist and belong to user
    """
    # Validate language
    lang = db.query(Language).filter(Language.id == translation.language_id).first()
    if lang is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )

    # Validate dictionary + ownership
    dic = (
        db.query(Dictionary)
        .options(selectinload(Dictionary.learning_profile))
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

    # Create row
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
# Text
# -----------------------------------------------------------------------------
@app.post("/create_text", response_model=TextRead, status_code=status.HTTP_201_CREATED)
def create_text(
    text: TextBase,
    current_user: Annotated["User", Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
) -> TextRead:
    """
        Create a new text for the current authenticated user.

        This endpoint creates a new `Text` object and associates it with the user's
        active `LearningProfile`. The text can optionally be linked to a dictionary entry.

        Parameters
        ----------
        text : TextBase
            The request body containing the text content and (optionally) a dictionary_id.
        current_user : User
            The authenticated user making the request. Injected by dependency `get_current_active_user`.
        db : Session
            The database session used to persist the new text.

        Returns
        -------
        TextRead
            The newly created `Text` object, serialized into the response schema.

        Raises
        ------
        HTTPException
            - 400 BAD REQUEST: If the user does not have an active learning profile,
            or if the text violates uniqueness constraints
            (`learning_profile_id + text` must be unique).
            - 401 UNAUTHORIZED: If the user is not authenticated.
            - 500 INTERNAL SERVER ERROR: If an unexpected database error occurs.

        Status Codes
        ------------
        - **201 Created**: Text was successfully created.
        - **400 Bad Request**: Invalid request (e.g., no active learning profile).
        - **401 Unauthorized**: Authentication failed.

        Example Request
        ---------------
        ```json
        {
        "learning_profile_id": 1,
        "dictionary_id": 1,
        "text": "Hello, there!"
        }
        ```

        Example Response
        ----------------
        ```json
        {
        "id": 101,
        "text": "나는 밥을 먹는다",
        "dictionary_id": 42,
        "learning_profile_id": 5,
        "created_at": "2025-08-23T10:00:00Z",
        "updated_at": "2025-08-23T10:00:00Z"
        }
        ```
    """
    # 1. Get active learning profile of current user
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

    # 2. Create new Text instance
    new_text = Text(
        text=text.text,
        dictionary_id=text.dictionary_id,  # can be None if not provided
        learning_profile_id=learning_profile.id
    )

    # 3. Add and commit
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
    



@app.post("/translate", response_model=TranslationRead)
def translate_text(text: TranslationInput):
    return generate_translation(text.text, text.src_language, text.tgt_language)

@app.post("/definition", response_model=DefinitionRead)
def definitions(text: DefinitionInput):
    return generate_definition(text.word, text.language, text.context)

@app.post("/examples", response_model=ExamplesRead)
def examples(text: ExamplesInput):
    try:
        return generate_examples(text.word, text.language, text.examples_number, text.definition)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating examples: {str(e)}")

