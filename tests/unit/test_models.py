"""
Unit tests for database models.

Tests model creation, validation, relationships, and database constraints.
"""

import pytest
from datetime import datetime, UTC
import uuid

from app.models.lead import Lead, LeadStatus
from app.models.user import User


class TestLeadModel:
    """Tests for Lead model."""
    
    def test_create_lead(self, db_session):
        """Test creating a lead with valid data."""
        lead = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resumes/test.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        db_session.add(lead)
        db_session.commit()
        
        assert lead.id is not None
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john@example.com"
        assert lead.status == LeadStatus.PENDING
        assert lead.reached_out_at is None
    
    def test_lead_default_status(self, db_session):
        """Test that lead status defaults to PENDING."""
        lead = Lead(
            id=uuid.uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            resume_path="resumes/jane.pdf"
        )
        
        db_session.add(lead)
        db_session.commit()
        
        assert lead.status == LeadStatus.PENDING
    
    def test_lead_unique_email_constraint(self, db_session):
        """Test that email must be unique."""
        lead1 = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="duplicate@example.com",
            resume_path="resumes/john.pdf"
        )
        db_session.add(lead1)
        db_session.commit()
        
        lead2 = Lead(
            id=uuid.uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="duplicate@example.com",
            resume_path="resumes/jane.pdf"
        )
        db_session.add(lead2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_lead_repr(self, db_session):
        """Test lead string representation."""
        lead = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resumes/test.pdf",
            status=LeadStatus.PENDING
        )
        
        db_session.add(lead)
        db_session.commit()
        
        repr_str = repr(lead)
        assert "Lead" in repr_str
        assert str(lead.id) in repr_str
        assert lead.email in repr_str
        assert "PENDING" in repr_str
    
    def test_lead_status_transition(self, db_session):
        """Test updating lead status."""
        lead = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resumes/test.pdf",
            status=LeadStatus.PENDING
        )
        db_session.add(lead)
        db_session.commit()
        
        lead.status = LeadStatus.REACHED_OUT
        lead.reached_out_at = datetime.now(UTC)
        db_session.commit()
        
        assert lead.status == LeadStatus.REACHED_OUT
        assert lead.reached_out_at is not None
    
    def test_lead_timestamps(self, db_session):
        """Test that timestamps are set correctly."""
        lead = Lead(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resumes/test.pdf"
        )
        db_session.add(lead)
        db_session.commit()
        
        assert lead.created_at is not None
        assert lead.updated_at is not None
        assert isinstance(lead.created_at, datetime)
        assert isinstance(lead.updated_at, datetime)


class TestUserModel:
    """Tests for User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user with valid data."""
        user = User(
            id=uuid.uuid4(),
            username="attorney1",
            email="attorney@test.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.now(UTC)
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "attorney1"
        assert user.email == "attorney@test.com"
        assert user.is_active is True
    
    def test_user_default_active_status(self, db_session):
        """Test that user is active by default."""
        user = User(
            id=uuid.uuid4(),
            username="attorney2",
            email="attorney2@test.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.is_active is True
    
    def test_user_unique_username_constraint(self, db_session):
        """Test that username must be unique."""
        user1 = User(
            id=uuid.uuid4(),
            username="duplicate",
            email="user1@test.com",
            hashed_password="$2b$12$hashedpassword"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            id=uuid.uuid4(),
            username="duplicate",
            email="user2@test.com",
            hashed_password="$2b$12$hashedpassword"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_user_unique_email_constraint(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            id=uuid.uuid4(),
            username="user1",
            email="duplicate@test.com",
            hashed_password="$2b$12$hashedpassword"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            id=uuid.uuid4(),
            username="user2",
            email="duplicate@test.com",
            hashed_password="$2b$12$hashedpassword"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_user_repr(self, db_session):
        """Test user string representation."""
        user = User(
            id=uuid.uuid4(),
            username="attorney1",
            email="attorney@test.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert user.username in repr_str
        assert "True" in repr_str
    
    def test_user_inactive_status(self, db_session):
        """Test creating inactive user."""
        user = User(
            id=uuid.uuid4(),
            username="inactive_user",
            email="inactive@test.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=False
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.is_active is False
    
    def test_user_timestamp(self, db_session):
        """Test that created_at timestamp is set."""
        user = User(
            id=uuid.uuid4(),
            username="attorney1",
            email="attorney@test.com",
            hashed_password="$2b$12$hashedpassword"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
