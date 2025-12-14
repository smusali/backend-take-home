"""
Authentication service for user registration and login.

Provides business logic for user authentication, token generation,
and authorization checks.
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import (
    hash_password,
    authenticate_user,
    create_access_token
)
from app.core.config import get_settings
from app.db.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, Token


class AuthService:
    """
    Authentication service for user management and token generation.
    
    Handles user registration, login, and authorization logic.
    """
    
    def __init__(self, db: Session):
        """
        Initialize authentication service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(User, db)
        self.settings = get_settings()
    
    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created User object
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username exists
        existing_user = self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        existing_email = self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hashed_password,
        }
        
        return self.user_repo.create(user_dict)
    
    def login(self, username: str, password: str) -> Token:
        """
        Authenticate user and generate access token.
        
        Args:
            username: Username for authentication
            password: Plain text password
            
        Returns:
            Token object with access token
            
        Raises:
            HTTPException: If authentication fails
        """
        user = authenticate_user(username, password, self.db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token_expires = timedelta(
            minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User object if found, None otherwise
        """
        return self.user_repo.get_by_username(username)
    
    def check_user_permissions(self, user: User, required_permission: str) -> bool:
        """
        Check if user has required permission.
        
        Args:
            user: User to check
            required_permission: Permission string to check
            
        Returns:
            True if user has permission, False otherwise
            
        Note:
            This is a placeholder for future role-based access control.
            Currently, all active users have all permissions.
        """
        # Future: Implement role-based permissions
        # For now, all active users have access
        return user.is_active
    
    def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: UUID of user to deactivate
            
        Returns:
            Updated User object if found, None otherwise
        """
        return self.user_repo.deactivate_user(user_id)
    
    def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: UUID of user to activate
            
        Returns:
            Updated User object if found, None otherwise
        """
        return self.user_repo.activate_user(user_id)


__all__ = ["AuthService"]
