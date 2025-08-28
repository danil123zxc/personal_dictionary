"""
Application settings and configuration.

This module centralizes all configuration settings for the application.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/dictionary",
        env="DATABASE_URL"
    )
    
    # Redis settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Ollama settings
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    OLLAMA_MODEL: str = Field(
        default="gemma3n",
        env="OLLAMA_MODEL"
    )
    
    # LangSmith settings
    LANGCHAIN_TRACING_V2: Optional[str] = Field(
        default=None,
        env="LANGCHAIN_TRACING_V2"
    )
    LANGCHAIN_ENDPOINT: Optional[str] = Field(
        default=None,
        env="LANGCHAIN_ENDPOINT"
    )
    LANGCHAIN_API_KEY: Optional[str] = Field(
        default=None,
        env="LANGCHAIN_API_KEY"
    )
    
    # Security settings
    SECRET_KEY: str = Field(
        default="your-secret-key-here",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Application settings
    DEBUG: bool = Field(
        default=False,
        env="DEBUG"
    )
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Personal Dictionary API"
    
    # Cache settings
    CACHE_EXPIRATION: int = Field(
        default=3600,  # 1 hour
        env="CACHE_EXPIRATION"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    LOG_FILE: Optional[str] = Field(
        default=None,
        env="LOG_FILE"
    )
    LOG_MAX_BYTES: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="LOG_MAX_BYTES"
    )
    LOG_BACKUP_COUNT: int = Field(
        default=5,
        env="LOG_BACKUP_COUNT"
    )
    
    # File paths
    HF_HOME: str = Field(
        default="/app/.cache/huggingface",
        env="HF_HOME"
    )
    SENTENCE_TRANSFORMERS_HOME: str = Field(
        default="/app/.cache/sentence-transformers",
        env="SENTENCE_TRANSFORMERS_HOME"
    )
    XDG_CACHE_HOME: str = Field(
        default="/app/.cache",
        env="XDG_CACHE_HOME"
    )
    
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "case_sensitive": True,
        "arbitrary_types_allowed": True
    }

# Global settings instance
settings = Settings()
