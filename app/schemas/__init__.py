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

from app.schemas.enums import (
    LeadStatus,
    LEAD_STATUS_DISPLAY_NAMES,
    LEAD_STATUS_DESCRIPTIONS,
    get_all_lead_statuses,
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
    # Enums
    "LeadStatus",
    "LEAD_STATUS_DISPLAY_NAMES",
    "LEAD_STATUS_DESCRIPTIONS",
    "get_all_lead_statuses",
]
