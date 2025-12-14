"""
Custom validation functions for schemas.

Provides reusable validators for file uploads, text sanitization,
and business rule validation.
"""

import re

from fastapi import UploadFile


# Allowed file extensions and MIME types for resume uploads
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_RESUME_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_file_size(file: UploadFile, max_size_bytes: int) -> None:
    """
    Validate file size doesn't exceed maximum.
    
    Args:
        file: The uploaded file
        max_size_bytes: Maximum allowed size in bytes
        
    Raises:
        ValueError: If file exceeds max size
        
    Note:
        This checks the Content-Length header. For more reliable validation,
        read the file stream in chunks in the service layer.
    """
    if hasattr(file, "size") and file.size is not None:
        if file.size > max_size_bytes:
            max_mb = max_size_bytes / (1024 * 1024)
            actual_mb = file.size / (1024 * 1024)
            raise ValueError(
                f"File size ({actual_mb:.2f}MB) exceeds maximum "
                f"allowed size ({max_mb:.2f}MB)"
            )


def validate_file_extension(filename: str, allowed_extensions: set[str]) -> None:
    """
    Validate file has an allowed extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (e.g., {'.pdf', '.doc'})
        
    Raises:
        ValueError: If file extension is not allowed
    """
    if not filename:
        raise ValueError("Filename is required")
    
    # Get file extension (lowercase for case-insensitive comparison)
    file_ext = "".join(
        [ext for ext in filename.split(".")[-1:] if ext]
    )
    if file_ext:
        file_ext = f".{file_ext.lower()}"
    
    if file_ext not in allowed_extensions:
        raise ValueError(
            f"File type '{file_ext}' not allowed. "
            f"Allowed types: {', '.join(sorted(allowed_extensions))}"
        )


def validate_resume_file(file: UploadFile, max_size_bytes: int = 5242880) -> None:
    """
    Validate resume file for type and size.
    
    Args:
        file: The uploaded resume file
        max_size_bytes: Maximum file size in bytes (default 5MB)
        
    Raises:
        ValueError: If validation fails
        
    Example:
        >>> validate_resume_file(resume_file, max_size_bytes=5*1024*1024)
    """
    if not file or not file.filename:
        raise ValueError("Resume file is required")
    
    # Validate file extension
    validate_file_extension(file.filename, ALLOWED_RESUME_EXTENSIONS)
    
    # Validate file size
    validate_file_size(file, max_size_bytes)
    
    # Validate MIME type if available
    if file.content_type and file.content_type not in ALLOWED_RESUME_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{file.content_type}'. "
            f"Allowed types: PDF, DOC, DOCX"
        )


def sanitize_name(name: str) -> str:
    """
    Sanitize name field by removing extra whitespace and dangerous characters.
    
    Args:
        name: The name string to sanitize
        
    Returns:
        Sanitized name string
        
    Example:
        >>> sanitize_name("  John   Doe  ")
        'John Doe'
        >>> sanitize_name("John<script>alert()</script>")
        'Johnscriptalert()script'
    """
    if not name:
        return name
    
    # Remove HTML/script tags (basic XSS prevention)
    name = re.sub(r'<[^>]*>', '', name)
    
    # Remove special characters that could be used for injection
    name = re.sub(r'[<>\"\'&;{}()\[\]]', '', name)
    
    # Collapse multiple spaces into single space
    name = re.sub(r'\s+', ' ', name)
    
    # Strip leading/trailing whitespace
    name = name.strip()
    
    return name


def validate_email_format(email: str) -> str:
    """
    Additional email validation beyond Pydantic's EmailStr.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email (lowercase)
        
    Raises:
        ValueError: If email format is invalid
    """
    if not email:
        raise ValueError("Email is required")
    
    # Basic email pattern (Pydantic handles most of this)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValueError(
            "Invalid email format. Must be a valid email address."
        )
    
    # Normalize to lowercase
    return email.lower()


def validate_status_transition(
    current_status: str,
    new_status: str,
    allowed_transitions: dict[str, list[str]]
) -> None:
    """
    Validate that a status transition is allowed.
    
    Args:
        current_status: Current status value
        new_status: Desired new status
        allowed_transitions: Dictionary mapping current status to allowed next statuses
        
    Raises:
        ValueError: If transition is not allowed
        
    Example:
        >>> allowed = {"PENDING": ["REACHED_OUT"]}
        >>> validate_status_transition("PENDING", "REACHED_OUT", allowed)  # OK
        >>> validate_status_transition("REACHED_OUT", "PENDING", allowed)  # Error
    """
    if current_status == new_status:
        raise ValueError("Status is already set to this value")
    
    allowed_next = allowed_transitions.get(current_status, [])
    
    if new_status not in allowed_next:
        raise ValueError(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {', '.join(allowed_next) if allowed_next else 'none'}"
        )


def validate_password_strength(password: str) -> None:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Raises:
        ValueError: If password doesn't meet requirements
        
    Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")


__all__ = [
    "validate_file_size",
    "validate_file_extension",
    "validate_resume_file",
    "sanitize_name",
    "validate_email_format",
    "validate_status_transition",
    "validate_password_strength",
    "ALLOWED_RESUME_EXTENSIONS",
    "ALLOWED_RESUME_MIME_TYPES",
]
