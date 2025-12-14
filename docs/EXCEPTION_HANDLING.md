# Exception Handling Documentation

## Overview

The Lead Management API implements a comprehensive exception handling system with custom exceptions, centralized error handling, and standardized error responses.

## Architecture

### Exception Hierarchy

```
Exception (Python built-in)
└── LeadManagementException (Base custom exception)
    ├── LeadNotFoundException (404)
    ├── DuplicateLeadException (409)
    ├── InvalidStatusTransitionException (400)
    ├── FileUploadException (400/500)
    ├── EmailSendException (500)
    ├── AuthenticationException (401)
    ├── UserNotFoundException (404)
    ├── DuplicateUserException (409)
    ├── InactiveUserException (403)
    └── ValidationException (422)
```

## Custom Exceptions

### Base Exception

**`LeadManagementException`**

Base class for all custom exceptions. Includes:
- Error message
- HTTP status code
- Optional details dictionary

```python
raise LeadManagementException(
    message="Something went wrong",
    status_code=500,
    details={"context": "additional info"}
)
```

### Domain-Specific Exceptions

#### LeadNotFoundException
```python
# HTTP 404 - Lead not found
raise LeadNotFoundException(lead_id="uuid-here")
```

#### DuplicateLeadException
```python
# HTTP 409 - Email already exists
raise DuplicateLeadException(email="john@example.com")
```

#### InvalidStatusTransitionException
```python
# HTTP 400 - Invalid status change
raise InvalidStatusTransitionException(
    from_status="REACHED_OUT",
    to_status="PENDING"
)
```

#### FileUploadException
```python
# HTTP 400/500 - File upload error
raise FileUploadException(
    message="File size exceeds 5MB limit",
    status_code=400
)
```

#### EmailSendException
```python
# HTTP 500 - Email sending failed
raise EmailSendException(
    recipient="user@example.com",
    reason="SMTP connection timeout"
)
```

#### AuthenticationException
```python
# HTTP 401 - Authentication failed
raise AuthenticationException(message="Invalid credentials")
```

#### UserNotFoundException
```python
# HTTP 404 - User not found
raise UserNotFoundException(username="attorney1")
```

#### DuplicateUserException
```python
# HTTP 409 - User already exists
raise DuplicateUserException(
    field="username",
    value="attorney1"
)
```

#### InactiveUserException
```python
# HTTP 403 - Inactive user
raise InactiveUserException(username="attorney1")
```

#### ValidationException
```python
# HTTP 422 - Validation error
raise ValidationException(
    field="email",
    message="Invalid email format"
)
```

## Error Response Format

All errors return a standardized JSON structure:

```json
{
  "error": {
    "message": "Lead with ID abc123 not found",
    "status_code": 404,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "details": {
      "additional": "context"
    },
    "request_id": "req-uuid-123"
  }
}
```

### Response Fields

- **message**: Human-readable error description
- **status_code**: HTTP status code
- **timestamp**: ISO 8601 timestamp when error occurred
- **details** (optional): Additional context about the error
- **request_id** (optional): Request tracking ID from `X-Request-ID` header

## Exception Handlers

### Custom Exception Handler

Handles all `LeadManagementException` subclasses:

```python
@app.exception_handler(LeadManagementException)
async def lead_management_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(...)
    )
```

### Validation Exception Handler

Handles Pydantic validation errors:

```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "timestamp": "2024-12-14T10:30:00Z",
    "details": {
      "validation_errors": [
        {
          "field": "body -> email",
          "message": "value is not a valid email address",
          "type": "value_error.email"
        }
      ]
    }
  }
}
```

### HTTP Exception Handler

Handles standard FastAPI/Starlette HTTP exceptions:

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(...)
    )
```

### General Exception Handler

Catches all unhandled exceptions (500 errors):

```python
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Logs full error but returns generic message to client
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "An unexpected error occurred",
                "status_code": 500
            }
        }
    )
```

## Usage Examples

### In Services

```python
from app.utils.exceptions import (
    LeadNotFoundException,
    DuplicateLeadException
)

class LeadService:
    def get_lead(self, lead_id: UUID):
        lead = self.repository.get(lead_id)
        if not lead:
            raise LeadNotFoundException(lead_id=str(lead_id))
        return lead
    
    def create_lead(self, data: LeadCreate):
        existing = self.repository.get_by_email(data.email)
        if existing:
            raise DuplicateLeadException(email=data.email)
        return self.repository.create(data)
```

### In Endpoints

```python
from app.utils.exceptions import InvalidStatusTransitionException

@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: UUID, update: LeadUpdate):
    # Exceptions are automatically caught and formatted
    lead = lead_service.get_lead(lead_id)  # May raise LeadNotFoundException
    
    if not is_valid_transition(lead.status, update.status):
        raise InvalidStatusTransitionException(
            from_status=lead.status,
            to_status=update.status
        )
    
    return lead_service.update(lead_id, update)
```

## HTTP Status Code Mapping

| Status Code | Exception Type | Description |
|-------------|---------------|-------------|
| 400 | InvalidStatusTransitionException | Bad request - invalid state change |
| 400 | FileUploadException | Bad request - file validation failed |
| 401 | AuthenticationException | Unauthorized - invalid credentials |
| 403 | InactiveUserException | Forbidden - user is inactive |
| 404 | LeadNotFoundException | Not found - lead doesn't exist |
| 404 | UserNotFoundException | Not found - user doesn't exist |
| 409 | DuplicateLeadException | Conflict - lead email already exists |
| 409 | DuplicateUserException | Conflict - username/email taken |
| 422 | ValidationException | Unprocessable - validation failed |
| 422 | RequestValidationError | Unprocessable - Pydantic validation |
| 500 | EmailSendException | Server error - email failed to send |
| 500 | FileUploadException | Server error - file storage failed |
| 500 | Exception | Server error - unexpected error |

## Integration with FastAPI

Exception handlers are automatically registered during application startup:

```python
# app/main.py
from app.utils.exception_handlers import register_exception_handlers

def create_application() -> FastAPI:
    app = FastAPI(...)
    
    # Register all exception handlers
    register_exception_handlers(app)
    
    return app
```

## Request Tracking

Include `X-Request-ID` header for request tracking:

```bash
curl -H "X-Request-ID: req-12345" http://localhost:8000/api/v1/leads
```

The request ID will be included in error responses for easier debugging.

## Best Practices

1. **Use Specific Exceptions**: Raise the most specific exception type available
2. **Include Context**: Use the `details` parameter for additional error context
3. **Don't Expose Secrets**: Never include sensitive data in error messages
4. **Log Full Errors**: While clients see generic messages, full errors are logged
5. **Consistent Messaging**: Use clear, actionable error messages
6. **Status Code Accuracy**: Use appropriate HTTP status codes for each error type

## Error Handling Flow

```
1. Exception raised in service/endpoint
   └─> Custom exception with status code + message

2. FastAPI catches exception
   └─> Routed to appropriate handler

3. Handler creates standardized response
   └─> JSON with error details + timestamp

4. Response sent to client
   └─> Appropriate HTTP status code

5. Error logged (if configured)
   └─> Full stack trace for debugging
```

## Testing Exception Handling

```python
import pytest
from app.utils.exceptions import LeadNotFoundException

def test_lead_not_found_exception():
    with pytest.raises(LeadNotFoundException) as exc_info:
        raise LeadNotFoundException(lead_id="test-123")
    
    assert exc_info.value.status_code == 404
    assert "test-123" in exc_info.value.message
```

## Future Enhancements

- **Error Codes**: Add unique error codes for programmatic error handling
- **Localization**: Support multiple languages for error messages
- **Error Analytics**: Track error frequency and patterns
- **Retry Logic**: Suggest retry strategies for transient errors
- **Documentation Links**: Include links to relevant documentation

## Related Documentation

- [API Overview](./API_OVERVIEW.md) - Complete API reference
- [Logging](./LOGGING.md) - Error logging configuration
- [Testing](./TESTING.md) - Exception testing strategies
