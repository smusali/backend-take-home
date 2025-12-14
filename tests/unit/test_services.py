"""
Unit tests for service layer.

Tests business logic, service methods, error handling, and integration
with repositories and external services.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, UploadFile
from io import BytesIO
import uuid

from app.services.lead_service import LeadService
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from app.services.email_service import EmailService
from app.models.lead import LeadStatus
from app.schemas.lead import LeadCreate
from app.schemas.user import UserCreate


class TestLeadService:
    """Tests for LeadService."""
    
    @pytest.mark.asyncio
    async def test_create_lead_success(self, db_session, mock_email_service, mock_file_service):
        """Test successful lead creation."""
        lead_data = LeadCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        resume_file = Mock(spec=UploadFile)
        resume_file.filename = "resume.pdf"
        
        with patch.object(FileService, 'save_file', new=mock_file_service.save_file):
            with patch.object(EmailService, 'send_prospect_confirmation', new=mock_email_service.send_prospect_confirmation):
                with patch.object(EmailService, 'send_attorney_notification', new=mock_email_service.send_attorney_notification):
                    service = LeadService(db_session)
                    result = await service.create_lead(lead_data, resume_file)
        
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert result.email == "john@example.com"
        assert result.status == LeadStatus.PENDING
        assert mock_email_service.send_prospect_confirmation.called
        assert mock_email_service.send_attorney_notification.called
    
    @pytest.mark.asyncio
    async def test_create_lead_duplicate_email(self, db_session, create_lead):
        """Test lead creation fails with duplicate email."""
        create_lead(email="duplicate@example.com")
        
        lead_data = LeadCreate(
            first_name="Jane",
            last_name="Smith",
            email="duplicate@example.com"
        )
        
        resume_file = Mock(spec=UploadFile)
        service = LeadService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_lead(lead_data, resume_file)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail
    
    def test_get_lead_success(self, db_session, create_lead):
        """Test retrieving a lead by ID."""
        lead = create_lead(first_name="John", last_name="Doe")
        
        service = LeadService(db_session)
        result = service.get_lead(lead.id)
        
        assert result.id == lead.id
        assert result.first_name == "John"
    
    def test_get_lead_not_found(self, db_session):
        """Test getting non-existent lead raises 404."""
        service = LeadService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_lead(uuid.uuid4())
        
        assert exc_info.value.status_code == 404
    
    def test_get_leads_pagination(self, db_session, sample_leads):
        """Test getting leads with pagination."""
        service = LeadService(db_session)
        
        results = service.get_leads(skip=0, limit=5)
        
        assert len(results) == 5
    
    def test_get_leads_with_status_filter(self, db_session, sample_leads):
        """Test filtering leads by status."""
        service = LeadService(db_session)
        
        pending_leads = service.get_leads(status_filter=LeadStatus.PENDING)
        
        assert all(lead.status == LeadStatus.PENDING for lead in pending_leads)
        assert len(pending_leads) > 0
    
    def test_get_leads_paginated_metadata(self, db_session, sample_leads):
        """Test paginated results include correct metadata."""
        service = LeadService(db_session)
        
        result = service.get_leads_paginated(page=1, page_size=5)
        
        assert "leads" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "total_pages" in result
        assert "has_next" in result
        assert "has_previous" in result
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert len(result["leads"]) <= 5
    
    def test_update_lead_status_success(self, db_session, create_lead):
        """Test updating lead status."""
        lead = create_lead(status=LeadStatus.PENDING)
        
        service = LeadService(db_session)
        result = service.update_lead_status(lead.id, LeadStatus.REACHED_OUT)
        
        assert result.status == LeadStatus.REACHED_OUT
        assert result.reached_out_at is not None
    
    def test_update_lead_status_invalid_transition(self, db_session, create_lead):
        """Test invalid status transition is rejected."""
        lead = create_lead(status=LeadStatus.REACHED_OUT)
        
        service = LeadService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_lead_status(lead.id, LeadStatus.PENDING)
        
        assert exc_info.value.status_code == 400
    
    def test_update_lead_status_not_found(self, db_session):
        """Test updating non-existent lead raises 404."""
        service = LeadService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.update_lead_status(uuid.uuid4(), LeadStatus.REACHED_OUT)
        
        assert exc_info.value.status_code == 404
    
    def test_get_recent_leads(self, db_session, sample_leads):
        """Test getting most recent leads."""
        service = LeadService(db_session)
        
        recent = service.get_recent_leads(limit=5)
        
        assert len(recent) <= 5
        assert all(hasattr(lead, 'created_at') for lead in recent)
    
    def test_get_lead_count_by_status(self, db_session, sample_leads):
        """Test getting lead counts by status."""
        service = LeadService(db_session)
        
        counts = service.get_lead_count_by_status()
        
        assert LeadStatus.PENDING in counts
        assert LeadStatus.REACHED_OUT in counts
        assert counts[LeadStatus.PENDING] >= 0
        assert counts[LeadStatus.REACHED_OUT] >= 0
    
    def test_delete_lead_success(self, db_session, create_lead):
        """Test deleting a lead."""
        lead = create_lead()
        
        with patch.object(FileService, 'delete_file', return_value=True):
            service = LeadService(db_session)
            result = service.delete_lead(lead.id)
        
        assert result is True
    
    def test_delete_lead_not_found(self, db_session):
        """Test deleting non-existent lead raises 404."""
        service = LeadService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_lead(uuid.uuid4())
        
        assert exc_info.value.status_code == 404


class TestAuthService:
    """Tests for AuthService."""
    
    def test_register_user_success(self, db_session):
        """Test successful user registration."""
        user_data = UserCreate(
            username="newattorney",
            email="new@test.com",
            password="SecurePass123"
        )
        
        service = AuthService(db_session)
        user = service.register_user(user_data)
        
        assert user.username == "newattorney"
        assert user.email == "new@test.com"
        assert user.hashed_password != "SecurePass123"
        assert user.is_active is True
    
    def test_register_user_duplicate_username(self, db_session, create_user):
        """Test registration fails with duplicate username."""
        create_user(username="duplicate")
        
        user_data = UserCreate(
            username="duplicate",
            email="different@test.com",
            password="SecurePass123"
        )
        
        service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()
    
    def test_register_user_duplicate_email(self, db_session, create_user):
        """Test registration fails with duplicate email."""
        create_user(email="duplicate@test.com")
        
        user_data = UserCreate(
            username="newuser",
            email="duplicate@test.com",
            password="SecurePass123"
        )
        
        service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()
    
    def test_login_success(self, db_session, create_user):
        """Test successful user login."""
        create_user(username="attorney1", password="TestPass123")
        
        service = AuthService(db_session)
        token = service.login("attorney1", "TestPass123")
        
        assert token.access_token is not None
        assert token.token_type == "bearer"
    
    def test_login_wrong_password(self, db_session, create_user):
        """Test login fails with wrong password."""
        create_user(username="attorney1", password="TestPass123")
        
        service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.login("attorney1", "WrongPassword")
        
        assert exc_info.value.status_code == 401
    
    def test_login_nonexistent_user(self, db_session):
        """Test login fails with non-existent user."""
        service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.login("nonexistent", "password")
        
        assert exc_info.value.status_code == 401
    
    def test_login_inactive_user(self, db_session, create_user):
        """Test login fails for inactive user."""
        create_user(username="inactive", password="TestPass123", is_active=False)
        
        service = AuthService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.login("inactive", "TestPass123")
        
        assert exc_info.value.status_code == 400
        assert "inactive" in exc_info.value.detail.lower()
    
    def test_get_user_by_username(self, db_session, create_user):
        """Test retrieving user by username."""
        user = create_user(username="attorney1")
        
        service = AuthService(db_session)
        result = service.get_user_by_username("attorney1")
        
        assert result is not None
        assert result.id == user.id
    
    def test_get_user_by_username_not_found(self, db_session):
        """Test getting non-existent user returns None."""
        service = AuthService(db_session)
        result = service.get_user_by_username("nonexistent")
        
        assert result is None
    
    def test_check_user_permissions_active(self, db_session, create_user):
        """Test active user has permissions."""
        user = create_user(is_active=True)
        
        service = AuthService(db_session)
        has_permission = service.check_user_permissions(user, "any_permission")
        
        assert has_permission is True
    
    def test_check_user_permissions_inactive(self, db_session, create_user):
        """Test inactive user has no permissions."""
        user = create_user(is_active=False)
        
        service = AuthService(db_session)
        has_permission = service.check_user_permissions(user, "any_permission")
        
        assert has_permission is False


class TestFileService:
    """Tests for FileService."""
    
    @pytest.mark.asyncio
    async def test_save_file_success(self, temp_upload_dir):
        """Test saving a file successfully."""
        content = b"PDF file content"
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(content),
            headers={"content-type": "application/pdf"}
        )
        file.size = len(content)
        
        service = FileService()
        result = await service.save_file(file)
        
        assert result is not None
        assert result.endswith(".pdf")
        assert service.file_exists(result)
    
    @pytest.mark.asyncio
    async def test_save_file_invalid_extension(self, temp_upload_dir):
        """Test saving file with invalid extension fails."""
        content = b"Text file content"
        file = UploadFile(
            filename="resume.txt",
            file=BytesIO(content)
        )
        file.size = len(content)
        
        service = FileService()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.save_file(file)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_save_file_too_large(self, temp_upload_dir):
        """Test saving file that's too large fails."""
        content = b"x" * (6 * 1024 * 1024)  # 6MB
        file = UploadFile(
            filename="resume.pdf",
            file=BytesIO(content),
            headers={"content-type": "application/pdf"}
        )
        file.size = len(content)
        
        service = FileService()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.save_file(file)
        
        assert exc_info.value.status_code in [400, 413]
    
    def test_get_file_path_success(self, temp_upload_dir):
        """Test getting file path for existing file."""
        temp_file = temp_upload_dir / "test_resume.pdf"
        temp_file.write_text("test content")
        
        service = FileService()
        file_path = service.get_file_path("test_resume.pdf")
        
        assert file_path.exists()
        assert file_path.name == "test_resume.pdf"
    
    def test_get_file_path_not_found(self, temp_upload_dir):
        """Test getting path for non-existent file raises 404."""
        service = FileService()
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_file_path("nonexistent.pdf")
        
        assert exc_info.value.status_code == 404
    
    def test_delete_file_success(self, temp_upload_dir):
        """Test deleting a file."""
        temp_file = temp_upload_dir / "delete_test.pdf"
        temp_file.write_text("test content")
        
        service = FileService()
        result = service.delete_file("delete_test.pdf")
        
        assert result is True
        assert not temp_file.exists()
    
    def test_delete_file_not_found(self, temp_upload_dir):
        """Test deleting non-existent file returns False."""
        service = FileService()
        result = service.delete_file("nonexistent.pdf")
        
        assert result is False
    
    def test_file_exists(self, temp_upload_dir):
        """Test checking if file exists."""
        temp_file = temp_upload_dir / "exists_test.pdf"
        temp_file.write_text("test content")
        
        service = FileService()
        
        assert service.file_exists("exists_test.pdf") is True
        assert service.file_exists("nonexistent.pdf") is False
    
    def test_get_file_size(self, temp_upload_dir):
        """Test getting file size."""
        content = "test content"
        temp_file = temp_upload_dir / "size_test.pdf"
        temp_file.write_text(content)
        
        service = FileService()
        size = service.get_file_size("size_test.pdf")
        
        assert size == len(content)
    
    def test_get_file_size_not_found(self, temp_upload_dir):
        """Test getting size of non-existent file returns None."""
        service = FileService()
        size = service.get_file_size("nonexistent.pdf")
        
        assert size is None


class TestEmailService:
    """Tests for EmailService."""
    
    @pytest.mark.asyncio
    async def test_send_prospect_confirmation(self, mock_smtp):
        """Test sending prospect confirmation email."""
        service = EmailService()
        
        with patch('aiosmtplib.SMTP', return_value=mock_smtp):
            result = await service.send_prospect_confirmation(
                prospect_email="john@example.com",
                prospect_name="John Doe",
                lead_id="123e4567-e89b-12d3-a456-426614174000"
            )
        
        assert result is True
        assert mock_smtp.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_attorney_notification(self, mock_smtp):
        """Test sending attorney notification email."""
        service = EmailService()
        
        with patch('aiosmtplib.SMTP', return_value=mock_smtp):
            result = await service.send_attorney_notification(
                lead_id="123e4567-e89b-12d3-a456-426614174000",
                prospect_name="John Doe",
                prospect_email="john@example.com",
                resume_filename="resume.pdf"
            )
        
        assert result is True
        assert mock_smtp.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_email_retry_on_failure(self, mock_smtp):
        """Test email service retries on failure."""
        mock_smtp.send_message.side_effect = [Exception("Network error"), None]
        
        service = EmailService()
        
        with patch('aiosmtplib.SMTP', return_value=mock_smtp):
            result = await service.send_prospect_confirmation(
                prospect_email="john@example.com",
                prospect_name="John Doe",
                lead_id="123"
            )
        
        assert result is True
        assert mock_smtp.send_message.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_send_email_max_retries_exceeded(self):
        """Test email service fails after max retries."""
        mock_smtp = AsyncMock()
        mock_smtp.send_message.side_effect = Exception("Network error")
        
        service = EmailService()
        
        with patch('aiosmtplib.SMTP', return_value=mock_smtp):
            with pytest.raises(HTTPException) as exc_info:
                await service.send_prospect_confirmation(
                    prospect_email="john@example.com",
                    prospect_name="John Doe",
                    lead_id="123"
                )
        
        assert exc_info.value.status_code == 500
