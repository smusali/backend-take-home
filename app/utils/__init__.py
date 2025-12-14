"""
Utility modules for the Lead Management API.

Contains reusable utilities including custom exceptions,
exception handlers, and other helper functions.
"""

from app.utils.exceptions import (
    LeadManagementException,
    LeadNotFoundException,
    DuplicateLeadException,
    InvalidStatusTransitionException,
    FileUploadException,
    EmailSendException,
    AuthenticationException,
    UserNotFoundException,
    DuplicateUserException,
    InactiveUserException,
    ValidationException,
)

from app.utils.exception_handlers import (
    register_exception_handlers,
    create_error_response,
)

__all__ = [
    # Exceptions
    "LeadManagementException",
    "LeadNotFoundException",
    "DuplicateLeadException",
    "InvalidStatusTransitionException",
    "FileUploadException",
    "EmailSendException",
    "AuthenticationException",
    "UserNotFoundException",
    "DuplicateUserException",
    "InactiveUserException",
    "ValidationException",
    # Exception Handlers
    "register_exception_handlers",
    "create_error_response",
]
