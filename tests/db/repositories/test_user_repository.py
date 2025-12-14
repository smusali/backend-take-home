"""
Unit tests for UserRepository.

Tests user-specific database operations including querying by username,
email, and user activation/deactivation.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.repositories.user_repository import UserRepository
from app.models.user import User
from app.db.database import get_engine, get_session_factory
from app.db.base import Base


class TestUserRepository:
    """Test suite for UserRepository operations."""
    
    def setup_method(self):
        """Setup test database and session before each test."""
        self.engine = get_engine()
        Base.metadata.create_all(bind=self.engine)
        
        session_factory = get_session_factory()
        self.db: Session = session_factory()
        self.repository = UserRepository(User, self.db)
    
    def teardown_method(self):
        """Cleanup test database after each test."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
    
    def test_get_by_username_found(self):
        """Test retrieving a user by username."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashedpassword123"
        }
        
        self.repository.create(user_data)
        user = self.repository.get_by_username("testuser")
        
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_get_by_username_not_found(self):
        """Test that getting a nonexistent username returns None."""
        user = self.repository.get_by_username("nonexistent")
        
        assert user is None
    
    def test_get_by_email_found(self):
        """Test retrieving a user by email."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashedpassword123"
        }
        
        self.repository.create(user_data)
        user = self.repository.get_by_email("test@example.com")
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
    
    def test_get_by_email_not_found(self):
        """Test that getting a nonexistent email returns None."""
        user = self.repository.get_by_email("nonexistent@example.com")
        
        assert user is None
    
    def test_get_active_users(self):
        """Test retrieving only active users."""
        # Create active users
        for i in range(3):
            self.repository.create({
                "username": f"active{i}",
                "email": f"active{i}@example.com",
                "hashed_password": "hashedpassword",
                "is_active": True
            })
        
        # Create inactive users
        for i in range(2):
            self.repository.create({
                "username": f"inactive{i}",
                "email": f"inactive{i}@example.com",
                "hashed_password": "hashedpassword",
                "is_active": False
            })
        
        active_users = self.repository.get_active_users()
        
        assert len(active_users) == 3
        assert all(user.is_active for user in active_users)
    
    def test_get_active_users_with_pagination(self):
        """Test retrieving active users with pagination."""
        for i in range(10):
            self.repository.create({
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "hashed_password": "hashedpassword",
                "is_active": True
            })
        
        first_page = self.repository.get_active_users(skip=0, limit=3)
        second_page = self.repository.get_active_users(skip=3, limit=3)
        
        assert len(first_page) == 3
        assert len(second_page) == 3
        # Verify different users
        assert first_page[0].id != second_page[0].id
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        user_data = {
            "username": "activeuser",
            "email": "active@example.com",
            "hashed_password": "hashedpassword",
            "is_active": True
        }
        
        user = self.repository.create(user_data)
        assert user.is_active is True
        
        deactivated_user = self.repository.deactivate_user(user.id)
        
        assert deactivated_user is not None
        assert deactivated_user.is_active is False
        assert deactivated_user.id == user.id
    
    def test_deactivate_nonexistent_user(self):
        """Test deactivating a nonexistent user returns None."""
        random_id = uuid.uuid4()
        result = self.repository.deactivate_user(random_id)
        
        assert result is None
    
    def test_activate_user(self):
        """Test activating a user."""
        user_data = {
            "username": "inactiveuser",
            "email": "inactive@example.com",
            "hashed_password": "hashedpassword",
            "is_active": False
        }
        
        user = self.repository.create(user_data)
        assert user.is_active is False
        
        activated_user = self.repository.activate_user(user.id)
        
        assert activated_user is not None
        assert activated_user.is_active is True
        assert activated_user.id == user.id
    
    def test_activate_nonexistent_user(self):
        """Test activating a nonexistent user returns None."""
        random_id = uuid.uuid4()
        result = self.repository.activate_user(random_id)
        
        assert result is None
    
    def test_user_default_is_active(self):
        """Test that users are active by default."""
        user_data = {
            "username": "defaultuser",
            "email": "default@example.com",
            "hashed_password": "hashedpassword"
        }
        
        user = self.repository.create(user_data)
        
        assert user.is_active is True
    
    def test_username_uniqueness(self):
        """Test that usernames must be unique."""
        user_data = {
            "username": "uniqueuser",
            "email": "user1@example.com",
            "hashed_password": "hashedpassword"
        }
        
        self.repository.create(user_data)
        
        # Attempt to create user with same username but different email
        from sqlalchemy.exc import IntegrityError
        try:
            self.repository.create({
                "username": "uniqueuser",
                "email": "user2@example.com",
                "hashed_password": "hashedpassword"
            })
            assert False, "Should have raised IntegrityError"
        except IntegrityError:
            self.db.rollback()
            assert True
    
    def test_email_uniqueness(self):
        """Test that emails must be unique."""
        user_data = {
            "username": "user1",
            "email": "unique@example.com",
            "hashed_password": "hashedpassword"
        }
        
        self.repository.create(user_data)
        
        # Attempt to create user with same email but different username
        from sqlalchemy.exc import IntegrityError
        try:
            self.repository.create({
                "username": "user2",
                "email": "unique@example.com",
                "hashed_password": "hashedpassword"
            })
            assert False, "Should have raised IntegrityError"
        except IntegrityError:
            self.db.rollback()
            assert True
