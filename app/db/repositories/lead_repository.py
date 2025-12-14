"""
Lead repository for lead-specific database operations.

Extends BaseRepository with methods specific to lead management,
including querying by status, email, and pagination.
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC

from sqlalchemy import select, func, or_

from app.db.repositories.base import BaseRepository
from app.models.lead import Lead, LeadStatus


class LeadRepository(BaseRepository[Lead]):
    """
    Repository for Lead model with lead-specific operations.
    
    Provides methods for querying leads by email, status, and
    retrieving paginated results with filtering and sorting.
    """
    
    def get_by_email(self, email: str) -> Optional[Lead]:
        """
        Retrieve a lead by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            Lead instance if found, None otherwise
        """
        stmt = select(Lead).where(Lead.email == email)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_by_status(
        self,
        status: LeadStatus,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lead]:
        """
        Retrieve leads by their current status.
        
        Args:
            status: The LeadStatus to filter by
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List of Lead instances with the specified status
        """
        stmt = (
            select(Lead)
            .where(Lead.status == status)
            .order_by(Lead.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def update_status(
        self,
        lead_id: str,
        status: LeadStatus
    ) -> Optional[Lead]:
        """
        Update a lead's status and set reached_out_at if transitioning to REACHED_OUT.
        
        Args:
            lead_id: The UUID of the lead to update
            status: The new status to set
            
        Returns:
            Updated Lead instance if found, None otherwise
        """
        lead = self.get(lead_id)
        if lead is None:
            return None
        
        lead.status = status
        
        # Set reached_out_at timestamp when transitioning to REACHED_OUT
        if status == LeadStatus.REACHED_OUT and lead.reached_out_at is None:
            lead.reached_out_at = datetime.now(UTC)
        
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def get_leads_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LeadStatus] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Lead], int]:
        """
        Retrieve paginated leads with optional filtering.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            status: Optional status filter
            search: Optional search term for first name, last name, or email
            
        Returns:
            Tuple of (list of Lead instances, total count)
        """
        # Build base query
        stmt = select(Lead)
        count_stmt = select(func.count(Lead.id))
        
        # Apply status filter if provided
        if status is not None:
            stmt = stmt.where(Lead.status == status)
            count_stmt = count_stmt.where(Lead.status == status)
        
        # Apply search filter if provided
        if search:
            search_filter = or_(
                Lead.first_name.ilike(f"%{search}%"),
                Lead.last_name.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%")
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        
        # Get total count
        total_count = self.db.execute(count_stmt).scalar()
        
        # Apply ordering and pagination
        stmt = stmt.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = self.db.execute(stmt)
        leads = list(result.scalars().all())
        
        return leads, total_count
    
    def get_recent_leads(self, limit: int = 10) -> List[Lead]:
        """
        Retrieve the most recently created leads.
        
        Args:
            limit: Maximum number of leads to return
            
        Returns:
            List of Lead instances ordered by creation date (newest first)
        """
        stmt = (
            select(Lead)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def count_by_status(self, status: LeadStatus) -> int:
        """
        Count leads with a specific status.
        
        Args:
            status: The LeadStatus to count
            
        Returns:
            Number of leads with the specified status
        """
        stmt = select(func.count(Lead.id)).where(Lead.status == status)
        return self.db.execute(stmt).scalar()
