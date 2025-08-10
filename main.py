from typing import List, Optional, Dict, Tuple, Any, Union, Set, Annotated
import subprocess
import os
import re
import json
from prompts import *
from fastapi import FastAPI, HTTPException, Query, Body, Depends
from generate import *
from langchain_ollama import ChatOllama
from database import *
from models import *

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency to get the database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[SessionLocal, Depends(get_db)]

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