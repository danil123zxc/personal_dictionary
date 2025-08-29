from pydantic import Field, BaseModel, EmailStr, field_validator, ValidationInfo, RootModel

from typing import List, Optional, Dict, Any, Set, TypedDict
from app.crud_schemas import WordBase
from app.database import get_db
from app.crud_schemas import LearningProfileRead
from sqlalchemy.orm import Session
from fastapi import Depends

class TranslationResponse(RootModel[Dict[str, List[str]]]):
    """
    Response model for translation results.
    
    This model represents the structured output from AI translation services.
    It maps words (lemmas) to their translations in the target language.
    
    Example:
        {
            "hello": ["hola", "buenos días"],
            "world": ["mundo"],
            "goodbye": ["adiós", "hasta luego"]
        }
    """
    pass
 
class DefinitionResponse(BaseModel):
    """
    Response model for definition generation.
    
    This model represents the structured output from AI definition services.
    It contains a list of definitions for a given word.
    
    Attributes:
        definition: List of definitions in the target language
    """
    definition: List[str] = Field(description="List of definition in the target language")

class ExamplesResponse(BaseModel):
    """
    Response model for example generation.
    
    This model represents the structured output from AI example services.
    It contains a list of usage examples for a given word.
    
    Attributes:
        examples: List of usage examples in the target language
    """
    examples: List[str] = Field(description="List of usage examples in the target language")

class TranslationInput(BaseModel):
    """
    Input model for translation requests.
    
    This model defines the required parameters for text translation services.
    
    Attributes:
        text: The input text to be translated
        src_language: Source language name (e.g., "English", "Español")
        tgt_language: Target language name (e.g., "Spanish", "English")
    """
    text: str
    src_language: str
    tgt_language: str

class DefinitionInput(WordBase):
    """
    Input model for definition generation requests.
    
    This model extends WordBase to include optional context for better
    definition accuracy.
    
    Attributes:
        context: Optional context sentence to help determine word meaning
    """
    context: Optional[str] = None

class ExamplesInput(WordBase):
    """
    Input model for example generation requests.
    
    This model extends WordBase to include parameters for example generation.
    
    Attributes:
        examples_number: Number of examples to generate (default: 1)
        definition: Optional definition to guide example generation
    """
    examples_number: Optional[int] = 1
    definition: Optional[str] = None

class TranslationRead(TranslationInput):
    """
    Complete translation response model.
    
    This model combines the input parameters with the translation results
    to provide a complete response for translation requests.
    
    Attributes:
        words: Translation results mapping words to their translations
    """
    words: TranslationResponse

class DefinitionRead(DefinitionInput, DefinitionResponse):
    """
    Complete definition response model.
    
    This model combines the input parameters with the definition results
    to provide a complete response for definition requests.
    """
    pass

class ExamplesRead(ExamplesInput, ExamplesResponse):
    """
    Complete examples response model.
    
    This model combines the input parameters with the example results
    to provide a complete response for example generation requests.
    """
    pass

class AllRead(TranslationInput, DefinitionRead, ExamplesRead):
    """
    Comprehensive response model for all language processing services.
    
    This model combines translation, definition, and example generation
    into a single comprehensive response. It's useful for workflows that
    need all three types of language processing.
    """
    pass

class Context(LearningProfileRead):
    """
    Context model for language processing workflows.
    
    This model extends LearningProfileRead to include additional context
    for language processing workflows.
    """
    db: Session = Depends(get_db)

class State(TypedDict):
    """
    Workflow state model for language processing pipelines.
    
    This model represents the state of a language processing workflow,
    tracking various intermediate results and processing status.
    
    Attributes:
        text: Original input text
        src_language: Source language
        tgt_language: Target language
        words: Set of extracted words
        translations: Dictionary mapping words to translations
        definitions: Dictionary mapping words to definitions
        examples: Dictionary mapping words to examples
        examples_number: Dictionary mapping words to number of examples
        similar_words: Dictionary mapping words to similar words
        saved_to_db: Flag indicating if results were saved
        created_words: List of words that were successfully created
        existing_words: List of words that already existed in the database  
    """
    text: str 
    chunks: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping chunks to words")
    words: Set[str] = Field(default_factory=set, description="Set of extracted words")
    translations: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping words to translations")
    definitions: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping words to definitions")
    examples: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping words to examples")
    examples_number: Dict[str, int] = Field(default_factory=dict, description="Dictionary mapping words to number of examples")
    synonyms: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping words to similar words")
    dictionaries: Dict[str, int] = Field(default_factory=dict, description="Dictionary mapping words to dictionary IDs")

class Output(BaseModel):
    """
    Output model for language processing workflows.
    
    This model represents the output of a language processing workflow.
    """
    text_id: int
    learning_profile_id: int
    created_words: List[str]
    created_dictionaries: List[str]
    created_translations: List[str]
    created_definitions: List[str]
    created_examples: List[str]
