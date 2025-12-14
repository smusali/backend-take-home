"""
Protected API endpoints for lead management (Attorney Dashboard).

Requires authentication for all endpoints.
Provides CRUD operations for leads with pagination, filtering, and sorting.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.lead import LeadResponse, LeadListResponse, LeadUpdate
from app.schemas.enums import LeadStatus
from app.services.lead_service import LeadService


router = APIRouter()


@router.get(
    "",
    response_model=LeadListResponse,
    summary="Get all leads",
    description="Retrieve a paginated list of leads with optional filtering and sorting"
)
async def get_leads(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status: Optional[LeadStatus] = Query(None, description="Filter by lead status"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, updated_at)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> LeadListResponse:
    """
    Get paginated list of leads with filtering and sorting.
    
    Requires authentication. Returns leads with pagination metadata.
    """
    try:
        lead_service = LeadService(db)
        
        # Validate sort_by field
        valid_sort_fields = ["created_at", "updated_at"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        # Validate sort_order
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid sort order. Must be 'asc' or 'desc'"
            )
        
        # Get paginated leads - note the service returns a dict, not tuple
        result = lead_service.get_leads_paginated(
            page=page,
            page_size=page_size,
            status_filter=status
        )
        
        leads = result["leads"]
        total = result["total"]
        
        # Apply sorting (service doesn't handle this yet)
        if sort_by == "created_at":
            leads = sorted(leads, key=lambda x: x.created_at, reverse=(sort_order == "desc"))
        elif sort_by == "updated_at":
            leads = sorted(leads, key=lambda x: x.updated_at, reverse=(sort_order == "desc"))
        
        return LeadListResponse(
            items=[LeadResponse.model_validate(lead) for lead in leads],
            total=total,
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leads: {str(e)}"
        )


@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Get lead by ID",
    description="Retrieve detailed information for a specific lead"
)
async def get_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> LeadResponse:
    """
    Get a single lead by ID.
    
    Requires authentication. Returns full lead details.
    """
    try:
        lead_service = LeadService(db)
        lead = lead_service.get_lead(lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        return LeadResponse.model_validate(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lead: {str(e)}"
        )


@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Update lead status",
    description="Update the status of a lead (e.g., mark as REACHED_OUT)"
)
async def update_lead(
    lead_id: UUID,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> LeadResponse:
    """
    Update a lead's status.
    
    Requires authentication. Validates status transitions and updates timestamp.
    """
    try:
        lead_service = LeadService(db)
        
        # Check if lead exists
        existing_lead = lead_service.get_lead(lead_id)
        if not existing_lead:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        # Update lead status
        updated_lead = lead_service.update_lead_status(
            lead_id=lead_id,
            new_status=lead_update.status
        )
        
        return LeadResponse.model_validate(updated_lead)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead: {str(e)}"
        )


@router.get(
    "/{lead_id}/resume",
    response_class=FileResponse,
    summary="Download lead resume",
    description="Download the resume file for a specific lead"
)
async def get_lead_resume(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> FileResponse:
    """
    Download a lead's resume file.
    
    Requires authentication. Returns the resume file with appropriate headers.
    """
    try:
        lead_service = LeadService(db)
        
        # Check if lead exists
        lead = lead_service.get_lead(lead_id)
        if not lead:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        # Get resume file
        file_response = lead_service.file_service.get_file_response(
            lead.resume_path
        )
        
        # Set download filename to include lead name
        filename = f"{lead.first_name}_{lead.last_name}_resume.{lead.resume_path.split('.')[-1]}"
        file_response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        
        return file_response
        
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Resume file not found for lead {lead_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume: {str(e)}"
        )


__all__ = ["router"]
