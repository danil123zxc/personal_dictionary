from sqlalchemy import (
    Boolean, Column, Integer, String, Text, ForeignKey, CHAR, Table, DateTime, func, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from app.database import Base

# Association table
word_translations = Table(
    'word_translations',
    Base.metadata,
    Column('word_id', Integer, ForeignKey('words.id', ondelete='CASCADE'), primary_key=True),
    Column('translation_id', Integer, ForeignKey('words.id', ondelete='CASCADE'), primary_key=True),
    CheckConstraint('word_id != translation_id', name='no_self_translation'),
    UniqueConstraint('word_id', 'translation_id', name='unique_translation_pair')
)

# Timestamp mixin
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# User
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    learning_profiles = relationship("LearningProfile", back_populates="user")

    @validates('username')
    def validate_username(self, key, username):
        assert len(username) >= 3, "Username must be at least 3 characters"
        return username

# Language
class Language(Base, TimestampMixin):
    __tablename__ = 'languages'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(CHAR(5), unique=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    learning_profiles_primary = relationship("LearningProfile", back_populates="primary_language", foreign_keys="LearningProfile.primary_language_id")
    learning_profiles_foreign = relationship("LearningProfile", back_populates="foreign_language", foreign_keys="LearningProfile.foreign_language_id")
    
    words = relationship("Word", back_populates="language")
    definitions = relationship("Definition", back_populates="language")
    examples = relationship("Example", back_populates="language")

# LearningProfile
class LearningProfile(Base, TimestampMixin):
    __tablename__ = 'learning_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    primary_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    foreign_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="learning_profiles")
    primary_language = relationship("Language", foreign_keys=[primary_language_id], back_populates="learning_profiles_primary")
    foreign_language = relationship("Language", foreign_keys=[foreign_language_id], back_populates="learning_profiles_foreign")
    dictionaries = relationship("Dictionary", back_populates="learning_profile")
    word_progress = relationship("UserWordProgress", back_populates="learning_profile")
    texts = relationship("Text", back_populates="learning_profile")

    __table_args__ = (
        CheckConstraint('primary_language_id != foreign_language_id', name='different_languages'),
    )

# Dictionary
class Dictionary(Base, TimestampMixin):
    __tablename__ = 'dictionaries'
    
    id = Column(Integer, primary_key=True, index=True)
    learning_profile_id = Column(Integer, ForeignKey('learning_profiles.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    notes = Column(Text, nullable=True)
    original_text_id = Column(Integer, ForeignKey('texts.id'))

    learning_profile = relationship("LearningProfile", back_populates="dictionaries")
    word = relationship("Word", back_populates="dictionaries")
    definitions = relationship("Definition", back_populates="dictionary")
    examples = relationship("Example", back_populates="dictionary")
    original_text = relationship("Text", back_populates="dictionaries")

# Word
class Word(Base, TimestampMixin):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True, index=True)
    lemma = Column(String, index=True, nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)

    language = relationship("Language", back_populates="words")
    dictionaries = relationship("Dictionary", back_populates="word")
    user_word_progress = relationship("UserWordProgress", back_populates="word")

    translations = relationship(
        "Word",
        secondary=word_translations,
        primaryjoin=id == word_translations.c.word_id,
        secondaryjoin=id == word_translations.c.translation_id,
        back_populates="translated_from"
    )
    translated_from = relationship(
        "Word",
        secondary=word_translations,
        primaryjoin=id == word_translations.c.translation_id,
        secondaryjoin=id == word_translations.c.word_id,
        back_populates="translations"
    )

# Definition
class Definition(Base, TimestampMixin):
    __tablename__ = 'definitions'
    
    id = Column(Integer, primary_key=True, index=True)
    definition_text = Column(Text, nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    dictionary_id = Column(Integer, ForeignKey('dictionaries.id'), nullable=False)
    original_text_id = Column(Integer, ForeignKey('texts.id'))

    language = relationship("Language", back_populates="definitions")
    dictionary = relationship("Dictionary", back_populates="definitions")
    original_text = relationship("Text", back_populates="definitions")

# Example
class Example(Base, TimestampMixin):
    __tablename__ = 'examples'
    
    id = Column(Integer, primary_key=True, index=True)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    dictionary_id = Column(Integer, ForeignKey('dictionaries.id'), nullable=False)
    example_text = Column(Text, nullable=False)
    
    language = relationship("Language", back_populates="examples")
    dictionary = relationship("Dictionary", back_populates="examples")

# UserWordProgress
class UserWordProgress(Base, TimestampMixin):
    __tablename__ = 'user_word_progress'
    
    id = Column(Integer, primary_key=True, index=True)
    learning_profile_id = Column(Integer, ForeignKey('learning_profiles.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    proficiency = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review_due = Column(DateTime(timezone=True), nullable=True)
    
    learning_profile = relationship("LearningProfile", back_populates="word_progress")
    word = relationship("Word", back_populates="user_word_progress")

# Text
class Text(Base, TimestampMixin):
    __tablename__ = 'texts'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    learning_profile_id = Column(Integer, ForeignKey('learning_profiles.id'), nullable=False)

    learning_profile = relationship("LearningProfile", back_populates="texts")
    dictionaries = relationship("Dictionary", back_populates="original_text")
    definitions = relationship("Definition", back_populates="original_text")

    __table_args__ = (
        UniqueConstraint('learning_profile_id', 'text', name='uq_user_text'),
    )
