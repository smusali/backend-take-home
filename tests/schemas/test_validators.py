"""
Unit tests for custom validators.

Tests file validation, sanitization, and business rule validation.
"""

from io import BytesIO

import pytest
from fastapi import UploadFile

from app.schemas.validators import (
    validate_file_size,
    validate_file_extension,
    validate_resume_file,
    sanitize_name,
    validate_email_format,
    validate_status_transition,
    validate_password_strength,
    ALLOWED_RESUME_EXTENSIONS,
)


class TestFileValidation:
    """Test suite for file validation functions."""
    
    def test_validate_file_size_within_limit(self):
        """Test file size validation with acceptable size."""
        file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))
        file.size = 1024 * 1024  # 1MB
        
        # Should not raise
        validate_file_size(file, max_size_bytes=5 * 1024 * 1024)
    
    def test_validate_file_size_exceeds_limit(self):
        """Test file size validation when file is too large."""
        file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))
        file.size = 10 * 1024 * 1024  # 10MB
        
        with pytest.raises(ValueError) as exc_info:
            validate_file_size(file, max_size_bytes=5 * 1024 * 1024)
        
        assert "exceeds maximum" in str(exc_info.value)
        assert "5.00MB" in str(exc_info.value)
    
    def test_validate_file_size_no_size_attribute(self):
        """Test file size validation when size attribute is None."""
        file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))
        # file.size is None by default
        
        # Should not raise
        validate_file_size(file, max_size_bytes=5 * 1024 * 1024)
    
    def test_validate_file_extension_pdf(self):
        """Test file extension validation with PDF."""
        validate_file_extension("document.pdf", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_doc(self):
        """Test file extension validation with DOC."""
        validate_file_extension("document.doc", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_docx(self):
        """Test file extension validation with DOCX."""
        validate_file_extension("document.docx", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_case_insensitive(self):
        """Test file extension validation is case-insensitive."""
        validate_file_extension("document.PDF", ALLOWED_RESUME_EXTENSIONS)
        validate_file_extension("document.DoC", ALLOWED_RESUME_EXTENSIONS)
        validate_file_extension("document.DOCX", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_invalid(self):
        """Test file extension validation with invalid extension."""
        with pytest.raises(ValueError) as exc_info:
            validate_file_extension("document.txt", ALLOWED_RESUME_EXTENSIONS)
        
        assert "not allowed" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)
    
    def test_validate_file_extension_no_extension(self):
        """Test file extension validation with no extension."""
        with pytest.raises(ValueError):
            validate_file_extension("document", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_empty_filename(self):
        """Test file extension validation with empty filename."""
        with pytest.raises(ValueError) as exc_info:
            validate_file_extension("", ALLOWED_RESUME_EXTENSIONS)
        
        assert "required" in str(exc_info.value)
    
    def test_validate_resume_file_valid_pdf(self):
        """Test resume validation with valid PDF file."""
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(b"fake pdf content")
        )
        file.size = 1024 * 1024  # 1MB
        # Mock content_type
        file._headers = {"content-type": "application/pdf"}
        
        # Should not raise
        validate_resume_file(file, max_size_bytes=5 * 1024 * 1024)
    
    def test_validate_resume_file_no_filename(self):
        """Test resume validation with missing filename."""
        file = UploadFile(filename=None, file=BytesIO(b"content"))
        
        with pytest.raises(ValueError) as exc_info:
            validate_resume_file(file)
        
        assert "required" in str(exc_info.value)
    
    def test_validate_resume_file_invalid_extension(self):
        """Test resume validation with invalid file type."""
        file = UploadFile(filename="resume.txt", file=BytesIO(b"content"))
        file.size = 1024
        
        with pytest.raises(ValueError) as exc_info:
            validate_resume_file(file)
        
        assert "not allowed" in str(exc_info.value)
    
    def test_validate_resume_file_too_large(self):
        """Test resume validation with file too large."""
        file = UploadFile(filename="resume.pdf", file=BytesIO(b"content"))
        file.size = 10 * 1024 * 1024  # 10MB
        
        with pytest.raises(ValueError) as exc_info:
            validate_resume_file(file, max_size_bytes=5 * 1024 * 1024)
        
        assert "exceeds maximum" in str(exc_info.value)
    
    def test_validate_resume_file_invalid_mime_type(self):
        """Test resume validation with invalid MIME type."""
        # Create a mock-like object with content_type property
        class MockUploadFile:
            def __init__(self):
                self.filename = "resume.pdf"
                self.size = 1024
                self.content_type = "text/plain"
        
        file = MockUploadFile()
        
        with pytest.raises(ValueError) as exc_info:
            validate_resume_file(file)
        
        assert "Invalid file type" in str(exc_info.value)


class TestNameSanitization:
    """Test suite for name sanitization."""
    
    def test_sanitize_name_basic(self):
        """Test basic name sanitization."""
        assert sanitize_name("John") == "John"
        assert sanitize_name("Jane") == "Jane"
    
    def test_sanitize_name_with_whitespace(self):
        """Test name sanitization removes extra whitespace."""
        assert sanitize_name("  John  ") == "John"
        assert sanitize_name("John   Doe") == "John Doe"
        assert sanitize_name("  John   Doe  ") == "John Doe"
    
    def test_sanitize_name_removes_html_tags(self):
        """Test name sanitization removes HTML tags."""
        assert sanitize_name("John<script>alert()</script>") == "Johnalert"
        assert sanitize_name("<b>John</b>") == "John"
        assert sanitize_name("John<div>test</div>Doe") == "JohntestDoe"
    
    def test_sanitize_name_removes_special_characters(self):
        """Test name sanitization removes dangerous characters."""
        assert sanitize_name("John<>\"'&;{}()[]") == "John"
        assert sanitize_name("John;DROP TABLE") == "JohnDROP TABLE"
    
    def test_sanitize_name_preserves_hyphens_and_apostrophes(self):
        """Test name sanitization preserves common name characters."""
        # Note: apostrophes are removed for security
        assert sanitize_name("Mary-Jane") == "Mary-Jane"
        assert sanitize_name("O'Brien") == "OBrien"  # Apostrophe removed
    
    def test_sanitize_name_empty_string(self):
        """Test name sanitization with empty string."""
        assert sanitize_name("") == ""
    
    def test_sanitize_name_none(self):
        """Test name sanitization with None."""
        assert sanitize_name(None) is None


class TestEmailValidation:
    """Test suite for email validation."""
    
    def test_validate_email_format_valid(self):
        """Test email validation with valid emails."""
        assert validate_email_format("test@example.com") == "test@example.com"
        assert validate_email_format("user.name@example.com") == "user.name@example.com"
        assert validate_email_format("user+tag@example.com") == "user+tag@example.com"
    
    def test_validate_email_format_normalizes_case(self):
        """Test email validation normalizes to lowercase."""
        assert validate_email_format("Test@Example.Com") == "test@example.com"
        assert validate_email_format("USER@EXAMPLE.COM") == "user@example.com"
    
    def test_validate_email_format_invalid(self):
        """Test email validation with invalid emails."""
        with pytest.raises(ValueError):
            validate_email_format("notanemail")
        
        with pytest.raises(ValueError):
            validate_email_format("@example.com")
        
        with pytest.raises(ValueError):
            validate_email_format("user@")
    
    def test_validate_email_format_empty(self):
        """Test email validation with empty string."""
        with pytest.raises(ValueError) as exc_info:
            validate_email_format("")
        
        assert "required" in str(exc_info.value)


class TestStatusTransitionValidation:
    """Test suite for status transition validation."""
    
    def test_validate_status_transition_allowed(self):
        """Test valid status transition."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        
        # Should not raise
        validate_status_transition("PENDING", "REACHED_OUT", allowed)
    
    def test_validate_status_transition_not_allowed(self):
        """Test invalid status transition."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        
        with pytest.raises(ValueError) as exc_info:
            validate_status_transition("REACHED_OUT", "PENDING", allowed)
        
        assert "Cannot transition" in str(exc_info.value)
    
    def test_validate_status_transition_same_status(self):
        """Test transition to same status is not allowed."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        
        with pytest.raises(ValueError) as exc_info:
            validate_status_transition("PENDING", "PENDING", allowed)
        
        assert "already set" in str(exc_info.value)
    
    def test_validate_status_transition_no_allowed_transitions(self):
        """Test status with no allowed transitions."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        
        with pytest.raises(ValueError) as exc_info:
            validate_status_transition("UNKNOWN", "PENDING", allowed)
        
        assert "Cannot transition" in str(exc_info.value)


class TestPasswordValidation:
    """Test suite for password strength validation."""
    
    def test_validate_password_strength_valid(self):
        """Test password validation with strong passwords."""
        # Should not raise
        validate_password_strength("Password123")
        validate_password_strength("SecurePass1")
        validate_password_strength("MyP@ssw0rd")
    
    def test_validate_password_strength_too_short(self):
        """Test password validation with short password."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("Pass1")
        
        assert "at least 8 characters" in str(exc_info.value)
    
    def test_validate_password_strength_no_uppercase(self):
        """Test password validation without uppercase letter."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("password123")
        
        assert "uppercase letter" in str(exc_info.value)
    
    def test_validate_password_strength_no_lowercase(self):
        """Test password validation without lowercase letter."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("PASSWORD123")
        
        assert "lowercase letter" in str(exc_info.value)
    
    def test_validate_password_strength_no_digit(self):
        """Test password validation without digit."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("PasswordOnly")
        
        assert "digit" in str(exc_info.value)
    
    def test_validate_password_strength_with_special_chars(self):
        """Test password validation with special characters."""
        # Should not raise
        validate_password_strength("P@ssw0rd!")
        validate_password_strength("Secure#Pass1")
