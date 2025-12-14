"""
User repository for user-specific database operations.

Extends BaseRepository with methods specific to user authentication
and management, including querying by username and email.
"""

from typing import Optional

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with user-specific operations.
    
    Provides methods for querying users by username and email,
    commonly needed for authentication and user management.
    """
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            User instance if found, None otherwise
        """
        stmt = select(User).where(User.username == username)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            User instance if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Retrieve active users with pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List of active User instances
        """
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: The UUID of the user to deactivate
            
        Returns:
            Updated User instance if found, None otherwise
        """
        user = self.get(user_id)
        if user is None:
            return None
        
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: The UUID of the user to activate
            
        Returns:
            Updated User instance if found, None otherwise
        """
        user = self.get(user_id)
        if user is None:
            return None
        
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
