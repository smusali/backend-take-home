"""
Unit tests for Pydantic schemas.

Tests schema validation, field validators, and data transformation.
"""

import pytest
from pydantic import ValidationError

from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse
from app.schemas.user import UserCreate, UserLogin, Token, TokenData
from app.schemas.enums import LeadStatus


class TestLeadSchemas:
    """Tests for lead-related schemas."""
    
    def test_lead_create_valid(self):
        """Test creating valid LeadCreate schema."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        }
        lead = LeadCreate(**data)
        
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john@example.com"
    
    def test_lead_create_email_normalization(self):
        """Test email is normalized to lowercase."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "JOHN@EXAMPLE.COM"
        }
        lead = LeadCreate(**data)
        
        assert lead.email == "john@example.com"
    
    def test_lead_create_name_sanitization(self):
        """Test name fields are sanitized."""
        data = {
            "first_name": "  John  ",
            "last_name": "  Doe  ",
            "email": "john@example.com"
        }
        lead = LeadCreate(**data)
        
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
    
    def test_lead_create_xss_prevention(self):
        """Test XSS characters are stripped from names."""
        data = {
            "first_name": "John<script>alert()</script>",
            "last_name": "Doe",
            "email": "john@example.com"
        }
        lead = LeadCreate(**data)
        
        assert "<script>" not in lead.first_name
        assert "alert()" not in lead.first_name
    
    def test_lead_create_invalid_email(self):
        """Test validation fails with invalid email."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_lead_create_missing_fields(self):
        """Test validation fails with missing required fields."""
        data = {"first_name": "John"}
        
        with pytest.raises(ValidationError) as exc_info:
            LeadCreate(**data)
        
        errors = exc_info.value.errors()
        missing_fields = [e["loc"][0] for e in errors]
        assert "last_name" in missing_fields
        assert "email" in missing_fields
    
    def test_lead_create_empty_name(self):
        """Test validation fails with empty name."""
        data = {
            "first_name": "",
            "last_name": "Doe",
            "email": "john@example.com"
        }
        
        with pytest.raises(ValidationError):
            LeadCreate(**data)
    
    def test_lead_create_name_too_long(self):
        """Test validation fails with name exceeding max length."""
        data = {
            "first_name": "A" * 101,
            "last_name": "Doe",
            "email": "john@example.com"
        }
        
        with pytest.raises(ValidationError):
            LeadCreate(**data)
    
    def test_lead_update_valid(self):
        """Test creating valid LeadUpdate schema."""
        data = {"status": LeadStatus.REACHED_OUT}
        update = LeadUpdate(**data)
        
        assert update.status == LeadStatus.REACHED_OUT
    
    def test_lead_update_invalid_status(self):
        """Test validation fails with invalid status."""
        data = {"status": "INVALID_STATUS"}
        
        with pytest.raises(ValidationError):
            LeadUpdate(**data)
    
    def test_lead_response_from_model(self, db_session, create_lead):
        """Test creating LeadResponse from database model."""
        lead = create_lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        response = LeadResponse.model_validate(lead)
        
        assert response.id == lead.id
        assert response.first_name == "John"
        assert response.last_name == "Doe"
        assert response.email == "john@example.com"
        assert response.status == LeadStatus.PENDING
        assert response.created_at is not None
    
    def test_lead_response_full_name_property(self, db_session, create_lead):
        """Test full_name computed property."""
        lead = create_lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        response = LeadResponse.model_validate(lead)
        
        assert response.full_name == "John Doe"
    
    def test_lead_list_response(self, db_session, sample_leads):
        """Test LeadListResponse with pagination."""
        lead_responses = [
            LeadResponse.model_validate(lead) for lead in sample_leads[:5]
        ]
        
        list_response = LeadListResponse(
            items=lead_responses,
            total=10,
            page=1,
            page_size=5
        )
        
        assert len(list_response.items) == 5
        assert list_response.total == 10
        assert list_response.page == 1
        assert list_response.page_size == 5
    
    def test_lead_list_response_pagination_properties(self):
        """Test LeadListResponse computed properties."""
        list_response = LeadListResponse(
            items=[],
            total=25,
            page=2,
            page_size=10
        )
        
        assert list_response.total_pages == 3
        assert list_response.has_next is True
        assert list_response.has_previous is True
    
    def test_lead_list_response_first_page(self):
        """Test pagination properties for first page."""
        list_response = LeadListResponse(
            items=[],
            total=25,
            page=1,
            page_size=10
        )
        
        assert list_response.has_previous is False
        assert list_response.has_next is True
    
    def test_lead_list_response_last_page(self):
        """Test pagination properties for last page."""
        list_response = LeadListResponse(
            items=[],
            total=25,
            page=3,
            page_size=10
        )
        
        assert list_response.has_previous is True
        assert list_response.has_next is False


class TestUserSchemas:
    """Tests for user-related schemas."""
    
    def test_user_create_valid(self):
        """Test creating valid UserCreate schema."""
        data = {
            "username": "attorney1",
            "email": "attorney@test.com",
            "password": "SecurePass123"
        }
        user = UserCreate(**data)
        
        assert user.username == "attorney1"
        assert user.email == "attorney@test.com"
        assert user.password == "SecurePass123"
    
    def test_user_create_email_normalization(self):
        """Test email is normalized to lowercase."""
        data = {
            "username": "attorney1",
            "email": "ATTORNEY@TEST.COM",
            "password": "SecurePass123"
        }
        user = UserCreate(**data)
        
        assert user.email == "attorney@test.com"
    
    def test_user_create_username_pattern(self):
        """Test username pattern validation."""
        data = {
            "username": "attorney_1-2",
            "email": "attorney@test.com",
            "password": "SecurePass123"
        }
        user = UserCreate(**data)
        
        assert user.username == "attorney_1-2"
    
    def test_user_create_invalid_username_pattern(self):
        """Test validation fails with invalid username characters."""
        data = {
            "username": "attorney@1",
            "email": "attorney@test.com",
            "password": "SecurePass123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_username_too_short(self):
        """Test validation fails with username too short."""
        data = {
            "username": "ab",
            "email": "attorney@test.com",
            "password": "SecurePass123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_password_too_short(self):
        """Test validation fails with password too short."""
        data = {
            "username": "attorney1",
            "email": "attorney@test.com",
            "password": "Short1"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_password_no_uppercase(self):
        """Test validation fails without uppercase letter."""
        data = {
            "username": "attorney1",
            "email": "attorney@test.com",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_password_no_lowercase(self):
        """Test validation fails without lowercase letter."""
        data = {
            "username": "attorney1",
            "email": "attorney@test.com",
            "password": "PASSWORD123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_create_password_no_digit(self):
        """Test validation fails without digit."""
        data = {
            "username": "attorney1",
            "email": "attorney@test.com",
            "password": "PasswordNoDigit"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**data)
    
    def test_user_login_valid(self):
        """Test creating valid UserLogin schema."""
        data = {
            "username": "attorney1",
            "password": "SecurePass123"
        }
        login = UserLogin(**data)
        
        assert login.username == "attorney1"
        assert login.password == "SecurePass123"
    
    def test_token_valid(self):
        """Test creating valid Token schema."""
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
            token_type="bearer"
        )
        
        assert token.access_token.startswith("eyJ")
        assert token.token_type == "bearer"
    
    def test_token_default_type(self):
        """Test Token has default token_type."""
        token = Token(access_token="test_token")
        
        assert token.token_type == "bearer"
    
    def test_token_data_valid(self):
        """Test creating valid TokenData schema."""
        import uuid
        
        data = {
            "username": "attorney1",
            "user_id": str(uuid.uuid4())
        }
        token_data = TokenData(**data)
        
        assert token_data.username == "attorney1"
        assert token_data.user_id is not None


class TestLeadStatusEnum:
    """Tests for LeadStatus enum."""
    
    def test_status_values(self):
        """Test getting all status values."""
        values = LeadStatus.values()
        
        assert "PENDING" in values
        assert "REACHED_OUT" in values
        assert len(values) == 2
    
    def test_status_is_valid(self):
        """Test validating status values."""
        assert LeadStatus.is_valid("PENDING") is True
        assert LeadStatus.is_valid("REACHED_OUT") is True
        assert LeadStatus.is_valid("INVALID") is False
    
    def test_status_from_string(self):
        """Test creating status from string."""
        status = LeadStatus.from_string("pending")
        
        assert status == LeadStatus.PENDING
    
    def test_status_from_string_case_insensitive(self):
        """Test from_string is case insensitive."""
        status1 = LeadStatus.from_string("PENDING")
        status2 = LeadStatus.from_string("pending")
        status3 = LeadStatus.from_string("Pending")
        
        assert status1 == status2 == status3 == LeadStatus.PENDING
    
    def test_status_from_string_invalid(self):
        """Test from_string raises error for invalid status."""
        with pytest.raises(ValueError) as exc_info:
            LeadStatus.from_string("INVALID")
        
        assert "Invalid status" in str(exc_info.value)
    
    def test_status_display_name(self):
        """Test display name property."""
        assert LeadStatus.PENDING.display_name == "Pending"
        assert LeadStatus.REACHED_OUT.display_name == "Reached Out"
    
    def test_status_description(self):
        """Test description property."""
        assert len(LeadStatus.PENDING.description) > 0
        assert "submitted" in LeadStatus.PENDING.description.lower()
    
    def test_status_can_transition_to(self):
        """Test status transition validation."""
        assert LeadStatus.PENDING.can_transition_to(LeadStatus.REACHED_OUT) is True
        assert LeadStatus.REACHED_OUT.can_transition_to(LeadStatus.PENDING) is True
    
    def test_status_transition_to_same(self):
        """Test cannot transition to same status."""
        assert LeadStatus.PENDING.can_transition_to(LeadStatus.PENDING) is False
