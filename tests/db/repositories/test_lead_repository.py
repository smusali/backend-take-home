"""
Unit tests for LeadRepository.

Tests lead-specific database operations including querying by email,
status, pagination, and status updates.
"""

import uuid
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.db.repositories.lead_repository import LeadRepository
from app.models.lead import Lead, LeadStatus
from app.db.database import get_engine, get_session_factory
from app.db.base import Base


class TestLeadRepository:
    """Test suite for LeadRepository operations."""
    
    def setup_method(self):
        """Setup test database and session before each test."""
        self.engine = get_engine()
        Base.metadata.create_all(bind=self.engine)
        
        session_factory = get_session_factory()
        self.db: Session = session_factory()
        self.repository = LeadRepository(Lead, self.db)
    
    def teardown_method(self):
        """Cleanup test database after each test."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
    
    def test_get_by_email_found(self):
        """Test retrieving a lead by email."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "resume_path": "/uploads/resume.pdf",
        }
        
        self.repository.create(lead_data)
        lead = self.repository.get_by_email("john@example.com")
        
        assert lead is not None
        assert lead.email == "john@example.com"
        assert lead.first_name == "John"
    
    def test_get_by_email_not_found(self):
        """Test that getting a nonexistent email returns None."""
        lead = self.repository.get_by_email("nonexistent@example.com")
        
        assert lead is None
    
    def test_get_by_status(self):
        """Test retrieving leads by status."""
        # Create pending leads
        for i in range(3):
            self.repository.create({
                "first_name": f"Pending{i}",
                "last_name": "User",
                "email": f"pending{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.PENDING
            })
        
        # Create reached out leads
        for i in range(2):
            self.repository.create({
                "first_name": f"Reached{i}",
                "last_name": "User",
                "email": f"reached{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.REACHED_OUT
            })
        
        pending_leads = self.repository.get_by_status(LeadStatus.PENDING)
        reached_leads = self.repository.get_by_status(LeadStatus.REACHED_OUT)
        
        assert len(pending_leads) == 3
        assert len(reached_leads) == 2
        assert all(lead.status == LeadStatus.PENDING for lead in pending_leads)
        assert all(lead.status == LeadStatus.REACHED_OUT for lead in reached_leads)
    
    def test_get_by_status_with_pagination(self):
        """Test retrieving leads by status with pagination."""
        for i in range(10):
            self.repository.create({
                "first_name": f"User{i}",
                "last_name": "Test",
                "email": f"user{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.PENDING
            })
        
        first_page = self.repository.get_by_status(
            LeadStatus.PENDING,
            skip=0,
            limit=3
        )
        second_page = self.repository.get_by_status(
            LeadStatus.PENDING,
            skip=3,
            limit=3
        )
        
        assert len(first_page) == 3
        assert len(second_page) == 3
        # Verify different records
        assert first_page[0].id != second_page[0].id
    
    def test_update_status_to_reached_out(self):
        """Test updating lead status to REACHED_OUT sets timestamp."""
        lead_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "resume_path": "/uploads/resume.pdf",
        }
        
        lead = self.repository.create(lead_data)
        assert lead.status == LeadStatus.PENDING
        assert lead.reached_out_at is None
        
        updated_lead = self.repository.update_status(lead.id, LeadStatus.REACHED_OUT)
        
        assert updated_lead is not None
        assert updated_lead.status == LeadStatus.REACHED_OUT
        assert updated_lead.reached_out_at is not None
        assert isinstance(updated_lead.reached_out_at, datetime)
    
    def test_update_status_to_reached_out_preserves_timestamp(self):
        """Test that updating to REACHED_OUT again doesn't change timestamp."""
        lead_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.REACHED_OUT,
            "reached_out_at": datetime.now(UTC)
        }
        
        lead = self.repository.create(lead_data)
        original_timestamp = lead.reached_out_at
        
        updated_lead = self.repository.update_status(lead.id, LeadStatus.REACHED_OUT)
        
        assert updated_lead.reached_out_at == original_timestamp
    
    def test_update_status_nonexistent_lead(self):
        """Test updating status of nonexistent lead returns None."""
        random_id = uuid.uuid4()
        result = self.repository.update_status(random_id, LeadStatus.REACHED_OUT)
        
        assert result is None
    
    def test_get_leads_paginated_no_filters(self):
        """Test paginated retrieval without filters."""
        for i in range(15):
            self.repository.create({
                "first_name": f"User{i}",
                "last_name": "Test",
                "email": f"user{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
            })
        
        leads, total = self.repository.get_leads_paginated(skip=0, limit=10)
        
        assert len(leads) == 10
        assert total == 15
    
    def test_get_leads_paginated_with_status_filter(self):
        """Test paginated retrieval with status filter."""
        for i in range(5):
            self.repository.create({
                "first_name": f"Pending{i}",
                "last_name": "User",
                "email": f"pending{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.PENDING
            })
        
        for i in range(3):
            self.repository.create({
                "first_name": f"Reached{i}",
                "last_name": "User",
                "email": f"reached{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.REACHED_OUT
            })
        
        leads, total = self.repository.get_leads_paginated(
            status=LeadStatus.PENDING,
            skip=0,
            limit=10
        )
        
        assert len(leads) == 5
        assert total == 5
        assert all(lead.status == LeadStatus.PENDING for lead in leads)
    
    def test_get_leads_paginated_with_search(self):
        """Test paginated retrieval with search filter."""
        self.repository.create({
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "resume_path": "/uploads/resume.pdf",
        })
        self.repository.create({
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com",
            "resume_path": "/uploads/resume.pdf",
        })
        self.repository.create({
            "first_name": "Charlie",
            "last_name": "Smith",
            "email": "charlie@example.com",
            "resume_path": "/uploads/resume.pdf",
        })
        
        # Search by last name
        leads, total = self.repository.get_leads_paginated(search="Smith")
        
        assert len(leads) == 2
        assert total == 2
        assert all("Smith" in lead.last_name for lead in leads)
    
    def test_get_leads_paginated_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        self.repository.create({
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "resume_path": "/uploads/resume.pdf",
        })
        
        leads, total = self.repository.get_leads_paginated(search="smith")
        
        assert len(leads) == 1
        assert total == 1
    
    def test_get_recent_leads(self):
        """Test retrieving recent leads."""
        for i in range(15):
            self.repository.create({
                "first_name": f"User{i}",
                "last_name": "Test",
                "email": f"user{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
            })
        
        recent_leads = self.repository.get_recent_leads(limit=5)
        
        assert len(recent_leads) == 5
        # Verify ordered by created_at descending
        for i in range(len(recent_leads) - 1):
            assert recent_leads[i].created_at >= recent_leads[i + 1].created_at
    
    def test_count_by_status(self):
        """Test counting leads by status."""
        for i in range(7):
            self.repository.create({
                "first_name": f"Pending{i}",
                "last_name": "User",
                "email": f"pending{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.PENDING
            })
        
        for i in range(3):
            self.repository.create({
                "first_name": f"Reached{i}",
                "last_name": "User",
                "email": f"reached{i}@example.com",
                "resume_path": "/uploads/resume.pdf",
                "status": LeadStatus.REACHED_OUT
            })
        
        pending_count = self.repository.count_by_status(LeadStatus.PENDING)
        reached_count = self.repository.count_by_status(LeadStatus.REACHED_OUT)
        
        assert pending_count == 7
        assert reached_count == 3
