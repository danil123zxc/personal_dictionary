from sqlalchemy import (
    Boolean, Column, Integer, String, Text, ForeignKey, CHAR, Table, DateTime, func, CheckConstraint, UniqueConstraint
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship, validates
from app.database import Base

# Vector embedding dimension for pgvector
# This should match the embedding model's output dimension
EMB_DIM = 384

class EmbeddingMixin:
    """
    Mixin class for models that support vector embeddings.
    
    This mixin provides vector storage capabilities using pgvector.
    It includes fields for storing embeddings, model information, and
    tracking when embeddings were last updated.
    
    Attributes:
        embedding: Vector column for storing embeddings (nullable)
        embedding_model: Name/identifier of the embedding model used
        embedding_updated_at: Timestamp of last embedding update
    """
    # Vector column for storing embeddings; nullable=True allows backfilling later
    embedding = Column(Vector(EMB_DIM), nullable=True)
    # Optional metadata about the embedding model used
    embedding_model = Column(String(64), nullable=True)
    # Timestamp for tracking when embeddings were last updated
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)

class TimestampMixin:
    """
    Mixin class for automatic timestamp management.
    
    This mixin provides automatic creation and update timestamps for models.
    It uses PostgreSQL's server-side functions for accurate timestamps.
    
    Attributes:
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """
    # Server-side default timestamp for creation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Server-side default and update timestamp
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class User(Base, TimestampMixin):
    """
    User model for authentication and user management.
    
    This model represents users of the Personal Dictionary API.
    It includes authentication fields, profile information, and
    relationship to learning profiles.
    
    Attributes:
        id: Primary key
        username: Unique username for login
        password: Hashed password (bcrypt)
        full_name: User's full name
        email: Unique email address
        disabled: Account status flag
        
    Relationships:
        learning_profiles: One-to-many relationship with LearningProfile
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Stored as bcrypt hash
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)

    # Relationship to learning profiles
    learning_profiles = relationship("LearningProfile", back_populates="user")

    @validates('username')
    def validate_username(self, key, username):
        """
        Validate username length and format.
        
        Args:
            key: Column name (unused)
            username: Username to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValueError: If username is invalid
        """
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        return username

class Language(Base, TimestampMixin):
    """
    Language model for supported languages.
    
    This model represents languages supported by the system.
    It includes ISO language codes and human-readable names.
    
    Attributes:
        id: Primary key
        code: ISO language code (e.g., 'en', 'es')
        name: Human-readable language name (e.g., 'English', 'Español')
        
    Relationships:
        learning_profiles_primary: Learning profiles where this is the primary language
        learning_profiles_foreign: Learning profiles where this is the foreign language
        translations: Translations in this language
        words: Words in this language
        definitions: Definitions in this language
        examples: Examples in this language
    """
    __tablename__ = 'languages'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(CHAR(5), unique=True, index=True)  # ISO language code
    name = Column(String, unique=True, index=True, nullable=False)

    # Relationships for learning profiles (both directions)
    learning_profiles_primary = relationship(
        "LearningProfile", back_populates="primary_language",
        foreign_keys="LearningProfile.primary_language_id"
    )
    learning_profiles_foreign = relationship(
        "LearningProfile", back_populates="foreign_language",
        foreign_keys="LearningProfile.foreign_language_id"
    )

    # Relationships to content in this language
    translations = relationship("Translation", back_populates="language")
    words = relationship("Word", back_populates="language")
    definitions = relationship("Definition", back_populates="language")
    examples = relationship("Example", back_populates="language")

class Word(Base, TimestampMixin, EmbeddingMixin):
    """
    Word model for vocabulary management.
    
    This model represents individual words/lemmas in the system.
    It includes vector embeddings for semantic search capabilities.
    
    Attributes:
        id: Primary key
        lemma: Base form of the word (e.g., 'run' for 'running')
        language_id: Foreign key to Language
        embedding: Vector representation for semantic search
        embedding_model: Name of the embedding model used
        
    Relationships:
        language: The language this word belongs to
        dictionaries: Dictionary entries containing this word
        user_word_progress: Learning progress for this word
    """
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True, index=True)
    lemma = Column(String, index=True, nullable=False)  # Base form of the word
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)

    # Relationships
    language = relationship("Language", back_populates="words")         
    dictionaries = relationship("Dictionary", back_populates="word")    
    user_word_progress = relationship("UserWordProgress", back_populates="word")

class UserWordProgress(Base, TimestampMixin):
    """
    User word progress tracking model.
    
    This model tracks individual user progress with specific words,
    including proficiency levels and review scheduling.
    
    Attributes:
        id: Primary key
        word_id: Foreign key to Word
        proficiency: Proficiency level (0-100)
        last_reviewed: Timestamp of last review
        next_review_due: Timestamp for next review
        learning_profile_id: Foreign key to LearningProfile
        
    Relationships:
        word: The word being tracked
        learning_profile: The learning profile this progress belongs to
    """
    __tablename__ = 'user_word_progress'

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    proficiency = Column(Integer, default=0)  # 0-100 scale
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    learning_profile_id = Column(Integer, ForeignKey('learning_profiles.id'))

    # Relationships
    word = relationship("Word", back_populates="user_word_progress")
    learning_profile = relationship("LearningProfile", back_populates="progress")

    # Ensure unique word per learning profile
    __table_args__ = (
        UniqueConstraint('learning_profile_id', 'word_id', name='uq_lprof_word'),
    )
    
class LearningProfile(Base, TimestampMixin):
    """
    Learning profile model for user language learning configuration.
    
    This model represents a user's language learning setup, defining
    which languages they're learning and their current status.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        primary_language_id: Foreign key to Language (user's native language)
        foreign_language_id: Foreign key to Language (language being learned)
        is_active: Whether this profile is currently active
        
    Relationships:
        user: The user this profile belongs to
        primary_language: User's native language
        foreign_language: Language being learned
        dictionaries: Dictionary entries for this profile
        texts: Text entries for this profile
        progress: Word progress tracking for this profile
    """
    __tablename__ = 'learning_profiles'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    primary_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    foreign_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="learning_profiles")
    primary_language = relationship("Language", foreign_keys=[primary_language_id], back_populates="learning_profiles_primary")
    foreign_language = relationship("Language", foreign_keys=[foreign_language_id], back_populates="learning_profiles_foreign")
    dictionaries = relationship("Dictionary", back_populates="learning_profile")
    texts = relationship("Text", back_populates="learning_profile")
    progress = relationship("UserWordProgress", back_populates="learning_profile")

    # Ensure unique language pair per user
    __table_args__ = (
        UniqueConstraint('user_id', 'primary_language_id', 'foreign_language_id', name='uq_user_lang_pair'),
    )

class Dictionary(Base, TimestampMixin):
    """
    Dictionary model for user's personal vocabulary.
    
    This model represents entries in a user's personal dictionary,
    linking words to learning profiles with optional notes.
    
    Attributes:
        id: Primary key
        learning_profile_id: Foreign key to LearningProfile
        word_id: Foreign key to Word
        notes: Optional user notes about the word
        
    Relationships:
        learning_profile: The learning profile this entry belongs to
        word: The word in this dictionary entry
        translations: Translations for this word
        definitions: Definitions for this word
        examples: Examples for this word
    """
    __tablename__ = 'dictionaries'
    id = Column(Integer, primary_key=True, index=True)
    learning_profile_id = Column(Integer, ForeignKey('learning_profiles.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    notes = Column(Text, nullable=True)  # User notes about the word

    # Relationships
    learning_profile = relationship("LearningProfile", back_populates="dictionaries")
    word = relationship("Word", back_populates="dictionaries")
    translations = relationship("Translation", back_populates="dictionary")
    definitions = relationship("Definition", back_populates="dictionary")
    examples = relationship("Example", back_populates="dictionary")

    # Ensure unique word per learning profile
    __table_args__ = (
        UniqueConstraint('learning_profile_id', 'word_id', name='uq_dict_lprof_word'),
    )

class Translation(Base, TimestampMixin):
    """
    Translation model for word translations.
    
    This model stores translations of words in different languages,
    linked to dictionary entries.
    
    Attributes:
        id: Primary key
        dictionary_id: Foreign key to Dictionary
        language_id: Foreign key to Language (translation language)
        translation: The translated text
        
    Relationships:
        dictionary: The dictionary entry this translation belongs to
        language: The language of this translation
    """
    __tablename__ = 'translations'
    id = Column(Integer, primary_key=True, index=True)
    dictionary_id = Column(Integer, ForeignKey('dictionaries.id'), nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    translation = Column(String, nullable=False)

    # Relationships
    dictionary = relationship("Dictionary", back_populates="translations")
    language = relationship("Language", back_populates="translations")

class Definition(Base, TimestampMixin):
    """
    Definition model for word definitions.
    
    This model stores definitions of words in different languages,
    linked to dictionary entries.
    
    Attributes:
        id: Primary key
        dictionary_id: Foreign key to Dictionary
        language_id: Foreign key to Language (definition language)
        definition_text: The definition text
        original_text_id: Optional foreign key to Text (context source)
        
    Relationships:
        dictionary: The dictionary entry this definition belongs to
        language: The language of this definition
        original_text: The text that provided context for this definition
    """
    __tablename__ = 'definitions'
    id = Column(Integer, primary_key=True, index=True)
    dictionary_id = Column(Integer, ForeignKey('dictionaries.id'), nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    definition_text = Column(Text, nullable=False)
    original_text_id = Column(Integer, ForeignKey('texts.id'), nullable=True)  # Optional context source

    # Relationships
    dictionary = relationship("Dictionary", back_populates="definitions")
    language = relationship("Language", back_populates="definitions")
    original_text = relationship("Text", back_populates="definitions")

class Example(Base, TimestampMixin):
    """
    Example model for word usage examples.
    
    This model stores example sentences showing how words are used,
    linked to dictionary entries.
    
    Attributes:
        id: Primary key
        dictionary_id: Foreign key to Dictionary
        language_id: Foreign key to Language (example language)
        example_text: The example sentence
        
    Relationships:
        dictionary: The dictionary entry this example belongs to
        language: The language of this example
    """
    __tablename__ = 'examples'
    id = Column(Integer, primary_key=True, index=True)
    dictionary_id = Column(Integer, ForeignKey('dictionaries.id'), nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    example_text = Column(Text, nullable=False)

    # Relationships
    dictionary = relationship("Dictionary", back_populates="examples")
    language = relationship("Language", back_populates="examples")

class Text(Base, TimestampMixin):
    """
    Text model for storing user text entries.
    
    This model stores text entries that users create for language learning,
    optionally linked to dictionary entries.
    
    Attributes:
        id: Primary key
        learning_profile_id: Foreign key to LearningProfile
        dictionary_id: Optional foreign key to Dictionary
        text: The text content
        
    Relationships:
        learning_profile: The learning profile this text belongs to
        dictionary: Optional dictionary entry this text is linked to
        definitions: Definitions generated from this text
    """
    __tablename__ = 'texts'
    id = Column(Integer, primary_key=True, index=True)
    learning_profile_id = Column(Integer, ForeignKey('learning_profiles.id'), nullable=False)
    dictionary_id = Column(Integer, ForeignKey('dictionaries.id'), nullable=True)  # Optional link
    text = Column(Text, nullable=False)

    # Relationships
    learning_profile = relationship("LearningProfile", back_populates="texts")
    dictionary = relationship("Dictionary")  # No back_populates to avoid circular reference
    definitions = relationship("Definition", back_populates="original_text")