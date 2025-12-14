"""
End-to-end tests for complete lead workflows.

Tests complete user journeys from lead submission through management,
including file uploads, email notifications, and status transitions.
"""

from io import BytesIO
from pathlib import Path

from app.schemas.enums import LeadStatus


class TestLeadSubmissionWorkflow:
    """Test complete lead submission workflow from prospect perspective."""
    
    def test_complete_lead_submission_flow(self, client, temp_upload_dir):
        """Test full lead submission flow including validation and notifications."""
        resume_content = b"PDF resume content for John Doe"
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            },
            files={
                "resume": ("john_doe_resume.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        
        assert response.status_code == 201
        lead_data = response.json()
        
        assert lead_data["first_name"] == "John"
        assert lead_data["last_name"] == "Doe"
        assert lead_data["email"] == "john.doe@example.com"
        assert lead_data["status"] == LeadStatus.PENDING.value
        assert "id" in lead_data
        assert "resume_path" in lead_data
        assert "created_at" in lead_data
        
        resume_path = Path(temp_upload_dir) / lead_data["resume_path"].split("/")[-1]
        assert resume_path.exists()
        
        return lead_data
    
    def test_lead_submission_with_different_file_types(self, client, temp_upload_dir):
        """Test lead submission supports multiple resume file formats."""
        file_types = [
            ("resume.pdf", "application/pdf"),
            ("resume.doc", "application/msword"),
            ("resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        ]
        
        for idx, (filename, content_type) in enumerate(file_types):
            response = client.post(
                "/api/v1/leads",
                data={
                    "first_name": f"Candidate{idx}",
                    "last_name": "Test",
                    "email": f"candidate{idx}@example.com"
                },
                files={
                    "resume": (filename, BytesIO(b"file content"), content_type)
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == LeadStatus.PENDING.value
    
    def test_duplicate_email_rejection(self, client, create_lead, temp_upload_dir):
        """Test that duplicate email submissions are properly rejected."""
        create_lead(email="existing@example.com")
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                "last_name": "Duplicate",
                "email": "existing@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "error" in error_data
        assert "already exists" in error_data["error"]["message"].lower()
    
    def test_invalid_file_type_rejection(self, client, temp_upload_dir):
        """Test that invalid file types are rejected."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            },
            files={
                "resume": ("malicious.exe", BytesIO(b"malware"), "application/x-msdownload")
            }
        )
        
        assert response.status_code == 400


class TestLeadManagementWorkflow:
    """Test complete lead management workflow from attorney perspective."""
    
    def test_complete_lead_management_flow(self, client, create_lead, test_user, auth_headers):
        """Test full lead management workflow including listing, viewing, and updating."""
        lead1 = create_lead(first_name="Alice", last_name="Johnson", email="alice@example.com")        
        list_response = client.get(
            "/api/v1/leads",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total"] >= 1
        assert len(list_data["items"]) >= 1
        
        detail_response = client.get(
            f"/api/v1/leads/{lead1.id}",
            headers=auth_headers
        )
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["email"] == "alice@example.com"
        assert detail_data["status"] == LeadStatus.PENDING.value
        
        update_response = client.patch(
            f"/api/v1/leads/{lead1.id}",
            headers=auth_headers,
            json={"status": LeadStatus.REACHED_OUT.value}
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["status"] == LeadStatus.REACHED_OUT.value
        
        verify_response = client.get(
            f"/api/v1/leads/{lead1.id}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == LeadStatus.REACHED_OUT.value
    
    def test_lead_filtering_and_pagination(self, client, create_lead, auth_headers):
        """Test filtering leads by status and pagination."""
        for i in range(5):
            create_lead(email=f"pending{i}@example.com", status=LeadStatus.PENDING)
        
        for i in range(3):
            create_lead(email=f"reached{i}@example.com", status=LeadStatus.REACHED_OUT)
        
        pending_response = client.get(
            f"/api/v1/leads?status={LeadStatus.PENDING.value}",
            headers=auth_headers
        )
        assert pending_response.status_code == 200
        pending_data = pending_response.json()
        assert pending_data["total"] >= 5
        
        reached_response = client.get(
            f"/api/v1/leads?status={LeadStatus.REACHED_OUT.value}",
            headers=auth_headers
        )
        assert reached_response.status_code == 200
        reached_data = reached_response.json()
        assert reached_data["total"] >= 3
        
        page1_response = client.get(
            "/api/v1/leads?page=1&page_size=3",
            headers=auth_headers
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["items"]) <= 3
        assert page1_data["page"] == 1
        
        page2_response = client.get(
            "/api/v1/leads?page=2&page_size=3",
            headers=auth_headers
        )
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert page2_data["page"] == 2
    
    def test_unauthorized_access_denied(self, client, create_lead):
        """Test that unauthenticated requests are properly denied."""
        lead = create_lead()
        
        endpoints = [
            ("/api/v1/leads", "get"),
            (f"/api/v1/leads/{lead.id}", "get"),
            (f"/api/v1/leads/{lead.id}", "patch"),
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            elif method == "patch":
                response = client.patch(endpoint, json={"status": "REACHED_OUT"})
            
            assert response.status_code == 401


class TestStatusTransitionWorkflow:
    """Test lead status transition workflows."""
    
    def test_valid_status_transitions(self, client, create_lead, auth_headers):
        """Test valid status transitions from PENDING to REACHED_OUT."""
        lead = create_lead(status=LeadStatus.PENDING)
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": LeadStatus.REACHED_OUT.value}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == LeadStatus.REACHED_OUT.value
    
    def test_invalid_status_transitions(self, client, create_lead, auth_headers):
        """Test that invalid status values are rejected."""
        lead = create_lead(status=LeadStatus.PENDING)
        
        response = client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": "INVALID_STATUS"}
        )
        
        assert response.status_code == 422
    
    def test_status_transition_persistence(self, client, create_lead, auth_headers):
        """Test that status updates persist correctly."""
        lead = create_lead(status=LeadStatus.PENDING)
        
        client.patch(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers,
            json={"status": LeadStatus.REACHED_OUT.value}
        )
        
        verify_response = client.get(
            f"/api/v1/leads/{lead.id}",
            headers=auth_headers
        )
        
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == LeadStatus.REACHED_OUT.value


class TestFileStorageWorkflow:
    """Test file storage workflows."""
    
    def test_resume_upload_and_retrieval(self, client, create_lead, auth_headers, temp_upload_dir):
        """Test complete file upload and retrieval workflow."""
        resume_content = b"Test resume content for file storage"
        
        create_response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "FileTest",
                "last_name": "User",
                "email": "filetest@example.com"
            },
            files={
                "resume": ("test_resume.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        
        assert create_response.status_code == 201
        lead_data = create_response.json()
        lead_id = lead_data["id"]
        
        download_response = client.get(
            f"/api/v1/leads/{lead_id}/resume",
            headers=auth_headers
        )
        
        assert download_response.status_code == 200
        assert download_response.content == resume_content
    
    def test_resume_file_persistence(self, client, create_lead, temp_upload_dir):
        """Test that uploaded files persist on filesystem."""
        resume_content = b"Persistent file content"
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Persistent",
                "last_name": "File",
                "email": "persistent@example.com"
            },
            files={
                "resume": ("persistent.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        
        assert response.status_code == 201
        lead_data = response.json()
        
        resume_filename = lead_data["resume_path"].split("/")[-1]
        file_path = Path(temp_upload_dir) / resume_filename
        
        assert file_path.exists()
        assert file_path.read_bytes() == resume_content
    
    def test_unique_filename_generation(self, client, temp_upload_dir):
        """Test that uploaded files get unique filenames to prevent conflicts."""
        resume_content = b"Content"
        
        response1 = client.post(
            "/api/v1/leads",
            data={
                "first_name": "User1",
                "last_name": "Test",
                "email": "user1@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        
        response2 = client.post(
            "/api/v1/leads",
            data={
                "first_name": "User2",
                "last_name": "Test",
                "email": "user2@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        path1 = response1.json()["resume_path"]
        path2 = response2.json()["resume_path"]
        
        assert path1 != path2


class TestAuthenticationWorkflow:
    """Test authentication and authorization workflows."""
    
    def test_user_registration_and_login_flow(self, client):
        """Test complete user registration and login workflow."""
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newattorney",
                "email": "attorney@example.com",
                "password": "SecurePass123"
            }
        )
        
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["username"] == "newattorney"
        assert user_data["email"] == "attorney@example.com"
        assert "id" in user_data
        
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "newattorney",
                "password": "SecurePass123"
            }
        )
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        access_token = token_data["access_token"]
        profile_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["username"] == "newattorney"
        assert profile_data["email"] == "attorney@example.com"
    
    def test_protected_endpoints_require_authentication(self, client, create_lead):
        """Test that all protected endpoints require valid authentication."""
        lead = create_lead()
        
        protected_endpoints = [
            ("/api/v1/leads", "GET"),
            (f"/api/v1/leads/{lead.id}", "GET"),
            (f"/api/v1/leads/{lead.id}", "PATCH"),
            (f"/api/v1/leads/{lead.id}/resume", "GET"),
            ("/api/v1/auth/me", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PATCH":
                response = client.patch(endpoint, json={"status": "REACHED_OUT"})
            
            assert response.status_code == 401
    
    def test_invalid_credentials_rejected(self, client, create_user):
        """Test that invalid credentials are properly rejected."""
        create_user(username="validuser", password="CorrectPass123")
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "validuser",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == 401


class TestErrorScenarios:
    """Test error handling in various scenarios."""
    
    def test_missing_required_fields(self, client, temp_upload_dir):
        """Test validation of required fields."""
        missing_fields = [
            {"last_name": "Doe", "email": "test@example.com"},
            {"first_name": "John", "email": "test@example.com"},
            {"first_name": "John", "last_name": "Doe"},
        ]
        
        for data in missing_fields:
            response = client.post(
                "/api/v1/leads",
                data=data,
                files={
                    "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
                }
            )
            assert response.status_code == 422
    
    def test_invalid_email_format(self, client, temp_upload_dir):
        """Test email format validation."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "not-an-email"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code in [422, 500]
    
    def test_nonexistent_lead_access(self, client, auth_headers):
        """Test accessing non-existent lead returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/leads/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_malformed_uuid_handling(self, client, auth_headers):
        """Test handling of malformed UUIDs."""
        response = client.get(
            "/api/v1/leads/not-a-valid-uuid",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_large_file_rejection(self, client, temp_upload_dir):
        """Test that excessively large files are rejected."""
        large_content = b"x" * (6 * 1024 * 1024)
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            },
            files={
                "resume": ("large.pdf", BytesIO(large_content), "application/pdf")
            }
        )
        
        assert response.status_code == 400


class TestCompleteUserJourney:
    """Test complete end-to-end user journeys."""
    
    def test_prospect_to_reached_out_journey(self, client, test_user, auth_headers, temp_upload_dir):
        """
        Test complete journey from prospect submission to attorney reaching out.
        
        This simulates:
        1. Prospect submits lead with resume
        2. Attorney logs in
        3. Attorney views lead list
        4. Attorney views lead details
        5. Attorney downloads resume
        6. Attorney updates status to REACHED_OUT
        """
        resume_content = b"Complete journey test resume"
        
        submit_response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Journey",
                "last_name": "Test",
                "email": "journey@example.com"
            },
            files={
                "resume": ("journey_resume.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        assert submit_response.status_code == 201
        lead_data = submit_response.json()
        lead_id = lead_data["id"]
        
        list_response = client.get("/api/v1/leads", headers=auth_headers)
        assert list_response.status_code == 200
        leads = list_response.json()["items"]
        assert any(lead["id"] == lead_id for lead in leads)
        
        detail_response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["email"] == "journey@example.com"
        assert detail["status"] == LeadStatus.PENDING.value
        
        resume_response = client.get(
            f"/api/v1/leads/{lead_id}/resume",
            headers=auth_headers
        )
        assert resume_response.status_code == 200
        assert resume_response.content == resume_content
        
        update_response = client.patch(
            f"/api/v1/leads/{lead_id}",
            headers=auth_headers,
            json={"status": LeadStatus.REACHED_OUT.value}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == LeadStatus.REACHED_OUT.value
        
        final_check = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert final_check.status_code == 200
        assert final_check.json()["status"] == LeadStatus.REACHED_OUT.value
    
    def test_multiple_attorneys_workflow(self, client, temp_upload_dir):
        """Test workflow with multiple attorneys managing different leads."""
        attorney1_register = client.post(
            "/api/v1/auth/register",
            json={
                "username": "attorney1",
                "email": "attorney1@law.com",
                "password": "Pass123Word"
            }
        )
        assert attorney1_register.status_code == 201
        
        attorney2_register = client.post(
            "/api/v1/auth/register",
            json={
                "username": "attorney2",
                "email": "attorney2@law.com",
                "password": "Pass123Word"
            }
        )
        assert attorney2_register.status_code == 201
        
        attorney1_login = client.post(
            "/api/v1/auth/login",
            data={"username": "attorney1", "password": "Pass123Word"}
        )
        token1 = attorney1_login.json()["access_token"]
        
        attorney2_login = client.post(
            "/api/v1/auth/login",
            data={"username": "attorney2", "password": "Pass123Word"}
        )
        token2 = attorney2_login.json()["access_token"]
        
        lead_response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Shared",
                "last_name": "Lead",
                "email": "shared@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        lead_id = lead_response.json()["id"]
        
        attorney1_view = client.get(
            f"/api/v1/leads/{lead_id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert attorney1_view.status_code == 200
        
        attorney2_view = client.get(
            f"/api/v1/leads/{lead_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert attorney2_view.status_code == 200
        
        attorney1_update = client.patch(
            f"/api/v1/leads/{lead_id}",
            headers={"Authorization": f"Bearer {token1}"},
            json={"status": LeadStatus.REACHED_OUT.value}
        )
        assert attorney1_update.status_code == 200
        
        attorney2_verify = client.get(
            f"/api/v1/leads/{lead_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert attorney2_verify.status_code == 200
        assert attorney2_verify.json()["status"] == LeadStatus.REACHED_OUT.value
