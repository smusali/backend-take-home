"""
Security utilities for authentication and authorization.

Provides password hashing, JWT token creation/verification,
and FastAPI dependencies for protected routes.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import TokenData

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("SecurePassword123")
        >>> hashed.startswith("$2b$")
        True
    """
    # Ensure password is a string and truncate if needed (bcrypt limit is 72 bytes)
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    
    # Truncate to 72 characters if needed (bcrypt limitation)
    if len(password) > 72:
        password = password[:72]
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password
        
    Returns:
        True if password matches hash, False otherwise
        
    Example:
        >>> hashed = hash_password("SecurePassword123")
        >>> verify_password("SecurePassword123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> isinstance(token, str)
        True
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData with decoded claims
        
    Raises:
        HTTPException: If token is invalid or expired
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> token_data = verify_token(token)
        >>> token_data.username
        'user123'
    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username)
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current User object
        
    Raises:
        HTTPException: If token is invalid or user not found
        
    Example:
        >>> @app.get("/protected")
        >>> def protected_route(current_user: User = Depends(get_current_user)):
        >>>     return {"username": current_user.username}
    """
    token_data = verify_token(token)
    
    user_repo = UserRepository(User, db)
    user = user_repo.get_by_username(token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get the current active user.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Current active User object
        
    Raises:
        HTTPException: If user is inactive
        
    Example:
        >>> @app.get("/protected")
        >>> def protected_route(user: User = Depends(get_current_active_user)):
        >>>     return {"username": user.username}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        username: Username to authenticate
        password: Plain text password
        db: Database session
        
    Returns:
        User object if authentication successful, None otherwise
        
    Example:
        >>> user = authenticate_user("attorney1", "Password123", db)
        >>> if user:
        >>>     print(f"Authenticated: {user.username}")
    """
    user_repo = UserRepository(User, db)
    user = user_repo.get_by_username(username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    "authenticate_user",
    "pwd_context",
    "oauth2_scheme",
]
