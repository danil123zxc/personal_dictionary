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
from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable
from langchain_core.documents import Document
from sqlalchemy.engine import Engine
import os
import math

# Get the root directory (parent of app directory)
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'

# Load the .env file from root directory
load_dotenv(dotenv_path=env_path)


# -----------------------------------------------------------------------------
# Embeddings backend configuration
# You can override these via your project's .env
#   EMBEDDINGS_MODEL_NAME=all-MiniLM-L6-v2
#   EMBEDDINGS_DEVICE=cuda   (or "cpu", "mps" on Apple Silicon)
# -----------------------------------------------------------------------------

# Model configuration from environment variables
EMBEDDINGS_MODEL_NAME = os.getenv("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDINGS_DEVICE = os.getenv("EMBEDDINGS_DEVICE", "cpu")

# Initialize HuggingFace embeddings model
# We enable L2 normalization on the model side — useful for cosine similarity,
# nearest neighbor search, and pgvector("cosine") indexing.
_embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDINGS_MODEL_NAME,
    model_kwargs={"device": EMBEDDINGS_DEVICE},
    encode_kwargs={"normalize_embeddings": True},  # ensures unit-length vectors
)

# Our gemma3n model is hosted on Ollama
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

@traceable(name='definitions')
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

@traceable(name="embed")
def embed(text: str, 
        chunk_size: Optional[int] = 220, 
        chunk_overlap: Optional[int] = 30
        ) -> List[Document]:
    """
    Split text into chunks, embed each chunk, and return Documents
    with embedding stored in metadata.

    This function processes input text by:
    1. Splitting it into manageable chunks using RecursiveCharacterTextSplitter
    2. Generating vector embeddings for each chunk using the configured model
    3. Storing embeddings and metadata in Document objects

    Parameters
    ----------
    text : str
        The input text to be segmented and embedded.
    chunk_size : int, optional (default=220)
        Maximum character length for each chunk. The text will be 
        split recursively to avoid exceeding this size.
    chunk_overlap : int, optional (default=30)
        Number of overlapping characters between consecutive chunks 
        to preserve semantic continuity.

    Returns
    -------
    List[Document]
        A list of LangChain `Document` objects. Each document has:
        - `page_content` : str
            The raw text content of the chunk.
        - `metadata["embedding"]` : List[float]
            The vector representation of the chunk produced by the
            configured embedding model.
        - `metadata["model"]` : str
            Name/identifier of the embedding model used.
        - `metadata["start_index"]` : int
            Character index in the original text where the chunk begins.
        - `metadata["end"]` : int
            Character index in the original text where the chunk ends.

    Example
    -------
    >>> text = "LangChain provides a standard interface for chains, as well as a collection of utilities..."
    >>> docs = embed(text, chunk_size=50, chunk_overlap=10)
    >>> docs[0].page_content
    'LangChain provides a standard interface for chains,'
    >>> docs[0].metadata.keys()
    dict_keys(['start_index', 'embedding', 'model', 'end'])
    >>> len(docs)
    3

    Notes
    -----
    - The function uses RecursiveCharacterTextSplitter which tries to split on
      natural boundaries (spaces, punctuation) before falling back to character-level splitting.
    - Embeddings are L2-normalized for consistent cosine similarity calculations.
    - The chunk_overlap helps maintain context between chunks for better semantic understanding.
    """
    # Initialize text splitter with specified parameters
    # add_start_index=True adds character position tracking to metadata

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap, 
        add_start_index=True
    )

    
    # Split text into documents
    docs = text_splitter.create_documents([text])
    
    # Extract text content from documents for embedding
    chunks = [doc.page_content for doc in docs]
    
    # Generate embeddings for all chunks in a single batch
    # This is more efficient than embedding chunks individually
    embs = _embeddings.embed_documents(chunks)

    # Attach embeddings and metadata to each document
    for doc, emb in zip(docs, embs):
        # Store the embedding vector in metadata
        doc.metadata["embedding"] = emb  
        # Store the model name for reference
        doc.metadata["model"] = EMBEDDINGS_MODEL_NAME
        # Calculate end position based on start position and content length
        start = doc.metadata["start_index"]
        doc.metadata["end"] = start + len(doc.page_content)

    return docs