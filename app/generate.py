from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from app.schemas import TranslationResponse, DefinitionResponse, ExamplesResponse, DefinitionRead, ExamplesRead, TranslationRead
from typing import Optional
from dotenv import load_dotenv
from langsmith import traceable
from pathlib import Path
from app.prompts import translation_prompt, definition_prompt, example_prompt
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

# Get the root directory (parent of app directory)
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'

# Load the .env file from root directory
load_dotenv(dotenv_path=env_path)

llm = ChatOllama( 
    model="gemma3n",
    base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
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

@traceable(name='translations')
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
    # Create a translation prompt using ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ('system', translation_prompt),
        ('human', 'Text: {text}')
    ])

    # Format the prompt with provided variables
    messages = prompt.format_messages(
        text=text,
        src_language=src_language,
        tgt_language=tgt_language,
    )
    structured_llm = llm.with_structured_output(TranslationResponse)
    # Use the LLM to generate the translation
    response = structured_llm.invoke(messages)
    structured_output = TranslationRead(words=response, text=text, src_language=src_language, tgt_language=tgt_language)
    return structured_output

@traceable('definitions')
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
    prompt = ChatPromptTemplate.from_messages([
        ('system', definition_prompt),
        ('human', 'Word: {word}, Context: {context}')
    ])
    
    # Format the prompt with the provided variables
    messages = prompt.format_messages(
        language=language,
        word=word,
        context=context
    )
    structured_llm = llm.with_structured_output(DefinitionResponse)
    # Use the llm to invoke the prompt and get the response
    response = structured_llm.invoke(messages)
    structured_output = DefinitionRead(definition=response.definition, word=word, language=language, context=context)
    return structured_output.model_dump()

@traceable(name='examples')
def generate_examples(word: str, language: str, examples_number: int = 1, definition: Optional[str] = None) -> dict:
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
    # Create an example prompt using ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ('system', example_prompt), 
        ('human', 'Definition: {definition}, Word: {word}')
    ])
    # Format the prompt with the provided variables
    messages = prompt.format_messages(word=word, 
                            language=language, 
                            definition=definition, 
                            examples_number=examples_number)
    # Use the llm to invoke the prompt and get the response
    structured_llm = llm.with_structured_output(ExamplesResponse)
    response = structured_llm.invoke(messages)

    return ExamplesRead(examples=response.examples, word=word, language=language, examples_number=examples_number, definition=definition)


# def get_similar_words_rag(word: str, text: str, k: int = 5) -> List[str]:
#     """
#     Retrieve a list of words similar to the given input word using a RAG (Retrieval-Augmented Generation) retriever.

#     This function queries a retriever object for documents related to the given `word` 
#     and then extracts similar words from the retrieved content. The retrieved documents 
#     are processed as either JSON (from which keys are extracted) or plain text.

#     Args:
#         word (str):
#             The input word to search for.
#         text (str):
#             The reference text or corpus to be searched against.
#             (Currently unused in this implementation.)
#         k (int, optional):
#             The maximum number of retrieved results to process.
#             Defaults to 5.

#     Returns:
#         List[str]:
#             A list of similar words found in the retrieved documents.
#             Returns an empty list if retrieval fails or no valid data is found.

#     Notes:
#         - Requires a global `retriever` object with an `.invoke()` method 
#           that returns either a list of documents or a single document.
#         - Each document must have a `.page_content` attribute.
#         - If `.page_content` is JSON, the keys are extracted as similar words.
#           If it's plain text, the content itself is added to the result.
#         - All retrieval and parsing errors are caugsht and logged to console.

#     Example:
#         >>> get_similar_words_rag("apple", "", k=3)
#         ['fruit', 'macintosh', 'granny smith']
#     """
#     try:
#         # Query retriever for documents related to the input word
#         results = retriever.invoke(word)

#         # Ensure results is always a list for consistent iteration
#         if not isinstance(results, list):
#             results = [results]

#         similar_words = []

#         # Process up to k retrieved documents
#         for doc in results[:k]:
#             try:
#                 # Try to parse content as JSON and extract dictionary keys
#                 data = json.loads(doc.page_content)
#                 similar_words.extend(data.keys())
#             except json.JSONDecodeError:
#                 # If parsing fails, treat content as plain text
#                 similar_words.append(doc.page_content)

#         return similar_words

#     except Exception as e:
#         # Log the retrieval failure
#         print(f"[DEBUG] RAG search failed for '{word}': {e}")
#         return []
