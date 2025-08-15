from pydantic import Field, BaseModel, EmailStr, field_validator, ValidationInfo, RootModel
from typing import List, Optional, Dict, Any, Optional, Set, TypedDict


class TranslationResponse(RootModel[Dict[str, List[str]]]):
    "Dictionary where keys are words (lemmas) and values are translations"
    pass
 
class DefinitionResponse(BaseModel):
    definition: List[str] = Field(description="List of definition in the target language")

class ExamplesResponse(BaseModel):
    examples: List[str] = Field(description="List of usage examples in the target language")
    
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str
    confirm_password: str
    
    @field_validator('confirm_password')
    def passwords_match(cls, v: str, *, info: Optional[ValidationInfo] = None):
        if info:
            password = info.data.get('password')

            if password != v:
                raise ValueError("Passwords do not match")
            
        if not v or len(v) < 8:
            raise ValueError("Length of your password must be at least 8 characters")
    
        return v
    
class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True

class LanguageBase(BaseModel):
    name: str

class LanguageRead(LanguageBase):

    id: int
    code: str

    class Config:
        orm_mode = True

class TranslationBase(BaseModel):
    text: str
    src_language: str
    tgt_language: str

class DefinitionBase(BaseModel):
    word: str
    language: str
    context: Optional[str]=None

class ExamplesBase(BaseModel):
    word: str
    language: str
    examples_number: int=1
    definition: Optional[str]=None

class TranslationRead(TranslationBase):
    words: TranslationResponse

class State(TypedDict):
    text: str  
    src_language: str
    tgt_language: str
    words: Set[str] 
    translations: Dict[str, List[str]] 
    definitions: Dict[str, List[str]]  
    examples: Dict[str, List[str]] 
    examples_number: Dict[str, int]
    similar_words: Dict[str, List[str]]  
    saved_to_json: bool