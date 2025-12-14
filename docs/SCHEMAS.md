# Request/Response Schemas

## ✅ Completed: Section 3.1 Request/Response Schemas

### Overview

Pydantic schemas provide type-safe validation for all API requests and responses, ensuring data integrity and automatic documentation generation for FastAPI endpoints.

### Files Created

#### **Schema Definitions (3 files):**

1. ✅ `app/schemas/__init__.py` - Package exports
2. ✅ `app/schemas/lead.py` - Lead-related schemas (127 lines)
3. ✅ `app/schemas/user.py` - User and authentication schemas (112 lines)

#### **Test Files (2 files):**

4. ✅ `tests/schemas/__init__.py` - Test package
5. ✅ `tests/schemas/test_lead.py` - Lead schema tests (23 tests)
6. ✅ `tests/schemas/test_user.py` - User schema tests (22 tests)

### Lead Schemas

#### **`LeadCreate`** - Public Lead Submission

Used when prospects submit their information through the public form.

**Fields:**
- ✅ `first_name` (str, 1-100 chars, required)
- ✅ `last_name` (str, 1-100 chars, required)
- ✅ `email` (EmailStr, required)

**Validation:**
- Minimum 1 character for names (no empty strings)
- Maximum 100 characters for names (prevents abuse)
- RFC-compliant email validation via Pydantic's `EmailStr`

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

#### **`LeadUpdate`** - Attorney Status Update

Used by attorneys to update lead status after reaching out.

**Fields:**
- ✅ `status` (LeadStatus enum, required)

**Valid Values:**
- `PENDING` - Lead hasn't been contacted yet
- `REACHED_OUT` - Attorney has contacted the lead

**Usage:**
```python
from app.schemas import LeadUpdate
from app.models.lead import LeadStatus

update = LeadUpdate(status=LeadStatus.REACHED_OUT)
```

#### **`LeadResponse`** - API Response Format

Complete lead information for API responses.

**Fields:**
- ✅ `id` (UUID)
- ✅ `first_name` (str)
- ✅ `last_name` (str)
- ✅ `email` (EmailStr)
- ✅ `resume_path` (str)
- ✅ `status` (LeadStatus)
- ✅ `created_at` (datetime)
- ✅ `updated_at` (datetime)
- ✅ `reached_out_at` (Optional[datetime])

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

#### **`LeadListResponse`** - Paginated Results

Wraps a list of leads with pagination metadata.

**Fields:**
- ✅ `items` (list[LeadResponse]) - Lead records for current page
- ✅ `total` (int, >= 0) - Total count matching query
- ✅ `page` (int, >= 1) - Current page number (1-indexed)
- ✅ `page_size` (int, 1-100) - Items per page

**Computed Properties:**
- `total_pages` - Total number of pages
- `has_next` - True if more pages exist
- `has_previous` - True if previous pages exist

**Validation:**
- `page_size` limited to 100 max (prevents abuse)
- `page` must be >= 1 (1-indexed)
- `total` must be >= 0 (non-negative)

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

#### **`UserCreate`** - User Registration

Used when creating a new attorney account.

**Fields:**
- ✅ `username` (str, 3-50 chars, alphanumeric + underscore/dash)
- ✅ `email` (EmailStr, required)
- ✅ `password` (str, 8-100 chars, required)

**Validation:**
- Username pattern: `^[a-zA-Z0-9_-]+$`
- Minimum 3 characters (prevents too short usernames)
- Password minimum 8 characters (security requirement)

**Usage:**
```python
from app.schemas import UserCreate

user_data = UserCreate(
    username="attorney1",
    email="attorney@lawfirm.com",
    password="SecurePassword123!"
)
```

#### **`UserLogin`** - Authentication Credentials

Used when attorney logs into the internal UI.

**Fields:**
- ✅ `username` (str, required)
- ✅ `password` (str, required)

**Usage:**
```python
from app.schemas import UserLogin

credentials = UserLogin(
    username="attorney1",
    password="SecurePassword123!"
)
```

#### **`UserResponse`** - User Profile Data

User information in API responses (excludes password).

**Fields:**
- ✅ `id` (UUID)
- ✅ `username` (str)
- ✅ `email` (EmailStr)
- ✅ `is_active` (bool)
- ✅ `created_at` (datetime)

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

#### **`Token`** - JWT Authentication Token

Returned after successful login.

**Fields:**
- ✅ `access_token` (str, required) - JWT token string
- ✅ `token_type` (str, default="bearer") - Token type

**Usage:**
```python
from app.schemas import Token

token_response = Token(
    access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    token_type="bearer"
)
```

#### **`TokenData`** - Decoded JWT Payload

Internal use for token validation.

**Fields:**
- ✅ `username` (Optional[str]) - Extracted from token
- ✅ `user_id` (Optional[UUID]) - Extracted from token

**Usage:**
```python
from app.schemas import TokenData

# After decoding JWT
token_data = TokenData(
    username="attorney1",
    user_id=user_uuid
)
```

### Validation Features

#### **String Length Constraints**

All string fields have min/max lengths to prevent:
- Empty submissions (min_length)
- Buffer overflow attacks (max_length)
- Database constraint violations

#### **Email Validation**

Uses Pydantic's `EmailStr` for RFC-compliant validation:
- ✅ Syntax validation
- ✅ Domain validation
- ✅ Handles international domains

#### **Pattern Validation**

Username pattern `^[a-zA-Z0-9_-]+$` allows:
- ✅ Letters (a-z, A-Z)
- ✅ Numbers (0-9)
- ✅ Underscores (_)
- ✅ Dashes (-)

Prevents:
- ❌ Spaces
- ❌ Special characters (@, #, $, etc.)
- ❌ SQL injection attempts

#### **Enum Validation**

`LeadStatus` enum ensures only valid statuses:
- Automatic validation by Pydantic
- Type-safe in Python code
- Auto-documented in API

### Computed Properties

#### **Full Name** (`LeadResponse`)

```python
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"
```

**Benefits:**
- Consistent formatting
- No duplication in database
- Easy display in UI

#### **Pagination Properties** (`LeadListResponse`)

```python
@property
def total_pages(self) -> int:
    return (self.total + self.page_size - 1) // self.page_size

@property
def has_next(self) -> bool:
    return self.page < self.total_pages

@property
def has_previous(self) -> bool:
    return self.page > 1
```

**Benefits:**
- Computed on-demand
- No additional API calls
- Simplifies UI pagination logic

### FastAPI Integration

#### **Automatic Documentation**

```python
from fastapi import FastAPI
from app.schemas import LeadCreate, LeadResponse

app = FastAPI()

@app.post("/leads", response_model=LeadResponse)
def create_lead(lead_data: LeadCreate):
    """
    OpenAPI automatically includes:
    - Request body schema with examples
    - Response schema with field descriptions
    - Validation error responses
    """
    pass
```

#### **Request Validation**

```python
@app.post("/leads")
def create_lead(lead_data: LeadCreate):
    # FastAPI automatically validates:
    # - first_name is 1-100 chars
    # - last_name is 1-100 chars
    # - email is valid format
    # Returns 422 if validation fails
    pass
```

#### **Response Validation**

```python
@app.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: UUID):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    # FastAPI automatically:
    # - Converts SQLAlchemy model to Pydantic schema
    # - Validates all fields
    # - Serializes to JSON
    return lead
```

### Test Coverage

#### **Lead Schema Tests (23 tests)**

- ✅ Valid data creation
- ✅ Required field validation
- ✅ String length validation (min/max)
- ✅ Email format validation
- ✅ Enum validation
- ✅ Computed properties
- ✅ Pagination logic
- ✅ Edge cases (empty lists, boundaries)

#### **User Schema Tests (22 tests)**

- ✅ Valid user creation
- ✅ Username pattern validation
- ✅ Password length validation
- ✅ Email validation
- ✅ Token structure
- ✅ Optional fields
- ✅ Default values

**Total Tests: 135 ✅ ALL PASSING** (90 existing + 45 new)

### Design Decisions

#### **Why Pydantic?**

1. **Type Safety** - Compile-time type checking
2. **Runtime Validation** - Automatic data validation
3. **FastAPI Integration** - Native support
4. **Auto Documentation** - OpenAPI schema generation
5. **Performance** - Rust-powered validation (fast!)

#### **Why Separate Create/Update/Response?**

1. **Security** - Different fields for different operations
2. **Clarity** - Clear intent for each operation
3. **Validation** - Different rules per operation
4. **Documentation** - Self-documenting API

**Example:**
- `UserCreate` - Includes plain password
- `UserResponse` - Excludes password completely
- `UserUpdate` - Would include only updatable fields

#### **Why `from_attributes=True`?**

Enables ORM mode for SQLAlchemy:
```python
# Without from_attributes - Error!
user_model = User(username="test")
user_response = UserResponse(user_model)  # ❌ Fails

# With from_attributes - Works!
user_response = UserResponse.from_orm(user_model)  # ✅ Success
```

### Usage Patterns

#### **In API Endpoints**

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

#### **With File Upload**

```python
from fastapi import UploadFile, File

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

#### **Pagination Example**

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

### Summary

**Section 3.1: Request/Response Schemas** provides:

✅ **Lead Schemas** - 4 schemas for CRUD operations  
✅ **User Schemas** - 5 schemas for auth and user management  
✅ **Validation** - Length, format, pattern constraints  
✅ **Computed Properties** - full_name, pagination helpers  
✅ **45 Unit Tests** - Comprehensive validation testing  
✅ **Type Safety** - Full Python type hints  
✅ **FastAPI Ready** - Auto-documentation and validation  

### Next Steps

Schemas are ready for:
1. ✅ API endpoint implementation
2. ✅ File upload validation (Section 3.3)
3. ✅ Service layer integration
4. ✅ OpenAPI documentation generation
