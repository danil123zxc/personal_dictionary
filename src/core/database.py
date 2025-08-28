from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.settings import settings
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends

# Database connection URL from settings
DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine with echo=True for debugging SQL queries
# future=True enables SQLAlchemy 2.0 style features
engine = create_engine(
    DATABASE_URL, 
    echo=True,  # Log all SQL statements to console
    future=True  # Enable SQLAlchemy 2.0 features
)

# Create session factory for database sessions
# autocommit=False: Manual transaction control
# autoflush=False: Manual flush control
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Base class for all SQLAlchemy models
# This is used by all model classes to inherit from
Base = declarative_base()

def get_db():
    """
    Database session dependency for FastAPI.
    
    This function creates a database session and ensures it's properly closed
    after the request is complete. It's designed to be used as a FastAPI dependency
    to inject database sessions into endpoint functions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    # Create a new database session
    db = SessionLocal()
    try:
        # Yield the session to the endpoint function
        yield db
    finally:
        # Always close the session, even if an exception occurs
        db.close()

# For backward compatibility - use Depends(get_db) directly in function signatures
# Example: db: Session = Depends(get_db)