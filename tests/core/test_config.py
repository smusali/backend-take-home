"""
Unit tests for application configuration.

Tests configuration loading, validation, and utility methods.
"""

import os
import pytest
from pydantic import ValidationError
from app.core.config import Settings


class TestSettings:
    """Test suite for Settings configuration class."""
    
    def test_settings_with_minimal_required_fields(self, monkeypatch):
        """Test that Settings can be instantiated with only required fields."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        
        settings = Settings()
        
        assert settings.SECRET_KEY == "a" * 32
        assert settings.SMTP_HOST == "smtp.example.com"
        assert settings.ALGORITHM == "HS256"  # Default value
    
    def test_secret_key_validation_too_short(self, monkeypatch):
        """Test that SECRET_KEY validation fails if too short."""
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "SECRET_KEY must be at least 32 characters long" in str(exc_info.value)
    
    def test_secret_key_validation_sufficient_length(self, monkeypatch):
        """Test that SECRET_KEY validation passes with sufficient length."""
        secret = "a" * 32
        monkeypatch.setenv("SECRET_KEY", secret)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        
        settings = Settings()
        assert settings.SECRET_KEY == secret
    
    def test_log_level_validation_valid(self, monkeypatch):
        """Test that LOG_LEVEL accepts valid logging levels."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("LOG_LEVEL", "debug")
        
        settings = Settings()
        assert settings.LOG_LEVEL == "DEBUG"
    
    def test_log_level_validation_invalid(self, monkeypatch):
        """Test that LOG_LEVEL validation fails for invalid levels."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "LOG_LEVEL must be one of" in str(exc_info.value)
    
    def test_max_file_size_validation_too_small(self, monkeypatch):
        """Test that MAX_FILE_SIZE validation fails if too small."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("MAX_FILE_SIZE", "100")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "MAX_FILE_SIZE must be at least 1MB" in str(exc_info.value)
    
    def test_max_file_size_validation_too_large(self, monkeypatch):
        """Test that MAX_FILE_SIZE validation fails if too large."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("MAX_FILE_SIZE", "100000000")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "MAX_FILE_SIZE cannot exceed 50MB" in str(exc_info.value)
    
    def test_max_file_size_validation_valid(self, monkeypatch):
        """Test that MAX_FILE_SIZE accepts valid sizes."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("MAX_FILE_SIZE", "5242880")
        
        settings = Settings()
        assert settings.MAX_FILE_SIZE == 5242880
    
    def test_token_expiry_validation_too_short(self, monkeypatch):
        """Test that ACCESS_TOKEN_EXPIRE_MINUTES validation fails if too short."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "ACCESS_TOKEN_EXPIRE_MINUTES must be at least 5" in str(exc_info.value)
    
    def test_token_expiry_validation_too_long(self, monkeypatch):
        """Test that ACCESS_TOKEN_EXPIRE_MINUTES validation fails if too long."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20000")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "ACCESS_TOKEN_EXPIRE_MINUTES cannot exceed 7 days" in str(exc_info.value)
    
    def test_get_cors_origins(self, monkeypatch):
        """Test that get_cors_origins parses CORS_ORIGINS correctly."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.com, http://localhost:8000")
        
        settings = Settings()
        origins = settings.get_cors_origins()
        
        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "https://example.com" in origins
        assert "http://localhost:8000" in origins
    
    def test_is_production_property(self, monkeypatch):
        """Test that is_production property works correctly."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("ENVIRONMENT", "production")
        
        settings = Settings()
        assert settings.is_production is True
        assert settings.is_development is False
    
    def test_is_development_property(self, monkeypatch):
        """Test that is_development property works correctly."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False
    
    def test_ensure_upload_directory(self, monkeypatch, tmp_path):
        """Test that ensure_upload_directory creates the directory."""
        upload_dir = tmp_path / "test_uploads"
        
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
        
        settings = Settings()
        
        assert not upload_dir.exists()
        settings.ensure_upload_directory()
        assert upload_dir.exists()
        assert upload_dir.is_dir()
    
    def test_email_validation(self, monkeypatch):
        """Test that email fields are validated properly."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "invalid-email")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "SMTP_FROM_EMAIL" in str(exc_info.value)
    
    def test_default_values(self, monkeypatch):
        """Test that default values are set correctly."""
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "password123")
        monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
        monkeypatch.setenv("ATTORNEY_EMAIL", "attorney@example.com")
        
        settings = Settings()
        
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
        assert settings.SMTP_PORT == 587
        assert settings.MAX_FILE_SIZE == 5242880
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is True
        assert settings.LOG_LEVEL == "INFO"
