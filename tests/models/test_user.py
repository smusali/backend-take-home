"""
Unit tests for User model.

Tests User model creation, field validation, and constraints.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestUserModel:
    """Test suite for User model."""
    
    def test_create_user_with_required_fields(self, session):
        """Test creating a user with all required fields."""
        user = User(
            username="johndoe",
            email="john.doe@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.username == "johndoe"
        assert user.email == "john.doe@example.com"
        assert user.hashed_password == "$2b$12$hashedpassword"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_default_is_active_is_true(self, session):
        """Test that default is_active is True."""
        user = User(
            username="janedoe",
            email="jane.doe@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user)
        session.commit()
        
        assert user.is_active is True
    
    def test_user_can_be_set_inactive(self, session):
        """Test that user can be set to inactive."""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=False
        )
        
        session.add(user)
        session.commit()
        
        assert user.is_active is False
    
    def test_user_username_must_be_unique(self, session):
        """Test that username uniqueness constraint is enforced."""
        user1 = User(
            username="sameusername",
            email="user1@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        user2 = User(
            username="sameusername",
            email="user2@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user1)
        session.commit()
        
        session.add(user2)
        with pytest.raises(Exception):
            session.commit()
    
    def test_user_email_must_be_unique(self, session):
        """Test that email uniqueness constraint is enforced."""
        user1 = User(
            username="user1",
            email="same@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        user2 = User(
            username="user2",
            email="same@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user1)
        session.commit()
        
        session.add(user2)
        with pytest.raises(Exception):
            session.commit()
    
    def test_user_repr(self, session):
        """Test User __repr__ method."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user)
        session.commit()
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "testuser" in repr_str
        assert "True" in repr_str
    
    def test_user_accepts_long_username(self, session):
        """Test that user accepts usernames up to 50 characters."""
        long_username = "a" * 50
        user = User(
            username=long_username,
            email="long.username@example.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user)
        session.commit()
        
        assert user.username == long_username
    
    def test_user_accepts_long_email(self, session):
        """Test that user accepts emails up to 255 characters."""
        long_email = "a" * 240 + "@example.com"
        user = User(
            username="longem",
            email=long_email,
            hashed_password="$2b$12$hashedpassword"
        )
        
        session.add(user)
        session.commit()
        
        assert user.email == long_email
    
    def test_user_accepts_long_hashed_password(self, session):
        """Test that user accepts hashed passwords up to 255 characters."""
        long_hash = "$2b$12$" + "a" * 240
        user = User(
            username="testpw",
            email="testpw@example.com",
            hashed_password=long_hash
        )
        
        session.add(user)
        session.commit()
        
        assert user.hashed_password == long_hash
