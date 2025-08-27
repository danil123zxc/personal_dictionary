import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.crud import (
    register_user, login, get_user_info, update_current_user, delete_current_user,
    create_language, create_learning_profile, create_word, create_in_dictionary,
    create_translation, create_text, get_synonyms, update_word, update_translation,
    update_example, update_definition
)
from app.crud_schemas import (
    UserCreate, UserUpdate, LanguageBase, LearningProfileBase, WordBase,
    DictionaryBase, TranslationBase, TextBase, DefinitionBase, ExampleBase
)
from app.models import User, Language, Word, LearningProfile, Dictionary, Translation, Definition, Example, Text


class TestUserFunctions:
    """Test user-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.disabled = False
        return user
    
    @pytest.fixture
    def user_create_data(self):
        return UserCreate(
            username="newuser",
            email="new@example.com",
            full_name="New User",
            password="password123",
            confirm_password="password123"
        )
    
    def test_register_user_success(self, mock_db, user_create_data):
        """Test successful user registration"""
        # Mock no existing user
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
                # Mock user creation
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = user_create_data.username
        mock_user.email = user_create_data.email
        mock_user.full_name = user_create_data.full_name
        mock_user.disabled = False

        # Mock the database operations
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch('app.crud.auth.get_password_hash', return_value="hashed_password"):
            with patch('app.crud.User', return_value=mock_user):
                result = register_user(mock_db, user_create_data)
        
        assert result.username == user_create_data.username
        assert result.email == user_create_data.email
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_register_user_duplicate_username(self, mock_db, user_create_data):
        """Test user registration with duplicate username"""
        # Mock existing user
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            register_user(mock_db, user_create_data)
        
        assert exc_info.value.status_code == 409
        assert "already registered" in exc_info.value.detail
    
    def test_login_success(self, mock_db):
        """Test successful login"""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        
        with patch('app.crud.auth.authenticate_user', return_value=mock_user), \
             patch('app.crud.auth.create_access_token', return_value="token123"), \
             patch('app.crud.auth.ACCESS_TOKEN_EXPIRE_MINUTES', 30):
            
            result = login(mock_db, "testuser", "password123")
        
        assert result.access_token == "token123"
        assert result.token_type == "bearer"
    
    def test_login_failure(self, mock_db):
        """Test login with invalid credentials"""
        with patch('app.crud.auth.authenticate_user', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                login(mock_db, "testuser", "wrongpassword")
        
        assert exc_info.value.status_code == 401
    
    def test_get_user_info_by_id(self, mock_db, mock_user):
        """Test getting user info by ID"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = get_user_info(mock_db, user_id=1)
        
        assert result.id == mock_user.id
        assert result.username == mock_user.username
    
    def test_get_user_info_by_username(self, mock_db, mock_user):
        """Test getting user info by username"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = get_user_info(mock_db, username="testuser")
        
        assert result.username == mock_user.username
    
    def test_get_user_info_no_criteria(self, mock_db):
        """Test getting user info without criteria"""
        with pytest.raises(HTTPException) as exc_info:
            get_user_info(mock_db)
        
        assert exc_info.value.status_code == 400
    
    def test_update_current_user_success(self, mock_db, mock_user):
        """Test successful user update"""
        update_data = UserUpdate(username="newusername", full_name="New Name")
        
        # Mock no duplicate username
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = update_current_user(mock_db, mock_user, update_data)
        
        assert mock_user.username == "newusername"
        assert mock_user.full_name == "New Name"
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
    
    def test_update_current_user_duplicate_username(self, mock_db, mock_user):
        """Test user update with duplicate username"""
        update_data = UserUpdate(username="existinguser")
        
        # Mock existing user with same username
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            update_current_user(mock_db, mock_user, update_data)
        
        assert exc_info.value.status_code == 409
    
    def test_delete_current_user_soft(self, mock_db, mock_user):
        """Test soft delete of user"""
        mock_user.disabled = False
        
        delete_current_user(mock_db, mock_user, hard=False)
        
        assert mock_user.disabled == True
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
    
    def test_delete_current_user_hard(self, mock_db, mock_user):
        """Test hard delete of user"""
        delete_current_user(mock_db, mock_user, hard=True)
        
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()


class TestLanguageFunctions:
    """Test language-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    def test_create_language_success(self, mock_db):
        """Test successful language creation"""
        language_data = LanguageBase(name="Español")
        
        # Mock language codes
        with patch('app.crud.language_codes', {'Español': 'es'}):
            # Mock no existing language
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
                    # Mock language creation
        mock_language = Mock(spec=Language)
        mock_language.id = 1
        mock_language.name = "Español"
        mock_language.code = "es"

        # Mock the database operations
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch('app.crud.Language', return_value=mock_language):
            result = create_language(mock_db, language_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_language_invalid(self, mock_db):
        """Test language creation with invalid language"""
        language_data = LanguageBase(name="InvalidLanguage")
        
        with patch('app.crud.language_codes', {'Español': 'es'}):
            with pytest.raises(HTTPException) as exc_info:
                create_language(mock_db, language_data)
        
        assert exc_info.value.status_code == 400


class TestLearningProfileFunctions:
    """Test learning profile CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    @pytest.fixture
    def learning_profile_data(self):
        return LearningProfileBase(
            user_id=1,
            primary_language_id=1,
            foreign_language_id=2,
            is_active=True
        )
    
    def test_create_learning_profile_success(self, mock_db, mock_user, learning_profile_data):
        """Test successful learning profile creation"""
        # Mock no existing profile
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock profile creation
        mock_profile = Mock(spec=LearningProfile)
        mock_profile.id = 1
        mock_profile.user_id = mock_user.id
        mock_profile.primary_language_id = learning_profile_data.primary_language_id
        mock_profile.foreign_language_id = learning_profile_data.foreign_language_id
        
        result = create_learning_profile(mock_db, learning_profile_data, mock_user)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_learning_profile_duplicate(self, mock_db, mock_user, learning_profile_data):
        """Test learning profile creation with duplicate"""
        # Mock existing profile
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            create_learning_profile(mock_db, learning_profile_data, mock_user)
        
        assert exc_info.value.status_code == 409


class TestWordFunctions:
    """Test word-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def word_data(self):
        return WordBase(lemma="hello", language_id=1)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    def test_create_word_success(self, mock_db, word_data):
        """Test successful word creation"""
        # Mock language exists
        mock_language = Mock(spec=Language)
        mock_language.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_language
        
        # Mock no existing word
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_language, None]
        
        # Mock embedding generation
        mock_embedding_doc = [Mock()]
        mock_embedding_doc[0].metadata = {'embedding': [0.1, 0.2, 0.3], 'model': 'test-model'}
        
        with patch('app.crud.embed', return_value=mock_embedding_doc):
            # Mock word creation
            mock_word = Mock(spec=Word)
            mock_word.id = 1
            mock_word.lemma = word_data.lemma
            mock_word.language_id = word_data.language_id
            
            result = create_word(mock_db, word_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_word_language_not_found(self, mock_db, word_data):
        """Test word creation with non-existent language"""
        # Mock language doesn't exist
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            create_word(mock_db, word_data)
        
        assert exc_info.value.status_code == 404
    
    def test_get_synonyms_success(self, mock_db, mock_user):
        """Test successful synonym retrieval"""
        # Mock embedding generation
        mock_embedding_doc = [Mock()]
        mock_embedding_doc[0].metadata = {'embedding': [0.1, 0.2, 0.3]}
        
        # Mock query results
        mock_word = Mock(spec=Word)
        mock_word.id = 1
        mock_word.lemma = "similar_word"
        
        with patch('app.crud.embed', return_value=mock_embedding_doc):
            mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_word]
            
            result = get_synonyms(mock_db, "hello", 1, 1, top_k=5, min_similarity=0.8)
        
        assert len(result) == 1
        assert result[0].lemma == "similar_word"
    
    def test_update_word_success(self, mock_db, mock_user):
        """Test successful word update"""
        # Mock word exists
        mock_word = Mock(spec=Word)
        mock_word.id = 1
        mock_word.lemma = "old_lemma"
        mock_word.language_id = 1
        
        # Mock user has access
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_word, Mock()]
        
        # Mock no duplicate
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_word, Mock(), None]
        
        # Mock embedding generation
        mock_embedding_doc = [Mock()]
        mock_embedding_doc[0].metadata = {'embedding': [0.1, 0.2, 0.3], 'model': 'test-model'}
        
        update_data = WordBase(lemma="new_lemma", language_id=1)
        
        with patch('app.crud.embed', return_value=mock_embedding_doc):
            result = update_word(mock_db, 1, update_data, mock_user)
        
        assert mock_word.lemma == "new_lemma"
        mock_db.add.assert_called_once_with(mock_word)
        mock_db.commit.assert_called_once()


class TestDictionaryFunctions:
    """Test dictionary-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    @pytest.fixture
    def dictionary_data(self):
        return DictionaryBase(learning_profile_id=1, word_id=1, notes="Test note")
    
    def test_create_in_dictionary_success(self, mock_db, mock_user, dictionary_data):
        """Test successful dictionary entry creation"""
        # Mock learning profile belongs to user
        mock_lp = Mock(spec=LearningProfile)
        mock_lp.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_lp
        
        # Mock no existing entry
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_lp, None]
        
        # Mock dictionary creation
        mock_dict = Mock(spec=Dictionary)
        mock_dict.id = 1
        mock_dict.learning_profile_id = dictionary_data.learning_profile_id
        mock_dict.word_id = dictionary_data.word_id
        
        result = create_in_dictionary(mock_db, dictionary_data, mock_user)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_in_dictionary_forbidden(self, mock_db, mock_user, dictionary_data):
        """Test dictionary creation with forbidden access"""
        # Mock learning profile doesn't belong to user
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            create_in_dictionary(mock_db, dictionary_data, mock_user)
        
        assert exc_info.value.status_code == 403


class TestTranslationFunctions:
    """Test translation-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    @pytest.fixture
    def translation_data(self):
        return TranslationBase(translation="hola", language_id=2, dictionary_id=1)
    
    def test_create_translation_success(self, mock_db, mock_user, translation_data):
        """Test successful translation creation"""
        # Mock language exists
        mock_language = Mock(spec=Language)
        mock_language.id = 2
        
        # Mock dictionary exists and belongs to user
        mock_dictionary = Mock(spec=Dictionary)
        mock_dictionary.learning_profile = Mock()
        mock_dictionary.learning_profile.user_id = mock_user.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_language, mock_dictionary]
        
        # Mock translation creation
        mock_translation = Mock(spec=Translation)
        mock_translation.id = 1
        mock_translation.translation = translation_data.translation
        
        result = create_translation(mock_db, translation_data, mock_user)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_update_translation_success(self, mock_db, mock_user):
        """Test successful translation update"""
        # Mock translation exists
        mock_translation = Mock(spec=Translation)
        mock_translation.id = 1
        mock_translation.translation = "old_translation"
        mock_translation.language_id = 1
        mock_translation.dictionary_id = 1
        
        # Mock dictionary belongs to user
        mock_dictionary = Mock(spec=Dictionary)
        mock_dictionary.learning_profile = Mock()
        mock_dictionary.learning_profile.user_id = mock_user.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_translation, mock_dictionary]
        
        # Mock embedding generation
        mock_embedding_doc = [Mock()]
        mock_embedding_doc[0].metadata = {'embedding': [0.1, 0.2, 0.3], 'model': 'test-model'}
        
        update_data = TranslationBase(translation="new_translation", language_id=2, dictionary_id=1)
        
        with patch('app.crud.embed', return_value=mock_embedding_doc):
            result = update_translation(mock_db, 1, update_data, mock_user)
        
        assert mock_translation.translation == "new_translation"
        mock_db.add.assert_called_once_with(mock_translation)
        mock_db.commit.assert_called_once()


class TestExampleFunctions:
    """Test example-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    def test_update_example_success(self, mock_db, mock_user):
        """Test successful example update"""
        # Mock example exists
        mock_example = Mock(spec=Example)
        mock_example.id = 1
        mock_example.example_text = "old example"
        mock_example.language_id = 1
        mock_example.dictionary_id = 1
        
        # Mock dictionary belongs to user
        mock_dictionary = Mock(spec=Dictionary)
        mock_dictionary.learning_profile = Mock()
        mock_dictionary.learning_profile.user_id = mock_user.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_example, mock_dictionary]
        
        # Mock embedding generation
        mock_embedding_doc = [Mock()]
        mock_embedding_doc[0].metadata = {'embedding': [0.1, 0.2, 0.3], 'model': 'test-model'}
        
        update_data = ExampleBase(example_text="new example", language_id=2, dictionary_id=1)
        
        with patch('app.crud.embed', return_value=mock_embedding_doc):
            result = update_example(mock_db, 1, update_data, mock_user)
        
        assert mock_example.example_text == "new example"
        mock_db.add.assert_called_once_with(mock_example)
        mock_db.commit.assert_called_once()


class TestDefinitionFunctions:
    """Test definition-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    def test_update_definition_success(self, mock_db, mock_user):
        """Test successful definition update"""
        # Mock definition exists
        mock_definition = Mock(spec=Definition)
        mock_definition.id = 1
        mock_definition.definition_text = "old definition"
        mock_definition.language_id = 1
        mock_definition.dictionary_id = 1
        
        # Mock dictionary belongs to user
        mock_dictionary = Mock(spec=Dictionary)
        mock_dictionary.learning_profile = Mock()
        mock_dictionary.learning_profile.user_id = mock_user.id
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_definition, mock_dictionary]
        
        # Mock embedding generation
        mock_embedding_doc = [Mock()]
        mock_embedding_doc[0].metadata = {'embedding': [0.1, 0.2, 0.3], 'model': 'test-model'}
        
        update_data = DefinitionBase(definition_text="new definition", language_id=2, dictionary_id=1)
        
        with patch('app.crud.embed', return_value=mock_embedding_doc):
            result = update_definition(mock_db, 1, update_data, mock_user)
        
        assert mock_definition.definition_text == "new definition"
        mock_db.add.assert_called_once_with(mock_definition)
        mock_db.commit.assert_called_once()


class TestTextFunctions:
    """Test text-related CRUD functions"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        return user
    
    @pytest.fixture
    def text_data(self):
        return TextBase(learning_profile_id=1, dictionary_id=1, text="Hello world")
    
    def test_create_text_success(self, mock_db, mock_user, text_data):
        """Test successful text creation"""
        # Mock active learning profile
        mock_profile = Mock(spec=LearningProfile)
        mock_profile.id = 1
        mock_profile.user_id = mock_user.id
        mock_profile.is_active = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        # Mock text creation
        mock_text = Mock(spec=Text)
        mock_text.id = 1
        mock_text.text = text_data.text
        mock_text.learning_profile_id = mock_profile.id
        
        result = create_text(mock_db, text_data, mock_user)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_text_no_active_profile(self, mock_db, mock_user, text_data):
        """Test text creation with no active learning profile"""
        # Mock no active learning profile
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            create_text(mock_db, text_data, mock_user)
        
        assert exc_info.value.status_code == 400


# Integration test helpers
class TestIntegrationHelpers:
    """Helper functions for integration tests"""
    
    @pytest.fixture
    def sample_user_data(self):
        return {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123",
            "confirm_password": "password123"
        }
    
    @pytest.fixture
    def sample_word_data(self):
        return {
            "lemma": "hello",
            "language_id": 1
        }
    
    @pytest.fixture
    def sample_translation_data(self):
        return {
            "translation": "hola",
            "language_id": 2,
            "dictionary_id": 1
        }
    
    def test_data_validation(self, sample_user_data, sample_word_data, sample_translation_data):
        """Test that sample data can be converted to Pydantic models"""
        # Test user data
        user_create = UserCreate(**sample_user_data)
        assert user_create.username == sample_user_data["username"]
        assert user_create.email == sample_user_data["email"]
        
        # Test word data
        word_base = WordBase(**sample_word_data)
        assert word_base.lemma == sample_word_data["lemma"]
        assert word_base.language_id == sample_word_data["language_id"]
        
        # Test translation data
        translation_base = TranslationBase(**sample_translation_data)
        assert translation_base.translation == sample_translation_data["translation"]
        assert translation_base.language_id == sample_translation_data["language_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
