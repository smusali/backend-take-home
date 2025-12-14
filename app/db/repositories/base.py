"""
Base repository providing generic CRUD operations.

Implements the repository pattern to abstract database operations
and provide a clean, reusable interface for data access.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing CRUD operations for any model.
    
    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages
    
    Attributes:
        model: The SQLAlchemy model class
        db: The database session
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model and database session.
        
        Args:
            model: The SQLAlchemy model class
            db: The database session for operations
        """
        self.model = model
        self.db = db
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new record in the database.
        
        Args:
            obj_in: Dictionary of field values for the new record
            
        Returns:
            The created model instance with all fields populated
            
        Raises:
            IntegrityError: If unique constraints are violated
            SQLAlchemyError: If database operation fails
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def get(self, id: UUID) -> Optional[ModelType]:
        """
        Retrieve a single record by its ID.
        
        Args:
            id: The UUID of the record to retrieve
            
        Returns:
            The model instance if found, None otherwise
        """
        stmt = select(self.model).where(self.model.id == id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def update(
        self,
        *,
        id: UUID,
        obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: The UUID of the record to update
            obj_in: Dictionary of fields to update
            
        Returns:
            The updated model instance if found, None otherwise
            
        Raises:
            IntegrityError: If unique constraints are violated
            SQLAlchemyError: If database operation fails
        """
        db_obj = self.get(id)
        if db_obj is None:
            return None
        
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: UUID) -> bool:
        """
        Delete a record from the database.
        
        Args:
            id: The UUID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        db_obj = self.get(id)
        if db_obj is None:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """
        Count total number of records in the table.
        
        Returns:
            Total count of records
        """
        stmt = select(self.model)
        result = self.db.execute(stmt)
        return len(list(result.scalars().all()))
