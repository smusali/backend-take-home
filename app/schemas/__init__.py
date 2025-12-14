"""
Schemas package for request/response validation.

Exports all schema classes for clean imports throughout the application.
"""

from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
)

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
)

__all__ = [
    # Lead schemas
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadListResponse",
    # User schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
]
