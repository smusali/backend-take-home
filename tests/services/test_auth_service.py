"""
Unit tests for AuthService.

Tests user registration, login, and authentication business logic.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.core.security import hash_password
from app.db.database import get_engine, get_session_factory
from app.db.base import Base
from app.models.user import User


class TestAuthService:
    """Test suite for AuthService."""
    
    def setup_method(self):
        """Setup test database and service."""
        self.engine = get_engine()
        Base.metadata.create_all(bind=self.engine)
        
        session_factory = get_session_factory()
        self.db: Session = session_factory()
        self.auth_service = AuthService(self.db)
    
    def teardown_method(self):
        """Cleanup test database."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
    
    def test_register_user_success(self):
        """Test successful user registration."""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="Password123"
        )
        
        user = self.auth_service.register_user(user_data)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.is_active is True
        assert user.hashed_password != "Password123"  # Password should be hashed
    
    def test_register_user_duplicate_username(self):
        """Test registration fails with duplicate username."""
        user_data = UserCreate(
            username="testuser",
            email="user1@example.com",
            password="Password123"
        )
        self.auth_service.register_user(user_data)
        
        # Try to register with same username
        duplicate_data = UserCreate(
            username="testuser",
            email="user2@example.com",
            password="Password456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(duplicate_data)
        
        assert exc_info.value.status_code == 400
        assert "Username already registered" in str(exc_info.value.detail)
    
    def test_register_user_duplicate_email(self):
        """Test registration fails with duplicate email."""
        user_data = UserCreate(
            username="user1",
            email="test@example.com",
            password="Password123"
        )
        self.auth_service.register_user(user_data)
        
        # Try to register with same email
        duplicate_data = UserCreate(
            username="user2",
            email="test@example.com",
            password="Password456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.register_user(duplicate_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_login_success(self):
        """Test successful user login."""
        # Register user
        user_data = UserCreate(
            username="loginuser",
            email="login@example.com",
            password="Password123"
        )
        self.auth_service.register_user(user_data)
        
        # Login
        token = self.auth_service.login("loginuser", "Password123")
        
        assert token.access_token is not None
        assert token.token_type == "bearer"
    
    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        # Register user
        user_data = UserCreate(
            username="loginuser",
            email="login@example.com",
            password="Password123"
        )
        self.auth_service.register_user(user_data)
        
        # Login with wrong password
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.login("loginuser", "WrongPassword")
        
        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)
    
    def test_login_nonexistent_user(self):
        """Test login fails with nonexistent username."""
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.login("nonexistent", "Password123")
        
        assert exc_info.value.status_code == 401
    
    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        from app.db.repositories.user_repository import UserRepository
        
        # Create inactive user directly
        user_repo = UserRepository(User, self.db)
        user_repo.create({
            "username": "inactiveuser",
            "email": "inactive@example.com",
            "hashed_password": hash_password("Password123"),
            "is_active": False
        })
        
        # Try to login
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.login("inactiveuser", "Password123")
        
        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)
    
    def test_get_user_by_username_found(self):
        """Test getting user by username."""
        # Register user
        user_data = UserCreate(
            username="findme",
            email="findme@example.com",
            password="Password123"
        )
        self.auth_service.register_user(user_data)
        
        # Get user
        user = self.auth_service.get_user_by_username("findme")
        
        assert user is not None
        assert user.username == "findme"
    
    def test_get_user_by_username_not_found(self):
        """Test getting nonexistent user returns None."""
        user = self.auth_service.get_user_by_username("nonexistent")
        
        assert user is None
    
    def test_check_user_permissions(self):
        """Test checking user permissions."""
        # Register user
        user_data = UserCreate(
            username="permuser",
            email="perm@example.com",
            password="Password123"
        )
        user = self.auth_service.register_user(user_data)
        
        # Check permissions (all active users have access currently)
        has_permission = self.auth_service.check_user_permissions(user, "any_permission")
        
        assert has_permission is True
    
    def test_check_user_permissions_inactive_user(self):
        """Test that inactive user has no permissions."""
        from app.db.repositories.user_repository import UserRepository
        
        # Create inactive user
        user_repo = UserRepository(User, self.db)
        user = user_repo.create({
            "username": "inactiveuser",
            "email": "inactive@example.com",
            "hashed_password": hash_password("Password123"),
            "is_active": False
        })
        
        # Check permissions
        has_permission = self.auth_service.check_user_permissions(user, "any_permission")
        
        assert has_permission is False
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        # Register user
        user_data = UserCreate(
            username="deactiveme",
            email="deactivate@example.com",
            password="Password123"
        )
        user = self.auth_service.register_user(user_data)
        
        # Deactivate
        deactivated = self.auth_service.deactivate_user(user.id)
        
        assert deactivated is not None
        assert deactivated.is_active is False
    
    def test_activate_user(self):
        """Test activating a user."""
        from app.db.repositories.user_repository import UserRepository
        
        # Create inactive user
        user_repo = UserRepository(User, self.db)
        user = user_repo.create({
            "username": "activateme",
            "email": "activate@example.com",
            "hashed_password": hash_password("Password123"),
            "is_active": False
        })
        
        # Activate
        activated = self.auth_service.activate_user(user.id)
        
        assert activated is not None
        assert activated.is_active is True
