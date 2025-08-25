from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable
from langchain_core.documents import Document
from sqlalchemy.engine import Engine
import os
import math

# -----------------------------------------------------------------------------
# Embeddings backend configuration
# You can override these via your project's .env
#   EMBEDDINGS_MODEL_NAME=all-MiniLM-L6-v2
#   EMBEDDINGS_DEVICE=cuda   (or "cpu", "mps" on Apple Silicon)
# -----------------------------------------------------------------------------
EMBEDDINGS_MODEL_NAME = os.getenv("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDINGS_DEVICE = os.getenv("EMBEDDINGS_DEVICE", "cpu")

# We enable L2 normalization on the model side — useful for cosine similarity,
# nearest neighbor search, and pgvector("cosine") indexing.
_embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDINGS_MODEL_NAME,
    model_kwargs={"device": EMBEDDINGS_DEVICE},
    encode_kwargs={"normalize_embeddings": True},  # ensures unit-length vectors
)

@traceable(name="embed")
def embed(text: str, 
          chunk_size: int=220, 
          chunk_overlap: int=30
          )-> List[Document]:
    """
    Split text into chunks, embed each chunk, and return Documents
    with embedding stored in metadata.

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
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True)
    docs = text_splitter.create_documents([text])
    chunks = [doc.page_content for doc in docs]
    embs = _embeddings.embed_documents(chunks)

    for doc, emb in zip(docs, embs):
        doc.metadata["embedding"] = emb  
        doc.metadata["model"] = EMBEDDINGS_MODEL_NAME
        start = doc.metadata["start_index"]
        doc.metadata["end"] = start + len(doc.page_content)

    return docs