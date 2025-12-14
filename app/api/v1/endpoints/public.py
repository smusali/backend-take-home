"""
Public API endpoints for lead submission.

These endpoints are accessible without authentication and handle
prospect lead submissions with resume uploads.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.lead import LeadCreate, LeadResponse
from app.services.lead_service import LeadService


router = APIRouter()


@router.post(
    "/leads",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new lead",
    description="Public endpoint for prospects to submit their information with a resume"
)
async def create_lead(
    first_name: str = Form(..., min_length=1, max_length=100, description="Prospect's first name"),
    last_name: str = Form(..., min_length=1, max_length=100, description="Prospect's last name"),
    email: str = Form(..., description="Prospect's email address"),
    resume: UploadFile = File(..., description="Resume file (PDF, DOC, or DOCX)"),
    db: Session = Depends(get_db)
) -> LeadResponse:
    """
    Create a new lead submission.
    
    This endpoint allows prospects to submit their information along with a resume.
    Upon successful submission:
    - Resume is stored securely
    - Lead is created in the database
    - Confirmation email is sent to the prospect
    - Notification email is sent to the attorney
    
    Args:
        first_name: Prospect's first name
        last_name: Prospect's last name
        email: Prospect's email address
        resume: Resume file (PDF, DOC, or DOCX, max 5MB)
        db: Database session (injected)
    
    Returns:
        LeadResponse: Created lead with ID and all fields
    
    Raises:
        400: Validation error (duplicate email, invalid file, etc.)
        500: Server error (file storage, database, or email failure)
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/leads" \\
          -F "first_name=John" \\
          -F "last_name=Doe" \\
          -F "email=john.doe@example.com" \\
          -F "resume=@resume.pdf"
        ```
    """
    try:
        # Create lead data from form fields
        lead_data = LeadCreate(
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        
        # Initialize lead service
        lead_service = LeadService(db)
        
        # Create lead with full workflow
        lead = await lead_service.create_lead(lead_data, resume)
        
        return lead
    
    except HTTPException:
        # Re-raise HTTP exceptions (from validation, duplicate check, etc.)
        raise
    
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )


__all__ = ["router"]
