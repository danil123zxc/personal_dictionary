from __future__ import annotations

from typing import Annotated, Optional, Dict, Any, List
from sqlalchemy.orm import Session, selectinload
from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from src.models.crud_schemas import (
    WordBase, WordRead, DictionaryBase, DictionaryRead, TranslationBase, TranslationRead,
    DefinitionBase, DefinitionRead, ExampleBase, ExampleRead, TextBase, TextRead,
    LearningProfileBase, LearningProfileRead, UserBase, UserUpdate, Token, UserCreate, UserRead,
    LanguageBase, LanguageRead
)
from src.models.models import (
    User, Language, Word, LearningProfile, Dictionary, Translation, Definition, Example, Text
)
from src.core.database import get_db
from src.services import auth
from datetime import timedelta
from src.services.generate import embed, language_codes
from pgvector.sqlalchemy import Vector
from sqlalchemy import func, alias


def register_user(db: Session, payload: UserCreate) -> UserRead:
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


def login(db: Session, username: str, password: str) -> Token:
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


def get_user_info(db: Session, user_id: Optional[int] = None, username: Optional[str] = None) -> UserRead:
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


def delete_current_user(db: Session, current_user: User, hard: bool) -> None:
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


def create_language(db: Session, language: LanguageBase) -> LanguageRead:
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
    db: Session, 
    learning_profile: LearningProfileBase, 
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
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


def create_word(
    db: Session, 
    word: WordBase
    ) -> WordRead:
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
    db: Session, dictionary: DictionaryBase, current_user: Annotated[User, Depends(auth.get_current_active_user)]
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
    db: Session, 
    translation: TranslationBase, 
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
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


def create_text(
    db: Session, 
    text: TextBase, 
    learning_profile_id: int
    ) -> TextRead:

    new_text = Text(
        text=text.text,
        dictionary_id=text.dictionary_id,
        learning_profile_id=learning_profile_id,
    )
    db.add(new_text)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create text: {str(e)}")
    db.refresh(new_text)
    return TextRead.model_validate(new_text, from_attributes=True)

def create_definition(db: Session, definition: DefinitionBase) -> DefinitionRead:
    try:
        definition_db = Definition(**definition.model_dump())
        db.add(definition_db)
        db.commit()
        db.refresh(definition_db)
        return DefinitionRead.model_validate(definition_db, from_attributes=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create definition: {str(e)}")

def create_example(
    db: Session, 
    example: ExampleBase
) -> ExampleRead:
    try:
        example_db = Example(**example.model_dump())
        db.add(example_db)
        db.commit()
        db.refresh(example_db)
        return ExampleRead.model_validate(example_db, from_attributes=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not create example: {str(e)}")


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
    # Use 1 - cosine_similarity for distance calculation
    neighbors: List[Word] = (
        query
        .filter(func.cosine_distance(Word.embedding, word_embedding) <= max_distance)
        .order_by(func.cosine_distance(Word.embedding, word_embedding))
        .limit(top_k)
        .all()
    )  

    return [WordRead.model_validate(w, from_attributes=True) for w in neighbors]

def get_learning_profile(
    db: Session, 
    primary_language: str,
    foreign_language: str,
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
    ) -> LearningProfileRead:
    # Use aliases for the two language joins
    PrimaryLanguage = alias(Language)
    ForeignLanguage = alias(Language)
    
    learning_profile = (
        db.query(LearningProfile)
        .join(PrimaryLanguage, PrimaryLanguage.id == LearningProfile.primary_language_id)
        .join(ForeignLanguage, ForeignLanguage.id == LearningProfile.foreign_language_id)
        .filter(
            LearningProfile.user_id == current_user.id, 
            PrimaryLanguage.name == primary_language,
            ForeignLanguage.name == foreign_language,
            LearningProfile.is_active == True
        )
        .first()
    )
    if not learning_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active learning profile found for current user.")
        
    return LearningProfileRead.model_validate(learning_profile, from_attributes=True)

def get_language_id(db: Session, language_name: Optional[str]=None, language_code: Optional[str]=None) -> int:

    if language_name:
        language = db.query(Language).filter(Language.name == language_name).first()
        if not language:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
        return language.id

    if language_code:
        language = db.query(Language).filter(Language.code == language_code).first()
        if not language:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
        return language.id

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No language provided")


def update_word(
    db: Session,
    word_id: int,
    updates: WordBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
) -> WordRead:
    """
    Update a word's information and optionally regenerate embeddings.
    
    Args:
        db: SQLAlchemy session
        word_id: ID of the word to update
        updates: Dictionary of fields to update (lemma, language_id)
        current_user: Current authenticated user
        
    Returns:
        WordRead: Updated word object
        
    Raises:
        HTTPException: 404 if word not found, 403 if not authorized, 409 if duplicate
    """
    # Find the word
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    
    # Check if user has access to this word through their dictionaries
    user_has_access = (
        db.query(Dictionary)
        .join(LearningProfile, LearningProfile.id == Dictionary.learning_profile_id)
        .filter(
            Dictionary.word_id == word_id,
            LearningProfile.user_id == current_user.id
        )
        .first()
    )
    
    if not user_has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this word")
    
    # Update fields
    if updates.lemma != word.lemma:
        # Check for duplicates if lemma is being changed
        existing = db.query(Word).filter(
            Word.lemma == updates.lemma,
            Word.language_id == word.language_id,
            Word.id != word_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Word already exists")
        
        word.lemma = updates.lemma
        # Regenerate embedding for new lemma
        try:
            embedding_doc = embed(word.lemma)
            word.embedding = embedding_doc[0].metadata.get('embedding')
            word.embedding_model = embedding_doc[0].metadata.get('model')
            word.embedding_updated_at = datetime.utcnow()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not generate embedding: {str(e)}")
    
    if updates.language_id != word.language_id:
        # Validate language exists
        language = db.query(Language).filter(Language.id == updates.language_id).first()
        if not language:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
        
        # Check for duplicates in new language
        existing = db.query(Word).filter(
            Word.lemma == word.lemma,
            Word.language_id == updates.language_id,
            Word.id != word_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Word already exists in this language")
        
        word.language_id = updates.language_id
    
    db.add(word)
    db.commit()
    db.refresh(word)
    return WordRead.model_validate(word, from_attributes=True)


def update_translation(
    db: Session,
    translation_id: int,
    updates: TranslationBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
) -> TranslationRead:
    """ 
    Update a translation's information and optionally regenerate embeddings.
    
    Args:
        db: SQLAlchemy session
        translation_id: ID of the translation to update
        updates: Dictionary of fields to update (translation, language_id)
        current_user: Current authenticated user
        
    Returns:
        TranslationRead: Updated translation object
        
    Raises:
        HTTPException: 404 if translation not found, 403 if not authorized
    """
    # Find the translation
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found")
    
    # Check if user owns the dictionary entry
    dictionary = (
        db.query(Dictionary)
        .options(selectinload(Dictionary.learning_profile))
        .filter(Dictionary.id == translation.dictionary_id)
        .first()
    )
    
    if not dictionary or dictionary.learning_profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this translation")
    
    # Update fields
    if updates.translation != translation.translation:
        translation.translation = updates.translation
        # Regenerate embedding for new translation text
        try:
            embedding_doc = embed(translation.translation)
            translation.embedding = embedding_doc[0].metadata.get('embedding')
            translation.embedding_model = embedding_doc[0].metadata.get('model')
            translation.embedding_updated_at = datetime.utcnow()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not generate embedding: {str(e)}")
    
    if updates.language_id != translation.language_id:
        # Validate language exists
        language = db.query(Language).filter(Language.id == updates.language_id).first()
        if not language:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
        
        translation.language_id = updates.language_id
    
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return TranslationRead.model_validate(translation, from_attributes=True)


def update_example(
    db: Session,
    example_id: int,
    updates: ExampleBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
) -> ExampleRead:
    """
    Update an example's information and optionally regenerate embeddings.
    
    Args:
        db: SQLAlchemy session
        example_id: ID of the example to update
        updates: Dictionary of fields to update (example_text, language_id)
        current_user: Current authenticated user
        
    Returns:
        ExampleRead: Updated example object
        
    Raises:
        HTTPException: 404 if example not found, 403 if not authorized
    """
    # Find the example
    example = db.query(Example).filter(Example.id == example_id).first()
    if not example:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Example not found")
    
    # Check if user owns the dictionary entry
    dictionary = (
        db.query(Dictionary)
        .options(selectinload(Dictionary.learning_profile))
        .filter(Dictionary.id == example.dictionary_id)
        .first()
    )
    
    if not dictionary or dictionary.learning_profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this example")
    
    # Update fields
    if updates.example_text != example.example_text:
        example.example_text = updates.example_text
        # Regenerate embedding for new example text
        try:
            embedding_doc = embed(example.example_text)
            example.embedding = embedding_doc[0].metadata.get('embedding')
            example.embedding_model = embedding_doc[0].metadata.get('model')
            example.embedding_updated_at = datetime.utcnow()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not generate embedding: {str(e)}")
    
    if updates.language_id != example.language_id:
        # Validate language exists
        language = db.query(Language).filter(Language.id == updates.language_id).first()
        if not language:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
        
        example.language_id = updates.language_id
    
    db.add(example)
    db.commit()
    db.refresh(example)
    return ExampleRead.model_validate(example, from_attributes=True)

def update_current_user(db: Session, current_user: User, payload: UserUpdate) -> UserRead:
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

def update_definition(
    db: Session,
    definition_id: int,
    updates: DefinitionBase,
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
) -> DefinitionRead:
    """
    Update a definition's information and optionally regenerate embeddings.
    
    Args:
        db: SQLAlchemy session
        definition_id: ID of the definition to update
        updates: Dictionary of fields to update (definition_text, language_id)
        current_user: Current authenticated user
        
    Returns:
        DefinitionRead: Updated definition object
        
    Raises:
        HTTPException: 404 if definition not found, 403 if not authorized
    """
    # Find the definition
    definition = db.query(Definition).filter(Definition.id == definition_id).first()
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")
    
    # Check if user owns the dictionary entry
    dictionary = (
        db.query(Dictionary)
        .options(selectinload(Dictionary.learning_profile))
        .filter(Dictionary.id == definition.dictionary_id)
        .first()
    )
    
    if not dictionary or dictionary.learning_profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this definition")
    
    # Update fields
    if updates.definition_text != definition.definition_text:
        definition.definition_text = updates.definition_text
        # Regenerate embedding for new definition text
        try:
            embedding_doc = embed(definition.definition_text)
            definition.embedding = embedding_doc[0].metadata.get('embedding')
            definition.embedding_model = embedding_doc[0].metadata.get('model')
            definition.embedding_updated_at = datetime.utcnow()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not generate embedding: {str(e)}")
    
    if updates.language_id != definition.language_id:
        # Validate language exists
        language = db.query(Language).filter(Language.id == updates.language_id).first()
        if not language:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
        
        definition.language_id = updates.language_id
    
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return DefinitionRead.model_validate(definition, from_attributes=True)