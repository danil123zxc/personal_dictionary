from typing import List, Optional, Dict, Tuple, Any, Union, Set, Annotated
import json
from app.prompts import *
from fastapi import FastAPI, HTTPException, Query, Body, Depends
from app.generate import generate_translation, generate_definition, generate_examples, language_codes, codes_language, llm
from app.database import Base, engine, get_db
from app.models import *
from app.schemas import WordBase, TranslationRead, ExamplesRead, DefinitionRead, TranslationResponse, TranslationInput, ExamplesInput, DefinitionInput
from sqlalchemy.orm import Session
from app.crud_schemas import UserBase, Token, UserCreate, UserRead, LanguageBase, LanguageRead
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from app import auth
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

app = FastAPI()
Base.metadata.create_all(bind=engine)

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: db_dependency)-> UserRead:
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
                   email=payload.email, 
                   password=auth.get_password_hash(payload.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
def login(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()])-> Token:
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username},  
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserRead)
def read_user_me(current_user: Annotated[UserBase, Depends(auth.get_current_active_user)]):
    return current_user 

@app.get("/user_info/", response_model=UserRead)
def get_user_info(db: db_dependency, user_id: Optional[int]=None, username: Optional[str]=None):
    
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

@app.post("/create_language", response_model=LanguageRead)
def create_language(language: LanguageBase, db: db_dependency):

    code = language_codes.get(language.name)

    if not code:
        raise HTTPException(status_code=400, detail="Invalid language")
    
    existing_language = db.query(Language).filter(
        (Language.name == language.name) |
        (Language.code == code)
    ).first()

    if existing_language:
        raise HTTPException(status_code=400, detail="Language already exists")
    
    db_language = Language(name=language.name, code=code)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

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

@app.post("/create_word/{user_id}")
def create_word(word: WordBase, db: db_dependency):
    
    word = db.query(Word).filter(Word.lemma == WordBase.word)
    if word:
        raise HTTPException(status_code=400, detail="Word already exists")
    
    language = db.query(Language).filter(Language.name == WordBase.language)
    if not language:
        HTTPException(status_code=404, detail="Language doesn't exist")

    db_word = Word(lemma=WordBase.word, language=language)
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word


def main():
    # Example usage
    get_db()  
    text = "Hello, how are you?"
    src_language = "English"
    tgt_language = "Русский"
    
    # Generate translations
    translation_result = generate_translation(text, src_language, tgt_language)
    print(json.dumps(translation_result, indent=2, ensure_ascii=False))
    
    # Generate definitions
    word = "hello"
    definition_result = generate_definition(word, tgt_language, context=text)
    print(json.dumps(definition_result, indent=2, ensure_ascii=False))
    
    # Generate examples
    examples_result = generate_examples(word, tgt_language, definition=definition_result['definition'][0], examples_number=3)
    print(json.dumps(examples_result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()  