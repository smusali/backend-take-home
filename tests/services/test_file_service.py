"""
Unit tests for FileService.

Tests file upload, retrieval, deletion, and security features.
"""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile, HTTPException

from app.services.file_service import FileService


class TestFileService:
    """Test suite for FileService."""
    
    def setup_method(self):
        """Setup test file service with temporary directory."""
        self.service = FileService()
        self.test_upload_dir = self.service.upload_dir
        
        # Ensure directory exists
        self.service._ensure_upload_directory()
    
    def teardown_method(self):
        """Cleanup test files."""
        # Remove all test files
        if self.test_upload_dir.exists():
            for file_path in self.test_upload_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
    
    def test_ensure_upload_directory_creates_dir(self):
        """Test that upload directory is created if it doesn't exist."""
        # Directory should exist after initialization
        assert self.test_upload_dir.exists()
        assert self.test_upload_dir.is_dir()
    
    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        filename = self.service._generate_unique_filename("resume.pdf")
        
        assert filename.endswith("_resume.pdf")
        assert len(filename) > 20  # UUID + underscore + name
    
    def test_generate_unique_filename_preserves_extension(self):
        """Test that file extension is preserved."""
        pdf_name = self.service._generate_unique_filename("test.pdf")
        doc_name = self.service._generate_unique_filename("test.doc")
        docx_name = self.service._generate_unique_filename("test.docx")
        
        assert pdf_name.endswith(".pdf")
        assert doc_name.endswith(".doc")
        assert docx_name.endswith(".docx")
    
    def test_generate_unique_filename_sanitizes_name(self):
        """Test that dangerous characters are removed from filename."""
        filename = self.service._generate_unique_filename("my<>resume.pdf")
        
        assert "<" not in filename
        assert ">" not in filename
        assert filename.endswith("_myresume.pdf")
    
    def test_generate_unique_filename_limits_length(self):
        """Test that filename length is limited."""
        long_name = "a" * 100 + ".pdf"
        filename = self.service._generate_unique_filename(long_name)
        
        # Should be limited to reasonable length
        assert len(filename) < 100
    
    def test_sanitize_file_path_valid_path(self):
        """Test path sanitization with valid path."""
        path = self.service._sanitize_file_path("test.pdf")
        
        assert isinstance(path, Path)
        assert str(path).startswith(str(self.test_upload_dir.resolve()))
    
    def test_sanitize_file_path_prevents_traversal(self):
        """Test that directory traversal is prevented."""
        with pytest.raises(ValueError) as exc_info:
            self.service._sanitize_file_path("../../etc/passwd")
        
        assert "directory traversal" in str(exc_info.value)
    
    def test_sanitize_file_path_prevents_absolute_paths(self):
        """Test that absolute paths are rejected."""
        with pytest.raises(ValueError):
            self.service._sanitize_file_path("/etc/passwd")
    
    @pytest.mark.asyncio
    async def test_save_file_success(self):
        """Test successful file upload."""
        content = b"PDF file content here"
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(content)
        )
        file.size = len(content)
        
        saved_path = await self.service.save_file(file)
        
        assert saved_path.endswith(".pdf")
        assert (self.test_upload_dir / saved_path).exists()
    
    @pytest.mark.asyncio
    async def test_save_file_creates_unique_names(self):
        """Test that multiple uploads create unique filenames."""
        content = b"PDF content"
        
        file1 = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file1.size = len(content)
        path1 = await self.service.save_file(file1)
        
        file2 = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file2.size = len(content)
        path2 = await self.service.save_file(file2)
        
        assert path1 != path2
    
    @pytest.mark.asyncio
    async def test_save_file_invalid_type(self):
        """Test that invalid file types are rejected."""
        content = b"Text file content"
        file = UploadFile(
            filename="resume.txt",
            file=BytesIO(content)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.save_file(file)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_save_file_too_large(self):
        """Test that files exceeding size limit are rejected."""
        # Create content larger than max size
        large_content = b"x" * (self.service.settings.MAX_FILE_SIZE + 1000)
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(large_content)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.save_file(file)
        
        assert exc_info.value.status_code == 413
    
    @pytest.mark.asyncio
    async def test_get_file_path_existing_file(self):
        """Test getting path to existing file."""
        # Save a file first
        content = b"PDF content"
        file = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file.size = len(content)
        saved_path = await self.service.save_file(file)
        
        # Get file path
        file_path = self.service.get_file_path(saved_path)
        
        assert file_path.exists()
        assert file_path.is_file()
    
    def test_get_file_path_nonexistent_file(self):
        """Test getting path to nonexistent file raises error."""
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_file_path("nonexistent.pdf")
        
        assert exc_info.value.status_code == 404
    
    def test_get_file_path_with_traversal_attempt(self):
        """Test that directory traversal is prevented."""
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_file_path("../../etc/passwd")
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_file_response(self):
        """Test getting FileResponse for download."""
        # Save a file first
        content = b"PDF content"
        file = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file.size = len(content)
        saved_path = await self.service.save_file(file)
        
        # Get file response
        response = self.service.get_file_response(saved_path)
        
        assert response.path == str(self.test_upload_dir.resolve() / saved_path)
        assert response.media_type == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_delete_file_existing(self):
        """Test deleting an existing file."""
        # Save a file first
        content = b"PDF content"
        file = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file.size = len(content)
        saved_path = await self.service.save_file(file)
        
        # Verify file exists
        assert (self.test_upload_dir / saved_path).exists()
        
        # Delete file
        deleted = self.service.delete_file(saved_path)
        
        assert deleted is True
        assert not (self.test_upload_dir / saved_path).exists()
    
    def test_delete_file_nonexistent(self):
        """Test deleting nonexistent file returns False."""
        deleted = self.service.delete_file("nonexistent.pdf")
        
        assert deleted is False
    
    def test_delete_file_with_traversal_attempt(self):
        """Test that directory traversal is prevented in delete."""
        with pytest.raises(HTTPException) as exc_info:
            self.service.delete_file("../../etc/passwd")
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_file_exists_true(self):
        """Test file_exists returns True for existing file."""
        # Save a file first
        content = b"PDF content"
        file = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file.size = len(content)
        saved_path = await self.service.save_file(file)
        
        # Check existence
        exists = self.service.file_exists(saved_path)
        
        assert exists is True
    
    def test_file_exists_false(self):
        """Test file_exists returns False for nonexistent file."""
        exists = self.service.file_exists("nonexistent.pdf")
        
        assert exists is False
    
    def test_file_exists_with_traversal_returns_false(self):
        """Test file_exists with traversal attempt returns False."""
        exists = self.service.file_exists("../../etc/passwd")
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_get_file_size(self):
        """Test getting file size."""
        # Save a file first
        content = b"PDF content with known size"
        file = UploadFile(filename="resume.pdf", file=BytesIO(content))
        file.size = len(content)
        saved_path = await self.service.save_file(file)
        
        # Get file size
        size = self.service.get_file_size(saved_path)
        
        assert size == len(content)
    
    def test_get_file_size_nonexistent(self):
        """Test getting size of nonexistent file returns None."""
        size = self.service.get_file_size("nonexistent.pdf")
        
        assert size is None
