"""
Integration tests for protected lead endpoints (Attorney Dashboard).

Tests authentication, pagination, filtering, sorting, and CRUD operations.
"""

from io import BytesIO
from datetime import datetime, UTC
from unittest.mock import patch, AsyncMock, MagicMock
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.database import get_db
from app.models.lead import Lead, LeadStatus
from app.models.user import User
from app.core.security import create_access_token, hash_password


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create and drop database tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create a test user for authentication."""
    db = TestingSessionLocal()
    try:
        user = User(
            username="testattorney",
            email="attorney@example.com",
            hashed_password=hash_password("TestPassword123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def auth_token(test_user):
    """Generate a valid JWT token for testing."""
    token = create_access_token(data={"sub": test_user.username})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Generate authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_leads(setup_database):
    """Create sample leads for testing."""
    db = TestingSessionLocal()
    try:
        leads = []
        for i in range(15):
            lead = Lead(
                first_name=f"John{i}",
                last_name=f"Doe{i}",
                email=f"john{i}@example.com",
                resume_path=f"resume{i}.pdf",
                status=LeadStatus.PENDING if i < 10 else LeadStatus.REACHED_OUT
            )
            db.add(lead)
            leads.append(lead)
        
        db.commit()
        for lead in leads:
            db.refresh(lead)
        return leads
    finally:
        db.close()


class TestGetLeads:
    """Test suite for GET /api/v1/leads endpoint."""
    
    def test_get_leads_requires_authentication(self):
        """Test that endpoint requires authentication."""
        response = client.get("/api/v1/leads")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_get_leads_with_invalid_token(self):
        """Test that invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/leads", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_leads_success(self, auth_headers, sample_leads):
        """Test successful retrieval of leads."""
        response = client.get("/api/v1/leads", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 15
        assert len(data["items"]) == 10  # Default page size
        assert data["page"] == 1
    
    def test_get_leads_with_pagination(self, auth_headers, sample_leads):
        """Test pagination parameters."""
        response = client.get(
            "/api/v1/leads?page=2&page_size=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 5
        assert data["page"] == 2
        assert data["page_size"] == 5
        assert data["total"] == 15
    
    def test_get_leads_filter_by_status(self, auth_headers, sample_leads):
        """Test filtering by status."""
        response = client.get(
            f"/api/v1/leads?status=PENDING",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 10
        for item in data["items"]:
            assert item["status"] == "PENDING"
    
    def test_get_leads_sort_by_created_at_desc(self, auth_headers, sample_leads):
        """Test sorting by created_at descending."""
        response = client.get(
            "/api/v1/leads?sort_by=created_at&sort_order=desc",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that items are sorted by created_at descending
        created_dates = [item["created_at"] for item in data["items"]]
        assert created_dates == sorted(created_dates, reverse=True)
    
    def test_get_leads_invalid_sort_field(self, auth_headers):
        """Test that invalid sort field returns 400."""
        response = client.get(
            "/api/v1/leads?sort_by=invalid_field",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid sort field" in response.json()["detail"]
    
    def test_get_leads_invalid_sort_order(self, auth_headers):
        """Test that invalid sort order returns 400."""
        response = client.get(
            "/api/v1/leads?sort_order=invalid",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid sort order" in response.json()["detail"]
    
    def test_get_leads_empty_list(self, auth_headers):
        """Test getting leads when database is empty."""
        response = client.get("/api/v1/leads", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert len(data["items"]) == 0


class TestGetLeadById:
    """Test suite for GET /api/v1/leads/{lead_id} endpoint."""
    
    def test_get_lead_requires_authentication(self, sample_leads):
        """Test that endpoint requires authentication."""
        lead = sample_leads[0]
        response = client.get(f"/api/v1/leads/{lead.id}")
        
        assert response.status_code == 401
    
    def test_get_lead_success(self, auth_headers, sample_leads):
        """Test successful retrieval of a single lead."""
        lead = sample_leads[0]
        response = client.get(f"/api/v1/leads/{lead.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(lead.id)
        assert data["first_name"] == lead.first_name
        assert data["last_name"] == lead.last_name
        assert data["email"] == lead.email
        assert data["status"] == lead.status
    
    def test_get_lead_not_found(self, auth_headers):
        """Test getting non-existent lead returns 404."""
        fake_uuid = str(uuid.uuid4())
        response = client.get(f"/api/v1/leads/{fake_uuid}", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_lead_invalid_uuid(self, auth_headers):
        """Test getting lead with invalid UUID format."""
        response = client.get("/api/v1/leads/invalid-uuid", headers=auth_headers)
        
        assert response.status_code == 422


class TestUpdateLead:
    """Test suite for PATCH /api/v1/leads/{lead_id} endpoint."""
    
    def test_update_lead_requires_authentication(self, sample_leads):
        """Test that endpoint requires authentication."""
        lead = sample_leads[0]
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            json={"status": LeadStatus.REACHED_OUT}
        )
        
        assert response.status_code == 401
    
    def test_update_lead_status_success(self, auth_headers, sample_leads):
        """Test successful status update."""
        lead = sample_leads[0]
        assert lead.status == LeadStatus.PENDING
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": "REACHED_OUT"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(lead.id)
        assert data["status"] == "REACHED_OUT"
        assert data["reached_out_at"] is not None
    
    def test_update_lead_not_found(self, auth_headers):
        """Test updating non-existent lead returns 404."""
        fake_uuid = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/leads/{fake_uuid}",
            headers=auth_headers,
            json={"status": "REACHED_OUT"}
        )
        
        assert response.status_code == 404
    
    def test_update_lead_invalid_status_transition(self, auth_headers, sample_leads):
        """Test that invalid status transitions are rejected."""
        lead = sample_leads[10]  # REACHED_OUT status
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": "PENDING"}
        )
        
        assert response.status_code == 400
        assert "transition" in response.json()["detail"].lower()


class TestGetLeadResume:
    """Test suite for GET /api/v1/leads/{lead_id}/resume endpoint."""
    
    def test_get_resume_requires_authentication(self, sample_leads):
        """Test that endpoint requires authentication."""
        lead = sample_leads[0]
        response = client.get(f"/api/v1/leads/{lead.id}/resume")
        
        assert response.status_code == 401
    
    @patch('app.api.v1.endpoints.leads.LeadService')
    def test_get_resume_success(self, mock_service_class, auth_headers, sample_leads):
        """Test successful resume download."""
        lead = sample_leads[0]
        
        # Create mock instances
        mock_service = MagicMock()
        mock_file_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock get_lead to return our test lead
        mock_service.get_lead.return_value = lead
        mock_service.file_service = mock_file_service
        
        # Mock file response
        from fastapi.responses import Response
        mock_response = Response(
            content=b"PDF content",
            media_type="application/pdf"
        )
        mock_file_service.get_file_response.return_value = mock_response
        
        response = client.get(
            f"/api/v1/leads/{lead.id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        mock_file_service.get_file_response.assert_called_once_with(lead.resume_path)
    
    def test_get_resume_lead_not_found(self, auth_headers):
        """Test getting resume for non-existent lead returns 404."""
        fake_uuid = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/leads/{fake_uuid}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @patch('app.api.v1.endpoints.leads.LeadService')
    def test_get_resume_file_not_found(self, mock_service_class, auth_headers, sample_leads):
        """Test getting resume when file doesn't exist returns 404."""
        lead = sample_leads[0]
        
        # Create mock instances
        mock_service = MagicMock()
        mock_file_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock get_lead to return our test lead
        mock_service.get_lead.return_value = lead
        mock_service.file_service = mock_file_service
        
        # Mock file service to raise FileNotFoundError
        mock_file_service.get_file_response.side_effect = FileNotFoundError("File not found")
        
        response = client.get(
            f"/api/v1/leads/{lead.id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestInactiveUser:
    """Test suite for inactive user scenarios."""
    
    def test_inactive_user_cannot_access_protected_endpoints(self):
        """Test that inactive users cannot access protected endpoints."""
        # Create inactive user
        db = TestingSessionLocal()
        try:
            user = User(
                username="inactiveattorney",
                email="inactive@example.com",
                hashed_password=hash_password("TestPassword123"),
                is_active=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        finally:
            db.close()
        
        # Generate token for inactive user
        token = create_access_token(data={"sub": "inactiveattorney"})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/leads", headers=headers)
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
