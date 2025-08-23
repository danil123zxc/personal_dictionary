from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
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
def embed(text: str)-> List[Document]:
    """
    Split text into chunks, embed each chunk, and return Documents
    with embedding stored in metadata.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=220, chunk_overlap=30, add_start_index=True)
    docs = text_splitter.create_documents([text])
    chunks = [doc.page_content for doc in docs]
    embs = _embeddings.embed_documents(chunks)

    for doc, emb in zip(docs, embs):
        doc.metadata["embedding"] = emb  
        doc.metadata["model"] = EMBEDDINGS_MODEL_NAME
        start = doc.metadata["start_index"]
        doc.metadata["end"] = start + len(doc.page_content)

    return docs