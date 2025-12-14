"""
Unit tests for Lead schemas.

Tests validation rules, field constraints, and schema behavior.
"""

import uuid
from datetime import datetime, UTC

import pytest
from pydantic import ValidationError

from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
)
from app.models.lead import LeadStatus


class TestLeadCreate:
    """Test suite for LeadCreate schema."""
    
    def test_valid_lead_create(self):
        """Test creating a valid lead."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        lead = LeadCreate(**data)
        
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john.doe@example.com"
    
    def test_first_name_required(self):
        """Test that first_name is required."""
        data = {
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "first_name" in str(exc_info.value)
    
    def test_last_name_required(self):
        """Test that last_name is required."""
        data = {
            "first_name": "John",
            "email": "john.doe@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "last_name" in str(exc_info.value)
    
    def test_email_required(self):
        """Test that email is required."""
        data = {
            "first_name": "John",
            "last_name": "Doe"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "email" in str(exc_info.value)
    
    def test_first_name_too_short(self):
        """Test that first_name must have minimum length."""
        data = {
            "first_name": "",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "first_name" in str(exc_info.value)
    
    def test_first_name_too_long(self):
        """Test that first_name has maximum length."""
        data = {
            "first_name": "A" * 101,
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "first_name" in str(exc_info.value)
    
    def test_last_name_too_long(self):
        """Test that last_name has maximum length."""
        data = {
            "first_name": "John",
            "last_name": "D" * 101,
            "email": "john.doe@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "last_name" in str(exc_info.value)
    
    def test_invalid_email_format(self):
        """Test that email must be valid format."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "not-an-email"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "email" in str(exc_info.value)
    
    def test_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "john@example.com",
            "john.doe@example.com",
            "john+tag@example.co.uk",
            "john_doe@example.com"
        ]
        
        for email in valid_emails:
            data = {
                "first_name": "John",
                "last_name": "Doe",
                "email": email
            }
            lead = LeadCreate(**data)
            assert lead.email == email


class TestLeadUpdate:
    """Test suite for LeadUpdate schema."""
    
    def test_valid_lead_update(self):
        """Test valid lead status update."""
        data = {"status": LeadStatus.REACHED_OUT}
        
        update = LeadUpdate(**data)
        
        assert update.status == LeadStatus.REACHED_OUT
    
    def test_status_required(self):
        """Test that status is required."""
        with pytest.raises(ValidationError) as exc_info:
            LeadUpdate()
        
        assert "status" in str(exc_info.value)
    
    def test_invalid_status_value(self):
        """Test that invalid status values are rejected."""
        data = {"status": "INVALID_STATUS"}
        
        with pytest.raises(ValidationError):
            LeadUpdate(**data)
    
    def test_pending_status(self):
        """Test updating to PENDING status."""
        data = {"status": LeadStatus.PENDING}
        
        update = LeadUpdate(**data)
        
        assert update.status == LeadStatus.PENDING


class TestLeadResponse:
    """Test suite for LeadResponse schema."""
    
    def test_valid_lead_response(self):
        """Test creating a valid lead response."""
        data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "reached_out_at": None
        }
        
        response = LeadResponse(**data)
        
        assert response.first_name == "John"
        assert response.last_name == "Doe"
        assert response.status == LeadStatus.PENDING
    
    def test_full_name_property(self):
        """Test the full_name computed property."""
        data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "reached_out_at": None
        }
        
        response = LeadResponse(**data)
        
        assert response.full_name == "John Doe"
    
    def test_with_reached_out_timestamp(self):
        """Test lead response with reached_out_at timestamp."""
        now = datetime.now(UTC)
        data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.REACHED_OUT,
            "created_at": now,
            "updated_at": now,
            "reached_out_at": now
        }
        
        response = LeadResponse(**data)
        
        assert response.reached_out_at is not None
        assert response.status == LeadStatus.REACHED_OUT


class TestLeadListResponse:
    """Test suite for LeadListResponse schema."""
    
    def test_valid_lead_list_response(self):
        """Test creating a valid paginated response."""
        lead_data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "reached_out_at": None
        }
        
        data = {
            "items": [LeadResponse(**lead_data)],
            "total": 25,
            "page": 1,
            "page_size": 10
        }
        
        response = LeadListResponse(**data)
        
        assert len(response.items) == 1
        assert response.total == 25
        assert response.page == 1
        assert response.page_size == 10
    
    def test_total_pages_calculation(self):
        """Test total_pages computed property."""
        lead_data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "reached_out_at": None
        }
        
        data = {
            "items": [LeadResponse(**lead_data)],
            "total": 25,
            "page": 1,
            "page_size": 10
        }
        
        response = LeadListResponse(**data)
        
        assert response.total_pages == 3
    
    def test_has_next_page(self):
        """Test has_next computed property."""
        lead_data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "reached_out_at": None
        }
        
        # First page should have next
        data = {
            "items": [LeadResponse(**lead_data)],
            "total": 25,
            "page": 1,
            "page_size": 10
        }
        response = LeadListResponse(**data)
        assert response.has_next is True
        
        # Last page should not have next
        data["page"] = 3
        response = LeadListResponse(**data)
        assert response.has_next is False
    
    def test_has_previous_page(self):
        """Test has_previous computed property."""
        lead_data = {
            "id": uuid.uuid4(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "reached_out_at": None
        }
        
        # First page should not have previous
        data = {
            "items": [LeadResponse(**lead_data)],
            "total": 25,
            "page": 1,
            "page_size": 10
        }
        response = LeadListResponse(**data)
        assert response.has_previous is False
        
        # Second page should have previous
        data["page"] = 2
        response = LeadListResponse(**data)
        assert response.has_previous is True
    
    def test_empty_list(self):
        """Test paginated response with no items."""
        data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10
        }
        
        response = LeadListResponse(**data)
        
        assert len(response.items) == 0
        assert response.total == 0
        assert response.total_pages == 0
        assert response.has_next is False
        assert response.has_previous is False
    
    def test_page_size_validation(self):
        """Test that page_size has reasonable limits."""
        data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 101
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadListResponse(**data)
        
        assert "page_size" in str(exc_info.value)
