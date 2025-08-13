from typing import List, Optional, Dict, Tuple, Any, Union, Set, Annotated
import json
from app.prompts import *
from fastapi import FastAPI, HTTPException, Query, Body, Depends
from generate import generate_translation, generate_definition, generate_examples, language_codes, codes_language, llm
from app.database import Base, engine, get_db
from app.models import User as Userdb, Language as Languagedb, Word as Worddb, Definition as Definitiondb, Example as Exampledb, LearningProfile as LearningProfiledb
from pydantic import BaseModel, Field, RootModel
from app.schemas import UserCreate, UserRead, LanguageBase, LanguageRead
from sqlalchemy.orm import Session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
Base.metadata.create_all(bind=engine)

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: db_dependency):
    #Checking if user with the same username of email already exists
    existing_user = db.query(Userdb).filter(
        (Userdb.username == user.username) |
        (Userdb.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    #Adding user to the db
    db_user = Userdb(username=user.username, full_name=user.full_name, email=user.email, password=pwd_context.hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/user_info/", response_model=UserRead)
def get_user_info(db: db_dependency, user_id: Optional[int]=None, username: Optional[str]=None):
    
    if user_id and username:
        user = db.query(Userdb).filter((Userdb.username == username) &
                                       (Userdb.id == user_id)).first()
    elif user_id:
        user = db.query(Userdb).filter(Userdb.id == user_id).first()
    elif username:
        user = db.query(Userdb).filter(Userdb.username == username).first()


    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/create_language", response_model=LanguageRead)
def create_language(language: LanguageBase, db: db_dependency):

    code = language_codes.get(language.name)

    if not code:
        raise HTTPException(status_code=400, detail="Invalid language")
    
    existing_language = db.query(Languagedb).filter(
        (Languagedb.name == language.name) |
        (Languagedb.code == code)
    ).first()

    if existing_language:
        raise HTTPException(status_code=400, detail="Language already exists")
    
    db_language = Languagedb(name=language.name, code=code)
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

@app.post("/translate")

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