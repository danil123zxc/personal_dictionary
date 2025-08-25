"""
Authentication and Authorization Module

This module handles user authentication, password hashing, and JWT token management
for the Personal Dictionary API. It provides secure user authentication using
bcrypt for password hashing and JWT tokens for session management.

Features:
- Password hashing with bcrypt
- JWT token generation and validation
- User authentication and authorization
- OAuth2 password bearer token support
- Environment-based configuration

Dependencies:
- passlib[bcrypt]
- pyjwt
- python-dotenv

Environment Variables:
- SECRET_KEY: Secret key for JWT token signing
- ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time (default: 30)

Security Features:
- Password hashing with bcrypt (industry standard)
- JWT tokens with expiration
- Secure password validation
- User account status checking (disabled users)
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from app.models import User
from app.crud_schemas import UserBase, Token, TokenData
from pathlib import Path
from dotenv import load_dotenv
import os
from app.database import get_db
from sqlalchemy.orm import Session

# Password hashing context using bcrypt
# bcrypt is a secure password hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer token scheme
# This defines the token endpoint for OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Load environment variables from .env file
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'

# Load the .env file from root directory
load_dotenv(dotenv_path=env_path)

# JWT configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"  # HMAC with SHA-256
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Default token expiration time

# Type alias for database session dependency
db_dependency = Annotated[Session, Depends(get_db)]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against its hashed version.
    
    This function uses bcrypt to safely compare the provided plain text password
    with the stored hashed password. This prevents timing attacks and ensures
    secure password verification.
    
    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The hashed password from the database
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> verify_password("mypassword", "$2b$12$...")
        True
    """
    return pwd_context.verify(plain_password, hashed_password)
 
def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    This function creates a secure hash of the provided password using bcrypt.
    The hash includes a salt and is suitable for secure storage in a database.
    
    Args:
        password (str): The plain text password to hash
        
    Returns:
        str: The hashed password string
        
    Example:
        >>> get_password_hash("mypassword")
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO'
    """
    return pwd_context.hash(password)

def get_user(db: db_dependency, username: str) -> User | None:
    """
    Retrieve a user from the database by username.
    
    This function queries the database to find a user with the specified username.
    It returns the User object if found, or None if not found.
    
    Args:
        db (Session): Database session
        username (str): Username to search for
        
    Returns:
        User | None: User object if found, None otherwise
        
    Example:
        >>> user = get_user(db, "john_doe")
        >>> if user:
        ...     print(f"Found user: {user.full_name}")
    """
    user = db.query(User).filter(User.username == username).first()
    return user

def authenticate_user(db: db_dependency, username: str, password: str) -> User | bool:
    """
    Authenticate a user with username and password.
    
    This function verifies user credentials by checking if the user exists
    and if the provided password matches the stored hash. It returns the
    User object on successful authentication, or False on failure.
    
    Args:
        db (Session): Database session
        username (str): Username to authenticate
        password (str): Plain text password to verify
        
    Returns:
        User | bool: User object if authentication succeeds, False otherwise
        
    Example:
        >>> user = authenticate_user(db, "john_doe", "mypassword")
        >>> if user:
        ...     print("Authentication successful")
        ... else:
        ...     print("Authentication failed")
    """
    # Get user from database
    user = get_user(db, username)
    if not user:
        return False
    
    # Verify password
    if not verify_password(password, user.password):
        return False
    
    return user     

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token with optional expiration.
    
    This function creates a JWT token containing the provided data and an
    expiration timestamp. The token is signed using the SECRET_KEY and
    can be used for authenticated API requests.
    
    Args:
        data (dict): Data to include in the JWT payload
        expires_delta (timedelta | None): Token expiration time (default: 15 minutes)
        
    Returns:
        str: JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "123"}, timedelta(minutes=30))
        >>> print(f"Token: {token}")
    """
    # Create a copy of the data to avoid modifying the original
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Add expiration to token payload
    to_encode.update({"exp": expire})
    
    # Encode and sign the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    db: Session = Depends(get_db),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    This function decodes the JWT token from the Authorization header and
    retrieves the corresponding user from the database. It's designed to be
    used as a FastAPI dependency for protected endpoints.
    
    Args:
        db (Session): Database session dependency
        token (str): JWT token from Authorization header
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
        
    Example:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello {current_user.username}"}
    """
    # Define credentials exception for consistent error handling
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        
        # Convert user ID from string back to integer
        # We store user.id as STRING in 'sub'; cast back to int
        user_id = int(sub)
    except (InvalidTokenError, ValueError):
        # Token is invalid or user_id is not a valid integer
        raise credentials_exception

    # Get user from database
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current active user (not disabled).
    
    This function extends get_current_user to also check if the user account
    is active (not disabled). It's used for endpoints that require an active
    user account.
    
    Args:
        current_user (User): Current authenticated user (from get_current_user)
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: 400 if user account is disabled
        
    Example:
        @app.post("/create_item")
        def create_item(current_user: User = Depends(get_current_active_user)):
            # Only active users can create items
            pass
    """
    # Check if user account is disabled
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user