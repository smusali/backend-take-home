"""
Unit tests for security utilities.

Tests password hashing, JWT token creation/verification,
and authentication functions.
"""

from datetime import timedelta

import pytest
from jose import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    authenticate_user,
)
from app.core.config import get_settings


class TestPasswordHashing:
    """Test suite for password hashing functions."""
    
    def test_hash_password_returns_different_hash(self):
        """Test that hashing same password twice produces different hashes."""
        password = "SecurePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # bcrypt uses random salt
    
    def test_hash_password_creates_bcrypt_hash(self):
        """Test that password hash uses bcrypt format."""
        password = "SecurePassword123"
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # bcrypt hashes are 60 chars
    
    def test_verify_password_with_correct_password(self):
        """Test password verification with correct password."""
        password = "SecurePassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "SecurePassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "SecurePassword123"
        hashed = hash_password(password)
        
        assert verify_password("securepassword123", hashed) is False


class TestJWTTokens:
    """Test suite for JWT token functions."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
    
    def test_create_access_token_contains_username(self):
        """Test that token contains the username in subject."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "testuser"
    
    def test_create_access_token_contains_expiration(self):
        """Test that token contains expiration time."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert "exp" in payload
    
    def test_verify_token_with_valid_token(self):
        """Test verifying a valid token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        token_data = verify_token(token)
        
        assert token_data.username == "testuser"
    
    def test_verify_token_with_invalid_token(self):
        """Test verifying an invalid token."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_with_tampered_token(self):
        """Test verifying a tampered token."""
        from fastapi import HTTPException
        
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Tamper with token
        parts = token.split(".")
        tampered_token = parts[0] + ".tampered." + parts[2]
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered_token)
        
        assert exc_info.value.status_code == 401


class TestAuthenticateUser:
    """Test suite for user authentication function."""
    
    def setup_method(self):
        """Setup test database and user."""
        from app.db.database import get_engine, get_session_factory
        from app.db.base import Base
        from app.db.repositories.user_repository import UserRepository
        from app.models.user import User
        
        self.engine = get_engine()
        Base.metadata.create_all(bind=self.engine)
        
        session_factory = get_session_factory()
        self.db = session_factory()
        self.user_repo = UserRepository(User, self.db)
        
        # Create test user
        self.test_password = "TestPassword123"
        self.test_user = self.user_repo.create({
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password(self.test_password)
        })
    
    def teardown_method(self):
        """Cleanup test database."""
        from app.db.base import Base
        
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
    
    def test_authenticate_user_with_correct_credentials(self):
        """Test authenticating with correct username and password."""
        user = authenticate_user("testuser", self.test_password, self.db)
        
        assert user is not None
        assert user.username == "testuser"
    
    def test_authenticate_user_with_wrong_password(self):
        """Test authentication fails with wrong password."""
        user = authenticate_user("testuser", "WrongPassword", self.db)
        
        assert user is None
    
    def test_authenticate_user_with_nonexistent_username(self):
        """Test authentication fails with nonexistent username."""
        user = authenticate_user("nonexistent", self.test_password, self.db)
        
        assert user is None
    
    def test_authenticate_user_case_sensitive_password(self):
        """Test that authentication is case-sensitive for password."""
        user = authenticate_user("testuser", self.test_password.lower(), self.db)
        
        assert user is None
