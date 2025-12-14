"""
User and authentication schemas.

Defines Pydantic models for user registration, login, and JWT tokens.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.schemas.validators import validate_email_format, validate_password_strength


class UserCreate(BaseModel):
    """
    Schema for creating a new attorney user account.
    
    Used during user registration.
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username for login",
        examples=["attorney1"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Attorney's email address",
        examples=["attorney@lawfirm.com"]
    )
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (will be hashed before storage)",
        examples=["SecurePassword123!"]
    )
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return validate_email_format(v)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        validate_password_strength(v)
        return v


class UserLogin(BaseModel):
    """
    Schema for user login credentials.
    
    Used when attorney logs into the internal UI.
    """
    
    username: str = Field(
        ...,
        description="Username for authentication",
        examples=["attorney1"]
    )
    
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePassword123!"]
    )


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.
    
    Excludes sensitive information like hashed password.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")


class Token(BaseModel):
    """
    Schema for JWT authentication token response.
    
    Returned after successful login.
    """
    
    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for JWT)"
    )


class TokenData(BaseModel):
    """
    Schema for decoded JWT token data.
    
    Used internally for authentication validation.
    """
    
    username: Optional[str] = Field(
        None,
        description="Username extracted from token"
    )
    
    user_id: Optional[UUID] = Field(
        None,
        description="User ID extracted from token"
    )
