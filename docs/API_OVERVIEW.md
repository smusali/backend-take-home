# Complete API Reference

## Overview

Lead Management API - A production-ready FastAPI application for managing attorney lead submissions with resume uploads, email notifications, and JWT authentication.

**Base URL:** `http://localhost:8000/api/v1`

## Quick Start

### 1. Start the Server
```bash
cd backend-take-home
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Test the API

**Submit a Lead (Public):**
```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john@example.com" \
  -F "resume=@resume.pdf"
```

**Register Attorney:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"attorney1","email":"attorney@law.com","password":"SecurePass123!"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=SecurePass123!"
```

**Get Leads (Protected):**
```bash
curl http://localhost:8000/api/v1/leads \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## API Endpoints

### Public Endpoints

#### Submit Lead
```http
POST /api/v1/leads
Content-Type: multipart/form-data
```

**Parameters:**
- `first_name` (required): Prospect's first name
- `last_name` (required): Prospect's last name
- `email` (required): Valid email address
- `resume` (required): PDF/DOC/DOCX file (max 5MB)

**Response:** Lead object with status `PENDING`

---

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json
```

**Body:**
```json
{
  "username": "attorney1",
  "email": "attorney@law.com",
  "password": "SecurePass123!"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Body:**
```
username=attorney1&password=SecurePass123!
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

---

### Protected Endpoints (Require JWT)

#### List Leads
```http
GET /api/v1/leads?page=1&page_size=10&status=PENDING&sort_by=created_at&sort_order=desc
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)
- `status` (optional): Filter by PENDING or REACHED_OUT
- `sort_by` (optional): created_at or updated_at
- `sort_order` (optional): asc or desc

#### Get Lead by ID
```http
GET /api/v1/leads/{lead_id}
Authorization: Bearer {token}
```

#### Update Lead Status
```http
PATCH /api/v1/leads/{lead_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "status": "REACHED_OUT"
}
```

#### Download Resume
```http
GET /api/v1/leads/{lead_id}/resume
Authorization: Bearer {token}
```

**Response:** File download

---

### Utility Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error, invalid transition) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found |
| 409 | Conflict (duplicate email/username) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

## Data Models

### Lead
```json
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "resume_path": "uuid_resume.pdf",
  "status": "PENDING",
  "created_at": "2024-12-14T10:00:00Z",
  "updated_at": "2024-12-14T10:00:00Z",
  "reached_out_at": null
}
```

### User
```json
{
  "id": "uuid",
  "username": "attorney1",
  "email": "attorney@law.com",
  "is_active": true,
  "created_at": "2024-12-14T10:00:00Z"
}
```

### Token
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Lead Status Flow

```
PENDING → REACHED_OUT
   ↓          ↓
(Cannot go back)
```

**Status Transitions:**
- ✅ PENDING → REACHED_OUT (valid)
- ❌ REACHED_OUT → PENDING (invalid)

## Authentication Flow

```
1. Register: POST /api/v1/auth/register
   └─> Creates user account

2. Login: POST /api/v1/auth/login
   └─> Returns JWT token

3. Access Protected Routes
   └─> Include: Authorization: Bearer {token}

4. Token expires after 30 minutes (configurable)
```

## Error Responses

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Errors:**
- `"Not authenticated"` - Missing or invalid token
- `"Inactive user"` - User account is deactivated
- `"Lead with email {email} already exists"` - Duplicate submission
- `"Invalid status transition"` - Cannot revert status
- `"Lead with ID {id} not found"` - Invalid lead ID

## File Upload

**Supported Formats:**
- PDF (.pdf)
- Microsoft Word (.doc, .docx)

**Size Limit:** 5MB (configurable)

**Storage:** Local filesystem in `uploads/` directory

**Filename Format:** `{uuid}_{original_name}.{ext}`

## Email Notifications

**Prospect Confirmation:**
- Sent automatically when lead is submitted
- Includes lead ID and company information

**Attorney Notification:**
- Sent to configured attorney email
- Includes prospect details and resume link

## Environment Configuration

Required environment variables:

```env
# Database
DATABASE_URL=sqlite:///./leads.db

# JWT
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@company.com
SMTP_FROM_NAME=Lead Management

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Application
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

## Rate Limiting

Currently not implemented. Consider adding for production:
- Public endpoints: 100 requests/hour per IP
- Auth endpoints: 10 login attempts/hour per IP
- Protected endpoints: 1000 requests/hour per user

## Testing

### Run All Tests
```bash
make unittest
```

### Test Coverage
- Unit Tests: 229 tests
- Integration Tests: 39 tests
- **Total:** 268+ tests

## Documentation Files

- [System Design](./DESIGN.md) - Architecture and design decisions
- [API Router](./API_ROUTER.md) - Routing configuration
- [Public API](./PUBLIC_API.md) - Public lead submission
- [Protected API](./PROTECTED_API.md) - Attorney dashboard
- [Auth API](./AUTH_API.md) - Authentication endpoints
- [Database](./DATABASE_CONNECTION.md) - Database setup
- [Services](./LEAD_SERVICE.md) - Business logic

## Support

For issues or questions:
1. Check the interactive documentation at `/docs`
2. Review error messages in API responses
3. Check application logs
4. Consult the detailed documentation files

---

**API Version:** 1.0.0  
**Last Updated:** December 2024  
**Framework:** FastAPI 0.115.6  
**Python:** 3.13+
