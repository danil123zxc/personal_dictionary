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
    UserBase, Token, UserCreate, UserRead, LanguageBase, LanguageRead)
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

@app.post("/login", response_model=Token)
def login(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()])-> Token:
    """
    OAuth2 password grant login.
    - Authenticates user by username/password.
    - Issues JWT with `sub` = user.id (string).
    - Make sure `auth.get_current_user` decodes `sub` as user_id.
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.id},  
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserRead)
def read_user_me(current_user: Annotated[User, Depends(auth.get_current_active_user)]):
    """
    Return the current authenticated user (Pydantic model).
    """
    return UserRead.model_validate(current_user, from_attributes=True) 

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

# -----------------------------------------------------------------------------
# Languages
# -----------------------------------------------------------------------------

@app.post("/create_language", response_model=LanguageRead)
def create_language(language: LanguageBase, db: db_dependency):
    """
    Create a language from its name (and optional code).
    - `language_codes` maps human-readable names to codes; if not found -> 400.
    - Enforces uniqueness on name/code.
    """
    code = language_codes.get(language.name)

    if not code:
        raise HTTPException(status_code=400, detail="Invalid language")
    
    existing_language = db.query(Language).filter(
        (Language.name == language.name) |
        (Language.code == code)
    ).first()

    if existing_language:
        raise HTTPException(status_code=409, detail="Language already exists")
    
    db_language = Language(name=language.name, code=code)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return LanguageRead.model_validate(db_language, from_attributes=True)

# -----------------------------------------------------------------------------
# Learning Profiles
# -----------------------------------------------------------------------------

@app.post("/create_learning_profile", response_model=LearningProfileRead)
def create_learning_profile(db: db_dependency, learning_profile: LearningProfileBase, 
                            current_user: Annotated[User, Depends(auth.get_current_active_user)])-> LearningProfileRead:
    """
    Create a learning profile for the current user.
    Security: ignore `user_id` from body and use `current_user.id`.
    Uniqueness: (user_id, primary_language_id, foreign_language_id) should be unique by convention.
    """
    learning_profile_db = db.query(LearningProfile).filter(LearningProfile.user_id == current_user.id &
                                     LearningProfile.primary_language_id == learning_profile.primary_language_id &
                                     LearningProfile.foreign_language_id == learning_profile.foreign_language_id).first()
    if learning_profile_db:
        raise HTTPException(status_code=400, detail="Profile already exists")
    created_lp = LearningProfile(user_id=current_user.id, 
                                 primary_language_id=learning_profile.primary_language_id,
                                 foreign_language_id=learning_profile.foreign_language_id,
                                 is_active=learning_profile.is_active)
    db.add(created_lp)
    db.commit()
    db.refresh(created_lp)
    return LearningProfileRead.model_validate(created_lp, from_attributes=True)
# -----------------------------------------------------------------------------
# Words
# -----------------------------------------------------------------------------

@app.post("/create_word", response_model=WordRead)
def create_word(word: WordBase, 
                db: db_dependency):
    """
    Create a Word by (lemma, language_id).
    - Checks duplicate (lemma, language_id).
    - Requires that the language_id exists.
    """

    language = db.query(Language).filter(Language.name == WordBase.language).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language doesn't exist")

    word = db.query(Word).filter(Word.lemma == WordBase.word)
    if word:
        raise HTTPException(status_code=409, detail="Word already exists")
    
    db_word = Word(lemma=WordBase.word, language=language)
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
        raise HTTPException(status_code=403, detail="Forbidden: profile doesn't belong to you")

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
        raise HTTPException(status_code=409, detail="This word already exists in your dictionary")

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
        raise HTTPException(status_code=404, detail="Language not found")

    # Validate dictionary + ownership
    dic = (
        db.query(Dictionary)
        .options(
            selectinload(Dictionary.learning_profile)
        )
        .filter(Dictionary.id == translation.dictionary_id)
        .first()
    )
    if dic is None:
        raise HTTPException(status_code=404, detail="Dictionary entry not found")
    if dic.learning_profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: dictionary entry doesn't belong to you")

    row = Translation(
        dictionary_id=translation.dictionary_id,
        language_id=translation.language_id,
        translation=translation.translation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # If you prefer to return ORM→DTO as-is:
    return TranslationRead.model_validate(row, from_attributes=True)


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

