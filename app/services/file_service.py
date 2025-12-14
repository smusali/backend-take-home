"""
File storage service for resume uploads and management.

Handles file upload, storage, retrieval, and deletion with
secure filename generation and validation.
"""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.schemas.validators import validate_resume_file


class FileService:
    """
    Service for managing file uploads and storage.
    
    Handles resume file uploads with validation, unique filename generation,
    and secure storage management.
    """
    
    def __init__(self):
        """Initialize file service with configuration."""
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self) -> None:
        """
        Ensure upload directory exists.
        
        Creates the directory and any parent directories if they don't exist.
        """
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename using UUID.
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            Unique filename with format: {uuid}_{sanitized_name}{extension}
            
        Example:
            >>> generate_unique_filename("resume.pdf")
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890_resume.pdf'
        """
        # Get file extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Sanitize base filename (remove extension and dangerous chars)
        base_name = Path(original_filename).stem
        base_name = "".join(c for c in base_name if c.isalnum() or c in "._-")
        base_name = base_name[:50]  # Limit length
        
        # Generate unique filename
        unique_id = uuid.uuid4()
        return f"{unique_id}_{base_name}{file_ext}"
    
    def _sanitize_file_path(self, file_path: str) -> Path:
        """
        Sanitize file path to prevent directory traversal attacks.
        
        Args:
            file_path: File path to sanitize
            
        Returns:
            Sanitized Path object within upload directory
            
        Raises:
            ValueError: If path attempts to escape upload directory
        """
        # Resolve to absolute path
        full_path = (self.upload_dir / file_path).resolve()
        
        # Ensure path is within upload directory
        if not str(full_path).startswith(str(self.upload_dir.resolve())):
            raise ValueError("Invalid file path - directory traversal detected")
        
        return full_path
    
    async def save_file(self, file: UploadFile) -> str:
        """
        Save an uploaded file to storage.
        
        Args:
            file: Uploaded file from FastAPI
            
        Returns:
            Relative file path (from upload directory)
            
        Raises:
            HTTPException: If validation fails or save fails
            
        Example:
            >>> path = await service.save_file(uploaded_file)
            >>> print(path)
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890_resume.pdf'
        """
        # Validate file
        try:
            validate_resume_file(file, max_size_bytes=self.settings.MAX_FILE_SIZE)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = self.upload_dir / unique_filename
        
        # Save file
        try:
            contents = await file.read()
            
            # Verify size after reading (more accurate than Content-Length)
            if len(contents) > self.settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size "
                           f"({self.settings.MAX_FILE_SIZE / (1024*1024):.2f}MB)"
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Return relative path
        return unique_filename
    
    def get_file_path(self, filename: str) -> Path:
        """
        Get the full path to a stored file.
        
        Args:
            filename: Relative filename
            
        Returns:
            Full Path to the file
            
        Raises:
            HTTPException: If file doesn't exist or path is invalid
        """
        try:
            file_path = self._sanitize_file_path(filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return file_path
    
    def get_file_response(self, filename: str) -> FileResponse:
        """
        Get a FileResponse for downloading a stored file.
        
        Args:
            filename: Relative filename
            
        Returns:
            FastAPI FileResponse for download
            
        Raises:
            HTTPException: If file doesn't exist or path is invalid
        """
        file_path = self.get_file_path(filename)
        
        # Determine media type based on extension
        media_type_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        media_type = media_type_map.get(file_path.suffix.lower(), "application/octet-stream")
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name
        )
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            filename: Relative filename
            
        Returns:
            True if file was deleted, False if file didn't exist
            
        Raises:
            HTTPException: If path is invalid or deletion fails
        """
        try:
            file_path = self._sanitize_file_path(filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            filename: Relative filename
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            file_path = self._sanitize_file_path(filename)
            return file_path.exists()
        except ValueError:
            return False
    
    def get_file_size(self, filename: str) -> Optional[int]:
        """
        Get the size of a stored file in bytes.
        
        Args:
            filename: Relative filename
            
        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            file_path = self._sanitize_file_path(filename)
            if file_path.exists():
                return file_path.stat().st_size
        except (ValueError, OSError):
            pass
        
        return None


__all__ = ["FileService"]
