"""
Integration tests for public API endpoints.

Tests the complete lead submission workflow including validation,
file uploads, database operations, and email notifications.
"""

from io import BytesIO


class TestCreateLead:
    """Tests for public lead creation endpoint."""
    
    def test_create_lead_with_valid_data(self, client, temp_upload_dir):
        """Test creating a lead with valid data."""
        resume_content = b"PDF file content here"
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(resume_content), "application/pdf")
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["status"] == "PENDING"
        assert "id" in data
        assert "resume_path" in data
        assert "created_at" in data
    
    def test_create_lead_with_doc_file(self, client, temp_upload_dir):
        """Test creating lead with DOC file."""
        resume_content = b"DOC file content"
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com"
            },
            files={
                "resume": ("resume.doc", BytesIO(resume_content), "application/msword")
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "jane.smith@example.com"
    
    def test_create_lead_with_docx_file(self, client, temp_upload_dir):
        """Test creating lead with DOCX file."""
        resume_content = b"DOCX file content"
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Bob",
                "last_name": "Wilson",
                "email": "bob.wilson@example.com"
            },
            files={
                "resume": ("resume.docx", BytesIO(resume_content), 
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            }
        )
        
        assert response.status_code == 201
    
    def test_create_lead_duplicate_email(self, client, create_lead, temp_upload_dir):
        """Test creating lead with duplicate email fails."""
        create_lead(email="duplicate@example.com")
        
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "duplicate@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already exists" in data["error"]["message"].lower()
    
    def test_create_lead_missing_first_name(self, client, temp_upload_dir):
        """Test validation fails with missing first name."""
        response = client.post(
            "/api/v1/leads",
            data={
                "last_name": "Doe",
                "email": "john@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 422
    
    def test_create_lead_missing_last_name(self, client, temp_upload_dir):
        """Test validation fails with missing last name."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "email": "john@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 422
    
    def test_create_lead_missing_email(self, client, temp_upload_dir):
        """Test validation fails with missing email."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 422
    
    def test_create_lead_missing_resume(self, client, temp_upload_dir):
        """Test validation fails with missing resume file."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            }
        )
        
        assert response.status_code == 422
    
    def test_create_lead_invalid_email_format(self, client, temp_upload_dir):
        """Test validation fails with invalid email format."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "invalid-email"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code in [422, 500]
    
    def test_create_lead_invalid_file_type(self, client, temp_upload_dir):
        """Test validation fails with invalid file type."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            },
            files={
                "resume": ("resume.txt", BytesIO(b"text content"), "text/plain")
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "not allowed" in data["error"]["message"].lower()
    
    def test_create_lead_empty_first_name(self, client, temp_upload_dir):
        """Test validation fails with empty first name."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "",
                "last_name": "Doe",
                "email": "john@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 422
    
    def test_create_lead_name_sanitization(self, client, temp_upload_dir):
        """Test that names are properly sanitized."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "  John  ",
                "last_name": "  Doe  ",
                "email": "john@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
    
    def test_create_lead_email_normalization(self, client, temp_upload_dir):
        """Test that email is normalized to lowercase."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "JOHN@EXAMPLE.COM"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "john@example.com"
    
    def test_create_lead_xss_prevention(self, client, temp_upload_dir):
        """Test that XSS attempts are sanitized."""
        response = client.post(
            "/api/v1/leads",
            data={
                "first_name": "John<script>alert('xss')</script>",
                "last_name": "Doe",
                "email": "john@example.com"
            },
            files={
                "resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "<script>" not in data["first_name"]
        assert "</script>" not in data["first_name"]
        assert "<" not in data["first_name"]
        assert ">" not in data["first_name"]
