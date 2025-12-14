"""
Lead model for prospect information.

Represents a lead submission from a prospect including their contact
information, resume, and current status in the outreach process.
"""

import enum
import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import String, Enum, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LeadStatus(str, enum.Enum):
    """
    Lead status enumeration.
    
    Represents the current state of a lead in the outreach process.
    """
    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"


class Lead(Base):
    """
    Lead model representing a prospect submission.
    
    Attributes:
        id: Unique identifier for the lead
        first_name: Prospect's first name
        last_name: Prospect's last name
        email: Prospect's email address (unique)
        resume_path: Path to the stored resume file
        status: Current lead status (PENDING or REACHED_OUT)
        created_at: Timestamp when the lead was created
        updated_at: Timestamp when the lead was last updated
        reached_out_at: Timestamp when attorney marked as reached out (nullable)
    """
    
    __tablename__ = "leads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    resume_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, native_enum=False, length=20),
        nullable=False,
        default=LeadStatus.PENDING,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
    
    reached_out_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    __table_args__ = (
        Index("idx_lead_status_created", "status", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, email={self.email}, status={self.status})>"
