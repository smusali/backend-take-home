"""
Unit tests for LeadService.

Tests lead creation workflow, retrieval, updates, and business logic
with integration of file storage and email services.
"""

import uuid
from io import BytesIO
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate
from app.services.lead_service import LeadService


class TestLeadService:
    """Test suite for LeadService."""
    
    def setup_method(self):
        """Setup test lead service with mocked dependencies."""
        self.mock_db = MagicMock(spec=Session)
        
        # We'll manually inject mocks instead of using decorators
        self.mock_repo = MagicMock()
        self.mock_file_service = MagicMock()
        self.mock_email_service = MagicMock()
        
        # Create service with mocked database
        with patch('app.services.lead_service.LeadRepository') as mock_repo_class, \
             patch('app.services.lead_service.FileService') as mock_file_class, \
             patch('app.services.lead_service.EmailService') as mock_email_class:
            
            mock_repo_class.return_value = self.mock_repo
            mock_file_class.return_value = self.mock_file_service
            mock_email_class.return_value = self.mock_email_service
            
            self.service = LeadService(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_create_lead_success(self):
        """Test successful lead creation with full workflow."""
        # Setup mocks
        self.mock_file_service.save_file = AsyncMock(return_value="resume-uuid_test.pdf")
        self.mock_email_service.send_prospect_confirmation = AsyncMock(return_value=True)
        self.mock_email_service.send_attorney_notification = AsyncMock(return_value=True)
        
        # Mock repository
        self.mock_repo.get_by_email = MagicMock(return_value=None)
        
        created_lead = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume-uuid_test.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        self.mock_repo.create = MagicMock(return_value=created_lead)
        
        # Create test data
        lead_data = LeadCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        resume_file = UploadFile(
            filename="test_resume.pdf",
            file=BytesIO(b"PDF content")
        )
        resume_file.size = 100
        
        # Execute
        result = await self.service.create_lead(lead_data, resume_file)
        
        # Verify
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert result.email == "john@example.com"
        
        # Verify workflow steps
        self.mock_file_service.save_file.assert_called_once()
        self.mock_repo.get_by_email.assert_called_once_with("john@example.com")
        self.mock_repo.create.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_email_service.send_prospect_confirmation.assert_called_once()
        self.mock_email_service.send_attorney_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_lead_duplicate_email(self):
        """Test that duplicate email raises error."""
        # Mock existing lead
        existing_lead = Lead(
            id=uuid.uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="john@example.com",
            resume_path="existing.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        self.mock_repo.get_by_email = MagicMock(return_value=existing_lead)
        
        lead_data = LeadCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        resume_file = UploadFile(filename="test.pdf", file=BytesIO(b"content"))
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.create_lead(lead_data, resume_file)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail
    
    @pytest.mark.asyncio
    @patch('app.services.lead_service.FileService')
    @patch('app.services.lead_service.EmailService')
    async def test_create_lead_rollback_on_email_failure(
        self,
        mock_email_service_class,
        mock_file_service_class
    ):
        """Test rollback when email sending fails."""
        # Setup mocks
        mock_file_service = MagicMock()
        mock_file_service.save_file = AsyncMock(return_value="resume.pdf")
        mock_file_service.delete_file = MagicMock(return_value=True)
        mock_file_service_class.return_value = mock_file_service
        
        mock_email_service = MagicMock()
        mock_email_service.send_prospect_confirmation = AsyncMock(
            side_effect=Exception("Email failed")
        )
        mock_email_service_class.return_value = mock_email_service
        
        self.mock_repo.get_by_email = MagicMock(return_value=None)
        
        created_lead = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        self.mock_repo.create = MagicMock(return_value=created_lead)
        
        lead_data = LeadCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        resume_file = UploadFile(filename="test.pdf", file=BytesIO(b"content"))
        resume_file.size = 100
        
        with pytest.raises(HTTPException):
            await self.service.create_lead(lead_data, resume_file)
        
        # Verify rollback - just ensure DB rollback was called
        self.mock_db.rollback.assert_called_once()
    
    def test_get_lead_success(self):
        """Test getting a lead by ID."""
        lead_id = uuid.uuid4()
        lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        self.mock_repo.get = MagicMock(return_value=lead)
        
        result = self.service.get_lead(lead_id)
        
        assert result.id == lead_id
        assert result.first_name == "John"
        self.mock_repo.get.assert_called_once_with(lead_id)
    
    def test_get_lead_not_found(self):
        """Test getting non-existent lead raises 404."""
        lead_id = uuid.uuid4()
        self.mock_repo.get = MagicMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_lead(lead_id)
        
        assert exc_info.value.status_code == 404
    
    def test_get_leads_without_filter(self):
        """Test getting all leads without filter."""
        leads = [
            Lead(
                id=uuid.uuid4(),
                first_name=f"Person{i}",
                last_name="Test",
                email=f"person{i}@example.com",
                resume_path="resume.pdf",
                status=LeadStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            for i in range(3)
        ]
        
        self.mock_repo.get_multi = MagicMock(return_value=leads)
        
        result = self.service.get_leads(skip=0, limit=10)
        
        assert len(result) == 3
        self.mock_repo.get_multi.assert_called_once_with(skip=0, limit=10)
    
    def test_get_leads_with_status_filter(self):
        """Test getting leads filtered by status."""
        pending_leads = [
            Lead(
                id=uuid.uuid4(),
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                resume_path="resume.pdf",
                status=LeadStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
        ]
        
        self.mock_repo.get_by_status = MagicMock(return_value=pending_leads)
        
        result = self.service.get_leads(
            skip=0,
            limit=10,
            status_filter=LeadStatus.PENDING
        )
        
        assert len(result) == 1
        self.mock_repo.get_by_status.assert_called_once()
    
    def test_get_leads_paginated(self):
        """Test getting leads with pagination metadata."""
        leads = [
            Lead(
                id=uuid.uuid4(),
                first_name=f"Person{i}",
                last_name="Test",
                email=f"person{i}@example.com",
                resume_path="resume.pdf",
                status=LeadStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            for i in range(5)
        ]
        
        self.mock_repo.get_multi = MagicMock(return_value=leads)
        self.mock_repo.count = MagicMock(return_value=15)
        
        result = self.service.get_leads_paginated(page=1, page_size=5)
        
        assert len(result["leads"]) == 5
        assert result["total"] == 15
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert result["total_pages"] == 3
        assert result["has_next"] is True
        assert result["has_previous"] is False
    
    def test_get_leads_paginated_last_page(self):
        """Test pagination metadata for last page."""
        leads = [
            Lead(
                id=uuid.uuid4(),
                first_name=f"Person{i}",
                last_name="Test",
                email=f"person{i}@example.com",
                resume_path="resume.pdf",
                status=LeadStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            for i in range(2)
        ]
        
        self.mock_repo.get_multi = MagicMock(return_value=leads)
        self.mock_repo.count = MagicMock(return_value=12)
        
        result = self.service.get_leads_paginated(page=3, page_size=5)
        
        assert result["page"] == 3
        assert result["total_pages"] == 3
        assert result["has_next"] is False
        assert result["has_previous"] is True
    
    def test_update_lead_status_success(self):
        """Test updating lead status."""
        lead_id = uuid.uuid4()
        lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        updated_lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.REACHED_OUT,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reached_out_at=datetime.now(UTC)
        )
        
        self.mock_repo.get = MagicMock(return_value=lead)
        self.mock_repo.update_status = MagicMock(return_value=updated_lead)
        
        result = self.service.update_lead_status(lead_id, LeadStatus.REACHED_OUT)
        
        assert result.status == LeadStatus.REACHED_OUT
        self.mock_repo.update_status.assert_called_once_with(
            lead_id,
            LeadStatus.REACHED_OUT
        )
        self.mock_db.commit.assert_called_once()
    
    def test_update_lead_status_invalid_transition(self):
        """Test that invalid status transition raises error."""
        lead_id = uuid.uuid4()
        lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.REACHED_OUT,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reached_out_at=datetime.now(UTC)
        )
        
        self.mock_repo.get = MagicMock(return_value=lead)
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.update_lead_status(lead_id, LeadStatus.PENDING)
        
        assert exc_info.value.status_code == 400
        assert "transition" in exc_info.value.detail.lower()
    
    def test_update_lead_status_not_found(self):
        """Test updating status of non-existent lead."""
        lead_id = uuid.uuid4()
        self.mock_repo.get = MagicMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.update_lead_status(lead_id, LeadStatus.REACHED_OUT)
        
        assert exc_info.value.status_code == 404
    
    def test_update_lead_with_status(self):
        """Test updating lead calls update_lead_status when status provided."""
        lead_id = uuid.uuid4()
        lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        updated_lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.REACHED_OUT,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reached_out_at=datetime.now(UTC)
        )
        
        self.mock_repo.get = MagicMock(return_value=lead)
        self.mock_repo.update_status = MagicMock(return_value=updated_lead)
        
        update_data = LeadUpdate(status=LeadStatus.REACHED_OUT)
        result = self.service.update_lead(lead_id, update_data)
        
        assert result.status == LeadStatus.REACHED_OUT
    
    def test_get_recent_leads(self):
        """Test getting recent leads."""
        recent_leads = [
            Lead(
                id=uuid.uuid4(),
                first_name=f"Person{i}",
                last_name="Test",
                email=f"person{i}@example.com",
                resume_path="resume.pdf",
                status=LeadStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            for i in range(5)
        ]
        
        self.mock_repo.get_recent_leads = MagicMock(return_value=recent_leads)
        
        result = self.service.get_recent_leads(limit=5)
        
        assert len(result) == 5
        self.mock_repo.get_recent_leads.assert_called_once_with(limit=5)
    
    def test_get_lead_count_by_status(self):
        """Test getting lead counts grouped by status."""
        self.mock_repo.count_by_status = MagicMock(side_effect=[10, 5])
        
        result = self.service.get_lead_count_by_status()
        
        assert result[LeadStatus.PENDING] == 10
        assert result[LeadStatus.REACHED_OUT] == 5
        assert self.mock_repo.count_by_status.call_count == 2
    
    def test_delete_lead_success(self):
        """Test deleting a lead and its resume."""
        lead_id = uuid.uuid4()
        lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        self.mock_repo.get = MagicMock(return_value=lead)
        self.mock_repo.delete = MagicMock(return_value=True)
        self.mock_file_service.delete_file = MagicMock(return_value=True)
        
        result = self.service.delete_lead(lead_id)
        
        assert result is True
        self.mock_file_service.delete_file.assert_called_once_with("resume.pdf")
        self.mock_repo.delete.assert_called_once_with(lead_id)
        self.mock_db.commit.assert_called_once()
    
    def test_delete_lead_not_found(self):
        """Test deleting non-existent lead raises 404."""
        lead_id = uuid.uuid4()
        self.mock_repo.get = MagicMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.delete_lead(lead_id)
        
        assert exc_info.value.status_code == 404
    
    def test_delete_lead_without_resume(self):
        """Test deleting lead without resume path."""
        lead_id = uuid.uuid4()
        lead = Lead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path=None,
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        self.mock_repo.get = MagicMock(return_value=lead)
        self.mock_repo.delete = MagicMock(return_value=True)
        self.mock_file_service.delete_file = MagicMock()
        
        result = self.service.delete_lead(lead_id)
        
        assert result is True
        self.mock_file_service.delete_file.assert_not_called()
        self.mock_repo.delete.assert_called_once()
