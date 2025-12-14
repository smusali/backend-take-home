"""
Unit tests for Lead model.

Tests Lead model creation, field validation, and enum behavior.
"""

import uuid
from datetime import datetime, UTC

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.lead import Lead, LeadStatus


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestLeadModel:
    """Test suite for Lead model."""
    
    def test_create_lead_with_required_fields(self, session):
        """Test creating a lead with all required fields."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            resume_path="/path/to/resume.pdf"
        )
        
        session.add(lead)
        session.commit()
        
        assert lead.id is not None
        assert isinstance(lead.id, uuid.UUID)
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john.doe@example.com"
        assert lead.resume_path == "/path/to/resume.pdf"
        assert lead.status == LeadStatus.PENDING
        assert lead.created_at is not None
        assert lead.updated_at is not None
        assert lead.reached_out_at is None
    
    def test_lead_default_status_is_pending(self, session):
        """Test that default status is PENDING."""
        lead = Lead(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            resume_path="/path/to/resume.pdf"
        )
        
        session.add(lead)
        session.commit()
        
        assert lead.status == LeadStatus.PENDING
    
    def test_lead_status_can_be_set_to_reached_out(self, session):
        """Test that status can be set to REACHED_OUT."""
        lead = Lead(
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            resume_path="/path/to/resume.pdf",
            status=LeadStatus.REACHED_OUT,
            reached_out_at=datetime.now(UTC)
        )
        
        session.add(lead)
        session.commit()
        
        assert lead.status == LeadStatus.REACHED_OUT
        assert lead.reached_out_at is not None
    
    def test_lead_email_must_be_unique(self, session):
        """Test that email uniqueness constraint is enforced."""
        lead1 = Lead(
            first_name="Alice",
            last_name="Williams",
            email="same@example.com",
            resume_path="/path/to/resume1.pdf"
        )
        
        lead2 = Lead(
            first_name="Charlie",
            last_name="Brown",
            email="same@example.com",
            resume_path="/path/to/resume2.pdf"
        )
        
        session.add(lead1)
        session.commit()
        
        session.add(lead2)
        with pytest.raises(Exception):
            session.commit()
    
    def test_lead_updated_at_changes_on_update(self, session):
        """Test that updated_at timestamp changes when lead is updated."""
        lead = Lead(
            first_name="David",
            last_name="Miller",
            email="david.miller@example.com",
            resume_path="/path/to/resume.pdf"
        )
        
        session.add(lead)
        session.commit()
        
        original_updated_at = lead.updated_at
        
        lead.status = LeadStatus.REACHED_OUT
        lead.reached_out_at = datetime.now(UTC)
        session.commit()
        
        assert lead.updated_at >= original_updated_at
    
    def test_lead_repr(self, session):
        """Test Lead __repr__ method."""
        lead = Lead(
            first_name="Emma",
            last_name="Davis",
            email="emma.davis@example.com",
            resume_path="/path/to/resume.pdf"
        )
        
        session.add(lead)
        session.commit()
        
        repr_str = repr(lead)
        assert "Lead" in repr_str
        assert str(lead.id) in repr_str
        assert "emma.davis@example.com" in repr_str
        assert "PENDING" in repr_str
    
    def test_lead_status_enum_values(self):
        """Test LeadStatus enum has correct values."""
        assert LeadStatus.PENDING.value == "PENDING"
        assert LeadStatus.REACHED_OUT.value == "REACHED_OUT"
        assert len(LeadStatus) == 2
    
    def test_lead_accepts_long_names(self, session):
        """Test that lead accepts names up to 100 characters."""
        long_name = "A" * 100
        lead = Lead(
            first_name=long_name,
            last_name=long_name,
            email="long.name@example.com",
            resume_path="/path/to/resume.pdf"
        )
        
        session.add(lead)
        session.commit()
        
        assert lead.first_name == long_name
        assert lead.last_name == long_name
    
    def test_lead_accepts_long_email(self, session):
        """Test that lead accepts emails up to 255 characters."""
        long_email = "a" * 240 + "@example.com"
        lead = Lead(
            first_name="Test",
            last_name="User",
            email=long_email,
            resume_path="/path/to/resume.pdf"
        )
        
        session.add(lead)
        session.commit()
        
        assert lead.email == long_email
    
    def test_lead_accepts_long_resume_path(self, session):
        """Test that lead accepts resume paths up to 500 characters."""
        long_path = "/path/" + "a" * 490 + ".pdf"
        lead = Lead(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            resume_path=long_path
        )
        
        session.add(lead)
        session.commit()
        
        assert lead.resume_path == long_path
