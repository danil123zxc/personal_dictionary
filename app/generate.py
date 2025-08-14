from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from schemas import TranslationResponse, DefinitionResponse, ExamplesResponse
from typing import Optional
import os
from dotenv import load_dotenv
from langsmith import traceable
from pathlib import Path

# Get the root directory (parent of app directory)
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'

# Load the .env file from root directory
load_dotenv(dotenv_path=env_path)

llm = ChatOllama( 
    model="gemma3n",
    temperature=0.5,
)

language_codes = {
    "English": "en",
    "Русский": "ru",
    "한국어": "ko",
    "中文": "zh",
    "日本語": "ja",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Português": "pt"
}
codes_language = {
    "en":"English",
    "ru":"Русский",
    "ko":"한국어",
    "zh":"中文",
    "ja":"日本語",
    "es":"Español",
    "fr":"Français",
    "de":"Deutsch",
    "it":"Italiano",
    "pt":"Português"
}

def generate_translation(text: str, src_language: str, tgt_language: str) -> dict:
    """
    Generate translations in a given text from the source language to the target language.

    Args:
        text (str): The input text containing one or more sentences to translate.
        src_language (str): The language of the original text (source language).
        tgt_language (str): The language into which the text will be translated (target language).

    Returns:
        dict: A dictionary containing:
            {{
                'word1': 
                {   
                    'translations': [''],
                },
                'word2': 
                {   
                    'translations': [''],
                }
            }}
 
    """
    # Create a translation prompt using PromptTemplate
    translation = PromptTemplate(
        input_variables=["text", "src_language", "tgt_language"],
        template=translation_prompt
    )

    # Format the prompt with provided variables
    prompt = translation.format(
        text=text,
        src_language=src_language,
        tgt_language=tgt_language,
    )

    # Use the LLM to generate the translation
    response = llm.invoke(prompt, config={"response_format": "json_object"})

    # Create parser instance with the response model
    parser = JsonOutputParser(pydantic_object=TranslationResponse)
    
    try:
        # Parse the response into the defined structure
        parsed_response = parser.parse(response.content)

    except Exception as e:
        parsed_response = {
            "original": text,
            "message": f"Error parsing response: {e}"
        }

    return parsed_response
    
def generate_definition(word: str, language: str,  context: Optional[str]=None) -> dict:
    """
    Generate definition for a given word in a specified language.
    
    Args:
        word (str): The word to define.
        language (str): The language in which definitions are to be provided.
        context (str): The original sentence or context in which the word is used.

    Returns:
        dict: A dictionary containing:
        {{
            "definition": ["single definition"],
        }}
    """
    # Create a definition prompt using PromptTemplate
    definition = PromptTemplate(
        input_variables=["word", "language", "context"],
        template=definition_prompt  # Changed from example_prompt to definition_prompt
    )
    
    # Format the prompt with the provided variables
    prompt = definition.format(
        language=language,
        word=word,
        context=context
    )
    
    # Use the llm to invoke the prompt and get the response
    response = llm.invoke(prompt, config={"response_format": "json_object"})

    # Create parser instance with the response model
    parser = JsonOutputParser(pydantic_object=DefinitionResponse)
    
    try:
        # Parse the response into the defined structure
        parsed_response = parser.parse(response.content)
        return parsed_response
    
    except Exception as e:
        return {
            "original": word,
            "message": f"Failed to parse response: {str(e)}"
        }

def generate_examples(word: str, language: str, definition: Optional[str] = None, examples_number: Optional[int] = 1) -> dict:
    """
    Generate examples of usage for a given type in a foreign language.
    Args:
        word(str)
        language (str): The language in which examples are to be provided.  
        definition (str): The definition of the word or phrase.
        examples_number (int): The number of examples to generate.
    Returns:
        dict: A dictionary containing:
        {
            "examples": ["example sentence 1", "example sentence 2", ...],
            "examples_number": {examples_number},
        }
    """
    # Create an example prompt using PromptTemplate
    example = PromptTemplate(
        input_variables=["word", "foreign_language", "definition", "examples_number"],
        template=example_prompt
    )
    # Format the prompt with the provided variables
    prompt = example.format(word=word, 
                            language=language, 
                            definition=definition, 
                            examples_number=examples_number)
    # Use the llm to invoke the prompt and get the response
    response = llm.invoke(prompt, config={"response_format": "json_object"})

    # Create parser instance with the response model
    parser = JsonOutputParser(pydantic_object=ExamplesResponse)
    
    try:
        # Parse the response into the defined structure
        parsed_response = parser.parse(response.content)
        return parsed_response
    
    except Exception as e:
        return {
            "original": word,
            "message": "Failed to parse response"
        }
