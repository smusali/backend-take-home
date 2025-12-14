"""
Repository package for data access layer.

Exports repository classes for clean imports throughout the application.
"""

from app.db.repositories.base import BaseRepository
from app.db.repositories.lead_repository import LeadRepository
from app.db.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "LeadRepository",
    "UserRepository",
]
