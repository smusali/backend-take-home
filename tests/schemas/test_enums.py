"""
Unit tests for enum definitions.

Tests validation methods, display names, and status transitions.
"""

import pytest

from app.schemas.enums import (
    LeadStatus,
    LEAD_STATUS_DISPLAY_NAMES,
    LEAD_STATUS_DESCRIPTIONS,
    get_all_lead_statuses,
)


class TestLeadStatus:
    """Test suite for LeadStatus enum."""
    
    def test_enum_values(self):
        """Test that enum has correct values."""
        assert LeadStatus.PENDING.value == "PENDING"
        assert LeadStatus.REACHED_OUT.value == "REACHED_OUT"
    
    def test_values_method(self):
        """Test values() class method returns all status values."""
        values = LeadStatus.values()
        
        assert isinstance(values, list)
        assert "PENDING" in values
        assert "REACHED_OUT" in values
        assert len(values) == 2
    
    def test_is_valid_with_valid_status(self):
        """Test is_valid() returns True for valid statuses."""
        assert LeadStatus.is_valid("PENDING") is True
        assert LeadStatus.is_valid("REACHED_OUT") is True
    
    def test_is_valid_with_invalid_status(self):
        """Test is_valid() returns False for invalid statuses."""
        assert LeadStatus.is_valid("INVALID") is False
        assert LeadStatus.is_valid("") is False
        assert LeadStatus.is_valid("pending") is False  # Case sensitive
    
    def test_from_string_with_valid_uppercase(self):
        """Test from_string() with valid uppercase strings."""
        status = LeadStatus.from_string("PENDING")
        assert status == LeadStatus.PENDING
        
        status = LeadStatus.from_string("REACHED_OUT")
        assert status == LeadStatus.REACHED_OUT
    
    def test_from_string_with_valid_lowercase(self):
        """Test from_string() is case-insensitive."""
        status = LeadStatus.from_string("pending")
        assert status == LeadStatus.PENDING
        
        status = LeadStatus.from_string("reached_out")
        assert status == LeadStatus.REACHED_OUT
    
    def test_from_string_with_valid_mixed_case(self):
        """Test from_string() with mixed case."""
        status = LeadStatus.from_string("Pending")
        assert status == LeadStatus.PENDING
        
        status = LeadStatus.from_string("ReAcHeD_OuT")
        assert status == LeadStatus.REACHED_OUT
    
    def test_from_string_with_invalid_value(self):
        """Test from_string() raises ValueError for invalid values."""
        with pytest.raises(ValueError) as exc_info:
            LeadStatus.from_string("INVALID")
        
        assert "Invalid status" in str(exc_info.value)
        assert "PENDING" in str(exc_info.value)
        assert "REACHED_OUT" in str(exc_info.value)
    
    def test_display_name_pending(self):
        """Test display_name property for PENDING status."""
        assert LeadStatus.PENDING.display_name == "Pending"
    
    def test_display_name_reached_out(self):
        """Test display_name property for REACHED_OUT status."""
        assert LeadStatus.REACHED_OUT.display_name == "Reached Out"
    
    def test_description_pending(self):
        """Test description property for PENDING status."""
        description = LeadStatus.PENDING.description
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "submitted" in description.lower()
    
    def test_description_reached_out(self):
        """Test description property for REACHED_OUT status."""
        description = LeadStatus.REACHED_OUT.description
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "reached out" in description.lower()
    
    def test_can_transition_from_pending_to_reached_out(self):
        """Test that PENDING can transition to REACHED_OUT."""
        assert LeadStatus.PENDING.can_transition_to(LeadStatus.REACHED_OUT) is True
    
    def test_can_transition_from_reached_out_to_pending(self):
        """Test that REACHED_OUT can transition to PENDING."""
        assert LeadStatus.REACHED_OUT.can_transition_to(LeadStatus.PENDING) is True
    
    def test_cannot_transition_to_same_status(self):
        """Test that status cannot transition to itself."""
        assert LeadStatus.PENDING.can_transition_to(LeadStatus.PENDING) is False
        assert LeadStatus.REACHED_OUT.can_transition_to(LeadStatus.REACHED_OUT) is False
    
    def test_enum_equality(self):
        """Test enum value equality."""
        status1 = LeadStatus.PENDING
        status2 = LeadStatus.PENDING
        
        assert status1 == status2
        assert status1 is status2
    
    def test_enum_inequality(self):
        """Test enum value inequality."""
        assert LeadStatus.PENDING != LeadStatus.REACHED_OUT
    
    def test_enum_string_representation(self):
        """Test enum string representation."""
        assert str(LeadStatus.PENDING) == "LeadStatus.PENDING"
        assert repr(LeadStatus.PENDING) == "<LeadStatus.PENDING: 'PENDING'>"
    
    def test_enum_iteration(self):
        """Test iterating over enum values."""
        statuses = list(LeadStatus)
        
        assert len(statuses) == 2
        assert LeadStatus.PENDING in statuses
        assert LeadStatus.REACHED_OUT in statuses


class TestLeadStatusConstants:
    """Test suite for LeadStatus constant mappings."""
    
    def test_display_names_has_all_statuses(self):
        """Test that display names dictionary has all statuses."""
        for status in LeadStatus:
            assert status in LEAD_STATUS_DISPLAY_NAMES
    
    def test_display_names_values(self):
        """Test display name values are human-readable."""
        assert LEAD_STATUS_DISPLAY_NAMES[LeadStatus.PENDING] == "Pending"
        assert LEAD_STATUS_DISPLAY_NAMES[LeadStatus.REACHED_OUT] == "Reached Out"
    
    def test_descriptions_has_all_statuses(self):
        """Test that descriptions dictionary has all statuses."""
        for status in LeadStatus:
            assert status in LEAD_STATUS_DESCRIPTIONS
    
    def test_descriptions_are_non_empty(self):
        """Test that all descriptions are non-empty strings."""
        for description in LEAD_STATUS_DESCRIPTIONS.values():
            assert isinstance(description, str)
            assert len(description) > 0


class TestGetAllLeadStatuses:
    """Test suite for get_all_lead_statuses() function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_all_lead_statuses()
        
        assert isinstance(result, list)
    
    def test_returns_all_statuses(self):
        """Test that all statuses are included."""
        result = get_all_lead_statuses()
        
        assert len(result) == 2
    
    def test_each_item_has_required_fields(self):
        """Test that each status dict has required fields."""
        result = get_all_lead_statuses()
        
        for item in result:
            assert "value" in item
            assert "display_name" in item
            assert "description" in item
    
    def test_includes_pending_status(self):
        """Test that PENDING status is included."""
        result = get_all_lead_statuses()
        
        pending = next((s for s in result if s["value"] == "PENDING"), None)
        assert pending is not None
        assert pending["display_name"] == "Pending"
        assert len(pending["description"]) > 0
    
    def test_includes_reached_out_status(self):
        """Test that REACHED_OUT status is included."""
        result = get_all_lead_statuses()
        
        reached_out = next((s for s in result if s["value"] == "REACHED_OUT"), None)
        assert reached_out is not None
        assert reached_out["display_name"] == "Reached Out"
        assert len(reached_out["description"]) > 0
    
    def test_can_be_used_for_api_response(self):
        """Test that result is suitable for API responses."""
        result = get_all_lead_statuses()
        
        # Should be JSON-serializable
        import json
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        
        assert len(parsed) == len(result)
        assert parsed[0]["value"] in ["PENDING", "REACHED_OUT"]
