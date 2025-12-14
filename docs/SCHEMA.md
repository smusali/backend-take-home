# Schema, Validation, and Enum Documentation

**Version:** 1.0.0  
**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Request/Response Schemas](#requestresponse-schemas)
3. [Enum Definitions](#enum-definitions)
4. [Validation Rules](#validation-rules)
5. [Best Practices](#best-practices)

---

## Overview

The schema layer provides type-safe data validation, serialization, and business rule enforcement using Pydantic. This layer ensures data integrity across the entire application and generates automatic API documentation for FastAPI.

### Architecture

```
┌─────────────────────────────────────────────┐
│         API Layer (FastAPI)                 │
│     - Automatic validation                  │
│     - Request parsing                       │
│     - Response serialization                │
└─────────────────┬───────────────────────────┘
                  │ uses
                  ▼
┌─────────────────────────────────────────────┐
│         Schema Layer (Pydantic)             │
│  ┌────────────────────────────────────┐    │
│  │   Request Schemas                   │    │
│  │   - LeadCreate, UserCreate          │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │   Response Schemas                  │    │
│  │   - LeadResponse, UserResponse      │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │   Enums & Validators                │    │
│  │   - LeadStatus, Custom Validators   │    │
│  └────────────────────────────────────┘    │
└─────────────────┬───────────────────────────┘
                  │ validates
                  ▼
┌─────────────────────────────────────────────┐
│         Service Layer                       │
│     (Business Logic)                        │
└─────────────────────────────────────────────┘
```

### Key Features

- **Type Safety**: Full Python type hints with runtime validation
- **Automatic Validation**: FastAPI integration for request/response validation
- **Custom Validators**: Reusable validation functions for complex rules
- **Enums**: Type-safe status values with transition logic
- **Security**: XSS prevention, file validation, password strength
- **Documentation**: Automatic OpenAPI schema generation

### Technology Stack

- **Pydantic**: 2.10.5 (data validation)
- **Email Validation**: pydantic[email] (RFC-compliant email validation)

---

## Request/Response Schemas

### Lead Schemas

#### LeadCreate

Used when prospects submit their information through the public form.

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `first_name` | str | 1-100 chars, required | Prospect's first name |
| `last_name` | str | 1-100 chars, required | Prospect's last name |
| `email` | EmailStr | required | RFC-compliant email address |

**Validation:**
- Minimum 1 character for names (no empty strings)
- Maximum 100 characters for names (prevents abuse)
- Automatic name sanitization (removes HTML/script tags)
- Email normalization (lowercase)

**Usage:**
```python
from app.schemas import LeadCreate

lead_data = LeadCreate(
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com"
)
```

**Note:** Resume file is handled separately as `UploadFile` in the endpoint.

#### LeadUpdate

Used by attorneys to update lead status after reaching out.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | LeadStatus | New lead status (PENDING or REACHED_OUT) |

**Valid Values:**
- `PENDING`: Lead hasn't been contacted yet
- `REACHED_OUT`: Attorney has contacted the prospect

**Usage:**
```python
from app.schemas import LeadUpdate
from app.schemas.enums import LeadStatus

update = LeadUpdate(status=LeadStatus.REACHED_OUT)
```

#### LeadResponse

Complete lead information for API responses.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `first_name` | str | Prospect's first name |
| `last_name` | str | Prospect's last name |
| `email` | EmailStr | Prospect's email |
| `resume_path` | str | Path to resume file |
| `status` | LeadStatus | Current lead status |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `reached_out_at` | Optional[datetime] | When attorney reached out |

**Computed Properties:**
- `full_name` - Returns `"{first_name} {last_name}"`

**Configuration:**
- `from_attributes=True` - Enables ORM mode for SQLAlchemy models

**Usage:**
```python
from app.models.lead import Lead
from app.schemas import LeadResponse

# Convert SQLAlchemy model to Pydantic schema
lead_model = db.query(Lead).first()
lead_response = LeadResponse.from_orm(lead_model)

# Access computed property
print(lead_response.full_name)  # "John Doe"
```

#### LeadListResponse

Wraps a list of leads with pagination metadata.

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `items` | list[LeadResponse] | required | Lead records for current page |
| `total` | int | >= 0 | Total count matching query |
| `page` | int | >= 1 | Current page number (1-indexed) |
| `page_size` | int | 1-100 | Items per page |

**Computed Properties:**
- `total_pages` - Total number of pages: `(total + page_size - 1) // page_size`
- `has_next` - True if more pages exist: `page < total_pages`
- `has_previous` - True if previous pages exist: `page > 1`

**Usage:**
```python
from app.schemas import LeadListResponse, LeadResponse

response = LeadListResponse(
    items=[lead1, lead2, lead3],
    total=25,
    page=1,
    page_size=10
)

print(response.total_pages)  # 3
print(response.has_next)     # True
print(response.has_previous) # False
```

### User Schemas

#### UserCreate

Used when creating a new attorney account.

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `username` | str | 3-50 chars, alphanumeric + _- | Username for login |
| `email` | EmailStr | required | User's email address |
| `password` | str | 8-100 chars, required | Plain password (will be hashed) |

**Validation:**
- Username pattern: `^[a-zA-Z0-9_-]+$`
- Minimum 3 characters (prevents too short usernames)
- Password minimum 8 characters (security requirement)
- Password must contain: uppercase, lowercase, and digit
- Email normalized to lowercase

**Usage:**
```python
from app.schemas import UserCreate

user_data = UserCreate(
    username="attorney1",
    email="attorney@lawfirm.com",
    password="SecurePassword123!"
)
```

#### UserLogin

Used when attorney logs into the internal UI.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `username` | str | Username for authentication |
| `password` | str | Plain password for verification |

**Usage:**
```python
from app.schemas import UserLogin

credentials = UserLogin(
    username="attorney1",
    password="SecurePassword123!"
)
```

#### UserResponse

User information in API responses (excludes password).

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `username` | str | Username |
| `email` | EmailStr | User's email |
| `is_active` | bool | Account status |
| `created_at` | datetime | Account creation timestamp |

**Security Note:** Hashed password is **never** included in responses.

**Configuration:**
- `from_attributes=True` - Enables ORM mode

**Usage:**
```python
from app.models.user import User
from app.schemas import UserResponse

user_model = db.query(User).first()
user_response = UserResponse.from_orm(user_model)
# password is automatically excluded
```

#### Token

JWT authentication token returned after successful login.

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `access_token` | str | required | JWT token string |
| `token_type` | str | "bearer" | Token type |

**Usage:**
```python
from app.schemas import Token

token_response = Token(
    access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    token_type="bearer"
)
```

#### TokenData

Internal use for JWT token validation.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `username` | Optional[str] | Username extracted from token |
| `user_id` | Optional[UUID] | User ID extracted from token |

**Usage:**
```python
from app.schemas import TokenData

# After decoding JWT
token_data = TokenData(
    username="attorney1",
    user_id=user_uuid
)
```

### Schema Integration Patterns

#### In API Endpoints

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import LeadCreate, LeadResponse
from app.db.repositories import LeadRepository
from app.db.database import get_db

app = FastAPI()

@app.post("/api/leads", response_model=LeadResponse, status_code=201)
def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db)
):
    repo = LeadRepository(Lead, db)
    
    # Check duplicate
    existing = repo.get_by_email(lead_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create lead
    lead = repo.create(lead_data.model_dump())
    
    # Return validated response
    return lead
```

#### With File Upload

```python
from fastapi import UploadFile, File, Form
from pydantic import EmailStr

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: EmailStr = Form(...),
    resume: UploadFile = File(...)
):
    # Validate using schema
    lead_data = LeadCreate(
        first_name=first_name,
        last_name=last_name,
        email=email
    )
    
    # Handle file separately
    # ... save resume ...
```

#### Pagination Example

```python
@app.get("/api/leads", response_model=LeadListResponse)
def list_leads(
    page: int = 1,
    page_size: int = 10,
    status: Optional[LeadStatus] = None,
    db: Session = Depends(get_db)
):
    repo = LeadRepository(Lead, db)
    
    skip = (page - 1) * page_size
    leads, total = repo.get_leads_paginated(
        skip=skip,
        limit=page_size,
        status=status
    )
    
    return LeadListResponse(
        items=leads,
        total=total,
        page=page,
        page_size=page_size
    )
```

---

## Enum Definitions

### LeadStatus Enum

Centralized enum definition with validation, display names, and transition logic.

Located in `app/schemas/enums.py`

#### Basic Values

```python
from app.schemas.enums import LeadStatus

LeadStatus.PENDING        # "PENDING"
LeadStatus.REACHED_OUT    # "REACHED_OUT"
```

#### Class Methods

**`values()` - Get All Values**

```python
>>> LeadStatus.values()
['PENDING', 'REACHED_OUT']
```

**Use Case:** Dropdown options, validation lists

**`is_valid(value: str) -> bool` - Validate String**

```python
>>> LeadStatus.is_valid('PENDING')
True
>>> LeadStatus.is_valid('INVALID')
False
```

**Use Case:** Quick validation before conversion

**`from_string(value: str) -> LeadStatus` - Case-Insensitive Conversion**

```python
>>> LeadStatus.from_string('pending')
<LeadStatus.PENDING: 'PENDING'>

>>> LeadStatus.from_string('REACHED_OUT')
<LeadStatus.REACHED_OUT: 'REACHED_OUT'>

>>> LeadStatus.from_string('invalid')
ValueError: Invalid status: invalid. Valid values are: PENDING, REACHED_OUT
```

**Features:**
- Case-insensitive conversion
- Clear error messages listing valid options
- Type-safe enum return

**Use Case:** API parameter parsing

#### Instance Properties

**`display_name` - Human-Readable Name**

```python
>>> LeadStatus.PENDING.display_name
'Pending'

>>> LeadStatus.REACHED_OUT.display_name
'Reached Out'
```

**Use Case:** UI labels, dropdown text

**`description` - Detailed Description**

```python
>>> LeadStatus.PENDING.description
'Lead has been submitted but not yet contacted by an attorney'

>>> LeadStatus.REACHED_OUT.description
'Attorney has reached out to the prospect'
```

**Use Case:** Tooltips, help text

#### Instance Methods

**`can_transition_to(new_status: LeadStatus) -> bool` - Validate Status Changes**

```python
>>> LeadStatus.PENDING.can_transition_to(LeadStatus.REACHED_OUT)
True

>>> LeadStatus.REACHED_OUT.can_transition_to(LeadStatus.PENDING)
True

>>> LeadStatus.PENDING.can_transition_to(LeadStatus.PENDING)
False
```

**Business Rules:**
- PENDING → REACHED_OUT (allowed)
- REACHED_OUT → PENDING (allowed for corrections)
- Same status → Same status (not allowed)

**Use Case:** Validate status updates before saving

### Display Mappings

**`LEAD_STATUS_DISPLAY_NAMES`**

Dictionary mapping enum values to display names:

```python
from app.schemas.enums import LEAD_STATUS_DISPLAY_NAMES

LEAD_STATUS_DISPLAY_NAMES = {
    LeadStatus.PENDING: "Pending",
    LeadStatus.REACHED_OUT: "Reached Out",
}
```

**`LEAD_STATUS_DESCRIPTIONS`**

Dictionary mapping enum values to descriptions:

```python
from app.schemas.enums import LEAD_STATUS_DESCRIPTIONS

LEAD_STATUS_DESCRIPTIONS = {
    LeadStatus.PENDING: "Lead has been submitted but not yet contacted...",
    LeadStatus.REACHED_OUT: "Attorney has reached out to the prospect",
}
```

### Utility Functions

**`get_all_lead_statuses()` - API Response Format**

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
- JSON-serializable
- Complete information
- Ready for API responses

**Use Case:** Status dropdown options endpoint

### Enum Usage Patterns

#### In API Endpoints

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

#### In UI Templates

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

#### In Service Layer

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

### Enum Design Decisions

**Why `str` Enum Base?**

```python
class LeadStatus(str, enum.Enum):
    PENDING = "PENDING"
```

**Benefits:**
- JSON serializable automatically
- Works with Pydantic validation
- Database-friendly (stores as string)
- FastAPI compatible

**Why Display Names?**
- User-Friendly: "Reached Out" vs "REACHED_OUT"
- Internationalization-Ready: Easy to add translations
- Consistent: Single source of truth

**Why Transition Validation?**
- Business Rules: Enforce state machine logic
- Data Integrity: Prevent invalid status changes
- Early Validation: Catch errors before database

---

## Validation Rules

### File Upload Validation

#### `validate_file_size(file, max_size_bytes)`

Validates uploaded file size doesn't exceed maximum.

```python
from app.schemas.validators import validate_file_size

validate_file_size(upload_file, max_size_bytes=5*1024*1024)  # 5MB
```

**Features:**
- Checks Content-Length header
- Human-readable error messages (shows MB)
- Gracefully handles missing size

**Error Example:**
```
File size (10.00MB) exceeds maximum allowed size (5.00MB)
```

#### `validate_file_extension(filename, allowed_extensions)`

Validates file has an allowed extension.

```python
from app.schemas.validators import validate_file_extension, ALLOWED_RESUME_EXTENSIONS

validate_file_extension("resume.pdf", ALLOWED_RESUME_EXTENSIONS)
```

**Features:**
- Case-insensitive comparison
- Lists allowed types in error
- Handles missing extensions

**Allowed Extensions:**
- `.pdf` - PDF documents
- `.doc` - Microsoft Word 97-2003
- `.docx` - Microsoft Word 2007+

#### `validate_resume_file(file, max_size_bytes)`

Complete resume file validation (extension + size + MIME type).

```python
from app.schemas.validators import validate_resume_file

validate_resume_file(resume_upload, max_size_bytes=5*1024*1024)
```

**Validates:**
- File exists
- Extension is allowed (.pdf, .doc, .docx)
- Size doesn't exceed limit
- MIME type is correct

**MIME Types:**
- `application/pdf`
- `application/msword`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

### Text Sanitization

#### `sanitize_name(name)`

Sanitizes name fields to prevent XSS and normalize whitespace.

```python
from app.schemas.validators import sanitize_name

clean_name = sanitize_name("  John   <script>alert()</script>  ")
# Returns: "John"
```

**Protection:**
- Removes HTML/script tags
- Removes dangerous characters (`<>\"'&;{}()[]`)
- Collapses multiple spaces
- Strips leading/trailing whitespace

**Examples:**
```python
sanitize_name("  John  ")                    # "John"
sanitize_name("John   Doe")                  # "John Doe"
sanitize_name("John<script>alert()</script>") # "Johnalert"
sanitize_name("John;DROP TABLE")             # "JohnDROP TABLE"
```

**Note:** This is basic XSS prevention. For production, consider additional layers like Content Security Policy (CSP).

### Email Validation

#### `validate_email_format(email)`

Additional email validation beyond Pydantic's EmailStr.

```python
from app.schemas.validators import validate_email_format

normalized = validate_email_format("User@Example.COM")
# Returns: "user@example.com"
```

**Features:**
- Pattern validation: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Normalizes to lowercase
- Works with Pydantic EmailStr

### Business Rules Validation

#### `validate_status_transition(current, new, allowed)`

Validates status transitions according to business rules.

```python
from app.schemas.validators import validate_status_transition

allowed = {"PENDING": ["REACHED_OUT"]}
validate_status_transition("PENDING", "REACHED_OUT", allowed)  # OK
validate_status_transition("REACHED_OUT", "PENDING", allowed)  # Error
```

**Prevents:**
- Transitioning to same status
- Invalid transitions per business rules
- Unknown statuses

**Error Examples:**
```
Status is already set to this value
Cannot transition from 'REACHED_OUT' to 'PENDING'. Allowed transitions: none
```

### Password Validation

#### `validate_password_strength(password)`

Validates password meets security requirements.

```python
from app.schemas.validators import validate_password_strength

validate_password_strength("Password123")  # OK
validate_password_strength("weak")        # Error
```

**Requirements:**
- At least 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Examples:**
```python
validate_password_strength("Password123")   # ✅ Valid
validate_password_strength("P@ssw0rd!")     # ✅ Valid
validate_password_strength("password")      # ❌ No uppercase or digit
validate_password_strength("PASSWORD123")   # ❌ No lowercase
validate_password_strength("Password")      # ❌ No digit
validate_password_strength("Pass1")         # ❌ Too short
```

### Schema Integration

#### LeadCreate with Validators

```python
from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.validators import sanitize_name, validate_email_format

class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    
    @field_validator("first_name", "last_name")
    @classmethod
    def sanitize_names(cls, v: str) -> str:
        return sanitize_name(v)
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return validate_email_format(v)
```

**Benefits:**
- Automatic validation on schema creation
- Consistent sanitization
- FastAPI integration

#### UserCreate with Password Validation

```python
from pydantic import BaseModel, field_validator
from app.schemas.validators import validate_password_strength

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v
```

### Validation Usage Patterns

#### File Upload Endpoint

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.schemas.validators import validate_resume_file
from app.core.config import get_settings

app = FastAPI()

@app.post("/api/leads/upload")
async def upload_resume(resume: UploadFile = File(...)):
    """Upload and validate resume file."""
    settings = get_settings()
    
    try:
        # Validate file
        validate_resume_file(resume, max_size_bytes=settings.MAX_FILE_SIZE)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Process file
    # ... save file logic ...
    
    return {"message": "File uploaded successfully"}
```

#### Status Update with Transition Validation

```python
from fastapi import FastAPI, HTTPException
from app.schemas.validators import validate_status_transition
from app.schemas.enums import LeadStatus

@app.patch("/api/leads/{lead_id}/status")
def update_status(lead_id: UUID, new_status: str):
    """Update lead status with business rule validation."""
    lead = get_lead(lead_id)
    
    # Define allowed transitions
    allowed_transitions = {
        "PENDING": ["REACHED_OUT"],
        "REACHED_OUT": ["PENDING"],
    }
    
    try:
        validate_status_transition(
            lead.status,
            new_status,
            allowed_transitions
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update status
    lead.status = new_status
    db.commit()
    
    return {"message": "Status updated"}
```

### Security Features

**XSS Prevention:**
```python
# Input: "<script>alert('XSS')</script>"
# Output: "alert"
```
Removes HTML tags and dangerous characters.

**SQL Injection Prevention:**
```python
# Input: "John'; DROP TABLE users--"
# Output: "John DROP TABLE users--"
```
Removes semicolons and special SQL characters.

**File Upload Security:**
- Extension whitelist (not blacklist)
- MIME type validation
- Size limits
- No path traversal (filename validation)

**Password Security:**
- Minimum length (8 characters)
- Complexity requirements
- Works with bcrypt hashing

### Constants & Configuration

**File Upload Constants:**

```python
from app.schemas.validators import (
    ALLOWED_RESUME_EXTENSIONS,
    ALLOWED_RESUME_MIME_TYPES
)

print(ALLOWED_RESUME_EXTENSIONS)
# {'.pdf', '.doc', '.docx'}

print(ALLOWED_RESUME_MIME_TYPES)
# {'application/pdf', 'application/msword', ...}
```

**Configuration Integration:**

```python
from app.core.config import get_settings

settings = get_settings()
max_size = settings.MAX_FILE_SIZE  # 5242880 (5MB)
```

---

## Best Practices

### Schema Design

**1. Separate Create/Update/Response Schemas**

```python
# ✅ Good - Clear intent
class LeadCreate(BaseModel):
    first_name: str
    email: EmailStr

class LeadResponse(BaseModel):
    id: UUID
    first_name: str
    email: EmailStr
    created_at: datetime

# ❌ Bad - Mixed purposes
class Lead(BaseModel):
    id: Optional[UUID]  # Required for response, not for create
    first_name: str
    email: EmailStr
```

**Benefits:**
- Security: Different fields for different operations
- Clarity: Clear intent for each operation
- Validation: Different rules per operation

**2. Use Computed Properties**

```python
# ✅ Good - Computed property
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"

# ❌ Bad - Storing redundant data
class LeadResponse(BaseModel):
    first_name: str
    last_name: str
    full_name: str  # Redundant
```

**3. Enable ORM Mode**

```python
# ✅ Good - Works with SQLAlchemy
class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# Now you can:
lead_response = LeadResponse.from_orm(lead_model)
```

### Validation Best Practices

**1. Always Validate User Input**

```python
# ✅ Good
@field_validator("first_name")
@classmethod
def sanitize_name(cls, v: str) -> str:
    return sanitize_name(v)

# ❌ Bad
first_name: str  # No validation
```

**2. Validate Files at Multiple Layers**

```python
# Layer 1: Client-side (UX)
# Layer 2: Schema validation (this layer)
# Layer 3: Service layer (re-check after upload)
```

**3. Use Whitelists, Not Blacklists**

```python
# ✅ Good - Whitelist
ALLOWED = {'.pdf', '.doc', '.docx'}

# ❌ Bad - Blacklist
FORBIDDEN = {'.exe', '.bat', '.sh'}  # Easy to bypass
```

**4. Provide Clear Error Messages**

```python
# ✅ Good
raise ValueError(f"File type '{ext}' not allowed. Allowed: .pdf, .doc, .docx")

# ❌ Bad
raise ValueError("Invalid file")
```

### Enum Best Practices

**1. Use String Enums for API Compatibility**

```python
# ✅ Good
class LeadStatus(str, enum.Enum):
    PENDING = "PENDING"

# ❌ Bad
class LeadStatus(enum.Enum):
    PENDING = 1  # Not JSON serializable
```

**2. Provide Display Names**

```python
# ✅ Good
@property
def display_name(self) -> str:
    return LEAD_STATUS_DISPLAY_NAMES[self]

# Usage in UI
print(status.display_name)  # "Pending" instead of "PENDING"
```

**3. Validate Transitions**

```python
# ✅ Good
def can_transition_to(self, new_status: "LeadStatus") -> bool:
    return new_status in self.allowed_transitions

# Prevents invalid state changes
```

### Error Handling

**Validation Errors:**

All validators raise `ValueError` with descriptive messages:

```python
try:
    validate_resume_file(file)
except ValueError as e:
    return {"error": str(e)}
```

**FastAPI Integration:**

Pydantic validators automatically return 422:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

---

## Related Documentation

- [API Documentation](./API.md) - API endpoint reference
- [Services Documentation](./SERVICES.md) - Business logic layer
- [Database Documentation](./DATABASE.md) - Database models and repositories
- [Design Documentation](./DESIGN.md) - System architecture

---

**Schema Version:** 1.0.0  
**Last Updated:** December 2025  
**Test Coverage:** 110+ tests across schemas, enums, and validators
