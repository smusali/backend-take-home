"""
Utility modules for the Lead Management API.

Contains reusable utilities including custom exceptions,
exception handlers, logging configuration, and other helper functions.
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

from app.utils.logging_config import (
    setup_logging,
    get_logger,
    log_lead_creation,
    log_lead_status_update,
    log_authentication_attempt,
    log_email_sent,
    log_file_upload,
    log_error,
    log_request,
    log_database_operation,
    log_startup,
    log_shutdown,
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
    # Logging
    "setup_logging",
    "get_logger",
    "log_lead_creation",
    "log_lead_status_update",
    "log_authentication_attempt",
    "log_email_sent",
    "log_file_upload",
    "log_error",
    "log_request",
    "log_database_operation",
    "log_startup",
    "log_shutdown",
]
