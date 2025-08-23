from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
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


@traceable(name="embed_word")
def embed_word(word: str) -> List[float]:
    """
    Compute an embedding for a SINGLE word (or short phrase).

    Args:
        word:      Non-empty string to embed.

    Returns:
        Embedding vector as a list of floats.
    """
    w = (word or "").strip()

    if not w:
        raise ValueError("word must be a non-empty string")

    vec = _embeddings.embed_query(w)  # List[float]

    return vec

@traceable(name="embed_text")
def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    texts = text_splitter.create_documents([text])
    
    return texts

@traceable(name="embed_text")
def embed_text(docs: Document, collection_name: str, connection: str | Engine):
    vec_store = PGVector(embeddings=_embeddings,
             collection_name=collection_name,
             connection=connection,
             use_jsonb=True)
    vec_store.add_documents(docs)