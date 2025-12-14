"""
Test fixtures and configuration for pytest.

Provides database fixtures, test client, authentication helpers,
sample data factories, and service mocks for testing.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
import uuid

import pytest
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.db.base import Base
from app.db.database import get_db
from app.models.user import User
from app.models.lead import Lead, LeadStatus
from app.core.security import hash_password, create_access_token
from app.core.config import get_settings


fake = Faker()


@pytest.fixture(scope="session")
def test_settings():
    """
    Override application settings for testing.
    
    Returns settings with test database and mock email configuration.
    """
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"
    os.environ["SMTP_HOST"] = "localhost"
    os.environ["SMTP_USERNAME"] = "test@example.com"
    os.environ["SMTP_PASSWORD"] = "test-password"
    os.environ["SMTP_FROM_EMAIL"] = "noreply@example.com"
    os.environ["ATTORNEY_EMAIL"] = "attorney@example.com"
    os.environ["DEBUG"] = "True"
    os.environ["ENVIRONMENT"] = "test"
    
    return get_settings()


@pytest.fixture(scope="function")
def db_engine(test_settings):
    """
    Create a fresh test database engine for each test.
    
    Uses SQLite in-memory database with StaticPool to maintain
    connection across threads.
    """
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a database session for testing.
    
    Automatically rolls back after each test to ensure isolation.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session, mock_smtp):
    """
    Create a FastAPI test client with database session override.
    
    Returns a synchronous test client for API testing.
    Automatically mocks SMTP to prevent actual email sending.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing async endpoints.
    
    Useful for testing async operations and concurrent requests.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Generate sample user data for testing."""
    return {
        "username": fake.user_name(),
        "email": fake.email(),
        "password": "SecurePassword123!",
    }


@pytest.fixture
def create_user(db_session):
    """
    Factory fixture to create users in the test database.
    
    Usage:
        user = create_user(username="attorney1", password="password")
    """
    def _create_user(
        username: str = None,
        email: str = None,
        password: str = "TestPassword123!",
        is_active: bool = True
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            username=username or fake.user_name(),
            email=email or fake.email(),
            hashed_password=hash_password(password),
            is_active=is_active,
            created_at=datetime.now(UTC)
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def test_user(create_user):
    """Create a default test user for authentication tests."""
    return create_user(
        username="test_attorney",
        email="attorney@test.com",
        password="TestPassword123!"
    )


@pytest.fixture
def auth_token(test_user):
    """
    Generate authentication token for test user.
    
    Returns a valid JWT token for making authenticated requests.
    """
    return create_access_token({"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token):
    """
    Generate authentication headers for API requests.
    
    Usage:
        response = client.get("/api/v1/leads", headers=auth_headers)
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_lead_data():
    """Generate sample lead data for testing."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
    }


@pytest.fixture
def create_lead(db_session):
    """
    Factory fixture to create leads in the test database.
    
    Usage:
        lead = create_lead(email="test@example.com", status=LeadStatus.PENDING)
    """
    def _create_lead(
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        resume_path: str = None,
        status: LeadStatus = LeadStatus.PENDING,
        reached_out_at: datetime = None
    ) -> Lead:
        lead = Lead(
            id=uuid.uuid4(),
            first_name=first_name or fake.first_name(),
            last_name=last_name or fake.last_name(),
            email=email or fake.email(),
            resume_path=resume_path or f"test_resumes/{uuid.uuid4()}.pdf",
            status=status,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            reached_out_at=reached_out_at
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)
        return lead
    
    return _create_lead


@pytest.fixture
def sample_leads(create_lead):
    """
    Create multiple sample leads for list/pagination testing.
    
    Returns a list of 10 leads with varied statuses.
    """
    leads = []
    for i in range(10):
        status = LeadStatus.PENDING if i % 3 != 0 else LeadStatus.REACHED_OUT
        reached_out_at = datetime.now(UTC) if status == LeadStatus.REACHED_OUT else None
        lead = create_lead(
            email=f"test{i}@example.com",
            status=status,
            reached_out_at=reached_out_at
        )
        leads.append(lead)
    return leads


@pytest.fixture(scope="function")
def temp_upload_dir(monkeypatch):
    """
    Create a temporary directory for file upload testing.
    
    Automatically cleaned up after test.
    Patches the environment variable so all Settings instances
    created during the test use this directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_path = Path(tmpdir) / "uploads" / "resumes"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Patch the environment variable so get_settings() returns correct path
        monkeypatch.setenv("UPLOAD_DIR", str(upload_path))
        
        yield upload_path


@pytest.fixture
def mock_resume_file():
    """
    Create a mock resume file for upload testing.
    
    Returns a file-like object that simulates a PDF upload.
    """
    def _create_mock_file(
        filename: str = "resume.pdf",
        content: bytes = b"Mock PDF content",
        content_type: str = "application/pdf"
    ):
        from io import BytesIO
        from fastapi import UploadFile
        
        file_obj = BytesIO(content)
        file_obj.name = filename
        
        return UploadFile(
            filename=filename,
            file=file_obj,
            content_type=content_type
        )
    
    return _create_mock_file


@pytest.fixture
def mock_email_service():
    """
    Mock EmailService for testing without sending actual emails.
    
    Tracks calls to email methods for verification.
    """
    with patch("app.services.email_service.EmailService") as mock_service:
        instance = mock_service.return_value
        instance.send_prospect_confirmation = AsyncMock(return_value=True)
        instance.send_attorney_notification = AsyncMock(return_value=True)
        instance.send_custom_email = AsyncMock(return_value=True)
        
        yield instance


@pytest.fixture
def mock_file_service():
    """
    Mock FileService for testing without actual file I/O.
    
    Simulates file operations and tracks method calls.
    """
    with patch("app.services.file_service.FileService") as mock_service:
        instance = mock_service.return_value
        instance.save_file = AsyncMock(return_value="mock_resume.pdf")
        instance.get_file_path = MagicMock(return_value=Path("/tmp/mock_resume.pdf"))
        instance.delete_file = MagicMock(return_value=True)
        instance.file_exists = MagicMock(return_value=True)
        instance.get_file_size = MagicMock(return_value=12345)
        
        yield instance


@pytest.fixture
def mock_smtp():
    """
    Mock SMTP connection for email testing.
    
    Prevents actual SMTP connections during tests.
    """
    with patch("aiosmtplib.SMTP") as mock:
        smtp_instance = AsyncMock()
        smtp_instance.connect = AsyncMock()
        smtp_instance.starttls = AsyncMock()
        smtp_instance.login = AsyncMock()
        smtp_instance.send_message = AsyncMock()
        smtp_instance.quit = AsyncMock()
        
        mock.return_value = smtp_instance
        yield smtp_instance


@pytest.fixture(autouse=True)
def reset_db_state(db_session):
    """
    Reset database state between tests.
    
    Ensures clean slate for each test by clearing all data.
    Handles sessions that may have been rolled back due to constraint violations.
    """
    yield
    
    # Check if session is in a valid state
    if db_session.is_active:
        try:
            # If there's a pending transaction that failed, roll it back first
            if db_session.in_transaction():
                db_session.rollback()
            
            # Now clean up test data
            db_session.query(Lead).delete()
            db_session.query(User).delete()
            db_session.commit()
        except Exception:
            # If cleanup fails for any reason, ensure we roll back
            db_session.rollback()


@pytest.fixture
def freeze_time():
    """
    Helper to freeze time for testing time-dependent functionality.
    
    Usage:
        with freeze_time(datetime(2025, 1, 1, 12, 0, 0)) as mock_dt:
            # time is frozen to the specified datetime
            pass
    """
    def _freeze(frozen_datetime: datetime):
        return patch("app.models.lead.datetime", return_value=frozen_datetime)
    
    return _freeze


@pytest.fixture
def assert_email_sent(mock_email_service):
    """
    Helper to assert that emails were sent correctly.
    
    Usage:
        assert_email_sent(
            mock_email_service.send_prospect_confirmation,
            email="test@example.com",
            times=1
        )
    """
    def _assert(method, times=1, **kwargs):
        assert method.call_count == times
        if kwargs:
            method.assert_called_with(**kwargs)
    
    return _assert


@pytest.fixture
def assert_file_saved(mock_file_service):
    """
    Helper to assert that files were saved correctly.
    
    Usage:
        assert_file_saved(times=1)
    """
    def _assert(times=1):
        assert mock_file_service.save_file.call_count == times
    
    return _assert


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"
