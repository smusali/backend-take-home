"""
Unit tests for utility functions and validators.

Tests validation functions, sanitization, and helper utilities.
"""

import pytest
from fastapi import UploadFile
from io import BytesIO

from app.schemas.validators import (
    validate_file_size,
    validate_file_extension,
    validate_resume_file,
    sanitize_name,
    validate_email_format,
    validate_status_transition,
    validate_password_strength,
    ALLOWED_RESUME_EXTENSIONS
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)


class TestFileValidators:
    """Tests for file validation functions."""
    
    def test_validate_file_size_within_limit(self):
        """Test file within size limit passes validation."""
        file = UploadFile(filename="test.pdf", file=BytesIO(b"content"))
        file.size = 1024 * 1024  # 1MB
        
        validate_file_size(file, max_size_bytes=5 * 1024 * 1024)
    
    def test_validate_file_size_exceeds_limit(self):
        """Test file exceeding size limit raises error."""
        file = UploadFile(filename="test.pdf", file=BytesIO(b"content"))
        file.size = 10 * 1024 * 1024  # 10MB
        
        with pytest.raises(ValueError) as exc_info:
            validate_file_size(file, max_size_bytes=5 * 1024 * 1024)
        
        assert "exceeds maximum" in str(exc_info.value).lower()
    
    def test_validate_file_extension_valid_pdf(self):
        """Test valid PDF extension passes validation."""
        validate_file_extension("resume.pdf", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_valid_doc(self):
        """Test valid DOC extension passes validation."""
        validate_file_extension("resume.doc", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_valid_docx(self):
        """Test valid DOCX extension passes validation."""
        validate_file_extension("resume.docx", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_case_insensitive(self):
        """Test extension validation is case insensitive."""
        validate_file_extension("resume.PDF", ALLOWED_RESUME_EXTENSIONS)
        validate_file_extension("resume.Pdf", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_invalid(self):
        """Test invalid extension raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_file_extension("resume.txt", ALLOWED_RESUME_EXTENSIONS)
        
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_validate_file_extension_no_extension(self):
        """Test file without extension raises error."""
        with pytest.raises(ValueError):
            validate_file_extension("resume", ALLOWED_RESUME_EXTENSIONS)
    
    def test_validate_file_extension_empty_filename(self):
        """Test empty filename raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_file_extension("", ALLOWED_RESUME_EXTENSIONS)
        
        assert "required" in str(exc_info.value).lower()
    
    def test_validate_resume_file_valid(self):
        """Test valid resume file passes validation."""
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(b"PDF content"),
            headers={"content-type": "application/pdf"}
        )
        file.size = 1024 * 1024
        
        validate_resume_file(file, max_size_bytes=5 * 1024 * 1024)
    
    def test_validate_resume_file_no_file(self):
        """Test validation fails with no file."""
        with pytest.raises(ValueError) as exc_info:
            validate_resume_file(None)
        
        assert "required" in str(exc_info.value).lower()
    
    def test_validate_resume_file_invalid_mime_type(self):
        """Test validation fails with invalid MIME type."""
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(b"content"),
            headers={"content-type": "text/plain"}
        )
        file.size = 1024
        
        with pytest.raises(ValueError) as exc_info:
            validate_resume_file(file)
        
        assert "invalid file type" in str(exc_info.value).lower()


class TestTextValidators:
    """Tests for text validation and sanitization."""
    
    def test_sanitize_name_basic(self):
        """Test basic name sanitization."""
        result = sanitize_name("John Doe")
        assert result == "John Doe"
    
    def test_sanitize_name_extra_whitespace(self):
        """Test removing extra whitespace."""
        result = sanitize_name("  John   Doe  ")
        assert result == "John Doe"
    
    def test_sanitize_name_remove_html_tags(self):
        """Test removing HTML tags."""
        result = sanitize_name("John<script>alert()</script>Doe")
        assert "<script>" not in result
        assert "alert()" not in result
    
    def test_sanitize_name_remove_dangerous_chars(self):
        """Test removing dangerous characters."""
        result = sanitize_name("John<>&\"'Doe")
        assert "<" not in result
        assert ">" not in result
        assert "&" not in result
    
    def test_sanitize_name_preserve_valid_chars(self):
        """Test preserving valid characters."""
        result = sanitize_name("Mary-Jane O'Connor")
        assert "Mary" in result
        assert "Jane" in result
    
    def test_sanitize_name_empty_string(self):
        """Test sanitizing empty string."""
        result = sanitize_name("")
        assert result == ""
    
    def test_validate_email_format_valid(self):
        """Test valid email format."""
        result = validate_email_format("user@example.com")
        assert result == "user@example.com"
    
    def test_validate_email_format_normalization(self):
        """Test email is normalized to lowercase."""
        result = validate_email_format("USER@EXAMPLE.COM")
        assert result == "user@example.com"
    
    def test_validate_email_format_invalid(self):
        """Test invalid email format raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_email_format("invalid-email")
        
        assert "invalid" in str(exc_info.value).lower()
    
    def test_validate_email_format_empty(self):
        """Test empty email raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_email_format("")
        
        assert "required" in str(exc_info.value).lower()


class TestPasswordValidation:
    """Tests for password validation."""
    
    def test_validate_password_strength_valid(self):
        """Test valid password passes validation."""
        validate_password_strength("SecurePass123")
    
    def test_validate_password_strength_too_short(self):
        """Test password too short raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("Short1")
        
        assert "8 characters" in str(exc_info.value)
    
    def test_validate_password_strength_no_uppercase(self):
        """Test password without uppercase raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("lowercase123")
        
        assert "uppercase" in str(exc_info.value).lower()
    
    def test_validate_password_strength_no_lowercase(self):
        """Test password without lowercase raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("UPPERCASE123")
        
        assert "lowercase" in str(exc_info.value).lower()
    
    def test_validate_password_strength_no_digit(self):
        """Test password without digit raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_password_strength("NoDigitsHere")
        
        assert "digit" in str(exc_info.value).lower()
    
    def test_validate_password_strength_with_special_chars(self):
        """Test password with special characters."""
        validate_password_strength("Secure!Pass123@")


class TestStatusTransition:
    """Tests for status transition validation."""
    
    def test_valid_transition(self):
        """Test valid status transition."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        validate_status_transition("PENDING", "REACHED_OUT", allowed)
    
    def test_invalid_transition(self):
        """Test invalid status transition raises error."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        
        with pytest.raises(ValueError) as exc_info:
            validate_status_transition("REACHED_OUT", "PENDING", allowed)
        
        assert "cannot transition" in str(exc_info.value).lower()
    
    def test_transition_to_same_status(self):
        """Test transitioning to same status raises error."""
        allowed = {"PENDING": ["REACHED_OUT"]}
        
        with pytest.raises(ValueError) as exc_info:
            validate_status_transition("PENDING", "PENDING", allowed)
        
        assert "already set" in str(exc_info.value).lower()
    
    def test_transition_no_allowed_transitions(self):
        """Test status with no allowed transitions."""
        allowed = {"REACHED_OUT": []}
        
        with pytest.raises(ValueError) as exc_info:
            validate_status_transition("REACHED_OUT", "PENDING", allowed)
        
        assert "cannot transition" in str(exc_info.value).lower()


class TestSecurityFunctions:
    """Tests for security utility functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
    
    def test_hash_password_different_hashes(self):
        """Test same password produces different hashes."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword", hashed) is False
    
    def test_create_access_token(self):
        """Test creating JWT access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test verifying valid JWT token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        token_data = verify_token(token)
        
        assert token_data.username == "testuser"
    
    def test_verify_token_invalid(self):
        """Test verifying invalid token raises error."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_expired(self):
        """Test verifying expired token raises error."""
        from datetime import timedelta
        from fastapi import HTTPException
        
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_hash_password_long_password(self):
        """Test hashing very long password (bcrypt truncates at 72 bytes)."""
        password = "A" * 100
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")
        assert verify_password(password, hashed) is True
