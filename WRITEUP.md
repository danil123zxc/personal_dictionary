# Technical Writeup: Personal Dictionary API - Offline AI Language Learning Application

## Table of Contents
1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Database Design](#3-database-design)
4. [API Design](#4-api-design)
5. [AI Pipeline Architecture](#5-ai-pipeline-architecture)
6. [Authentication & Security](#6-authentication--security)
7. [Vector Embeddings & Semantic Search](#7-vector-embeddings--semantic-search)
8. [Technology Stack](#8-technology-stack)
9. [Implementation Details](#9-implementation-details)
10. [Performance Considerations](#10-performance-considerations)
11. [Challenges & Solutions](#11-challenges--solutions)
12. [Future Enhancements](#12-future-enhancements)

## 1. Introduction

### 1.1 Project Overview

The Personal Dictionary API is a comprehensive, offline-first language learning application that leverages AI to help users build vocabulary effectively. The system processes text input to extract, translate, define, and exemplify words while maintaining complete privacy through local processing.

### 1.2 Key Objectives

- **Privacy-First Design**: Complete offline operation with local AI processing
- **Context-Aware Learning**: Generate translations and definitions based on actual usage context
- **Scalable Architecture**: FastAPI-based REST API with PostgreSQL backend
- **Semantic Intelligence**: Vector embeddings for similarity search and related word discovery
- **User-Centric**: Personalized learning profiles and progress tracking

### 1.3 Core Features

- **AI-Powered Translation**: Extract content words and generate context-aware translations
- **Smart Definitions**: Generate precise definitions based on word context
- **Example Generation**: Create natural example sentences for vocabulary reinforcement
- **Semantic Search**: Find related words using vector similarity
- **User Management**: Secure authentication and personalized learning profiles
- **Vector Storage**: Efficient semantic search using pgvector

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │   Ollama LLM    │
│                 │    │   + pgvector    │    │   (Gemma 3n)    │
│  - REST API     │◄──►│  - User Data    │    │  - Translation  │
│  - Auth         │    │  - Words        │    │  - Definitions  │
│  - Business     │    │  - Embeddings   │    │  - Examples     │
│     Logic       │    │  - Relations    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HuggingFace   │    │   Alembic       │    │   LangChain     │
│   Embeddings    │    │   Migrations    │    │   Pipeline      │
│  - MiniLM       │    │  - Schema       │    │  - Orchestration│
│  - Vector Gen   │    │  - Versioning   │    │  - Structured   │
│                 │    │                 │    │     Output      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Component Interaction Flow

1. **User Authentication**: JWT-based authentication with bcrypt password hashing
2. **Request Processing**: FastAPI handles HTTP requests with Pydantic validation
3. **Business Logic**: SQLAlchemy ORM manages database operations
4. **AI Processing**: LangChain orchestrates LLM interactions with structured output
5. **Vector Operations**: pgvector handles similarity search and embeddings storage
6. **Response Generation**: Structured JSON responses with proper error handling

## 3. Database Design

### 3.1 Entity Relationship Diagram

```
Users (1) ──── (N) LearningProfiles (1) ──── (N) Dictionaries
   │                                              │
   │                                              │
   └── (N) UserWordProgress                       └── (1) Words (N) ─── (1) Languages
                                                           │
                                                           │
                                                    (N) Translations
                                                    (N) Definitions
                                                    (N) Examples
```

### 3.2 Core Entities

#### Users
- **Purpose**: User authentication and profile management
- **Key Fields**: `id`, `username`, `email`, `password_hash`, `full_name`, `disabled`
- **Relationships**: One-to-many with LearningProfiles

#### Languages
- **Purpose**: Supported language definitions and codes
- **Key Fields**: `id`, `name`, `code` (ISO language code)
- **Relationships**: One-to-many with Words, Translations, Definitions, Examples

#### LearningProfiles
- **Purpose**: User language learning configurations
- **Key Fields**: `id`, `user_id`, `primary_language_id`, `foreign_language_id`, `is_active`
- **Constraints**: Unique (user_id, primary_language_id, foreign_language_id)

#### Words
- **Purpose**: Vocabulary storage with vector embeddings
- **Key Fields**: `id`, `lemma`, `language_id`, `embedding`, `embedding_model`
- **Features**: Vector embeddings for semantic search

#### Dictionaries
- **Purpose**: User's personal vocabulary collections
- **Key Fields**: `id`, `learning_profile_id`, `word_id`, `notes`
- **Constraints**: Unique (learning_profile_id, word_id)

### 3.3 Vector Storage Strategy

```sql
-- pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Word embeddings table with vector column
CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    lemma VARCHAR(255) NOT NULL,
    language_id INTEGER REFERENCES languages(id),
    embedding vector(384),  -- 384-dimensional embeddings
    embedding_model VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for efficient similarity search
CREATE INDEX ON words USING ivfflat (embedding vector_cosine_ops);
```

## 4. API Design

### 4.1 RESTful Endpoint Structure

#### Authentication Endpoints
```http
POST /register          # User registration
POST /login             # User authentication
GET  /users/me          # Current user profile
PUT  /update_user/me    # Update user profile
DELETE /user_delete/me  # Delete user account
```

#### Language Management
```http
POST /create_language   # Add supported language
```

#### Learning Profiles
```http
POST /create_learning_profile  # Create language learning profile
```

#### Word Management
```http
POST /create_word              # Add word with embeddings
POST /create_in_dictionary     # Add word to personal dictionary
POST /create_translation       # Add word translation
POST /create_text             # Create text entry
```

#### AI-Powered Generation
```http
POST /translate    # Generate translations
POST /definition   # Generate definitions
POST /examples     # Generate examples
```

### 4.2 Request/Response Schemas

#### Translation Request
```json
{
  "text": "Hello world, how are you today?",
  "src_language": "English",
  "tgt_language": "Spanish"
}
```

#### Translation Response
```json
{
  "text": "Hello world, how are you today?",
  "src_language": "English",
  "tgt_language": "Spanish",
  "words": {
    "hello": ["hola", "buenos días"],
    "world": ["mundo"],
    "today": ["hoy"]
  }
}
```

### 4.3 Error Handling Strategy

```python
# Standardized error responses
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "validation_error"
}

# HTTP Status Codes
200: Success
201: Created
400: Bad Request
401: Unauthorized
403: Forbidden
404: Not Found
409: Conflict
500: Internal Server Error
```

## 5. AI Pipeline Architecture

### 5.1 LangGraph Pipeline Overview

The AI processing pipeline is orchestrated using LangGraph's `StateGraph`, providing a modular and maintainable approach to complex NLP workflows.

```python
# Pipeline state structure
State = TypedDict({
    'text': str,
    'src_language': str,
    'tgt_language': str,
    'words': Set[str],
    'translations': Dict[str, List[str]],
    'definitions': Dict[str, List[str]],
    'examples': Dict[str, List[str]],
    'examples_number': Dict[str, int],
    'similar_words': Dict[str, List[str]],
    'saved_to_json': bool
})
```

### 5.2 Pipeline Nodes

#### 5.2.1 Translation Node
```python
@traceable(name='translations')
def translate_words_node(state: State) -> State:
    """
    Extract content words and generate translations.
    
    Process:
    1. Extract content words (exclude stopwords)
    2. Lemmatize words to base form
    3. Translate to target language
    4. Remove duplicates
    """
    # Implementation details...
```

#### 5.2.2 Definition Node
```python
@traceable(name='definitions')
def generate_definitions_node(state: State) -> State:
    """
    Generate context-aware definitions for extracted words.
    
    Process:
    1. Use original sentence context
    2. Generate single, clear definition
    3. Ensure definition matches context
    """
    # Implementation details...
```

#### 5.2.3 Example Node
```python
@traceable(name='examples')
def generate_examples_node(state: State) -> State:
    """
    Generate usage examples for vocabulary words.
    
    Process:
    1. Use word definition as context
    2. Generate simple, natural sentences
    3. Ensure grammatical correctness
    """
    # Implementation details...
```

#### 5.2.4 Similar Words Node
```python
@traceable(name='similar_words')
def generate_similar_node(state: State) -> State:
    """
    Find semantically similar words using RAG.
    
    Process:
    1. Generate embeddings for input words
    2. Query existing vocabulary embeddings
    3. Return top-k similar words
    """
    # Implementation details...
```

### 5.3 Prompt Engineering Strategy

#### Translation Prompt
```
You receive a text.

Task:
1. For each sentence, extract all **content words** only (exclude stopwords)
2. Convert each extracted word to its **base dictionary form (lemma)**
3. Translate each lemma from {src_language} to **{tgt_language}**
4. Remove duplicates — only include unique lemmas

Only include unique words per input (no duplicates).
Do not add extra explanations or context.
```

#### Definition Prompt
```
Generate a single definition for the word in {language}, based only on its meaning in the given sentence:

Rules:
1. Provide exactly one short, clear definition matching the word's meaning in this sentence.
2. No other meanings, no examples.
3. The definition must be in {language}.
4. If unsure give your best guess.
```

#### Example Prompt
```
Generate {examples_number} simple sentences for the word in {language} using only the given definition:
Rules:
1. Sentences must match this definition exactly; ignore other meanings.
2. Grammar must be correct and natural.
3. Use simple, clear vocabulary for learners.
4. Avoid repeating the same structure or idea.
5. If definition is not given use the most common meaning of this word.
```

## 6. Authentication & Security

### 6.1 JWT Authentication Flow

```python
# Token generation
def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Token validation
def get_current_user(token: str, db: Session) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = int(payload.get("sub"))
    return db.get(User, user_id)
```

### 6.2 Password Security

```python
# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### 6.3 Security Features

- **Bcrypt Hashing**: Industry-standard password hashing
- **JWT Tokens**: Stateless authentication with expiration
- **OAuth2 Password Flow**: Standard authentication protocol
- **User Isolation**: Data access restricted to authenticated users
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## 7. Vector Embeddings & Semantic Search

### 7.1 Embedding Generation

```python
# HuggingFace embeddings configuration
_embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

@traceable(name="embed")
def embed(text: str, chunk_size: int = 220, chunk_overlap: int = 30) -> List[Document]:
    """
    Generate vector embeddings for text with metadata.
    
    Returns:
        List[Document] with embeddings in metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap, 
        add_start_index=True
    )
    docs = text_splitter.create_documents([text])
    chunks = [doc.page_content for doc in docs]
    embs = _embeddings.embed_documents(chunks)
    
    for doc, emb in zip(docs, embs):
        doc.metadata["embedding"] = emb
        doc.metadata["model"] = EMBEDDINGS_MODEL_NAME
    
    return docs
```

### 7.2 Similarity Search Implementation

```python
# Vector similarity search using pgvector
def find_similar_words(word_embedding: List[float], top_k: int = 5) -> List[Word]:
    """
    Find semantically similar words using cosine similarity.
    """
    similar_words = (
        db.query(Word)
        .filter(Word.embedding.cosine_distance(word_embedding) < 0.3)
        .order_by(Word.embedding.cosine_distance(word_embedding))
        .limit(top_k)
        .all()
    )
    return similar_words
```

### 7.3 Embedding Storage Strategy

- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Normalization**: L2 normalization for cosine similarity
- **Indexing**: IVFFlat index for efficient similarity search
- **Storage**: PostgreSQL with pgvector extension
- **Metadata**: Model name and generation timestamp

## 8. Technology Stack

### 8.1 Backend Framework
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **SQLAlchemy 2.0**: Type-safe ORM with async support
- **Alembic**: Database migration and versioning
- **Pydantic**: Data validation and serialization

### 8.2 Database & Storage
- **PostgreSQL**: Primary relational database
- **pgvector**: Vector similarity search extension

### 8.3 AI & Machine Learning
- **Ollama**: Local LLM deployment and management
- **Gemma 3n**: Multilingual language model (2B parameters)
- **LangChain**: LLM application framework
- **HuggingFace**: Transformers and embeddings
- **Sentence Transformers**: Semantic text embeddings

### 8.4 Security & Authentication
- **JWT**: JSON Web Tokens for stateless authentication
- **Passlib**: Password hashing with bcrypt
- **OAuth2**: Standard authentication protocol

### 8.5 Development & Deployment
- **Docker**: Containerization for consistent deployment
- **Docker Compose**: Multi-service orchestration
- **Uvicorn**: ASGI server for FastAPI
- **Python 3.8+**: Core programming language

## 9. Implementation Details

### 9.1 Database Migrations

```python
# Alembic migration example
"""Add vector embeddings to words table

Revision ID: 66a79084ba5f
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add embedding columns to words table
    op.add_column('words', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('words', sa.Column('embedding_model', sa.String(64), nullable=True))
    op.add_column('words', sa.Column('embedding_updated_at', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column('words', 'embedding_updated_at')
    op.drop_column('words', 'embedding_model')
    op.drop_column('words', 'embedding')
```

### 9.2 Dependency Injection

```python
# FastAPI dependency injection
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in endpoints
@app.post("/create_word")
def create_word(word: WordBase, db: Session = Depends(get_db)):
    # Database operations...
```

### 9.3 Error Handling

```python
# Custom exception handling
from fastapi import HTTPException, status

class WordAlreadyExistsError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Word already exists in this language"
        )

# Usage in business logic
if existing_word:
    raise WordAlreadyExistsError()
```

### 9.4 Structured Output Parsing

```python
# LangChain structured output
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class TranslationResponse(BaseModel):
    translations: Dict[str, List[str]] = Field(
        description="Word to translation mapping"
    )

# LLM with structured output
structured_llm = llm.with_structured_output(TranslationResponse)
response = structured_llm.invoke(messages)
```

## 10. Performance Considerations

### 10.1 Database Optimization

- **Indexing Strategy**: Composite indexes for common query patterns
- **Vector Indexing**: IVFFlat index for similarity search
- **Connection Pooling**: SQLAlchemy connection pool configuration
- **Query Optimization**: Eager loading for related data

### 10.2 Caching Strategy

```python
# Redis caching for frequently accessed data
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time: int = 3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached_result = redis_client.get(cache_key)
            
            if cached_result:
                return json.loads(cached_result)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expire_time, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 10.3 LLM Optimization

- **Batch Processing**: Process multiple words in single LLM calls
- **Temperature Control**: Balance creativity vs. consistency
- **Prompt Optimization**: Minimize token usage while maintaining quality
- **Response Caching**: Cache similar requests to reduce LLM calls

### 10.4 Vector Search Optimization

- **Index Tuning**: Optimize IVFFlat parameters for dataset size
- **Batch Embedding**: Generate embeddings in batches
- **Similarity Thresholds**: Use appropriate distance thresholds
- **Result Limiting**: Limit search results to prevent performance issues

## 11. Challenges & Solutions

### 11.1 LLM Output Consistency

**Challenge**: Ensuring structured JSON output from LLM responses.

**Solution**: 
- Implemented Pydantic output parsers with retry logic
- Used structured prompts with explicit JSON formatting instructions
- Added fallback parsing for malformed responses

```python
def parse_llm_response(response: str) -> Dict:
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Fallback parsing logic
        return extract_structured_data(response)
```

### 11.2 Vector Embedding Performance

**Challenge**: Efficient storage and retrieval of high-dimensional vectors.

**Solution**:
- Implemented pgvector with optimized indexing
- Used L2 normalization for consistent similarity calculations
- Implemented batch processing for embedding generation

### 11.3 Offline AI Processing

**Challenge**: Running large language models locally without cloud dependencies.

**Solution**:
- Used Ollama for local LLM deployment
- Implemented Gemma 3n quantization for reduced memory usage
- Optimized prompts for faster inference

### 11.4 User Data Privacy

**Challenge**: Ensuring complete data privacy while maintaining functionality.

**Solution**:
- All processing performed locally
- No external API calls for core functionality
- Encrypted storage for sensitive user data
- JWT tokens for secure authentication

### 11.5 Multilingual Support

**Challenge**: Supporting multiple languages with consistent quality.

**Solution**:
- Used multilingual Gemma 3n model
- Implemented language-specific prompts
- Added language validation and mapping
- Used ISO language codes for standardization

## 12. Future Enhancements

### 12.1 Planned Features

#### Spaced Repetition System
```python
# Spaced repetition algorithm implementation
class SpacedRepetition:
    def calculate_next_review(self, word: Word, user_progress: UserWordProgress) -> datetime:
        """Calculate optimal next review time based on forgetting curve."""
        # Implementation details...
```

#### Interactive Quizzes
- Multiple choice questions based on vocabulary
- Fill-in-the-blank exercises
- Sentence completion tasks
- Progress tracking and analytics

#### Multimodal Support
- **Audio Processing**: Speech-to-text for pronunciation practice
- **Image Processing**: OCR for learning from images
- **Video Support**: Extract text from video content

#### Advanced Analytics
- Learning progress visualization
- Vocabulary retention metrics
- Study time tracking
- Performance recommendations

### 12.2 Technical Improvements

#### Performance Optimizations
- **Async Processing**: Implement async/await for I/O operations
- **Background Tasks**: Queue-based processing for long-running operations
- **Microservices**: Split into specialized services
- **CDN Integration**: Static asset delivery optimization

#### AI Enhancements
- **Fine-tuning**: Custom model training on user data
- **Ensemble Methods**: Combine multiple LLM outputs
- **Active Learning**: Adaptive prompt selection
- **Personalization**: User-specific model adaptation

#### Scalability Improvements
- **Horizontal Scaling**: Load balancing across multiple instances
- **Database Sharding**: Distribute data across multiple databases
- **Caching Layers**: Multi-level caching strategy
- **Message Queues**: Asynchronous task processing

### 12.3 Integration Opportunities

#### External Services
- **Anki Integration**: Export vocabulary to Anki decks
- **Google Translate API**: Fallback for complex translations
- **Wikipedia API**: Rich context and definitions
- **YouTube API**: Video content for learning

#### Mobile Applications
- **React Native**: Cross-platform mobile app
- **Offline Sync**: Local-first architecture
- **Push Notifications**: Reminder system
- **Voice Input**: Speech recognition for input

#### Educational Platforms
- **LMS Integration**: Canvas, Moodle, Blackboard
- **API Partnerships**: Language learning platforms
- **Content Marketplaces**: Share and discover learning materials
- **Social Features**: Collaborative learning communities

---

## Conclusion

The Personal Dictionary API represents a comprehensive solution for offline, privacy-first language learning. By combining modern web technologies with local AI processing, the system provides a powerful yet accessible platform for vocabulary building.

Key achievements include:
- **Complete offline operation** with local AI processing
- **Scalable architecture** using FastAPI and PostgreSQL
- **Semantic intelligence** through vector embeddings
- **Secure authentication** with JWT and bcrypt
- **Modular design** enabling easy extension and maintenance

The project demonstrates the feasibility of building sophisticated AI applications that prioritize user privacy while maintaining high performance and usability. The combination of LangGraph orchestration, vector similarity search, and structured LLM outputs creates a robust foundation for future enhancements.

As language learning technology continues to evolve, this architecture provides a solid foundation for incorporating new AI capabilities, multimodal inputs, and personalized learning experiences while maintaining the core principles of privacy and offline functionality.
