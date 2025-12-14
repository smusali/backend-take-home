"""
Database models.

Exports all models for easy import and Alembic discovery.
"""

from app.db.base import Base
from app.models.lead import Lead, LeadStatus
from app.models.user import User

__all__ = ["Base", "Lead", "LeadStatus", "User"]
