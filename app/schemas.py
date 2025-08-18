from pydantic import Field, BaseModel, EmailStr, field_validator, ValidationInfo, RootModel
from typing import List, Optional, Dict, Any, Optional, Set, TypedDict


class WordBase(BaseModel):
    word: str
    language: str

class TranslationResponse(RootModel[Dict[str, List[str]]]):
    "Dictionary where keys are words (lemmas) and values are translations"
    pass
 
class DefinitionResponse(BaseModel):
    definition: List[str] = Field(description="List of definition in the target language")

class ExamplesResponse(BaseModel):
    examples: List[str] = Field(description="List of usage examples in the target language")

class TranslationInput(BaseModel):
    text: str
    src_language: str
    tgt_language: str

class DefinitionInput(WordBase):
    context: Optional[str]=None

class ExamplesInput(WordBase):
    examples_number: Optional[int]=1
    definition: Optional[str]=None

class TranslationRead(TranslationInput):
    words: TranslationResponse

class DefinitionRead(DefinitionInput, DefinitionResponse):
    pass

class ExamplesRead(ExamplesInput, ExamplesResponse):
    pass

class AllRead(TranslationInput, DefinitionRead, ExamplesRead):
    pass

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