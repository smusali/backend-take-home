"""
Pytest configuration and fixtures.

Provides common fixtures and configuration for all tests.
"""

import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """
    Set minimal environment variables for test session.
    
    This prevents Settings validation errors during test collection
    when no .env file exists.
    """
    os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-characters-long")
    os.environ.setdefault("SMTP_HOST", "smtp.test.com")
    os.environ.setdefault("SMTP_USERNAME", "test@test.com")
    os.environ.setdefault("SMTP_PASSWORD", "test-password")
    os.environ.setdefault("SMTP_FROM_EMAIL", "noreply@test.com")
    os.environ.setdefault("ATTORNEY_EMAIL", "attorney@test.com")
