"""
Database base configuration.

Provides the declarative base for all SQLAlchemy models.
Imports all models to ensure they are registered with Alembic.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Import all models here to ensure they are registered with Base.metadata
# This is required for Alembic to detect models for migrations
from app.models.lead import Lead  # noqa: F401, E402
from app.models.user import User  # noqa: F401, E402
