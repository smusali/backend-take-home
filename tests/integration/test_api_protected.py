"""
Integration tests for protected API endpoints.

Tests attorney dashboard endpoints including lead listing, details,
updates, resume downloads, pagination, filtering, and authorization.
"""

import uuid

from app.schemas.enums import LeadStatus


class TestGetLeads:
    """Tests for lead listing endpoint."""
    
    def test_get_leads_requires_authentication(self, client):
        """Test that getting leads requires authentication."""
        response = client.get("/api/v1/leads/")
        
        assert response.status_code == 401
    
    def test_get_leads_with_authentication(self, client, auth_headers, sample_leads):
        """Test getting leads with valid authentication."""
        response = client.get("/api/v1/leads/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
    
    def test_get_leads_default_pagination(self, client, auth_headers, sample_leads):
        """Test default pagination parameters."""
        response = client.get("/api/v1/leads/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10
    
    def test_get_leads_custom_page_size(self, client, auth_headers, sample_leads):
        """Test custom page size."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"page_size": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5
    
    def test_get_leads_pagination(self, client, auth_headers, sample_leads):
        """Test pagination across multiple pages."""
        response_page1 = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"page": 1, "page_size": 5}
        )
        response_page2 = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"page": 2, "page_size": 5}
        )
        
        assert response_page1.status_code == 200
        assert response_page2.status_code == 200
        
        data1 = response_page1.json()
        data2 = response_page2.json()
        
        ids_page1 = {item["id"] for item in data1["items"]}
        ids_page2 = {item["id"] for item in data2["items"]}
        
        assert ids_page1.isdisjoint(ids_page2)
    
    def test_get_leads_filter_by_status_pending(self, client, auth_headers, sample_leads):
        """Test filtering by PENDING status."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"status": "PENDING"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for item in data["items"]:
            assert item["status"] == "PENDING"
    
    def test_get_leads_filter_by_status_reached_out(self, client, auth_headers, sample_leads):
        """Test filtering by REACHED_OUT status."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"status": "REACHED_OUT"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for item in data["items"]:
            assert item["status"] == "REACHED_OUT"
    
    def test_get_leads_sort_by_created_desc(self, client, auth_headers, sample_leads):
        """Test sorting by created_at descending."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"sort_by": "created_at", "sort_order": "desc"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["items"]) > 1:
            for i in range(len(data["items"]) - 1):
                assert data["items"][i]["created_at"] >= data["items"][i + 1]["created_at"]
    
    def test_get_leads_sort_by_created_asc(self, client, auth_headers, sample_leads):
        """Test sorting by created_at ascending."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"sort_by": "created_at", "sort_order": "asc"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["items"]) > 1:
            for i in range(len(data["items"]) - 1):
                assert data["items"][i]["created_at"] <= data["items"][i + 1]["created_at"]
    
    def test_get_leads_invalid_sort_field(self, client, auth_headers):
        """Test invalid sort field returns error."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"sort_by": "invalid_field"}
        )
        
        assert response.status_code == 400
    
    def test_get_leads_invalid_sort_order(self, client, auth_headers):
        """Test invalid sort order returns error."""
        response = client.get(
            "/api/v1/leads/",
            headers=auth_headers,
            params={"sort_order": "invalid"}
        )
        
        assert response.status_code == 400
    
    def test_get_leads_empty_list(self, client, auth_headers):
        """Test getting leads when none exist."""
        response = client.get("/api/v1/leads/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["items"] == []


class TestGetLead:
    """Tests for single lead retrieval endpoint."""
    
    def test_get_lead_requires_authentication(self, client, create_lead):
        """Test that getting a lead requires authentication."""
        lead = create_lead()
        
        response = client.get(f"/api/v1/leads/{lead.id}")
        
        assert response.status_code == 401
    
    def test_get_lead_with_authentication(self, client, auth_headers, create_lead):
        """Test getting a lead with valid authentication."""
        lead = create_lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        response = client.get(f"/api/v1/leads/{lead.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(lead.id)
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john@example.com"
    
    def test_get_lead_not_found(self, client, auth_headers):
        """Test getting non-existent lead returns 404."""
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/leads/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_lead_invalid_uuid(self, client, auth_headers):
        """Test getting lead with invalid UUID format."""
        response = client.get("/api/v1/leads/invalid-uuid", headers=auth_headers)
        
        assert response.status_code == 422


class TestUpdateLead:
    """Tests for lead update endpoint."""
    
    def test_update_lead_requires_authentication(self, client, create_lead):
        """Test that updating a lead requires authentication."""
        lead = create_lead(status=LeadStatus.PENDING)
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            json={"status": "REACHED_OUT"}
        )
        
        assert response.status_code == 401
    
    def test_update_lead_status_to_reached_out(self, client, auth_headers, create_lead):
        """Test updating lead status from PENDING to REACHED_OUT."""
        lead = create_lead(status=LeadStatus.PENDING)
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": "REACHED_OUT"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "REACHED_OUT"
        assert data["reached_out_at"] is not None
    
    def test_update_lead_status_invalid_transition(self, client, auth_headers, create_lead):
        """Test invalid status transition is rejected."""
        lead = create_lead(status=LeadStatus.REACHED_OUT)
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": "PENDING"}
        )
        
        assert response.status_code == 400
    
    def test_update_lead_not_found(self, client, auth_headers):
        """Test updating non-existent lead returns 404."""
        fake_id = str(uuid.uuid4())
        
        response = client.patch(
            f"/api/v1/leads/{fake_id}",
            headers=auth_headers,
            json={"status": "REACHED_OUT"}
        )
        
        assert response.status_code == 404
    
    def test_update_lead_invalid_status(self, client, auth_headers, create_lead):
        """Test updating with invalid status value."""
        lead = create_lead()
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": "INVALID_STATUS"}
        )
        
        assert response.status_code == 422


class TestGetLeadResume:
    """Tests for resume download endpoint."""
    
    def test_get_resume_requires_authentication(self, client, create_lead, temp_upload_dir):
        """Test that downloading resume requires authentication."""
        lead = create_lead()
        
        response = client.get(f"/api/v1/leads/{lead.id}/resume")
        
        assert response.status_code == 401
    
    def test_get_resume_with_authentication(self, client, auth_headers, create_lead, temp_upload_dir):
        """Test downloading resume with valid authentication."""
        resume_file = temp_upload_dir / "test_resume.pdf"
        resume_file.write_bytes(b"PDF content here")
        
        lead = create_lead(resume_path="test_resume.pdf")
        
        response = client.get(
            f"/api/v1/leads/{lead.id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")
    
    def test_get_resume_not_found(self, client, auth_headers):
        """Test downloading resume for non-existent lead."""
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/leads/{fake_id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_resume_file_not_found(self, client, auth_headers, create_lead, temp_upload_dir):
        """Test downloading when resume file doesn't exist."""
        lead = create_lead(resume_path="nonexistent.pdf")
        
        response = client.get(
            f"/api/v1/leads/{lead.id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_resume_filename_format(self, client, auth_headers, create_lead, temp_upload_dir):
        """Test that downloaded filename includes lead name."""
        resume_file = temp_upload_dir / "test_resume.pdf"
        resume_file.write_bytes(b"PDF content")
        
        lead = create_lead(
            first_name="John",
            last_name="Doe",
            resume_path="test_resume.pdf"
        )
        
        response = client.get(
            f"/api/v1/leads/{lead.id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        content_disposition = response.headers.get("content-disposition", "")
        assert "John_Doe_resume.pdf" in content_disposition


class TestAuthorizationAndPermissions:
    """Tests for authorization and permission checks."""
    
    def test_invalid_token_rejected(self, client):
        """Test that invalid JWT token is rejected."""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = client.get("/api/v1/leads/", headers=invalid_headers)
        
        assert response.status_code == 401
    
    def test_malformed_auth_header(self, client):
        """Test that malformed auth header is rejected."""
        malformed_headers = {"Authorization": "InvalidFormat token"}
        
        response = client.get("/api/v1/leads/", headers=malformed_headers)
        
        assert response.status_code == 401
    
    def test_missing_auth_header(self, client, create_lead):
        """Test that missing auth header returns 401."""
        lead = create_lead()
        
        endpoints = [
            "/api/v1/leads/",
            f"/api/v1/leads/{lead.id}",
            f"/api/v1/leads/{lead.id}/resume"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_inactive_user_rejected(self, client, create_user):
        """Test that inactive user cannot access protected endpoints."""
        from app.core.security import create_access_token
        
        user = create_user(is_active=False)
        token = create_access_token({"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/leads/", headers=headers)
        
        assert response.status_code == 400
