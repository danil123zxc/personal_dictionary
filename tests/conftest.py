import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models import User, Language, Word, LearningProfile, Dictionary, Translation, Definition, Example, Text


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.disabled = False
    return user


@pytest.fixture
def sample_language():
    """Create a sample language for testing"""
    language = Mock(spec=Language)
    language.id = 1
    language.name = "English"
    language.code = "en"
    return language


@pytest.fixture
def sample_word():
    """Create a sample word for testing"""
    word = Mock(spec=Word)
    word.id = 1
    word.lemma = "hello"
    word.language_id = 1
    word.embedding = [0.1, 0.2, 0.3]
    word.embedding_model = "test-model"
    return word


@pytest.fixture
def sample_learning_profile():
    """Create a sample learning profile for testing"""
    profile = Mock(spec=LearningProfile)
    profile.id = 1
    profile.user_id = 1
    profile.primary_language_id = 1
    profile.foreign_language_id = 2
    profile.is_active = True
    return profile


@pytest.fixture
def sample_dictionary():
    """Create a sample dictionary entry for testing"""
    dictionary = Mock(spec=Dictionary)
    dictionary.id = 1
    dictionary.learning_profile_id = 1
    dictionary.word_id = 1
    dictionary.notes = "Test note"
    return dictionary


@pytest.fixture
def sample_translation():
    """Create a sample translation for testing"""
    translation = Mock(spec=Translation)
    translation.id = 1
    translation.translation = "hola"
    translation.language_id = 2
    translation.dictionary_id = 1
    translation.embedding = [0.1, 0.2, 0.3]
    translation.embedding_model = "test-model"
    return translation


@pytest.fixture
def sample_definition():
    """Create a sample definition for testing"""
    definition = Mock(spec=Definition)
    definition.id = 1
    definition.definition_text = "A greeting"
    definition.language_id = 1
    definition.dictionary_id = 1
    definition.embedding = [0.1, 0.2, 0.3]
    definition.embedding_model = "test-model"
    return definition


@pytest.fixture
def sample_example():
    """Create a sample example for testing"""
    example = Mock(spec=Example)
    example.id = 1
    example.example_text = "Hello, how are you?"
    example.language_id = 1
    example.dictionary_id = 1
    example.embedding = [0.1, 0.2, 0.3]
    example.embedding_model = "test-model"
    return example


@pytest.fixture
def sample_text():
    """Create a sample text for testing"""
    text = Mock(spec=Text)
    text.id = 1
    text.text = "Hello world"
    text.learning_profile_id = 1
    text.dictionary_id = 1
    return text


@pytest.fixture
def mock_embedding_response():
    """Create a mock embedding response"""
    mock_doc = Mock()
    mock_doc.metadata = {
        'embedding': [0.1, 0.2, 0.3, 0.4, 0.5] * 76,  # 384-dimensional vector
        'model': 'all-MiniLM-L6-v2'
    }
    return [mock_doc]


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123",
        "confirm_password": "password123"
    }


@pytest.fixture
def sample_word_data():
    """Sample word data for testing"""
    return {
        "lemma": "hello",
        "language_id": 1
    }


@pytest.fixture
def sample_translation_data():
    """Sample translation data for testing"""
    return {
        "translation": "hola",
        "language_id": 2,
        "dictionary_id": 1
    }


@pytest.fixture
def sample_definition_data():
    """Sample definition data for testing"""
    return {
        "definition_text": "A greeting",
        "language_id": 1,
        "dictionary_id": 1
    }


@pytest.fixture
def sample_example_data():
    """Sample example data for testing"""
    return {
        "example_text": "Hello, how are you?",
        "language_id": 1,
        "dictionary_id": 1
    }


@pytest.fixture
def sample_text_data():
    """Sample text data for testing"""
    return {
        "learning_profile_id": 1,
        "dictionary_id": 1,
        "text": "Hello world"
    }


@pytest.fixture
def sample_dictionary_data():
    """Sample dictionary data for testing"""
    return {
        "learning_profile_id": 1,
        "word_id": 1,
        "notes": "Test note"
    }


@pytest.fixture
def sample_learning_profile_data():
    """Sample learning profile data for testing"""
    return {
        "user_id": 1,
        "primary_language_id": 1,
        "foreign_language_id": 2,
        "is_active": True
    }


@pytest.fixture
def sample_language_data():
    """Sample language data for testing"""
    return {
        "name": "Spanish"
    }
