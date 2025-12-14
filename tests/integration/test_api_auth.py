"""
Integration tests for authentication API endpoints.

Tests user registration, login, token validation, and profile retrieval.
"""


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_with_valid_data(self, client):
        """Test registering a new user with valid data."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newattorney",
                "email": "new@attorney.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == "newattorney"
        assert data["email"] == "new@attorney.com"
        assert "id" in data
        assert "hashed_password" not in data
        assert data["is_active"] is True
    
    def test_register_duplicate_username(self, client, create_user):
        """Test that duplicate username is rejected."""
        create_user(username="existing")
        
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "existing",
                "email": "different@email.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already registered" in data["error"]["message"].lower()
    
    def test_register_duplicate_email(self, client, create_user):
        """Test that duplicate email is rejected."""
        create_user(email="existing@email.com")
        
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "existing@email.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already registered" in data["error"]["message"].lower()
    
    def test_register_invalid_username_pattern(self, client):
        """Test that invalid username pattern is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "user@invalid",
                "email": "user@email.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_username_too_short(self, client):
        """Test that too short username is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",
                "email": "user@email.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_weak_password(self, client):
        """Test that weak password is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "user@email.com",
                "password": "weak"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_password_no_uppercase(self, client):
        """Test that password without uppercase is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "user@email.com",
                "password": "lowercase123"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_password_no_digit(self, client):
        """Test that password without digit is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "user@email.com",
                "password": "NoDigitsHere"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test that invalid email format is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_missing_fields(self, client):
        """Test that missing required fields are rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "newuser"}
        )
        
        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_with_valid_credentials(self, client, create_user):
        """Test logging in with valid credentials."""
        create_user(username="attorney1", password="TestPass123")
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "attorney1",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    def test_login_wrong_password(self, client, create_user):
        """Test login fails with wrong password."""
        create_user(username="attorney1", password="TestPass123")
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "attorney1",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login fails with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client, create_user):
        """Test login fails for inactive user."""
        create_user(username="inactive", password="TestPass123", is_active=False)
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "inactive" in data["error"]["message"].lower()
    
    def test_login_missing_username(self, client):
        """Test login fails with missing username."""
        response = client.post(
            "/api/v1/auth/login",
            data={"password": "password"}
        )
        
        assert response.status_code == 422
    
    def test_login_missing_password(self, client):
        """Test login fails with missing password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "user"}
        )
        
        assert response.status_code == 422
    
    def test_login_empty_credentials(self, client):
        """Test login fails with empty credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "", "password": ""}
        )
        
        assert response.status_code == 401


class TestTokenValidation:
    """Tests for JWT token validation."""
    
    def test_valid_token_grants_access(self, client, auth_headers):
        """Test that valid token grants access to protected endpoints."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_invalid_token_rejected(self, client):
        """Test that invalid token is rejected."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/auth/me", headers=invalid_headers)
        
        assert response.status_code == 401
    
    def test_expired_token_rejected(self, client, create_user):
        """Test that expired token is rejected."""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        user = create_user()
        expired_token = create_access_token(
            {"sub": user.username},
            expires_delta=timedelta(seconds=-1)
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_malformed_token_rejected(self, client):
        """Test that malformed token is rejected."""
        malformed_headers = {"Authorization": "Bearer malformed.token.here"}
        
        response = client.get("/api/v1/auth/me", headers=malformed_headers)
        
        assert response.status_code == 401
    
    def test_missing_bearer_prefix(self, client, auth_token):
        """Test that token without Bearer prefix is rejected."""
        invalid_headers = {"Authorization": auth_token}
        
        response = client.get("/api/v1/auth/me", headers=invalid_headers)
        
        assert response.status_code == 401
    
    def test_token_for_nonexistent_user(self, client, create_user, db_session):
        """Test that token for deleted user is rejected."""
        from app.core.security import create_access_token
        
        user = create_user()
        token = create_access_token({"sub": user.username})
        
        db_session.delete(user)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for current user profile endpoint."""
    
    def test_get_current_user_profile(self, client, auth_headers, test_user):
        """Test getting current user's profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data
    
    def test_get_current_user_requires_auth(self, client):
        """Test that getting profile requires authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_with_inactive_account(self, client, create_user):
        """Test that inactive user cannot access profile."""
        from app.core.security import create_access_token
        
        user = create_user(is_active=False)
        token = create_access_token({"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 400


class TestUnauthorizedAccess:
    """Tests for unauthorized access attempts."""
    
    def test_protected_endpoints_without_auth(self, client):
        """Test that all protected endpoints reject unauthenticated requests."""
        protected_endpoints = [
            "/api/v1/leads/",
            "/api/v1/auth/me"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
    
    def test_authentication_error_format(self, client):
        """Test that authentication errors have correct format."""
        response = client.get("/api/v1/leads/")
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "message" in data["error"]
    
    def test_www_authenticate_header(self, client):
        """Test that 401 responses include WWW-Authenticate header."""
        response = client.get("/api/v1/leads/")
        
        assert response.status_code == 401
        assert "www-authenticate" in response.headers
