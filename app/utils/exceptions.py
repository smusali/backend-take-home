"""
Custom exception classes for the Lead Management API.

Provides domain-specific exceptions with appropriate HTTP status codes
and error messages for consistent error handling across the application.
"""

from typing import Optional


class LeadManagementException(Exception):
    """
    Base exception for all lead management errors.
    
    All custom exceptions inherit from this base class for consistent
    error handling and categorization.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None
    ):
        """
        Initialize exception with message and metadata.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code for this error
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class LeadNotFoundException(LeadManagementException):
    """
    Raised when a requested lead is not found in the database.
    
    HTTP Status: 404 Not Found
    
    Example:
        >>> raise LeadNotFoundException(lead_id="a1b2c3d4")
    """
    
    def __init__(self, lead_id: str, details: Optional[dict] = None):
        message = f"Lead with ID {lead_id} not found"
        super().__init__(message=message, status_code=404, details=details)


class DuplicateLeadException(LeadManagementException):
    """
    Raised when attempting to create a lead with an email that already exists.
    
    HTTP Status: 409 Conflict
    
    Example:
        >>> raise DuplicateLeadException(email="john@example.com")
    """
    
    def __init__(self, email: str, details: Optional[dict] = None):
        message = f"A lead with email {email} already exists"
        super().__init__(message=message, status_code=409, details=details)


class InvalidStatusTransitionException(LeadManagementException):
    """
    Raised when attempting an invalid lead status transition.
    
    HTTP Status: 400 Bad Request
    
    Example:
        >>> raise InvalidStatusTransitionException(
        ...     from_status="REACHED_OUT",
        ...     to_status="PENDING"
        ... )
    """
    
    def __init__(
        self,
        from_status: str,
        to_status: str,
        details: Optional[dict] = None
    ):
        message = (
            f"Invalid status transition from {from_status} to {to_status}. "
            f"Status can only progress forward, not backward."
        )
        super().__init__(message=message, status_code=400, details=details)


class FileUploadException(LeadManagementException):
    """
    Raised when file upload operations fail.
    
    HTTP Status: 400 Bad Request (validation) or 500 Internal Server Error (storage)
    
    Example:
        >>> raise FileUploadException(
        ...     message="File size exceeds 5MB limit",
        ...     status_code=400
        ... )
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[dict] = None
    ):
        super().__init__(message=message, status_code=status_code, details=details)


class EmailSendException(LeadManagementException):
    """
    Raised when email sending operations fail.
    
    HTTP Status: 500 Internal Server Error
    
    Example:
        >>> raise EmailSendException(
        ...     recipient="user@example.com",
        ...     reason="SMTP connection timeout"
        ... )
    """
    
    def __init__(
        self,
        recipient: str,
        reason: str,
        details: Optional[dict] = None
    ):
        message = f"Failed to send email to {recipient}: {reason}"
        super().__init__(message=message, status_code=500, details=details)


class AuthenticationException(LeadManagementException):
    """
    Raised when authentication or authorization fails.
    
    HTTP Status: 401 Unauthorized
    
    Example:
        >>> raise AuthenticationException(message="Invalid credentials")
    """
    
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(message=message, status_code=401, details=details)


class UserNotFoundException(LeadManagementException):
    """
    Raised when a requested user is not found.
    
    HTTP Status: 404 Not Found
    
    Example:
        >>> raise UserNotFoundException(username="attorney1")
    """
    
    def __init__(self, username: str, details: Optional[dict] = None):
        message = f"User {username} not found"
        super().__init__(message=message, status_code=404, details=details)


class DuplicateUserException(LeadManagementException):
    """
    Raised when attempting to create a user that already exists.
    
    HTTP Status: 409 Conflict
    
    Example:
        >>> raise DuplicateUserException(field="username", value="attorney1")
    """
    
    def __init__(self, field: str, value: str, details: Optional[dict] = None):
        message = f"User with {field} '{value}' already exists"
        super().__init__(message=message, status_code=409, details=details)


class InactiveUserException(LeadManagementException):
    """
    Raised when an inactive user attempts to access protected resources.
    
    HTTP Status: 403 Forbidden
    
    Example:
        >>> raise InactiveUserException(username="attorney1")
    """
    
    def __init__(self, username: str, details: Optional[dict] = None):
        message = f"User {username} is inactive and cannot access this resource"
        super().__init__(message=message, status_code=403, details=details)


class ValidationException(LeadManagementException):
    """
    Raised when input validation fails.
    
    HTTP Status: 422 Unprocessable Entity
    
    Example:
        >>> raise ValidationException(
        ...     field="email",
        ...     message="Invalid email format"
        ... )
    """
    
    def __init__(self, field: str, message: str, details: Optional[dict] = None):
        error_message = f"Validation error for field '{field}': {message}"
        super().__init__(message=error_message, status_code=422, details=details)


__all__ = [
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
]
