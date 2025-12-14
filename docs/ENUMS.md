# Enum Definitions

## ✅ Completed: Section 3.2 Enum Definitions

### Overview

Enhanced enum definitions provide validation methods, display name mappings, and business logic for API use while maintaining compatibility with database models.

### Files Created

#### **Enum Definition (1 file):**
1. ✅ `app/schemas/enums.py` - LeadStatus enum with utilities (182 lines)

#### **Test Files (1 file):**
2. ✅ `tests/schemas/test_enums.py` - 29 enum tests (241 lines)

#### **Updated Files:**
3. ✅ `app/schemas/__init__.py` - Added enum exports
4. ✅ `app/schemas/lead.py` - Import from schemas.enums

### LeadStatus Enum

Centralized enum definition with validation, display names, and transition logic.

#### **Basic Values:**

```python
from app.schemas.enums import LeadStatus

LeadStatus.PENDING        # "PENDING"
LeadStatus.REACHED_OUT    # "REACHED_OUT"
```

#### **Class Methods:**

##### **`values()` - Get All Values**

```python
>>> LeadStatus.values()
['PENDING', 'REACHED_OUT']
```

**Use Case:** Dropdown options, validation lists

##### **`is_valid()` - Validate String**

```python
>>> LeadStatus.is_valid('PENDING')
True
>>> LeadStatus.is_valid('INVALID')
False
```

**Use Case:** Quick validation before conversion

##### **`from_string()` - Case-Insensitive Conversion**

```python
>>> LeadStatus.from_string('pending')
<LeadStatus.PENDING: 'PENDING'>

>>> LeadStatus.from_string('REACHED_OUT')
<LeadStatus.REACHED_OUT: 'REACHED_OUT'>

>>> LeadStatus.from_string('invalid')
ValueError: Invalid status: invalid. Valid values are: PENDING, REACHED_OUT
```

**Features:**
- ✅ Case-insensitive
- ✅ Clear error messages
- ✅ Lists valid options

**Use Case:** API parameter parsing

#### **Instance Properties:**

##### **`display_name` - Human-Readable Name**

```python
>>> LeadStatus.PENDING.display_name
'Pending'

>>> LeadStatus.REACHED_OUT.display_name
'Reached Out'
```

**Use Case:** UI labels, dropdown text

##### **`description` - Detailed Description**

```python
>>> LeadStatus.PENDING.description
'Lead has been submitted but not yet contacted by an attorney'

>>> LeadStatus.REACHED_OUT.description
'Attorney has reached out to the prospect'
```

**Use Case:** Tooltips, help text

#### **Instance Methods:**

##### **`can_transition_to()` - Validate Status Changes**

```python
>>> LeadStatus.PENDING.can_transition_to(LeadStatus.REACHED_OUT)
True

>>> LeadStatus.REACHED_OUT.can_transition_to(LeadStatus.PENDING)
True

>>> LeadStatus.PENDING.can_transition_to(LeadStatus.PENDING)
False
```

**Business Rules:**
- ✅ PENDING → REACHED_OUT (allowed)
- ✅ REACHED_OUT → PENDING (allowed for corrections)
- ❌ Same status → Same status (not allowed)

**Use Case:** Validate status updates before saving

### Display Name Mappings

#### **`LEAD_STATUS_DISPLAY_NAMES`**

Dictionary mapping enum values to display names:

```python
from app.schemas.enums import LEAD_STATUS_DISPLAY_NAMES

LEAD_STATUS_DISPLAY_NAMES = {
    LeadStatus.PENDING: "Pending",
    LeadStatus.REACHED_OUT: "Reached Out",
}
```

**Use Case:** Batch conversions, template rendering

#### **`LEAD_STATUS_DESCRIPTIONS`**

Dictionary mapping enum values to descriptions:

```python
from app.schemas.enums import LEAD_STATUS_DESCRIPTIONS

LEAD_STATUS_DESCRIPTIONS = {
    LeadStatus.PENDING: "Lead has been submitted but not yet contacted...",
    LeadStatus.REACHED_OUT: "Attorney has reached out to the prospect",
}
```

**Use Case:** Help text, documentation

### Utility Functions

#### **`get_all_lead_statuses()` - API Response Format**

Returns all statuses with display information:

```python
from app.schemas.enums import get_all_lead_statuses

>>> get_all_lead_statuses()
[
    {
        'value': 'PENDING',
        'display_name': 'Pending',
        'description': 'Lead has been submitted but not yet contacted...'
    },
    {
        'value': 'REACHED_OUT',
        'display_name': 'Reached Out',
        'description': 'Attorney has reached out to the prospect'
    }
]
```

**Features:**
- ✅ JSON-serializable
- ✅ Complete information
- ✅ Ready for API responses

**Use Case:** Status dropdown options endpoint

### Usage Patterns

#### **In API Endpoints:**

```python
from fastapi import FastAPI, HTTPException
from app.schemas.enums import LeadStatus, get_all_lead_statuses

app = FastAPI()

@app.get("/api/statuses")
def list_statuses():
    """Get all available lead statuses with display info."""
    return get_all_lead_statuses()

@app.patch("/api/leads/{lead_id}/status")
def update_lead_status(lead_id: UUID, new_status: str):
    """Update lead status with validation."""
    # Validate status value
    if not LeadStatus.is_valid(new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {LeadStatus.values()}"
        )
    
    # Convert to enum
    status_enum = LeadStatus.from_string(new_status)
    
    # Validate transition
    current_status = lead.status
    if not current_status.can_transition_to(status_enum):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {current_status.display_name} "
                   f"to {status_enum.display_name}"
        )
    
    # Update status
    lead.status = status_enum
    db.commit()
    
    return {"message": f"Status updated to {status_enum.display_name}"}
```

#### **In UI Templates:**

```html
<!-- Dropdown with display names -->
<select name="status">
  {% for status in statuses %}
    <option value="{{ status.value }}" title="{{ status.description }}">
      {{ status.display_name }}
    </option>
  {% endfor %}
</select>
```

#### **In Service Layer:**

```python
from app.schemas.enums import LeadStatus

class LeadService:
    def update_lead_status(self, lead_id: UUID, new_status: str):
        """Update lead status with business logic validation."""
        lead = self.lead_repo.get(lead_id)
        
        # Convert string to enum
        try:
            status_enum = LeadStatus.from_string(new_status)
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Check transition validity
        if not lead.status.can_transition_to(status_enum):
            raise BusinessRuleError(
                f"Cannot change status from "
                f"{lead.status.display_name} to "
                f"{status_enum.display_name}"
            )
        
        # Update
        return self.lead_repo.update_status(lead_id, status_enum)
```

### Test Coverage

#### **Enum Tests (29 tests)**

**Value Tests (2):**
- ✅ Enum has correct values
- ✅ values() returns all statuses

**Validation Tests (4):**
- ✅ is_valid() with valid statuses
- ✅ is_valid() with invalid statuses
- ✅ from_string() with various cases
- ✅ from_string() error handling

**Display Tests (4):**
- ✅ display_name for each status
- ✅ description for each status
- ✅ All statuses have display names
- ✅ All statuses have descriptions

**Transition Tests (3):**
- ✅ Valid transitions allowed
- ✅ Invalid transitions rejected
- ✅ Same-status transitions rejected

**Enum Behavior Tests (6):**
- ✅ Equality/inequality
- ✅ String representation
- ✅ Iteration
- ✅ Dictionary lookups

**Utility Function Tests (6):**
- ✅ get_all_lead_statuses() structure
- ✅ JSON serialization
- ✅ Complete information included

**Total Tests: 164 ✅ ALL PASSING** (135 existing + 29 new)

### Design Decisions

#### **Why Separate Enum from Model?**

1. **Avoid Circular Imports** - Models and schemas can both use it
2. **Schema-Layer Features** - Add validation without polluting models
3. **Clean Separation** - Business logic in schemas, data structure in models

#### **Why `str` Enum Base?**

```python
class LeadStatus(str, enum.Enum):
    PENDING = "PENDING"
```

**Benefits:**
- ✅ JSON serializable automatically
- ✅ Works with Pydantic validation
- ✅ Database-friendly (stores as string)
- ✅ FastAPI compatible

#### **Why Display Names?**

- **User-Friendly** - "Reached Out" vs "REACHED_OUT"
- **Internationalization-Ready** - Easy to add translations
- **Consistent** - Single source of truth

#### **Why Transition Validation?**

- **Business Rules** - Enforce state machine logic
- **Data Integrity** - Prevent invalid status changes
- **Early Validation** - Catch errors before database

### Integration with FastAPI

#### **Automatic Validation:**

```python
from pydantic import BaseModel
from app.schemas.enums import LeadStatus

class LeadUpdate(BaseModel):
    status: LeadStatus  # Automatically validates against enum values
```

**FastAPI will:**
- ✅ Reject invalid values with 422
- ✅ Include enum values in OpenAPI docs
- ✅ Generate dropdown in Swagger UI

#### **OpenAPI Documentation:**

Enum automatically appears in API docs:

```json
{
  "LeadStatus": {
    "type": "string",
    "enum": ["PENDING", "REACHED_OUT"],
    "description": "Lead status enumeration"
  }
}
```

### Benefits

#### **1. Type Safety:**
```python
# Type hints work correctly
def process_lead(status: LeadStatus):
    # IDE knows valid values
    if status == LeadStatus.PENDING:
        ...
```

#### **2. Validation:**
```python
# Automatic validation
LeadStatus.is_valid("PENDING")  # True
LeadStatus.is_valid("INVALID")  # False
```

#### **3. Display:**
```python
# Human-readable names
status = LeadStatus.PENDING
print(status.display_name)  # "Pending"
print(status.description)   # Full description
```

#### **4. Business Logic:**
```python
# Enforce transitions
current.can_transition_to(new_status)  # True/False
```

### Future Enhancements

Potential additions for more complex workflows:

1. **More Statuses** - CONTACTED, QUALIFIED, REJECTED, etc.
2. **Role-Based Transitions** - Different rules per user role
3. **Audit Trail** - Track who changed status and when
4. **Notifications** - Trigger emails on status changes
5. **Workflow Engine** - Complex state machine logic

### Summary

**Section 3.2: Enum Definitions** provides:

✅ **LeadStatus Enum** - With validation and display utilities  
✅ **Class Methods** - values(), is_valid(), from_string()  
✅ **Properties** - display_name, description  
✅ **Transition Logic** - can_transition_to()  
✅ **Display Mappings** - Human-readable names  
✅ **Utility Functions** - get_all_lead_statuses()  
✅ **29 Unit Tests** - Comprehensive validation  
✅ **FastAPI Integration** - Auto-validation and docs  

### Next Steps

Enum definitions are ready for:
1. ✅ Custom validators (Section 3.3)
2. ✅ API endpoint implementation
3. ✅ Status transition enforcement
4. ✅ UI dropdown generation
