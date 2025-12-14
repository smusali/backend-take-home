# Lead Management API Documentation

**Version:** 1.0.0  
**Last Updated:** December 2025  
**Framework:** FastAPI 0.115.6  
**Python:** 3.13+

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Public Endpoints](#public-endpoints)
5. [Protected Endpoints](#protected-endpoints)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Testing](#testing)

---

## Overview

The Lead Management API is a production-ready FastAPI application for managing attorney lead submissions with resume uploads, email notifications, and JWT-based authentication. The API enables prospects to submit their information publicly while providing attorneys with secure access to manage leads through an authenticated dashboard.

### Key Features

- **Public Lead Submission**: Prospects can submit information with resume uploads
- **Email Notifications**: Automated emails to both prospects and attorneys
- **JWT Authentication**: Secure token-based authentication for attorneys
- **Lead Management**: View, filter, sort, and update lead statuses
- **Resume Downloads**: Secure access to uploaded resume files
- **Status Tracking**: Lead progression from PENDING to REACHED_OUT

### Base URL

```
http://localhost:8000/api/v1
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs (recommended)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Quick Start

### 1. Start the Server

```bash
cd backend-take-home
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Register an Attorney Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "attorney1",
    "email": "attorney@lawfirm.com",
    "password": "SecurePass123!"
  }'
```

### 3. Login to Get JWT Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=SecurePass123!"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. Submit a Lead (Public)

```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john.doe@example.com" \
  -F "resume=@resume.pdf"
```

### 5. Access Protected Endpoints

```bash
curl http://localhost:8000/api/v1/leads \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Authentication

### Overview

The API uses JWT (JSON Web Tokens) for authentication. Protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

```
1. Register User (optional)
   POST /api/v1/auth/register
   └─> Returns user profile

2. Login
   POST /api/v1/auth/login
   └─> Returns JWT token (valid for 24 hours)

3. Access Protected Resources
   Include header: Authorization: Bearer <token>
   └─> Access all /api/v1/leads/* endpoints

4. Token Refresh
   Login again to get a new token
```

### Authorization Header Format

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Authentication Endpoints

### POST /api/v1/auth/register

Register a new attorney user account.

**Request Body:**
```json
{
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "password": "SecurePassword123!"
}
```

**Validation Rules:**
- **Username**: 3-50 characters, alphanumeric and underscores only
- **Email**: Valid email format, must be unique
- **Password**: Minimum 8 characters with at least one uppercase, one lowercase, and one digit

**Response (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "is_active": true,
  "created_at": "2025-12-14T10:00:00Z"
}
```

**Error Responses:**
- `409 Conflict`: Username or email already exists
- `422 Unprocessable Entity`: Validation error (invalid format, missing fields)
- `500 Internal Server Error`: Server error during registration

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "attorney1",
    "email": "attorney@lawfirm.com",
    "password": "SecurePassword123!"
  }'
```

---

### POST /api/v1/auth/login

Authenticate and receive a JWT token.

**Request Body (OAuth2 Form):**
```
username=attorney1&password=SecurePassword123!
```

**Note**: Uses OAuth2 password flow (`application/x-www-form-urlencoded`) for OpenAPI compatibility.

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Details:**
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 24 hours (1440 minutes, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Claims**: `sub` (subject) contains user ID, additional claims include username

**Error Responses:**
- `401 Unauthorized`: Invalid username or password
- `500 Internal Server Error`: Server error during authentication

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=SecurePassword123!"
```

---

### GET /api/v1/auth/me

Get the current authenticated user's profile information.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "is_active": true,
  "created_at": "2025-12-14T10:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid, expired, or missing token
- `400 Bad Request`: User account is inactive

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Public Endpoints

These endpoints are publicly accessible without authentication.

### POST /api/v1/leads

Create a new lead submission with resume upload.

**URL:** `POST /api/v1/leads`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `first_name` (required): Prospect's first name (1-100 characters)
- `last_name` (required): Prospect's last name (1-100 characters)
- `email` (required): Prospect's email address (valid email format, unique)
- `resume` (required): Resume file (PDF, DOC, or DOCX, maximum 5MB)

**File Requirements:**
- **Allowed formats**: PDF (.pdf), Microsoft Word (.doc, .docx)
- **Maximum size**: 5MB (5,242,880 bytes)
- **Validation**: MIME type and file extension checked

**Response (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_resume.pdf",
  "status": "PENDING",
  "created_at": "2025-12-14T10:30:00Z",
  "updated_at": "2025-12-14T10:30:00Z",
  "reached_out_at": null
}
```

**Success Actions:**
- Lead record created in database with status `PENDING`
- Resume file stored securely with unique filename
- Confirmation email sent to prospect
- Notification email sent to attorney

**Error Responses:**

**400 Bad Request** - Duplicate email or invalid file:
```json
{
  "detail": "A lead with email john.doe@example.com already exists"
}
```

**413 Payload Too Large** - File exceeds size limit:
```json
{
  "detail": "File size exceeds maximum allowed size (5.00MB)"
}
```

**415 Unsupported Media Type** - Invalid file type:
```json
{
  "detail": "Invalid file type. Allowed types: pdf, doc, docx"
}
```

**422 Unprocessable Entity** - Validation error:
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

**500 Internal Server Error** - Server error:
```json
{
  "detail": "Failed to create lead: <error message>"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/leads" \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john.doe@example.com" \
  -F "resume=@/path/to/resume.pdf"
```

---

## Protected Endpoints

All protected endpoints require JWT authentication via the Authorization header.

### GET /api/v1/leads

Get a paginated list of leads with optional filtering and sorting.

**Authentication:** Required (JWT Token)

**Query Parameters:**
- `page` (optional, default: 1): Page number (minimum: 1)
- `size` (optional, default: 50, maximum: 100): Items per page
- `status` (optional): Filter by lead status (`PENDING` or `REACHED_OUT`)
- `sort_by` (optional, default: `created_at`): Sort field (`created_at` or `updated_at`)
- `sort_desc` (optional, default: `true`): Sort in descending order

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "resume_path": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_resume.pdf",
      "status": "PENDING",
      "created_at": "2025-12-14T10:00:00Z",
      "updated_at": "2025-12-14T10:00:00Z",
      "reached_out_at": null
    }
  ],
  "total": 42,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid, expired, or missing token
- `422 Unprocessable Entity`: Invalid query parameters

**Example:**
```bash
curl "http://localhost:8000/api/v1/leads?page=1&size=10&status=PENDING&sort_by=created_at&sort_desc=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### GET /api/v1/leads/{lead_id}

Get detailed information for a specific lead.

**Authentication:** Required (JWT Token)

**Path Parameters:**
- `lead_id` (required): Lead UUID identifier

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_resume.pdf",
  "status": "PENDING",
  "created_at": "2025-12-14T10:00:00Z",
  "updated_at": "2025-12-14T10:00:00Z",
  "reached_out_at": null
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid, expired, or missing token
- `404 Not Found`: Lead with specified ID does not exist
- `422 Unprocessable Entity`: Invalid UUID format

**Example:**
```bash
curl "http://localhost:8000/api/v1/leads/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### PATCH /api/v1/leads/{lead_id}

Update a lead's status.

**Authentication:** Required (JWT Token)

**Path Parameters:**
- `lead_id` (required): Lead UUID identifier

**Request Body:**
```json
{
  "status": "REACHED_OUT"
}
```

**Valid Status Values:**
- `PENDING`: Initial state when lead is submitted
- `REACHED_OUT`: Attorney has contacted the prospect

**Status Transitions:**
- ✅ `PENDING` → `REACHED_OUT` (valid)
- ✅ `REACHED_OUT` → `PENDING` (valid - allows reverting)

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_resume.pdf",
  "status": "REACHED_OUT",
  "created_at": "2025-12-14T10:00:00Z",
  "updated_at": "2025-12-14T11:00:00Z",
  "reached_out_at": "2025-12-14T11:00:00Z"
}
```

**Note**: When transitioning to `REACHED_OUT`, the `reached_out_at` timestamp is automatically set.

**Error Responses:**
- `400 Bad Request`: Invalid status transition (currently all transitions are valid)
- `401 Unauthorized`: Invalid, expired, or missing token
- `404 Not Found`: Lead with specified ID does not exist
- `422 Unprocessable Entity`: Invalid request body or UUID format

**Example:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/leads/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"status": "REACHED_OUT"}'
```

---

### GET /api/v1/leads/{lead_id}/resume

Download the resume file for a specific lead.

**Authentication:** Required (JWT Token)

**Path Parameters:**
- `lead_id` (required): Lead UUID identifier

**Response (200 OK):**
- **Content-Type**: `application/pdf`, `application/msword`, or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition**: `attachment; filename="uuid_resume.pdf"`
- **Body**: Binary file content

**Error Responses:**
- `401 Unauthorized`: Invalid, expired, or missing token
- `404 Not Found`: Lead or resume file does not exist
- `500 Internal Server Error`: File read error

**Example:**
```bash
curl "http://localhost:8000/api/v1/leads/a1b2c3d4-e5f6-7890-abcd-ef1234567890/resume" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -o resume.pdf
```

---

## Utility Endpoints

### GET /health

Health check endpoint for monitoring and load balancers.

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

## Data Models

### Lead

Represents a prospect's submission.

```json
{
  "id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "email": "string (email format)",
  "resume_path": "string",
  "status": "PENDING | REACHED_OUT",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)",
  "reached_out_at": "string (ISO 8601 datetime) | null"
}
```

**Field Descriptions:**
- `id`: Unique identifier (UUID v4)
- `first_name`: Prospect's first name (1-100 characters)
- `last_name`: Prospect's last name (1-100 characters)
- `email`: Prospect's email address (unique across all leads)
- `resume_path`: Relative path to stored resume file
- `status`: Current lead status (enum: PENDING, REACHED_OUT)
- `created_at`: Timestamp when lead was created
- `updated_at`: Timestamp of last update
- `reached_out_at`: Timestamp when status changed to REACHED_OUT (null if PENDING)

---

### User

Represents an attorney user account.

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string (email format)",
  "is_active": "boolean",
  "created_at": "string (ISO 8601 datetime)"
}
```

**Field Descriptions:**
- `id`: Unique identifier (UUID v4)
- `username`: Username for login (3-50 characters, alphanumeric and underscores)
- `email`: User's email address (unique)
- `is_active`: Account active status (inactive users cannot authenticate)
- `created_at`: Account creation timestamp

---

### Token

JWT authentication token response.

```json
{
  "access_token": "string (JWT token)",
  "token_type": "bearer"
}
```

**Field Descriptions:**
- `access_token`: JWT token string for authorization
- `token_type`: Always "bearer" (OAuth2 bearer token type)

---

### Paginated Response

Generic pagination wrapper for list endpoints.

```json
{
  "items": ["array of items"],
  "total": "integer",
  "page": "integer",
  "size": "integer",
  "pages": "integer"
}
```

**Field Descriptions:**
- `items`: Array of results for current page
- `total`: Total number of items across all pages
- `page`: Current page number (1-indexed)
- `size`: Number of items per page
- `pages`: Total number of pages

---

## Error Handling

### Standard Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), the response includes detailed field-level information:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request (business logic error) |
| 401 | Unauthorized | Missing or invalid authentication |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists (duplicate) |
| 413 | Payload Too Large | File size exceeds limit |
| 415 | Unsupported Media Type | Invalid file type |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Unexpected server error |

### Common Error Messages

**Authentication Errors:**
- `"Not authenticated"` - Missing or invalid token
- `"Could not validate credentials"` - Token validation failed
- `"Inactive user"` - User account is deactivated
- `"Incorrect username or password"` - Invalid login credentials

**Lead Errors:**
- `"A lead with email {email} already exists"` - Duplicate email submission
- `"Lead with ID {id} not found"` - Invalid or non-existent lead ID
- `"Invalid status transition from {current} to {new}"` - Business rule violation

**File Errors:**
- `"File size exceeds maximum allowed size (5.00MB)"` - File too large
- `"Invalid file type. Allowed types: pdf, doc, docx"` - Unsupported file format
- `"File not found"` - Resume file missing from storage

**Validation Errors:**
- `"value is not a valid email address"` - Invalid email format
- `"ensure this value has at least 8 characters"` - Password too short
- `"field required"` - Missing required field

---

## Examples

### Complete Workflow Example

This example demonstrates the complete workflow from registration to lead management.

#### 1. Register Attorney Account

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "attorney1",
    "email": "attorney@lawfirm.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "is_active": true,
  "created_at": "2025-12-14T10:00:00Z"
}
```

#### 2. Login to Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=SecurePass123!"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ1c2VybmFtZSI6ImF0dG9ybmV5MSIsImV4cCI6MTYzNDIxNzYwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "token_type": "bearer"
}
```

#### 3. Prospect Submits Lead

```bash
curl -X POST "http://localhost:8000/api/v1/leads" \
  -F "first_name=Sarah" \
  -F "last_name=Johnson" \
  -F "email=sarah.johnson@example.com" \
  -F "resume=@sarah_resume.pdf"
```

**Response:**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah.johnson@example.com",
  "resume_path": "7c9e6679-7425-40de-944b-e07fc1f90ae7_sarah_resume.pdf",
  "status": "PENDING",
  "created_at": "2025-12-14T10:30:00Z",
  "updated_at": "2025-12-14T10:30:00Z",
  "reached_out_at": null
}
```

#### 4. Attorney Lists Pending Leads

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl "http://localhost:8000/api/v1/leads?status=PENDING&page=1&size=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "items": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "first_name": "Sarah",
      "last_name": "Johnson",
      "email": "sarah.johnson@example.com",
      "resume_path": "7c9e6679-7425-40de-944b-e07fc1f90ae7_sarah_resume.pdf",
      "status": "PENDING",
      "created_at": "2025-12-14T10:30:00Z",
      "updated_at": "2025-12-14T10:30:00Z",
      "reached_out_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

#### 5. Attorney Downloads Resume

```bash
curl "http://localhost:8000/api/v1/leads/7c9e6679-7425-40de-944b-e07fc1f90ae7/resume" \
  -H "Authorization: Bearer $TOKEN" \
  -o sarah_resume.pdf
```

#### 6. Attorney Updates Lead Status

```bash
curl -X PATCH "http://localhost:8000/api/v1/leads/7c9e6679-7425-40de-944b-e07fc1f90ae7" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "REACHED_OUT"}'
```

**Response:**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah.johnson@example.com",
  "resume_path": "7c9e6679-7425-40de-944b-e07fc1f90ae7_sarah_resume.pdf",
  "status": "REACHED_OUT",
  "created_at": "2025-12-14T10:30:00Z",
  "updated_at": "2025-12-14T11:00:00Z",
  "reached_out_at": "2025-12-14T11:00:00Z"
}
```

---

## Testing

### Interactive API Testing

The easiest way to test the API is through the Swagger UI:

1. Start the server: `uvicorn app.main:app --reload`
2. Open http://localhost:8000/docs
3. Click "Authorize" button
4. Login to get a token
5. Test any endpoint interactively

### Automated Test Suite

The project includes comprehensive test coverage:

**Test Statistics:**
- **Total Tests**: 220+ tests
- **Unit Tests**: 131 tests (models, schemas, services, utilities)
- **Integration Tests**: 73 tests (API endpoints)
- **End-to-End Tests**: 16 tests (complete workflows)
- **Code Coverage**: >95%

**Run Tests:**
```bash
# All tests
make test

# Specific test suites
make unit-test           # Unit tests only
make integration-test    # Integration tests only
make e2e-test           # End-to-end tests only

# With coverage report
make test-coverage
```

### Test Coverage by Component

**Public API** (17 tests):
- ✅ Successful lead creation
- ✅ Duplicate email rejection
- ✅ Invalid file type handling
- ✅ Missing required fields
- ✅ Email format validation
- ✅ File size limits
- ✅ Various file formats (PDF, DOC, DOCX)

**Authentication API** (29 tests):
- ✅ User registration validation
- ✅ Login with valid/invalid credentials
- ✅ Token generation and validation
- ✅ Expired token handling
- ✅ Malformed token handling
- ✅ Current user profile retrieval

**Protected API** (31 tests):
- ✅ Authentication requirements
- ✅ Pagination functionality
- ✅ Status filtering
- ✅ Sorting (ascending/descending)
- ✅ Lead CRUD operations
- ✅ Status transition validation
- ✅ Resume file downloads
- ✅ Inactive user handling

**End-to-End** (16 tests):
- ✅ Complete lead submission workflow
- ✅ Complete lead management workflow
- ✅ Email notification testing
- ✅ File storage verification
- ✅ Status transition flows

---

## Configuration

### Environment Variables

The API requires the following environment variables:

```env
# Database Configuration
DATABASE_URL=sqlite:///./leads.db

# Security Configuration
SECRET_KEY=your-secret-key-minimum-32-characters-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMTP Configuration (for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Lead Management System
ATTORNEY_EMAIL=attorney@yourdomain.com

# File Upload Configuration
UPLOAD_DIR=./uploads/resumes
MAX_FILE_SIZE=5242880

# Application Configuration
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Important Security Notes:**
- Use a strong `SECRET_KEY` (minimum 32 characters) for production
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Set `DEBUG=False` in production
- Restrict `CORS_ORIGINS` to your actual frontend domain(s)

### Setup Instructions

1. **Create virtual environment:**
   ```bash
   make venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Configure environment:**
   ```bash
   make env  # Creates .env from .env.example
   # Edit .env with your actual values
   ```

4. **Run database migrations:**
   ```bash
   make migrate-up
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## API Versioning

### Current Version: v1

All endpoints are prefixed with `/api/v1` for version control:

```
/api/v1/leads          ✓ Current version
/api/v2/leads          Future version (when needed)
```

**Versioning Strategy:**
- URL-based versioning for clarity
- Multiple versions can coexist
- Backward compatibility maintained
- Deprecation notices provided before removal
- Version support policy: N-1 (current + previous version)

---

## Rate Limiting

**Current Status**: Not implemented

**Production Recommendations**:
- Public endpoints: 100 requests/hour per IP address
- Authentication endpoints: 10 login attempts/hour per IP address
- Protected endpoints: 1000 requests/hour per authenticated user
- Use middleware like `slowapi` for implementation

---

## Security Features

### Implemented Security Measures

**Authentication & Authorization:**
- JWT token-based authentication
- bcrypt password hashing with automatic salt
- Token expiration (24 hours default)
- Active user validation

**Input Validation:**
- Pydantic schema validation for all inputs
- Email format validation
- File type and size validation
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention through input sanitization

**File Upload Security:**
- Allowed file types: PDF, DOC, DOCX only
- Maximum file size enforcement (5MB)
- Unique filename generation (UUID-based)
- MIME type validation
- Secure file storage outside web root

**API Security:**
- CORS configuration for cross-origin requests
- Secure password requirements
- Request/response logging
- Error message sanitization (no sensitive data exposure)

---

## Support & Resources

### Documentation

- **This API Documentation**: Complete endpoint reference
- **System Design** (`DESIGN.md`): Architecture and design decisions
- **Testing Guide** (`TESTING.md`): Test strategy and coverage
- **README** (`README.md`): Project setup and overview

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs (recommended for testing)
- **ReDoc**: http://localhost:8000/redoc (better for reading)

### Troubleshooting

1. **Check the interactive documentation** at `/docs` for request/response examples
2. **Review error messages** in API responses for specific issues
3. **Check application logs** for detailed error information
4. **Verify environment configuration** in `.env` file
5. **Run health check** at `/health` to verify server status

### Common Issues

**Authentication Failed:**
- Ensure token is not expired (24-hour lifetime)
- Verify `Authorization: Bearer <token>` header format
- Check user account is active

**File Upload Failed:**
- Verify file format is PDF, DOC, or DOCX
- Check file size is under 5MB
- Ensure filename contains valid characters

**Email Not Sending:**
- Verify SMTP credentials in `.env`
- For Gmail, use App Password
- Check firewall/network settings

---

**API Version:** 1.0.0  
**Framework:** FastAPI 0.115.6  
**Python:** 3.13+  
**Last Updated:** December 2025

---

*For questions, issues, or contributions, please refer to the project README and other documentation files.*
