# Manual QA Testing Guide

**Version:** 1.0.0  
**Last Updated:** December 2025  
**Application:** Lead Management API  
**Framework:** FastAPI 0.115.6  
**Python:** 3.13+

---

## Test Environment Setup

### Prerequisites

**Local Environment:**
- Python 3.13+ installed
- Virtual environment activated
- Database initialized with migrations
- `.env` file configured with valid SMTP credentials
- Server running on http://localhost:8000

**Docker Environment:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- Services running via `docker-compose up -d`
- Database initialized in container

### Start Application

**Local:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
docker-compose up -d
docker-compose logs -f api
```

### Verify Health

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Authentication Flow Tests

### TEST-AUTH-001: User Registration - Valid Data

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney1",
  "email": "attorney1@lawfirm.com",
  "password": "SecurePass123!"
}
```

**Steps:**
1. Send POST request to `/api/v1/auth/register`
2. Include test data in request body
3. Verify response status code
4. Verify response structure
5. Extract user ID for later tests

**Expected Response:**
- Status: `201 Created`
- Body:
```json
{
  "id": "<uuid>",
  "username": "attorney1",
  "email": "attorney1@lawfirm.com",
  "is_active": true,
  "created_at": "<timestamp>"
}
```

**Validation:**
- ✓ Response status is 201
- ✓ `id` is valid UUID format
- ✓ `username` matches input
- ✓ `email` matches input (lowercase)
- ✓ `is_active` is true
- ✓ `created_at` is ISO 8601 timestamp
- ✓ Password is NOT in response

---

### TEST-AUTH-002: User Registration - Duplicate Username

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney1",
  "email": "different@lawfirm.com",
  "password": "SecurePass123!"
}
```

**Steps:**
1. Register user with TEST-AUTH-001 data first
2. Attempt to register with same username but different email
3. Verify error response

**Expected Response:**
- Status: `400 Bad Request`
- Body:
```json
{
  "detail": "Username already exists"
}
```

**Validation:**
- ✓ Response status is 400
- ✓ Error message indicates username conflict
- ✓ User count in database remains 1

---

### TEST-AUTH-003: User Registration - Duplicate Email

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney2",
  "email": "attorney1@lawfirm.com",
  "password": "SecurePass123!"
}
```

**Steps:**
1. Register user with TEST-AUTH-001 data first
2. Attempt to register with different username but same email
3. Verify error response

**Expected Response:**
- Status: `400 Bad Request`
- Body:
```json
{
  "detail": "Email already exists"
}
```

**Validation:**
- ✓ Response status is 400
- ✓ Error message indicates email conflict

---

### TEST-AUTH-004: User Registration - Invalid Username (Too Short)

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "ab",
  "email": "test@lawfirm.com",
  "password": "SecurePass123!"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`
- Body includes validation error for username

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates minimum 3 characters required

---

### TEST-AUTH-005: User Registration - Invalid Username (Special Characters)

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney@#$",
  "email": "test@lawfirm.com",
  "password": "SecurePass123!"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`
- Body includes validation error for username format

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates only alphanumeric and underscores allowed

---

### TEST-AUTH-006: User Registration - Invalid Email Format

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney3",
  "email": "invalid-email",
  "password": "SecurePass123!"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`
- Body:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Validation:**
- ✓ Response status is 422
- ✓ Error identifies email field
- ✓ Error message indicates invalid format

---

### TEST-AUTH-007: User Registration - Weak Password (Too Short)

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney4",
  "email": "attorney4@lawfirm.com",
  "password": "Pass1"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`
- Body includes validation error for password length

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates minimum 8 characters required

---

### TEST-AUTH-008: User Registration - Weak Password (No Uppercase)

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney5",
  "email": "attorney5@lawfirm.com",
  "password": "password123"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`
- Body includes validation error for password complexity

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates uppercase letter required

---

### TEST-AUTH-009: User Registration - Weak Password (No Lowercase)

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney6",
  "email": "attorney6@lawfirm.com",
  "password": "PASSWORD123"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates lowercase letter required

---

### TEST-AUTH-010: User Registration - Weak Password (No Digit)

**Endpoint:** `POST /api/v1/auth/register`

**Test Data:**
```json
{
  "username": "attorney7",
  "email": "attorney7@lawfirm.com",
  "password": "PasswordOnly"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates digit required

---

### TEST-AUTH-011: User Login - Valid Credentials

**Endpoint:** `POST /api/v1/auth/login`

**Test Data:**
```
username=attorney1
password=SecurePass123!
```

**Content-Type:** `application/x-www-form-urlencoded`

**Steps:**
1. Register user with TEST-AUTH-001 data first
2. Send POST request with form data
3. Verify token response
4. Save token for subsequent tests

**Expected Response:**
- Status: `200 OK`
- Body:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Validation:**
- ✓ Response status is 200
- ✓ `access_token` is non-empty string
- ✓ Token starts with JWT structure (three base64 segments)
- ✓ `token_type` is "bearer"
- ✓ Token can be decoded to verify payload structure

---

### TEST-AUTH-012: User Login - Invalid Username

**Endpoint:** `POST /api/v1/auth/login`

**Test Data:**
```
username=nonexistent
password=SecurePass123!
```

**Expected Response:**
- Status: `401 Unauthorized`
- Body:
```json
{
  "detail": "Incorrect username or password"
}
```

**Validation:**
- ✓ Response status is 401
- ✓ Error message is generic (no information leakage)

---

### TEST-AUTH-013: User Login - Invalid Password

**Endpoint:** `POST /api/v1/auth/login`

**Test Data:**
```
username=attorney1
password=WrongPassword123
```

**Expected Response:**
- Status: `401 Unauthorized`
- Body:
```json
{
  "detail": "Incorrect username or password"
}
```

**Validation:**
- ✓ Response status is 401
- ✓ Error message is generic (doesn't reveal which field is wrong)

---

### TEST-AUTH-014: User Login - Missing Username

**Endpoint:** `POST /api/v1/auth/login`

**Test Data:**
```
password=SecurePass123!
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates missing required field

---

### TEST-AUTH-015: User Login - Missing Password

**Endpoint:** `POST /api/v1/auth/login`

**Test Data:**
```
username=attorney1
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates missing required field

---

### TEST-AUTH-016: Get Current User - Valid Token

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer <valid_token_from_TEST-AUTH-011>
```

**Steps:**
1. Login to get valid token (TEST-AUTH-011)
2. Send GET request with Authorization header
3. Verify user profile response

**Expected Response:**
- Status: `200 OK`
- Body:
```json
{
  "id": "<uuid>",
  "username": "attorney1",
  "email": "attorney1@lawfirm.com",
  "is_active": true,
  "created_at": "<timestamp>"
}
```

**Validation:**
- ✓ Response status is 200
- ✓ User data matches registered user
- ✓ Password is NOT in response

---

### TEST-AUTH-017: Get Current User - Missing Token

**Endpoint:** `GET /api/v1/auth/me`

**Headers:** None

**Expected Response:**
- Status: `401 Unauthorized`
- Body:
```json
{
  "detail": "Not authenticated"
}
```

**Validation:**
- ✓ Response status is 401
- ✓ Error indicates missing authentication

---

### TEST-AUTH-018: Get Current User - Invalid Token

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer invalid.token.here
```

**Expected Response:**
- Status: `401 Unauthorized`
- Body:
```json
{
  "detail": "Could not validate credentials"
}
```

**Validation:**
- ✓ Response status is 401
- ✓ Error indicates invalid credentials

---

### TEST-AUTH-019: Get Current User - Expired Token

**Endpoint:** `GET /api/v1/auth/me`

**Steps:**
1. Generate token with very short expiration (modify settings temporarily)
2. Wait for token to expire
3. Attempt to use expired token

**Expected Response:**
- Status: `401 Unauthorized`
- Body:
```json
{
  "detail": "Could not validate credentials"
}
```

**Validation:**
- ✓ Response status is 401
- ✓ Expired tokens are rejected

---

### TEST-AUTH-020: Get Current User - Malformed Token

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.malformed
```

**Expected Response:**
- Status: `401 Unauthorized`

**Validation:**
- ✓ Response status is 401
- ✓ Malformed tokens are rejected gracefully

---

## Public Lead Submission Tests

### TEST-LEAD-PUB-001: Create Lead - Valid Data with PDF Resume

**Endpoint:** `POST /api/v1/leads`

**Content-Type:** `multipart/form-data`

**Test Data:**
```
first_name=John
last_name=Doe
email=john.doe@example.com
resume=<valid_pdf_file_under_5MB>
```

**Steps:**
1. Prepare valid PDF file (< 5MB)
2. Send POST request with form data
3. Verify successful creation
4. Check database for new record
5. Verify resume file stored on disk
6. Check email inbox for both confirmation and notification emails

**Expected Response:**
- Status: `201 Created`
- Body:
```json
{
  "id": "<uuid>",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "<uuid>_resume.pdf",
  "status": "PENDING",
  "created_at": "<timestamp>",
  "updated_at": "<timestamp>",
  "reached_out_at": null
}
```

**Validation:**
- ✓ Response status is 201
- ✓ Lead ID is valid UUID
- ✓ Status is "PENDING"
- ✓ Email is lowercase
- ✓ `reached_out_at` is null
- ✓ Resume file exists in uploads directory
- ✓ Confirmation email sent to john.doe@example.com
- ✓ Notification email sent to attorney email (from settings)

---

### TEST-LEAD-PUB-002: Create Lead - Valid Data with DOC Resume

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=Jane
last_name=Smith
email=jane.smith@example.com
resume=<valid_doc_file_under_5MB>
```

**Expected Response:**
- Status: `201 Created`
- Resume path ends with `.doc`

**Validation:**
- ✓ Response status is 201
- ✓ DOC files are accepted
- ✓ File stored correctly

---

### TEST-LEAD-PUB-003: Create Lead - Valid Data with DOCX Resume

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=Bob
last_name=Johnson
email=bob.johnson@example.com
resume=<valid_docx_file_under_5MB>
```

**Expected Response:**
- Status: `201 Created`
- Resume path ends with `.docx`

**Validation:**
- ✓ Response status is 201
- ✓ DOCX files are accepted
- ✓ File stored correctly

---

### TEST-LEAD-PUB-004: Create Lead - Duplicate Email

**Endpoint:** `POST /api/v1/leads`

**Steps:**
1. Create lead with TEST-LEAD-PUB-001 data first
2. Attempt to create another lead with same email
3. Verify rejection

**Test Data:**
```
first_name=John
last_name=Different
email=john.doe@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `400 Bad Request`
- Body:
```json
{
  "detail": "A lead with email john.doe@example.com already exists"
}
```

**Validation:**
- ✓ Response status is 400
- ✓ Error message identifies duplicate email
- ✓ Second lead NOT created in database
- ✓ No duplicate file stored

---

### TEST-LEAD-PUB-005: Create Lead - Missing First Name

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
last_name=Doe
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error identifies missing first_name field

---

### TEST-LEAD-PUB-006: Create Lead - Missing Last Name

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error identifies missing last_name field

---

### TEST-LEAD-PUB-007: Create Lead - Missing Email

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error identifies missing email field

---

### TEST-LEAD-PUB-008: Create Lead - Missing Resume

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error identifies missing resume file

---

### TEST-LEAD-PUB-009: Create Lead - Invalid Email Format

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=invalid-email
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates invalid email format

---

### TEST-LEAD-PUB-010: Create Lead - First Name Too Long

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=<string_over_100_characters>
last_name=Doe
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates maximum length exceeded

---

### TEST-LEAD-PUB-011: Create Lead - Last Name Too Long

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=<string_over_100_characters>
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates maximum length exceeded

---

### TEST-LEAD-PUB-012: Create Lead - Empty First Name

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=
last_name=Doe
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Error indicates field cannot be empty

---

### TEST-LEAD-PUB-013: Create Lead - Invalid File Type (TXT)

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com
resume=<txt_file>
```

**Expected Response:**
- Status: `415 Unsupported Media Type`
- Body:
```json
{
  "detail": "Invalid file type. Allowed types: pdf, doc, docx"
}
```

**Validation:**
- ✓ Response status is 415
- ✓ Error lists allowed file types
- ✓ File NOT stored on disk

---

### TEST-LEAD-PUB-014: Create Lead - Invalid File Type (JPG)

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com
resume=<jpg_image>
```

**Expected Response:**
- Status: `415 Unsupported Media Type`

**Validation:**
- ✓ Response status is 415
- ✓ Image files rejected

---

### TEST-LEAD-PUB-015: Create Lead - File Too Large (Over 5MB)

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com
resume=<pdf_file_over_5MB>
```

**Expected Response:**
- Status: `413 Payload Too Large`
- Body:
```json
{
  "detail": "File size exceeds maximum allowed size (5.00MB)"
}
```

**Validation:**
- ✓ Response status is 413
- ✓ Error indicates size limit
- ✓ File NOT stored on disk

---

### TEST-LEAD-PUB-016: Create Lead - File Exactly 5MB

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com
resume=<pdf_file_exactly_5MB>
```

**Expected Response:**
- Status: `201 Created`

**Validation:**
- ✓ Response status is 201
- ✓ Files at maximum size are accepted

---

### TEST-LEAD-PUB-017: Create Lead - Special Characters in Name

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=O'Brien
last_name=de Silva
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `201 Created`

**Validation:**
- ✓ Response status is 201
- ✓ Special characters handled correctly
- ✓ Names sanitized for XSS prevention

---

### TEST-LEAD-PUB-018: Create Lead - XSS Attempt in Name

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=<script>alert('xss')</script>
last_name=Doe
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `201 Created`
- First name in response should be sanitized (script tags removed)

**Validation:**
- ✓ Response status is 201
- ✓ Script tags removed from name
- ✓ Lead created with sanitized data

---

### TEST-LEAD-PUB-019: Create Lead - Email Case Insensitive

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=John.Doe@EXAMPLE.COM
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `201 Created`
- Email in response should be lowercase: `john.doe@example.com`

**Validation:**
- ✓ Response status is 201
- ✓ Email normalized to lowercase

---

### TEST-LEAD-PUB-020: Create Lead - Unicode Characters in Name

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=José
last_name=Müller
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Response:**
- Status: `201 Created`

**Validation:**
- ✓ Response status is 201
- ✓ Unicode characters preserved correctly

---

## Protected Lead Management Tests

### TEST-LEAD-PROT-001: Get All Leads - No Filters

**Endpoint:** `GET /api/v1/leads`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create multiple leads (TEST-LEAD-PUB-001 to TEST-LEAD-PUB-003)
2. Login to get token
3. Send GET request with token
4. Verify paginated response

**Expected Response:**
- Status: `200 OK`
- Body:
```json
{
  "items": [
    {
      "id": "<uuid>",
      "first_name": "Bob",
      "last_name": "Johnson",
      "email": "bob.johnson@example.com",
      "resume_path": "<uuid>_resume.docx",
      "status": "PENDING",
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>",
      "reached_out_at": null
    },
    {
      "id": "<uuid>",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "resume_path": "<uuid>_resume.doc",
      "status": "PENDING",
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>",
      "reached_out_at": null
    },
    {
      "id": "<uuid>",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "resume_path": "<uuid>_resume.pdf",
      "status": "PENDING",
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>",
      "reached_out_at": null
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

**Validation:**
- ✓ Response status is 200
- ✓ Items array contains all leads
- ✓ Total matches number of created leads
- ✓ Page is 1
- ✓ Leads sorted by created_at descending (newest first)

---

### TEST-LEAD-PROT-002: Get All Leads - Without Authentication

**Endpoint:** `GET /api/v1/leads`

**Headers:** None

**Expected Response:**
- Status: `401 Unauthorized`
- Body:
```json
{
  "detail": "Not authenticated"
}
```

**Validation:**
- ✓ Response status is 401
- ✓ Protected endpoint requires authentication

---

### TEST-LEAD-PROT-003: Get All Leads - With Pagination (Page 1)

**Endpoint:** `GET /api/v1/leads?page=1&page_size=2`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create 5 leads
2. Request page 1 with size 2

**Expected Response:**
- Status: `200 OK`
- Body includes 2 items
- `total` is 5
- `page` is 1
- `page_size` is 2
- `total_pages` is 3
- `has_next` is true
- `has_previous` is false

**Validation:**
- ✓ Correct number of items returned
- ✓ Pagination metadata accurate

---

### TEST-LEAD-PROT-004: Get All Leads - With Pagination (Page 2)

**Endpoint:** `GET /api/v1/leads?page=2&page_size=2`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `200 OK`
- Body includes 2 items (items 3-4)
- `page` is 2
- `has_next` is true
- `has_previous` is true

**Validation:**
- ✓ Middle page navigation works
- ✓ Different items than page 1

---

### TEST-LEAD-PROT-005: Get All Leads - With Pagination (Last Page)

**Endpoint:** `GET /api/v1/leads?page=3&page_size=2`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `200 OK`
- Body includes 1 item (last item)
- `page` is 3
- `has_next` is false
- `has_previous` is true

**Validation:**
- ✓ Last page returns remaining items
- ✓ `has_next` correctly false

---

### TEST-LEAD-PROT-006: Get All Leads - Invalid Page Number (0)

**Endpoint:** `GET /api/v1/leads?page=0&page_size=10`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Page numbers must be >= 1

---

### TEST-LEAD-PROT-007: Get All Leads - Invalid Page Size (0)

**Endpoint:** `GET /api/v1/leads?page=1&page_size=0`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Page size must be >= 1

---

### TEST-LEAD-PROT-008: Get All Leads - Page Size Too Large (Over 100)

**Endpoint:** `GET /api/v1/leads?page=1&page_size=150`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Maximum page size enforced

---

### TEST-LEAD-PROT-009: Get All Leads - Filter by Status PENDING

**Endpoint:** `GET /api/v1/leads?status=PENDING`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create 3 leads
2. Update 1 lead to REACHED_OUT status
3. Request leads with status=PENDING
4. Verify only PENDING leads returned

**Expected Response:**
- Status: `200 OK`
- All items have `status: "PENDING"`
- Total reflects only PENDING leads

**Validation:**
- ✓ Response status is 200
- ✓ All returned leads have PENDING status
- ✓ REACHED_OUT leads excluded

---

### TEST-LEAD-PROT-010: Get All Leads - Filter by Status REACHED_OUT

**Endpoint:** `GET /api/v1/leads?status=REACHED_OUT`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create 3 leads
2. Update 2 leads to REACHED_OUT status
3. Request leads with status=REACHED_OUT
4. Verify only REACHED_OUT leads returned

**Expected Response:**
- Status: `200 OK`
- All items have `status: "REACHED_OUT"`
- Total reflects only REACHED_OUT leads
- Items have `reached_out_at` timestamps

**Validation:**
- ✓ Response status is 200
- ✓ All returned leads have REACHED_OUT status
- ✓ PENDING leads excluded
- ✓ `reached_out_at` is not null

---

### TEST-LEAD-PROT-011: Get All Leads - Invalid Status Filter

**Endpoint:** `GET /api/v1/leads?status=INVALID`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Invalid enum values rejected

---

### TEST-LEAD-PROT-012: Get All Leads - Sort by created_at Descending

**Endpoint:** `GET /api/v1/leads?sort_by=created_at&sort_order=desc`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create 3 leads with delay between each
2. Request with descending sort
3. Verify newest lead is first

**Expected Response:**
- Status: `200 OK`
- Items sorted newest to oldest

**Validation:**
- ✓ Response status is 200
- ✓ First item is most recent
- ✓ Last item is oldest

---

### TEST-LEAD-PROT-013: Get All Leads - Sort by created_at Ascending

**Endpoint:** `GET /api/v1/leads?sort_by=created_at&sort_order=asc`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `200 OK`
- Items sorted oldest to newest

**Validation:**
- ✓ Response status is 200
- ✓ First item is oldest
- ✓ Last item is most recent

---

### TEST-LEAD-PROT-014: Get All Leads - Sort by updated_at Descending

**Endpoint:** `GET /api/v1/leads?sort_by=updated_at&sort_order=desc`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create 3 leads
2. Update one lead's status
3. Request sorted by updated_at descending
4. Verify updated lead is first

**Expected Response:**
- Status: `200 OK`
- Recently updated lead appears first

**Validation:**
- ✓ Response status is 200
- ✓ Sorting by updated_at works correctly

---

### TEST-LEAD-PROT-015: Get All Leads - Invalid Sort Field

**Endpoint:** `GET /api/v1/leads?sort_by=invalid_field`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `400 Bad Request`
- Body:
```json
{
  "detail": "Invalid sort field. Must be one of: created_at, updated_at"
}
```

**Validation:**
- ✓ Response status is 400
- ✓ Only valid sort fields accepted

---

### TEST-LEAD-PROT-016: Get All Leads - Invalid Sort Order

**Endpoint:** `GET /api/v1/leads?sort_by=created_at&sort_order=invalid`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `400 Bad Request`
- Body:
```json
{
  "detail": "Invalid sort order. Must be 'asc' or 'desc'"
}
```

**Validation:**
- ✓ Response status is 400
- ✓ Only asc/desc accepted

---

### TEST-LEAD-PROT-017: Get Lead by ID - Valid ID

**Endpoint:** `GET /api/v1/leads/{lead_id}`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create a lead (save ID)
2. Request lead by ID
3. Verify complete lead details returned

**Expected Response:**
- Status: `200 OK`
- Body:
```json
{
  "id": "<uuid>",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "<uuid>_resume.pdf",
  "status": "PENDING",
  "created_at": "<timestamp>",
  "updated_at": "<timestamp>",
  "reached_out_at": null
}
```

**Validation:**
- ✓ Response status is 200
- ✓ All fields present
- ✓ Data matches created lead

---

### TEST-LEAD-PROT-018: Get Lead by ID - Without Authentication

**Endpoint:** `GET /api/v1/leads/{lead_id}`

**Headers:** None

**Expected Response:**
- Status: `401 Unauthorized`

**Validation:**
- ✓ Response status is 401
- ✓ Authentication required

---

### TEST-LEAD-PROT-019: Get Lead by ID - Nonexistent ID

**Endpoint:** `GET /api/v1/leads/00000000-0000-0000-0000-000000000000`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `404 Not Found`
- Body:
```json
{
  "detail": "Lead with ID 00000000-0000-0000-0000-000000000000 not found"
}
```

**Validation:**
- ✓ Response status is 404
- ✓ Error message includes lead ID

---

### TEST-LEAD-PROT-020: Get Lead by ID - Invalid UUID Format

**Endpoint:** `GET /api/v1/leads/invalid-uuid`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Invalid UUID format rejected

---

### TEST-LEAD-PROT-021: Update Lead Status - PENDING to REACHED_OUT

**Endpoint:** `PATCH /api/v1/leads/{lead_id}`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Test Data:**
```json
{
  "status": "REACHED_OUT"
}
```

**Steps:**
1. Create a PENDING lead
2. Send PATCH request to update status
3. Verify status change and timestamp

**Expected Response:**
- Status: `200 OK`
- Body:
```json
{
  "id": "<uuid>",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "<uuid>_resume.pdf",
  "status": "REACHED_OUT",
  "created_at": "<timestamp>",
  "updated_at": "<new_timestamp>",
  "reached_out_at": "<new_timestamp>"
}
```

**Validation:**
- ✓ Response status is 200
- ✓ Status changed to REACHED_OUT
- ✓ `reached_out_at` timestamp set
- ✓ `updated_at` timestamp updated

---

### TEST-LEAD-PROT-022: Update Lead Status - REACHED_OUT to PENDING

**Endpoint:** `PATCH /api/v1/leads/{lead_id}`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Test Data:**
```json
{
  "status": "PENDING"
}
```

**Steps:**
1. Create a lead and update to REACHED_OUT
2. Send PATCH request to revert to PENDING
3. Verify status reverted

**Expected Response:**
- Status: `200 OK`
- Status changed to PENDING
- `reached_out_at` remains (historical record)

**Validation:**
- ✓ Response status is 200
- ✓ Status reverted to PENDING
- ✓ Reversal allowed (business rule)

---

### TEST-LEAD-PROT-023: Update Lead Status - Without Authentication

**Endpoint:** `PATCH /api/v1/leads/{lead_id}`

**Headers:** None

**Test Data:**
```json
{
  "status": "REACHED_OUT"
}
```

**Expected Response:**
- Status: `401 Unauthorized`

**Validation:**
- ✓ Response status is 401
- ✓ Authentication required for updates

---

### TEST-LEAD-PROT-024: Update Lead Status - Nonexistent Lead

**Endpoint:** `PATCH /api/v1/leads/00000000-0000-0000-0000-000000000000`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Test Data:**
```json
{
  "status": "REACHED_OUT"
}
```

**Expected Response:**
- Status: `404 Not Found`

**Validation:**
- ✓ Response status is 404
- ✓ Cannot update nonexistent lead

---

### TEST-LEAD-PROT-025: Update Lead Status - Invalid Status Value

**Endpoint:** `PATCH /api/v1/leads/{lead_id}`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Test Data:**
```json
{
  "status": "INVALID_STATUS"
}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Invalid enum values rejected

---

### TEST-LEAD-PROT-026: Update Lead Status - Missing Status Field

**Endpoint:** `PATCH /api/v1/leads/{lead_id}`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Test Data:**
```json
{}
```

**Expected Response:**
- Status: `422 Unprocessable Entity`

**Validation:**
- ✓ Response status is 422
- ✓ Status field required

---

### TEST-LEAD-PROT-027: Download Resume - Valid Lead

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create a lead with PDF resume
2. Send GET request to download resume
3. Verify file download

**Expected Response:**
- Status: `200 OK`
- Headers:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="John_Doe_resume.pdf"`
- Body: Binary file content

**Validation:**
- ✓ Response status is 200
- ✓ Content-Type header correct for file type
- ✓ Content-Disposition includes lead name
- ✓ File content matches uploaded file

---

### TEST-LEAD-PROT-028: Download Resume - DOC File

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create a lead with DOC resume
2. Download resume

**Expected Response:**
- Status: `200 OK`
- `Content-Type: application/msword`

**Validation:**
- ✓ Response status is 200
- ✓ Correct MIME type for DOC files

---

### TEST-LEAD-PROT-029: Download Resume - DOCX File

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create a lead with DOCX resume
2. Download resume

**Expected Response:**
- Status: `200 OK`
- `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`

**Validation:**
- ✓ Response status is 200
- ✓ Correct MIME type for DOCX files

---

### TEST-LEAD-PROT-030: Download Resume - Without Authentication

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`

**Headers:** None

**Expected Response:**
- Status: `401 Unauthorized`

**Validation:**
- ✓ Response status is 401
- ✓ Resume download requires authentication

---

### TEST-LEAD-PROT-031: Download Resume - Nonexistent Lead

**Endpoint:** `GET /api/v1/leads/00000000-0000-0000-0000-000000000000/resume`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Expected Response:**
- Status: `404 Not Found`

**Validation:**
- ✓ Response status is 404
- ✓ Cannot download from nonexistent lead

---

### TEST-LEAD-PROT-032: Download Resume - Missing File

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`

**Headers:**
```
Authorization: Bearer <valid_token>
```

**Steps:**
1. Create a lead
2. Manually delete resume file from disk
3. Attempt to download

**Expected Response:**
- Status: `404 Not Found`

**Validation:**
- ✓ Response status is 404
- ✓ Missing files handled gracefully

---

## Email Notification Tests

### TEST-EMAIL-001: Prospect Confirmation Email - Lead Creation

**Trigger:** Create lead via `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=john.doe@example.com
resume=<valid_pdf_file>
```

**Steps:**
1. Create lead
2. Check prospect's email inbox
3. Verify email received and content

**Expected Email:**
- **To:** john.doe@example.com
- **From:** SMTP_FROM_EMAIL (from settings)
- **Subject:** "Thank you for your submission" or similar
- **Body Contains:**
  - Prospect's name (John Doe)
  - Lead ID for reference
  - Confirmation of submission
  - Next steps information
  - Timeline expectations
  - Professional formatting

**Validation:**
- ✓ Email delivered to correct address
- ✓ Subject line appropriate
- ✓ Body is HTML formatted
- ✓ Prospect name personalized
- ✓ Lead ID included for reference
- ✓ No sensitive information exposed

---

### TEST-EMAIL-002: Attorney Notification Email - Lead Creation

**Trigger:** Create lead via `POST /api/v1/leads`

**Test Data:**
```
first_name=Jane
last_name=Smith
email=jane.smith@example.com
resume=<valid_pdf_file>
```

**Steps:**
1. Create lead
2. Check attorney's email inbox (ATTORNEY_EMAIL from settings)
3. Verify email received and content

**Expected Email:**
- **To:** ATTORNEY_EMAIL (from settings)
- **From:** SMTP_FROM_EMAIL (from settings)
- **Subject:** "New Lead Submission - Jane Smith" or similar
- **Body Contains:**
  - "NEW LEAD" badge or indicator
  - Prospect's full name (Jane Smith)
  - Prospect's email (clickable mailto link)
  - Resume filename
  - Lead ID
  - Current status (PENDING)
  - Link to dashboard (if configured)
  - Action required notice

**Validation:**
- ✓ Email delivered to attorney
- ✓ Subject includes prospect name
- ✓ Body is HTML formatted with alert styling
- ✓ All lead details included
- ✓ Email is actionable

---

### TEST-EMAIL-003: Email Failure - Invalid SMTP Configuration

**Trigger:** Create lead with invalid SMTP settings

**Steps:**
1. Temporarily misconfigure SMTP settings (wrong password)
2. Create lead
3. Verify lead still created despite email failure

**Expected Behavior:**
- Lead creation succeeds (201 Created)
- Error logged for email failure
- Lead record exists in database
- Resume file stored on disk

**Validation:**
- ✓ Lead creation not blocked by email failure
- ✓ System remains operational
- ✓ Error logged appropriately
- ✓ Graceful degradation

---

### TEST-EMAIL-004: Email Failure - Network Timeout

**Trigger:** Create lead with SMTP server unreachable

**Steps:**
1. Temporarily point SMTP_HOST to unreachable server
2. Create lead
3. Verify retry mechanism and eventual graceful failure

**Expected Behavior:**
- Lead creation succeeds
- Multiple retry attempts made (3 retries)
- Error logged after retries exhausted

**Validation:**
- ✓ Retry logic executed
- ✓ Lead creation not blocked
- ✓ Appropriate timeout handling

---

### TEST-EMAIL-005: Email Content - HTML Rendering

**Trigger:** Create lead and inspect email HTML

**Steps:**
1. Create lead
2. View email source code
3. Verify HTML structure

**Validation:**
- ✓ Valid HTML5 structure
- ✓ Responsive design with mobile support
- ✓ Professional styling (CSS inline)
- ✓ No broken layout
- ✓ Images (if any) load correctly

---

### TEST-EMAIL-006: Email Content - Special Characters in Name

**Trigger:** Create lead with special characters

**Test Data:**
```
first_name=José
last_name=O'Brien
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Behavior:**
- Email uses correct character encoding (UTF-8)
- Special characters display correctly
- No garbled text

**Validation:**
- ✓ UTF-8 encoding used
- ✓ Special characters render properly
- ✓ Name displayed correctly in both emails

---

### TEST-EMAIL-007: Email Content - XSS Prevention

**Trigger:** Create lead with potential XSS in name

**Test Data:**
```
first_name=<script>alert('xss')</script>
last_name=Doe
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Behavior:**
- Script tags sanitized before email
- Email displays safe content
- No script execution possible

**Validation:**
- ✓ Script tags removed or escaped
- ✓ Email safe to open
- ✓ No security vulnerability

---

## End-to-End Workflow Tests

### TEST-E2E-001: Complete Lead Submission to Management Flow

**Scenario:** Prospect submits lead → Attorney logs in → Views lead → Updates status → Downloads resume

**Steps:**

1. **Prospect Submits Lead**
   - POST `/api/v1/leads` with valid data
   - Verify 201 response
   - Save lead ID

2. **Verify Emails Sent**
   - Check prospect email inbox
   - Check attorney email inbox
   - Verify both emails received

3. **Attorney Registers**
   - POST `/api/v1/auth/register` with credentials
   - Verify 201 response

4. **Attorney Logs In**
   - POST `/api/v1/auth/login`
   - Verify 200 response
   - Save access token

5. **Attorney Views All Leads**
   - GET `/api/v1/leads` with token
   - Verify 200 response
   - Verify created lead in list

6. **Attorney Views Specific Lead**
   - GET `/api/v1/leads/{lead_id}` with token
   - Verify 200 response
   - Verify all lead details

7. **Attorney Downloads Resume**
   - GET `/api/v1/leads/{lead_id}/resume` with token
   - Verify 200 response
   - Verify file downloaded

8. **Attorney Updates Status**
   - PATCH `/api/v1/leads/{lead_id}` to REACHED_OUT
   - Verify 200 response
   - Verify status updated
   - Verify `reached_out_at` timestamp set

9. **Attorney Views Updated Lead**
   - GET `/api/v1/leads/{lead_id}` with token
   - Verify status is REACHED_OUT
   - Verify timestamp present

10. **Attorney Filters by Status**
    - GET `/api/v1/leads?status=REACHED_OUT` with token
    - Verify only REACHED_OUT leads returned

**Validation:**
- ✓ Complete workflow executes successfully
- ✓ All API calls return expected results
- ✓ Data consistency maintained throughout
- ✓ Emails delivered correctly

---

### TEST-E2E-002: Multiple Leads Management

**Scenario:** Create 10 leads, update 5 to REACHED_OUT, test filtering and pagination

**Steps:**

1. Create 10 leads with different data
2. Login as attorney
3. View all leads (verify count = 10)
4. Update 5 leads to REACHED_OUT
5. Filter by PENDING (verify count = 5)
6. Filter by REACHED_OUT (verify count = 5)
7. Test pagination with page_size=3
8. Verify all leads accessible across pages

**Validation:**
- ✓ All 10 leads created successfully
- ✓ Status updates work correctly
- ✓ Filtering returns correct results
- ✓ Pagination math correct

---

### TEST-E2E-003: Concurrent Lead Submissions

**Scenario:** Multiple prospects submit leads simultaneously

**Steps:**
1. Prepare 5 different lead submissions
2. Send all requests concurrently
3. Verify all succeed or fail appropriately
4. Check for race conditions

**Validation:**
- ✓ All valid submissions succeed
- ✓ Duplicate emails detected correctly
- ✓ No data corruption
- ✓ File storage handles concurrency

---

### TEST-E2E-004: Session Expiration Handling

**Scenario:** Token expires during session

**Steps:**
1. Login and get token
2. Use token successfully
3. Wait for token expiration (or modify expiry time)
4. Attempt to use expired token
5. Verify rejection
6. Login again and continue

**Validation:**
- ✓ Expired tokens rejected
- ✓ Clear error message
- ✓ Re-login works
- ✓ Session state managed correctly

---

### TEST-E2E-005: Error Recovery

**Scenario:** Test system behavior after errors

**Steps:**
1. Attempt invalid operations
2. Verify error handling
3. Attempt valid operations after errors
4. Verify system still functional

**Validation:**
- ✓ Errors don't corrupt state
- ✓ System recovers gracefully
- ✓ Valid operations work after errors

---

## API Documentation Tests

### TEST-DOC-001: Swagger UI Access

**Endpoint:** `GET /docs`

**Steps:**
1. Open http://localhost:8000/docs in browser
2. Verify Swagger UI loads
3. Check all endpoints listed

**Validation:**
- ✓ Page loads without errors
- ✓ All endpoints visible
- ✓ Authentication section present
- ✓ Models/schemas displayed
- ✓ Try it out functionality works

---

### TEST-DOC-002: ReDoc Access

**Endpoint:** `GET /redoc`

**Steps:**
1. Open http://localhost:8000/redoc in browser
2. Verify ReDoc interface loads
3. Check documentation completeness

**Validation:**
- ✓ Page loads without errors
- ✓ All endpoints documented
- ✓ Request/response examples present
- ✓ Navigation works

---

### TEST-DOC-003: OpenAPI JSON

**Endpoint:** `GET /openapi.json`

**Steps:**
1. Request OpenAPI spec
2. Verify valid JSON
3. Check completeness

**Validation:**
- ✓ Valid JSON format
- ✓ All endpoints documented
- ✓ Schemas defined
- ✓ Security schemes present

---

## Security Tests

### TEST-SEC-001: SQL Injection - Email Field

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com' OR '1'='1
resume=<valid_pdf_file>
```

**Expected Behavior:**
- Email validation rejects malformed email
- OR: Lead created with sanitized email
- No SQL injection executed

**Validation:**
- ✓ SQL injection prevented
- ✓ Database integrity maintained

---

### TEST-SEC-002: SQL Injection - Name Fields

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John'; DROP TABLE leads; --
last_name=Doe
email=test@example.com
resume=<valid_pdf_file>
```

**Expected Behavior:**
- Name sanitized
- Lead created with safe name
- No SQL injection executed

**Validation:**
- ✓ Injection attempt prevented
- ✓ Name sanitized correctly

---

### TEST-SEC-003: Path Traversal - File Download

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`

**Steps:**
1. Create lead
2. Attempt to access file with path traversal:
   - Manually construct request with `../../../etc/passwd` in path

**Expected Response:**
- Status: `400 Bad Request` or `404 Not Found`
- No system files accessed

**Validation:**
- ✓ Path traversal prevented
- ✓ Only allowed files accessible

---

### TEST-SEC-004: XSS - Script Tags in Name

**Covered in TEST-LEAD-PUB-018**

---

### TEST-SEC-005: Authorization - Access Other User's Resources

**Scenario:** User A tries to access User B's protected data

**Steps:**
1. Register User A and User B
2. User A logs in (get token)
3. User B logs in (get token)
4. User A attempts operations with User B's token

**Expected Behavior:**
- Operations work (both users can access all leads)
- Current design: all authenticated users see all leads

**Note:** Future implementation may add user-specific access control

**Validation:**
- ✓ Current behavior consistent with design
- ✓ Authentication required for all operations

---

### TEST-SEC-006: Brute Force - Login Attempts

**Endpoint:** `POST /api/v1/auth/login`

**Steps:**
1. Attempt login with wrong password 10 times rapidly
2. Check if rate limiting applies

**Expected Behavior:**
- All attempts processed (current: no rate limiting)
- Future: Rate limiting after N attempts

**Validation:**
- ✓ Bcrypt slows down attempts
- ✓ System remains stable under rapid requests

---

### TEST-SEC-007: Token Tampering

**Endpoint:** `GET /api/v1/auth/me`

**Steps:**
1. Get valid token
2. Modify token payload
3. Attempt to use tampered token

**Expected Response:**
- Status: `401 Unauthorized`
- Token signature validation fails

**Validation:**
- ✓ Tampered tokens rejected
- ✓ Signature verification works

---

### TEST-SEC-008: CORS - Cross-Origin Requests

**Scenario:** Request from unauthorized origin

**Steps:**
1. Send request with Origin header from non-allowed domain
2. Verify CORS headers in response

**Expected Behavior:**
- Request processed (CORS configured)
- Response includes appropriate CORS headers

**Validation:**
- ✓ CORS configuration active
- ✓ Allowed origins enforced

---

## Performance Tests

### TEST-PERF-001: Large File Upload

**Endpoint:** `POST /api/v1/leads`

**Test Data:**
```
first_name=John
last_name=Doe
email=test@example.com
resume=<4.9MB_pdf_file>
```

**Steps:**
1. Prepare file just under 5MB limit
2. Upload file
3. Measure response time

**Validation:**
- ✓ Upload completes within reasonable time (< 5 seconds)
- ✓ File stored correctly
- ✓ No timeout errors

---

### TEST-PERF-002: Pagination Performance

**Endpoint:** `GET /api/v1/leads?page=1&page_size=100`

**Steps:**
1. Create 1000 leads
2. Request page with maximum size (100)
3. Measure response time

**Validation:**
- ✓ Response time < 2 seconds
- ✓ All 100 items returned
- ✓ Pagination metadata correct

---

### TEST-PERF-003: Concurrent Requests

**Scenario:** 10 simultaneous read requests

**Steps:**
1. Create test data
2. Send 10 GET requests simultaneously
3. Verify all complete successfully

**Validation:**
- ✓ All requests succeed
- ✓ Response times reasonable
- ✓ No race conditions

---

## Regression Tests

### TEST-REG-001: Previously Fixed Bugs

**Scenario:** Verify past bug fixes remain fixed

**Test Cases:**
- Duplicate email detection
- File size validation
- Status transition logic
- Email encoding issues

**Validation:**
- ✓ All previously fixed bugs still fixed
- ✓ No regressions introduced

---

## Test Summary Template

**Test Session Information:**
- Date:
- Tester:
- Environment: (Local/Docker)
- Application Version:
- Database: (SQLite/PostgreSQL)

**Test Results:**
- Total Tests Executed:
- Passed:
- Failed:
- Blocked:
- Skipped:

**Failed Tests Details:**
- Test ID:
- Expected Result:
- Actual Result:
- Steps to Reproduce:
- Screenshots/Logs:

**Blocking Issues:**
- Issue Description:
- Impact:
- Workaround:

**Notes:**
- Additional observations
- Recommendations
- Areas needing attention

---

## Test Data Management

### Setup Test Data

**Script Location:** `scripts/seed_db.py`

**Run:**
```bash
make seed-db
```

**Creates:**
- Default admin user
- Sample leads (if configured)

### Cleanup Test Data

**Development:**
```bash
rm leads.db
make migrate-up
```

**Docker:**
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

---

## Test Tools

**cURL Examples:**
```bash
# Create lead
curl -X POST http://localhost:8000/api/v1/leads \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john@example.com" \
  -F "resume=@resume.pdf"

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=SecurePass123!"

# Get leads (authenticated)
curl http://localhost:8000/api/v1/leads \
  -H "Authorization: Bearer TOKEN_HERE"
```

**Postman Collection:**
- Import from `/docs/postman_collection.json` (if provided)
- Set environment variables for base URL and token

**HTTPie Examples:**
```bash
# Create lead
http -f POST localhost:8000/api/v1/leads \
  first_name=John last_name=Doe \
  email=john@example.com resume@resume.pdf

# Login
http -f POST localhost:8000/api/v1/auth/login \
  username=attorney1 password=SecurePass123!

# Get leads
http localhost:8000/api/v1/leads \
  Authorization:"Bearer TOKEN_HERE"
```

---

## Troubleshooting

**Issue: Server not responding**
- Check if server is running: `curl http://localhost:8000/health`
- Check logs: `docker-compose logs -f api` or local terminal
- Verify port not in use: `lsof -i :8000`

**Issue: Database errors**
- Verify migrations applied: `make migrate-current`
- Reset database: `rm leads.db && make migrate-up`
- Check database URL in `.env`

**Issue: Email not sending**
- Verify SMTP credentials in `.env`
- Test SMTP connection separately
- Check firewall/network settings
- Review application logs for SMTP errors

**Issue: File upload fails**
- Verify upload directory exists: `ls -la uploads/resumes/`
- Check file permissions: `chmod -R 755 uploads/`
- Verify file size under 5MB
- Check available disk space

**Issue: Authentication fails**
- Verify SECRET_KEY set in `.env`
- Check token not expired (24 hour default)
- Verify user exists and is active
- Check Authorization header format

---

**End of QA Testing Guide**
