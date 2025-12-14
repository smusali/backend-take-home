"""
Lead request and response schemas.

Defines Pydantic models for lead creation, updates, and API responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.enums import LeadStatus


class LeadCreate(BaseModel):
    """
    Schema for creating a new lead.
    
    Used when a prospect submits their information through the public form.
    Note: resume is handled separately as an UploadFile in the endpoint.
    """
    
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Prospect's first name",
        examples=["John"]
    )
    
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Prospect's last name",
        examples=["Doe"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Prospect's email address",
        examples=["john.doe@example.com"]
    )


class LeadUpdate(BaseModel):
    """
    Schema for updating an existing lead.
    
    Used by attorneys to update lead status after reaching out.
    """
    
    status: LeadStatus = Field(
        ...,
        description="New status for the lead",
        examples=[LeadStatus.REACHED_OUT]
    )


class LeadResponse(BaseModel):
    """
    Schema for lead data in API responses.
    
    Includes all lead information from the database.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique lead identifier")
    first_name: str = Field(..., description="Prospect's first name")
    last_name: str = Field(..., description="Prospect's last name")
    email: EmailStr = Field(..., description="Prospect's email address")
    resume_path: str = Field(..., description="Path to stored resume file")
    status: LeadStatus = Field(..., description="Current lead status")
    created_at: datetime = Field(..., description="When the lead was created")
    updated_at: datetime = Field(..., description="Last update timestamp")
    reached_out_at: Optional[datetime] = Field(
        None,
        description="When attorney marked as reached out"
    )
    
    @property
    def full_name(self) -> str:
        """Computed property for display purposes."""
        return f"{self.first_name} {self.last_name}"


class LeadListResponse(BaseModel):
    """
    Schema for paginated list of leads.
    
    Includes pagination metadata for UI rendering.
    """
    
    items: list[LeadResponse] = Field(
        ...,
        description="List of lead records for current page"
    )
    
    total: int = Field(
        ...,
        ge=0,
        description="Total number of leads matching the query"
    )
    
    page: int = Field(
        ...,
        ge=1,
        description="Current page number (1-indexed)"
    )
    
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page"
    )
    
    @property
    def total_pages(self) -> int:
        """Computed property for total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1
