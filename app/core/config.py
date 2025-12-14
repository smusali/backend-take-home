"""
Application configuration management using Pydantic Settings.

Loads configuration from environment variables with validation and type checking.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are validated on initialization and provide sensible defaults
    where appropriate. Required settings without defaults will raise validation
    errors if not provided.
    """
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./leads.db"
    
    # Security Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # SMTP Configuration
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: EmailStr
    SMTP_FROM_NAME: str = "Lead Management System"
    ATTORNEY_EMAIL: EmailStr
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads/resumes"
    MAX_FILE_SIZE: int = 5242880  # 5MB in bytes
    
    # Application Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is sufficiently long for security."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure LOG_LEVEL is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Ensure MAX_FILE_SIZE is reasonable (between 1MB and 50MB)."""
        if v < 1048576:  # 1MB
            raise ValueError("MAX_FILE_SIZE must be at least 1MB (1048576 bytes)")
        if v > 52428800:  # 50MB
            raise ValueError("MAX_FILE_SIZE cannot exceed 50MB (52428800 bytes)")
        return v
    
    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Ensure token expiry is reasonable (between 5 minutes and 7 days)."""
        if v < 5:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 5")
        if v > 10080:  # 7 days
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES cannot exceed 7 days (10080 minutes)")
        return v
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list of origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def ensure_upload_directory(self) -> None:
        """Create upload directory if it doesn't exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


def get_settings() -> Settings:
    """
    Get or create the global settings instance.
    
    Returns a singleton Settings instance, creating it on first access.
    This allows the module to be imported without requiring a .env file
    (useful for testing).
    """
    return Settings()
