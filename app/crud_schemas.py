from pydantic import ConfigDict, Field, BaseModel, EmailStr, field_validator, ValidationInfo, RootModel
from typing import List, Optional, Dict, Any, Optional, Set, TypedDict

#User
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    disabled: bool = False

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

    model_config = ConfigDict(from_attributes=True)

#Language
class LanguageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    code: Optional[str] = Field(None, max_length=5)


class LanguageRead(LanguageBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

#Word
class WordBase(BaseModel):
    lemma: str = Field(..., min_length=1, max_length=255)
    language_id: int


class WordRead(WordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

#Learning profile
class LearningProfileBase(BaseModel):
    user_id: int
    primary_language_id: int
    foreign_language_id: int
    is_active: Optional[bool] = True

class LearningProfileRead(LearningProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

#Dictionary
class DictionaryBase(BaseModel):
    learning_profile_id: int
    word_id: int
    notes: Optional[str] = None

class DictionaryRead(DictionaryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

#Translation
class TranslationBase(BaseModel):
    translation: str = Field(..., min_length=1)
    language_id: int
    dictionary_id: int


class TranslationRead(TranslationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

#Definition
class DefinitionBase(BaseModel):
    definition_text: str = Field(..., min_length=1)
    language_id: int
    dictionary_id: int
    original_text_id: Optional[int] = None

class DefinitionRead(DefinitionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
#Examples
class ExampleBase(BaseModel):
    example_text: str = Field(..., min_length=1)
    language_id: int
    dictionary_id: int

class ExampleRead(ExampleBase):
    id: int
    model_config = ConfigDict(from_attributes=True) 
#Text

class TextBase(BaseModel):
    learning_profile_id: int
    text: str = Field(..., min_length=1)

class TextRead(TextBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

#Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str