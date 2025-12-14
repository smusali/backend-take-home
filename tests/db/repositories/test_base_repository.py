"""
Unit tests for BaseRepository.

Tests generic CRUD operations provided by the base repository class.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.repositories.base import BaseRepository
from app.models.lead import Lead, LeadStatus
from app.db.database import get_engine, get_session_factory
from app.db.base import Base


class TestBaseRepository:
    """Test suite for BaseRepository generic CRUD operations."""
    
    def setup_method(self):
        """Setup test database and session before each test."""
        self.engine = get_engine()
        Base.metadata.create_all(bind=self.engine)
        
        session_factory = get_session_factory()
        self.db: Session = session_factory()
        self.repository = BaseRepository(Lead, self.db)
    
    def teardown_method(self):
        """Cleanup test database after each test."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
    
    def test_create_record(self):
        """Test creating a new record."""
        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "resume_path": "/uploads/resume.pdf",
            "status": LeadStatus.PENDING
        }
        
        lead = self.repository.create(lead_data)
        
        assert lead.id is not None
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john@example.com"
        assert lead.status == LeadStatus.PENDING
        assert lead.created_at is not None
    
    def test_get_record_by_id(self):
        """Test retrieving a record by ID."""
        lead_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "resume_path": "/uploads/resume2.pdf",
        }
        
        created_lead = self.repository.create(lead_data)
        retrieved_lead = self.repository.get(created_lead.id)
        
        assert retrieved_lead is not None
        assert retrieved_lead.id == created_lead.id
        assert retrieved_lead.email == "jane@example.com"
    
    def test_get_nonexistent_record_returns_none(self):
        """Test that getting a nonexistent record returns None."""
        random_id = uuid.uuid4()
        lead = self.repository.get(random_id)
        
        assert lead is None
    
    def test_get_multi_records(self):
        """Test retrieving multiple records."""
        for i in range(5):
            self.repository.create({
                "first_name": f"User{i}",
                "last_name": f"Test{i}",
                "email": f"user{i}@example.com",
                "resume_path": f"/uploads/resume{i}.pdf",
            })
        
        leads = self.repository.get_multi(skip=0, limit=3)
        
        assert len(leads) == 3
    
    def test_get_multi_with_skip(self):
        """Test pagination with skip parameter."""
        for i in range(5):
            self.repository.create({
                "first_name": f"User{i}",
                "last_name": f"Test{i}",
                "email": f"user{i}@example.com",
                "resume_path": f"/uploads/resume{i}.pdf",
            })
        
        leads = self.repository.get_multi(skip=2, limit=10)
        
        assert len(leads) == 3
    
    def test_update_record(self):
        """Test updating a record."""
        lead_data = {
            "first_name": "Original",
            "last_name": "Name",
            "email": "original@example.com",
            "resume_path": "/uploads/resume.pdf",
        }
        
        lead = self.repository.create(lead_data)
        updated_lead = self.repository.update(
            id=lead.id,
            obj_in={"first_name": "Updated"}
        )
        
        assert updated_lead is not None
        assert updated_lead.first_name == "Updated"
        assert updated_lead.last_name == "Name"
        assert updated_lead.email == "original@example.com"
    
    def test_update_nonexistent_record_returns_none(self):
        """Test that updating a nonexistent record returns None."""
        random_id = uuid.uuid4()
        result = self.repository.update(
            id=random_id,
            obj_in={"first_name": "Updated"}
        )
        
        assert result is None
    
    def test_delete_record(self):
        """Test deleting a record."""
        lead_data = {
            "first_name": "Delete",
            "last_name": "Me",
            "email": "delete@example.com",
            "resume_path": "/uploads/resume.pdf",
        }
        
        lead = self.repository.create(lead_data)
        deleted = self.repository.delete(lead.id)
        
        assert deleted is True
        
        # Verify record is gone
        retrieved = self.repository.get(lead.id)
        assert retrieved is None
    
    def test_delete_nonexistent_record_returns_false(self):
        """Test that deleting a nonexistent record returns False."""
        random_id = uuid.uuid4()
        deleted = self.repository.delete(random_id)
        
        assert deleted is False
    
    def test_count_records(self):
        """Test counting records."""
        for i in range(7):
            self.repository.create({
                "first_name": f"User{i}",
                "last_name": f"Test{i}",
                "email": f"user{i}@example.com",
                "resume_path": f"/uploads/resume{i}.pdf",
            })
        
        count = self.repository.count()
        
        assert count == 7
    
    def test_count_empty_table(self):
        """Test counting records in an empty table."""
        count = self.repository.count()
        
        assert count == 0
