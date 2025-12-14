"""
Unit tests for User schemas.

Tests validation rules for user registration, login, and authentication.
"""

import uuid
from datetime import datetime, UTC

import pytest
from pydantic import ValidationError

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
)


class TestUserCreate:
    """Test suite for UserCreate schema."""
    
    def test_valid_user_create(self):
        """Test creating a valid user."""
        data = {
            "username": "attorney1",
            "email": "attorney@lawfirm.com",
            "password": "SecurePassword123!"
        }
        
        user = UserCreate(**data)
        
        assert user.username == "attorney1"
        assert user.email == "attorney@lawfirm.com"
        assert user.password == "SecurePassword123!"
    
    def test_username_required(self):
        """Test that username is required."""
        data = {
            "email": "attorney@lawfirm.com",
            "password": "SecurePassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "username" in str(exc_info.value)
    
    def test_email_required(self):
        """Test that email is required."""
        data = {
            "username": "attorney1",
            "password": "SecurePassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "email" in str(exc_info.value)
    
    def test_password_required(self):
        """Test that password is required."""
        data = {
            "username": "attorney1",
            "email": "attorney@lawfirm.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "password" in str(exc_info.value)
    
    def test_username_too_short(self):
        """Test that username has minimum length."""
        data = {
            "username": "ab",
            "email": "attorney@lawfirm.com",
            "password": "SecurePassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "username" in str(exc_info.value)
    
    def test_username_too_long(self):
        """Test that username has maximum length."""
        data = {
            "username": "a" * 51,
            "email": "attorney@lawfirm.com",
            "password": "SecurePassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "username" in str(exc_info.value)
    
    def test_username_pattern_validation(self):
        """Test that username only allows valid characters."""
        invalid_usernames = [
            "user@name",
            "user name",
            "user.name",
            "user!name"
        ]
        
        for username in invalid_usernames:
            data = {
                "username": username,
                "email": "attorney@lawfirm.com",
                "password": "SecurePassword123!"
            }
            
            with pytest.raises(ValidationError):
                UserCreate(**data)
    
    def test_valid_username_patterns(self):
        """Test valid username patterns."""
        valid_usernames = [
            "attorney1",
            "attorney_1",
            "attorney-1",
            "ATTORNEY1",
            "Attorney_1"
        ]
        
        for username in valid_usernames:
            data = {
                "username": username,
                "email": "attorney@lawfirm.com",
                "password": "SecurePassword123!"
            }
            user = UserCreate(**data)
            assert user.username == username
    
    def test_password_too_short(self):
        """Test that password has minimum length."""
        data = {
            "username": "attorney1",
            "email": "attorney@lawfirm.com",
            "password": "Short1!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "password" in str(exc_info.value)
    
    def test_password_too_long(self):
        """Test that password has maximum length."""
        data = {
            "username": "attorney1",
            "email": "attorney@lawfirm.com",
            "password": "A" * 101
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "password" in str(exc_info.value)
    
    def test_invalid_email_format(self):
        """Test that email must be valid format."""
        data = {
            "username": "attorney1",
            "email": "not-an-email",
            "password": "SecurePassword123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "email" in str(exc_info.value)


class TestUserLogin:
    """Test suite for UserLogin schema."""
    
    def test_valid_user_login(self):
        """Test valid login credentials."""
        data = {
            "username": "attorney1",
            "password": "SecurePassword123!"
        }
        
        login = UserLogin(**data)
        
        assert login.username == "attorney1"
        assert login.password == "SecurePassword123!"
    
    def test_username_required(self):
        """Test that username is required."""
        data = {"password": "SecurePassword123!"}
        
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)
        
        assert "username" in str(exc_info.value)
    
    def test_password_required(self):
        """Test that password is required."""
        data = {"username": "attorney1"}
        
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)
        
        assert "password" in str(exc_info.value)


class TestUserResponse:
    """Test suite for UserResponse schema."""
    
    def test_valid_user_response(self):
        """Test creating a valid user response."""
        data = {
            "id": uuid.uuid4(),
            "username": "attorney1",
            "email": "attorney@lawfirm.com",
            "is_active": True,
            "created_at": datetime.now(UTC)
        }
        
        response = UserResponse(**data)
        
        assert response.username == "attorney1"
        assert response.email == "attorney@lawfirm.com"
        assert response.is_active is True
    
    def test_inactive_user_response(self):
        """Test user response with inactive status."""
        data = {
            "id": uuid.uuid4(),
            "username": "attorney1",
            "email": "attorney@lawfirm.com",
            "is_active": False,
            "created_at": datetime.now(UTC)
        }
        
        response = UserResponse(**data)
        
        assert response.is_active is False


class TestToken:
    """Test suite for Token schema."""
    
    def test_valid_token(self):
        """Test creating a valid token response."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
            "token_type": "bearer"
        }
        
        token = Token(**data)
        
        assert token.access_token.startswith("eyJ")
        assert token.token_type == "bearer"
    
    def test_token_type_default(self):
        """Test that token_type defaults to 'bearer'."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        }
        
        token = Token(**data)
        
        assert token.token_type == "bearer"
    
    def test_access_token_required(self):
        """Test that access_token is required."""
        with pytest.raises(ValidationError) as exc_info:
            Token()
        
        assert "access_token" in str(exc_info.value)


class TestTokenData:
    """Test suite for TokenData schema."""
    
    def test_valid_token_data(self):
        """Test creating valid token data."""
        user_id = uuid.uuid4()
        data = {
            "username": "attorney1",
            "user_id": user_id
        }
        
        token_data = TokenData(**data)
        
        assert token_data.username == "attorney1"
        assert token_data.user_id == user_id
    
    def test_token_data_with_username_only(self):
        """Test token data with only username."""
        data = {"username": "attorney1"}
        
        token_data = TokenData(**data)
        
        assert token_data.username == "attorney1"
        assert token_data.user_id is None
    
    def test_token_data_with_user_id_only(self):
        """Test token data with only user_id."""
        user_id = uuid.uuid4()
        data = {"user_id": user_id}
        
        token_data = TokenData(**data)
        
        assert token_data.username is None
        assert token_data.user_id == user_id
    
    def test_empty_token_data(self):
        """Test that token data can be empty."""
        token_data = TokenData()
        
        assert token_data.username is None
        assert token_data.user_id is None
