"""
Lead service for orchestrating lead management workflows.

Handles lead creation, retrieval, updates, and business logic validation
with integration of file storage and email notification services.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.repositories.lead_repository import LeadRepository
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.schemas.validators import validate_status_transition
from app.services.file_service import FileService
from app.services.email_service import EmailService


class LeadService:
    """
    Service for managing lead lifecycle and business logic.
    
    Orchestrates file storage, database operations, and email notifications
    for complete lead management workflow.
    """
    
    def __init__(self, db: Session):
        """
        Initialize lead service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.lead_repo = LeadRepository(db)
        self.file_service = FileService()
        self.email_service = EmailService()
        self.settings = get_settings()
    
    async def create_lead(
        self,
        lead_data: LeadCreate,
        resume_file: UploadFile
    ) -> LeadResponse:
        """
        Create a new lead with complete workflow.
        
        Workflow:
        1. Validate lead data (done by Pydantic)
        2. Check for duplicate email
        3. Save resume file
        4. Create lead in database
        5. Send confirmation email to prospect
        6. Send notification email to attorney
        7. Handle rollback on any failure
        
        Args:
            lead_data: Validated lead creation data
            resume_file: Uploaded resume file
            
        Returns:
            Created lead response with all fields
            
        Raises:
            HTTPException(400): Duplicate email or validation error
            HTTPException(500): File storage, database, or email error
            
        Example:
            >>> lead_data = LeadCreate(
            ...     first_name="John",
            ...     last_name="Doe",
            ...     email="john@example.com"
            ... )
            >>> resume = UploadFile(...)
            >>> lead = await service.create_lead(lead_data, resume)
        """
        resume_path = None
        lead = None
        
        try:
            # Check for duplicate email
            existing_lead = self.lead_repo.get_by_email(lead_data.email)
            if existing_lead:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A lead with email {lead_data.email} already exists"
                )
            
            # Save resume file
            resume_path = await self.file_service.save_file(resume_file)
            
            # Create lead in database
            lead_dict = lead_data.model_dump()
            lead_dict["resume_path"] = resume_path
            lead = self.lead_repo.create(lead_dict)
            self.db.commit()
            self.db.refresh(lead)
            
            # Send confirmation email to prospect
            prospect_name = f"{lead.first_name} {lead.last_name}"
            await self.email_service.send_prospect_confirmation(
                prospect_email=lead.email,
                prospect_name=prospect_name,
                lead_id=str(lead.id)
            )
            
            # Send notification email to attorney
            await self.email_service.send_attorney_notification(
                lead_id=str(lead.id),
                prospect_name=prospect_name,
                prospect_email=lead.email,
                resume_filename=resume_path
            )
            
            return LeadResponse.model_validate(lead)
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            self._rollback_lead_creation(resume_path, lead)
            raise
            
        except Exception as e:
            # Handle unexpected errors
            self._rollback_lead_creation(resume_path, lead)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create lead: {str(e)}"
            )
    
    def _rollback_lead_creation(
        self,
        resume_path: Optional[str],
        lead: Optional[Lead]
    ) -> None:
        """
        Rollback lead creation on failure.
        
        Removes uploaded file and rolls back database transaction.
        
        Args:
            resume_path: Path to uploaded resume file (if exists)
            lead: Created lead object (if exists)
        """
        # Rollback database changes
        self.db.rollback()
        
        # Delete uploaded file if it exists
        if resume_path:
            try:
                self.file_service.delete_file(resume_path)
            except Exception:
                # Log error but don't fail rollback
                pass
    
    def get_lead(self, lead_id: UUID) -> LeadResponse:
        """
        Get a single lead by ID.
        
        Args:
            lead_id: UUID of the lead
            
        Returns:
            Lead response with all fields
            
        Raises:
            HTTPException(404): Lead not found
            
        Example:
            >>> lead = service.get_lead(UUID("a1b2c3d4-..."))
        """
        lead = self.lead_repo.get(lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        return LeadResponse.model_validate(lead)
    
    def get_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[LeadStatus] = None
    ) -> List[LeadResponse]:
        """
        Get all leads with optional filtering and pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            status_filter: Optional status filter
            
        Returns:
            List of lead responses
            
        Example:
            >>> # Get first 20 pending leads
            >>> leads = service.get_leads(
            ...     skip=0,
            ...     limit=20,
            ...     status_filter=LeadStatus.PENDING
            ... )
        """
        if status_filter:
            leads = self.lead_repo.get_by_status(
                status=status_filter,
                skip=skip,
                limit=limit
            )
        else:
            leads = self.lead_repo.get_multi(skip=skip, limit=limit)
        
        return [LeadResponse.model_validate(lead) for lead in leads]
    
    def get_leads_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[LeadStatus] = None
    ) -> dict:
        """
        Get leads with pagination metadata.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status filter
            
        Returns:
            Dictionary with leads, total count, and pagination metadata
            
        Example:
            >>> result = service.get_leads_paginated(page=1, page_size=20)
            >>> print(result["total"])
            >>> print(result["leads"])
            >>> print(result["page"], result["page_size"])
        """
        # Calculate offset
        skip = (page - 1) * page_size
        
        # Get leads
        leads = self.get_leads(
            skip=skip,
            limit=page_size,
            status_filter=status_filter
        )
        
        # Get total count
        if status_filter:
            total = self.lead_repo.count_by_status(status_filter)
        else:
            total = self.lead_repo.count()
        
        # Calculate pagination metadata
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return {
            "leads": leads,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous
        }
    
    def update_lead_status(
        self,
        lead_id: UUID,
        new_status: LeadStatus,
        validate_transition: bool = True
    ) -> LeadResponse:
        """
        Update lead status with validation.
        
        Args:
            lead_id: UUID of the lead
            new_status: New status to set
            validate_transition: Whether to validate status transition
            
        Returns:
            Updated lead response
            
        Raises:
            HTTPException(404): Lead not found
            HTTPException(400): Invalid status transition
            
        Example:
            >>> lead = service.update_lead_status(
            ...     lead_id=UUID("a1b2c3d4-..."),
            ...     new_status=LeadStatus.REACHED_OUT
            ... )
        """
        # Get existing lead
        lead = self.lead_repo.get(lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        # Validate transition if requested
        if validate_transition:
            allowed_transitions = {
                LeadStatus.PENDING.value: [LeadStatus.REACHED_OUT.value],
                LeadStatus.REACHED_OUT.value: []
            }
            
            try:
                validate_status_transition(
                    current_status=lead.status.value,
                    new_status=new_status.value,
                    allowed_transitions=allowed_transitions
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        # Update status using repository method (handles reached_out_at)
        updated_lead = self.lead_repo.update_status(lead_id, new_status)
        self.db.commit()
        self.db.refresh(updated_lead)
        
        return LeadResponse.model_validate(updated_lead)
    
    def update_lead(
        self,
        lead_id: UUID,
        lead_update: LeadUpdate
    ) -> LeadResponse:
        """
        Update lead with partial data.
        
        Args:
            lead_id: UUID of the lead
            lead_update: Partial update data
            
        Returns:
            Updated lead response
            
        Raises:
            HTTPException(404): Lead not found
            HTTPException(400): Invalid update data
            
        Example:
            >>> update_data = LeadUpdate(status=LeadStatus.REACHED_OUT)
            >>> lead = service.update_lead(UUID("a1b2c3d4-..."), update_data)
        """
        # Get existing lead
        lead = self.lead_repo.get(lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        # If status is being updated, use update_lead_status
        if lead_update.status is not None:
            return self.update_lead_status(lead_id, lead_update.status)
        
        # Otherwise, update other fields
        update_dict = lead_update.model_dump(exclude_unset=True)
        updated_lead = self.lead_repo.update(lead_id, update_dict)
        self.db.commit()
        self.db.refresh(updated_lead)
        
        return LeadResponse.model_validate(updated_lead)
    
    def get_recent_leads(self, limit: int = 10) -> List[LeadResponse]:
        """
        Get most recent leads.
        
        Args:
            limit: Maximum number of leads to return
            
        Returns:
            List of lead responses sorted by creation date (newest first)
            
        Example:
            >>> recent = service.get_recent_leads(limit=5)
        """
        leads = self.lead_repo.get_recent_leads(limit=limit)
        return [LeadResponse.model_validate(lead) for lead in leads]
    
    def get_lead_count_by_status(self) -> dict:
        """
        Get count of leads grouped by status.
        
        Returns:
            Dictionary with status as key and count as value
            
        Example:
            >>> counts = service.get_lead_count_by_status()
            >>> print(counts[LeadStatus.PENDING])
            >>> print(counts[LeadStatus.REACHED_OUT])
        """
        return {
            LeadStatus.PENDING: self.lead_repo.count_by_status(LeadStatus.PENDING),
            LeadStatus.REACHED_OUT: self.lead_repo.count_by_status(LeadStatus.REACHED_OUT)
        }
    
    def delete_lead(self, lead_id: UUID) -> bool:
        """
        Delete a lead and its associated resume file.
        
        Args:
            lead_id: UUID of the lead
            
        Returns:
            True if lead was deleted
            
        Raises:
            HTTPException(404): Lead not found
            
        Example:
            >>> service.delete_lead(UUID("a1b2c3d4-..."))
        """
        # Get lead to retrieve resume path
        lead = self.lead_repo.get(lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        # Delete resume file if it exists
        if lead.resume_path:
            try:
                self.file_service.delete_file(lead.resume_path)
            except Exception:
                # Log error but continue with lead deletion
                pass
        
        # Delete lead from database
        deleted = self.lead_repo.delete(lead_id)
        self.db.commit()
        
        return deleted


__all__ = ["LeadService"]
