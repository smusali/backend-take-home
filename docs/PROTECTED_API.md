# Protected API Endpoints Documentation

## Overview

Protected endpoints for the Attorney Dashboard require JWT authentication. These endpoints enable attorneys to view, manage, and update leads.

## Authentication

All endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

## Endpoints

### GET /api/v1/leads

Get paginated list of leads with filtering and sorting.

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 10, max: 100): Items per page
- `status` (optional): Filter by status (PENDING, REACHED_OUT)
- `sort_by` (optional, default: created_at): Sort field (created_at, updated_at)
- `sort_order` (optional, default: desc): Sort order (asc, desc)

**Response (200):**
```json
{
  "items": [
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
  ],
  "total": 25,
  "page": 1,
  "page_size": 10
}
```

---

### GET /api/v1/leads/{lead_id}

Get detailed information for a specific lead.

**Path Parameters:**
- `lead_id` (UUID): Lead identifier

**Response (200):** Lead object  
**Response (404):** Lead not found

---

### PATCH /api/v1/leads/{lead_id}

Update a lead's status.

**Path Parameters:**
- `lead_id` (UUID): Lead identifier

**Request Body:**
```json
{
  "status": "REACHED_OUT"
}
```

**Response (200):** Updated lead object  
**Response (400):** Invalid status transition  
**Response (404):** Lead not found

---

### GET /api/v1/leads/{lead_id}/resume

Download the resume file for a specific lead.

**Path Parameters:**
- `lead_id` (UUID): Lead identifier

**Response (200):** File download with appropriate content-type  
**Response (404):** Lead or file not found

**Headers:**
- `Content-Disposition`: attachment with formatted filename

---

## Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**400 Bad Request:**
```json
{
  "detail": "Inactive user"
}
```

**404 Not Found:**
```json
{
  "detail": "Lead with ID {uuid} not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to retrieve leads: {error}"
}
```

## Test Coverage

22 integration tests covering:
- ✅ Authentication requirements
- ✅ Pagination and filtering
- ✅ Sorting functionality
- ✅ CRUD operations
- ✅ Status validation
- ✅ File downloads
- ✅ Inactive user handling
- ✅ Error scenarios

## Related Documentation

- [Authentication](./AUTHENTICATION.md) - JWT token management
- [Lead Service](./LEAD_SERVICE.md) - Business logic
- [Public API](./PUBLIC_API.md) - Public endpoints
