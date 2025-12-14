# Public API Endpoints Documentation

## Overview

Public endpoints allow prospects to submit lead applications without authentication. These endpoints handle multipart form data with file uploads and integrate the complete lead creation workflow.

## Endpoint: POST /api/v1/leads

Create a new lead submission with resume upload.

### Request

**URL:** `POST /api/v1/leads`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `first_name` (required): Prospect's first name (1-100 chars)
- `last_name` (required): Prospect's last name (1-100 chars)  
- `email` (required): Prospect's email address (valid email format)
- `resume` (required): Resume file (PDF, DOC, or DOCX, max 5MB)

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/leads" \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john.doe@example.com" \
  -F "resume=@/path/to/resume.pdf"
```

### Response

**Success (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "uuid_resume.pdf",
  "status": "PENDING",
  "created_at": "2024-12-14T10:30:00Z",
  "updated_at": "2024-12-14T10:30:00Z",
  "reached_out_at": null
}
```

**Errors:**

- **400 Bad Request**: Duplicate email or invalid file
```json
{
  "detail": "A lead with email john@example.com already exists"
}
```

- **422 Unprocessable Entity**: Validation error (missing fields, invalid format)
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

- **500 Internal Server Error**: Server error (file storage, database, or email failure)
```json
{
  "detail": "Failed to create lead: <error message>"
}
```

## Test Coverage

**17 integration tests** covering:
- ✅ Successful lead creation
- ✅ Duplicate email rejection
- ✅ Invalid file handling
- ✅ Missing required fields
- ✅ Email format validation
- ✅ Field length validation
- ✅ Various file types (PDF, DOC, DOCX)
- ✅ Health check endpoint
- ✅ OpenAPI documentation

## Related Documentation

- [Lead Service](./LEAD_SERVICE.md) - Business logic
- [File Storage](./FILE_STORAGE.md) - Resume handling
- [Email Service](./EMAIL_SERVICE.md) - Notifications
