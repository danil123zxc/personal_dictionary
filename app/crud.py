from __future__ import annotations

from typing import Annotated, Optional, Dict, Any, List
from sqlalchemy.orm import Session, selectinload
from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.crud_schemas import (
    WordBase, WordRead, DictionaryBase, DictionaryRead, TranslationBase, TranslationRead,
    DefinitionBase, DefinitionRead, ExampleBase, ExampleRead, TextBase, TextRead,
    LearningProfileBase, LearningProfileRead, UserBase, UserUpdate, Token, UserCreate, UserRead,
    LanguageBase, LanguageRead
)
from app.models import (
    User, Language, Word, LearningProfile, Dictionary, Translation, Definition, Example, Text
)
from app.database import get_db
from app import auth
from datetime import timedelta
from app.embeddings import embed
from pgvector.sqlalchemy import cosine_distance

db_dependency = Annotated[Session, Depends(get_db)]


def register_user(db: db_dependency, payload: UserCreate) -> UserRead:
    email_norm = payload.email.strip().lower()
    existing_user = db.query(User).filter(
        (User.username == payload.username) | (User.email == email_norm)
    ).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already registered")

    db_user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=email_norm,
        password=auth.get_password_hash(payload.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserRead.model_validate(db_user)


def login(db: db_dependency, username: str, password: str) -> Token:
    user = auth.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


def get_user_info(db: db_dependency, user_id: Optional[int] = None, username: Optional[str] = None) -> UserRead:
    if user_id and username:
        user = db.query(User).filter((User.username == username) & (User.id == user_id)).first()
    elif user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif username:
        user = db.query(User).filter(User.username == username).first()
    else:
        raise HTTPException(status_code=400, detail="Must provide either user_id or username")
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return UserRead.model_validate(user)


def update_current_user(db: db_dependency, current_user: User, payload: UserUpdate) -> UserRead:
    if (
        payload.username is None
        and payload.full_name is None
        and payload.email is None
        and payload.disabled is None
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if payload.username and payload.username != current_user.username:
        exists = db.query(User).filter(User.username == payload.username).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    if payload.email and payload.email != current_user.email:
        exists = db.query(User).filter(User.email == payload.email).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if payload.username is not None:
        current_user.username = payload.username
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.email is not None:
        current_user.email = payload.email
    if payload.disabled is not None:
        current_user.disabled = payload.disabled

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserRead.model_validate(current_user)


def delete_current_user(db: db_dependency, current_user: User, hard: bool) -> None:
    if not hard:
        if not current_user.disabled:
            current_user.disabled = True
            db.add(current_user)
            db.commit()
        return
    try:
        db.delete(current_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hard delete failed: related records exist. Enable cascade or remove dependents first.",
        )


def create_language(db: db_dependency, language: LanguageBase) -> LanguageRead:
    from app.generate import language_codes

    code = language_codes.get(language.name)
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid language")

    existing_language = (
        db.query(Language).filter((Language.name == language.name) | (Language.code == code)).first()
    )
    if existing_language:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Language already exists")

    db_language = Language(name=language.name, code=code)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return LanguageRead.model_validate(db_language, from_attributes=True)


def create_learning_profile(
    db: db_dependency, learning_profile: LearningProfileBase, current_user: User
) -> LearningProfileRead:
    learning_profile_db = (
        db.query(LearningProfile)
        .filter(
            (LearningProfile.user_id == current_user.id)
            & (LearningProfile.primary_language_id == learning_profile.primary_language_id)
            & (LearningProfile.foreign_language_id == learning_profile.foreign_language_id)
        )
        .first()
    )
    if learning_profile_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")

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


def create_word(db: db_dependency, word: WordBase) -> WordRead:
    language = db.query(Language).filter(Language.id == word.language_id).first()
    if not language:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language doesn't exist")

    exists = (
        db.query(Word)
        .filter((Word.lemma == word.lemma) & (Word.language_id == word.language_id))
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Word already exists")

    embedding_doc = embed(word.lemma)
    embedding = embedding_doc[0].metadata.get('embedding')
    embedding_model = embedding_doc[0].metadata.get('model')

    db_word = Word(
        lemma=word.lemma,
        language_id=language.id,
        embedding=embedding,
        embedding_model=embedding_model,
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return WordRead.model_validate(db_word, from_attributes=True)


def create_in_dictionary(
    db: db_dependency, dictionary: DictionaryBase, current_user: User
) -> DictionaryRead:
    lp = (
        db.query(LearningProfile)
        .filter(
            (LearningProfile.id == dictionary.learning_profile_id)
            & (LearningProfile.user_id == current_user.id)
        )
        .first()
    )
    if lp is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: profile doesn't belong to you")

    exists = (
        db.query(Dictionary)
        .filter(
            (Dictionary.learning_profile_id == dictionary.learning_profile_id)
            & (Dictionary.word_id == dictionary.word_id)
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This word already exists in your dictionary")

    create_dictionary = Dictionary(**dictionary.model_dump())
    db.add(create_dictionary)
    db.commit()
    db.refresh(create_dictionary)
    return DictionaryRead.model_validate(create_dictionary, from_attributes=True)


def create_translation(
    db: db_dependency, 
    translation: TranslationBase, current_user: User
) -> TranslationRead:
    lang = db.query(Language).filter(Language.id == translation.language_id).first()
    if lang is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")

    dic = (
        db.query(Dictionary)
        .options(selectinload(Dictionary.learning_profile))
        .filter(Dictionary.id == translation.dictionary_id)
        .first()
    )
    if dic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictionary entry not found")
    if dic.learning_profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: dictionary entry doesn't belong to you")

    row = Translation(
        dictionary_id=translation.dictionary_id,
        language_id=translation.language_id,
        translation=translation.translation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TranslationRead.model_validate(row, from_attributes=True)


def create_text(db: Session, text: TextBase, current_user: User) -> TextRead:
    learning_profile = (
        db.query(LearningProfile)
        .filter(LearningProfile.user_id == current_user.id, LearningProfile.is_active == True)
        .first()
    )
    if not learning_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active learning profile found for current user.")

    new_text = Text(
        text=text.text,
        dictionary_id=text.dictionary_id,
        learning_profile_id=learning_profile.id,
    )
    db.add(new_text)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create text: {str(e)}")
    db.refresh(new_text)
    return TextRead.model_validate(new_text, from_attributes=True)


def get_synonyms(
    db: Session,
    word: str,
    learning_profile_id: int,
    language_id: int,
    top_k: int = 10,
    min_similarity: Optional[float] = 0.7,
) -> List[WordRead]:
    """
    Retrieve semantically similar words to a base word, restricted to a specific
    learning profile and language, using pgvector cosine distance.

    Args:
        db: SQLAlchemy session
        word: The word to find similar words for
        learning_profile_id: Scope results to this learning profile's dictionary
        language_id: Scope results to this language
        top_k: Max number of neighbors to return

    Returns:
        List[WordRead]: Top-k nearest words as public schema models
    """

    # Get embedding for the query word
    try:
        word_embedding = embed(word)[0].metadata.get('embedding')
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not embed word: {str(e)}")

    query = (
        db.query(Word)
        .join(Dictionary, Dictionary.word_id == Word.id)
        .filter(
            Dictionary.learning_profile_id == learning_profile_id,
            Word.language_id == language_id,
            Word.lemma != word 
        )
    )

    # Since cosine_distance = 1 - cosine_similarity, this becomes distance <= 1 - min_similarity
    if not (0.0 <= min_similarity <= 1.0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="min_similarity must be between 0 and 1")
    max_distance = 1.0 - min_similarity
    
    # Single query with similarity threshold and ordering
    neighbors: List[Word] = (
        query
        .filter(cosine_distance(Word.embedding, word_embedding) <= max_distance)
        .order_by(cosine_distance(Word.embedding, word_embedding))
        .limit(top_k)
        .all()
    )  

    return [WordRead.model_validate(w, from_attributes=True) for w in neighbors]