# Personal Dictionary API - Offline AI Language Learning Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **offline**, **privacy-first** AI-powered language learning API that helps you **translate**, **define**, and **practice vocabulary** directly from any text — **no internet required**.

Powered by the **Gemma 3n** language model running locally via **Ollama**, this FastAPI application provides context-aware translations, definitions, example sentences, and related word suggestions. All results are stored in a PostgreSQL database with vector embeddings for semantic search.

## ✨ Features

### 🤖 AI-Powered Language Processing
- **Offline AI Processing** — Works entirely offline for maximum privacy
- **Context-Aware Translations** — Extracts key content words, lemmatizes them, and translates them into your target language
- **Smart Definitions** — Generates short, precise definitions based on the word's meaning in your specific context
- **Example Sentences** — Creates simple, clear example sentences to reinforce learning
- **Semantic Similar Words** — Finds related vocabulary using vector embeddings and similarity search

### 🔐 User Management & Security
- **JWT Authentication** — Secure user authentication with token-based sessions
- **User Registration & Profiles** — Create and manage user accounts with learning profiles
- **Password Security** — Bcrypt hashing for secure password storage
- **Role-Based Access** — User-specific data isolation and permissions

### 📚 Learning Management
- **Personal Dictionary** — Save words, translations, definitions, and examples to your personal database
- **Learning Profiles** — Manage multiple language pairs and learning goals
- **Progress Tracking** — Monitor your vocabulary learning progress
- **Vector Search** — Find similar words using semantic embeddings

### 🌍 Multilingual Support
- **Multiple Languages** — English, Russian, Korean, Chinese, Japanese, Spanish, French, German, Italian, Portuguese
- **Language Pairs** — Support for any combination of supported languages
- **ISO Language Codes** — Standard language identification and mapping

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 13+ with pgvector extension
- Ollama with Gemma 3n model
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd personal_dictionary
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📖 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Authenticate and get JWT token
- `GET /users/me` - Get current user profile
- `PUT /update_user/me` - Update user profile
- `DELETE /user_delete/me` - Delete user account

### Language Management
- `POST /create_language` - Add a new language to the system

### Learning Profiles
- `POST /create_learning_profile` - Create a learning profile for language pair

### Word Management
- `POST /create_word` - Add a word with vector embeddings
- `POST /create_in_dictionary` - Add word to personal dictionary
- `POST /create_translation` - Add translation for a word
- `POST /create_text` - Create text entry for learning

### AI-Powered Generation
- `POST /translate` - Generate translations for text
- `POST /definition` - Generate word definitions
- `POST /examples` - Generate usage examples

## 🛠️ How It Works

### 1. Text Processing Pipeline
```
Input Text → Word Extraction → Translation → Definition → Examples → Storage
```

### 2. AI Processing Steps
1. **Input any text** — e.g., a news article, short story, or paragraph
2. **Word extraction & lemmatization** — Extract content words in base form
3. **Translation** — Translate words into target language
4. **Definition generation** — Generate context-aware definitions
5. **Example creation** — Create natural example sentences
6. **Similar words search** — Find semantically related vocabulary
7. **Database storage** — Save everything with vector embeddings

### 3. Vector Embeddings
- Uses **all-MiniLM-L6-v2** for semantic embeddings
- **pgvector** for efficient similarity search
- **384-dimensional** vectors for optimal performance

## 🧠 Tech Stack

### Supported Languages

| Language | Code | Name |
|----------|------|------|
| English | `en` | English |
| Russian | `ru` | Русский |
| Korean | `ko` | 한국어 |
| Chinese | `zh` | 中文 |
| Japanese | `ja` | 日本語 |
| Spanish | `es` | Español |
| French | `fr` | Français |
| German | `de` | Deutsch |
| Italian | `it` | Italiano |
| Portuguese | `pt` | Português |

## 🚀 Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "password": "securepassword123",
    "confirm_password": "securepassword123"
  }'
```

### Generate Translations
```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world, how are you today?",
    "src_language": "English",
    "tgt_language": "Spanish"
  }'
```

### Generate Definitions
```bash
curl -X POST "http://localhost:8000/definition" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "hello",
    "language": "English",
    "context": "Hello, how are you?"
  }'
```

## 🔮 Future Plans

- **Spaced Repetition System** — Optimized review scheduling
- **Interactive Quizzes** — Active recall practice
- **Multimodal Support** — Learn from audio and images
- **Custom Export Formats** — Anki and flashcard integration
- **Mobile App** — Native mobile application
- **Collaborative Learning** — Share and learn with others
- **Advanced Analytics** — Learning progress insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


**Built with ❤️ for language learners everywhere**
