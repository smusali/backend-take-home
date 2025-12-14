"""
Enum definitions with validation and display utilities.

Provides enums for API use with additional validation methods
and human-readable display name mappings.
"""

import enum
from typing import List


class LeadStatus(str, enum.Enum):
    """
    Lead status enumeration with validation and display utilities.
    
    Represents the current state of a lead in the outreach process.
    """
    
    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"
    
    @classmethod
    def values(cls) -> List[str]:
        """
        Get list of all valid status values.
        
        Returns:
            List of status string values
            
        Example:
            >>> LeadStatus.values()
            ['PENDING', 'REACHED_OUT']
        """
        return [status.value for status in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """
        Check if a value is a valid status.
        
        Args:
            value: String value to validate
            
        Returns:
            True if valid, False otherwise
            
        Example:
            >>> LeadStatus.is_valid('PENDING')
            True
            >>> LeadStatus.is_valid('INVALID')
            False
        """
        try:
            cls(value)
            return True
        except (ValueError, KeyError):
            return False
    
    @classmethod
    def from_string(cls, value: str) -> "LeadStatus":
        """
        Convert string to LeadStatus enum, case-insensitive.
        
        Args:
            value: String value to convert
            
        Returns:
            LeadStatus enum value
            
        Raises:
            ValueError: If value is not a valid status
            
        Example:
            >>> LeadStatus.from_string('pending')
            <LeadStatus.PENDING: 'PENDING'>
        """
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(
                f"Invalid status: {value}. "
                f"Valid values are: {', '.join(cls.values())}"
            )
    
    @property
    def display_name(self) -> str:
        """
        Get human-readable display name for the status.
        
        Returns:
            Formatted display name
            
        Example:
            >>> LeadStatus.PENDING.display_name
            'Pending'
            >>> LeadStatus.REACHED_OUT.display_name
            'Reached Out'
        """
        return LEAD_STATUS_DISPLAY_NAMES.get(self, self.value)
    
    @property
    def description(self) -> str:
        """
        Get detailed description of the status.
        
        Returns:
            Status description for tooltips/help text
        """
        return LEAD_STATUS_DESCRIPTIONS.get(self, "")
    
    def can_transition_to(self, target_status: "LeadStatus") -> bool:
        """
        Check if transition to target status is allowed.
        
        Args:
            target_status: The status to transition to
            
        Returns:
            True if transition is allowed, False otherwise
            
        Example:
            >>> LeadStatus.PENDING.can_transition_to(LeadStatus.REACHED_OUT)
            True
            >>> LeadStatus.REACHED_OUT.can_transition_to(LeadStatus.PENDING)
            True
        """
        # Define allowed transitions
        allowed_transitions = {
            LeadStatus.PENDING: [LeadStatus.REACHED_OUT],
            LeadStatus.REACHED_OUT: [LeadStatus.PENDING],
        }
        
        return target_status in allowed_transitions.get(self, [])


# Display name mappings for UI
LEAD_STATUS_DISPLAY_NAMES = {
    LeadStatus.PENDING: "Pending",
    LeadStatus.REACHED_OUT: "Reached Out",
}

# Detailed descriptions for tooltips
LEAD_STATUS_DESCRIPTIONS = {
    LeadStatus.PENDING: "Lead has been submitted but not yet contacted by an attorney",
    LeadStatus.REACHED_OUT: "Attorney has reached out to the prospect",
}


def get_all_lead_statuses() -> List[dict]:
    """
    Get all lead statuses with their display information.
    
    Returns:
        List of dictionaries containing status information
        
    Example:
        >>> get_all_lead_statuses()
        [
            {
                'value': 'PENDING',
                'display_name': 'Pending',
                'description': '...'
            },
            ...
        ]
    """
    return [
        {
            "value": status.value,
            "display_name": status.display_name,
            "description": status.description,
        }
        for status in LeadStatus
    ]


__all__ = [
    "LeadStatus",
    "LEAD_STATUS_DISPLAY_NAMES",
    "LEAD_STATUS_DESCRIPTIONS",
    "get_all_lead_statuses",
]
