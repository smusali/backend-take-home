# Middleware, Exception Handling, and Logging Documentation

**Version:** 1.0.0  
**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Middleware](#middleware)
3. [Exception Handling](#exception-handling)
4. [Logging](#logging)
5. [Integration](#integration)
6. [Best Practices](#best-practices)

---

## Overview

The Lead Management API implements a comprehensive middleware, exception handling, and logging system that provides:
- Request/response tracking with unique IDs
- Standardized error responses
- Structured logging with file rotation
- Complete observability and debugging capability

### System Architecture

```
┌─────────────────────────────────────────────┐
│         Client Request                      │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│    1. RequestLoggingMiddleware              │
│    - Generate/extract request ID            │
│    - Log request start                      │
│    - Track timing                           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│    2. ErrorTrackingMiddleware               │
│    - Track errors and warnings              │
│    - Log error context                      │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│    3. CORSMiddleware                        │
│    - Handle CORS headers                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│    4. Exception Handlers                    │
│    - Custom exceptions                      │
│    - Validation errors                      │
│    - HTTP exceptions                        │
│    - General exceptions                     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│    5. API Router & Endpoints                │
│    - Business logic                         │
│    - Service layer                          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         Client Response                     │
│    - Standardized format                    │
│    - Request ID in header                   │
│    - Logged with timing                     │
└─────────────────────────────────────────────┘
```

---

## Middleware

### RequestLoggingMiddleware

Automatically logs all HTTP requests with timing and context.

**Features:**
- Request ID generation/tracking
- Request timing (duration in milliseconds)
- User identification (if authenticated)
- Method and path logging
- Status code tracking
- Error context on failures

**Example Log Output:**
```
2025-12-14 10:30:00 | INFO | POST /api/v1/leads | Status: 201 | Duration: 45.32ms | User: attorney1
```

**Implementation:**
```python
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.debug(f"Request started | ID: {request_id} | {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log completion
            logger.info(
                f"{request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration_ms:.2f}ms | "
                f"User: {getattr(request.state, 'user', None)}"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed | ID: {request_id} | "
                f"{request.method} {request.url.path} | "
                f"Duration: {duration_ms:.2f}ms | "
                f"Error: {type(e).__name__}"
            )
            raise
```

### ErrorTrackingMiddleware

Tracks and logs application errors during request processing.

**Features:**
- Unhandled exception logging
- 4xx client error warnings
- 5xx server error alerts
- Full stack traces
- Error context preservation

**Example Log Output:**
```
2025-12-14 10:30:00 | ERROR | Unhandled exception | POST /api/v1/leads | Error: ValidationError: Invalid data
```

**Implementation:**
```python
class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            
            # Log client errors (4xx)
            if 400 <= response.status_code < 500:
                logger.warning(
                    f"Client error | {request.method} {request.url.path} | "
                    f"Status: {response.status_code}"
                )
            
            # Log server errors (5xx)
            elif response.status_code >= 500:
                logger.error(
                    f"Server error | {request.method} {request.url.path} | "
                    f"Status: {response.status_code}"
                )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Unhandled exception | {request.method} {request.url.path} | "
                f"Error: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            raise
```

### Request ID Tracking

#### What is a Request ID?

A unique identifier for each HTTP request used for:
- Distributed tracing across services
- Correlating logs for a single request
- Debugging issues with specific requests
- Performance monitoring

#### How It Works

**1. Client Provides ID (Optional):**
```bash
curl -H "X-Request-ID: custom-req-123" http://localhost:8000/api/v1/leads
```

**2. Auto-Generated if Missing:**
```python
# Middleware generates UUID if header not present
request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
```

**3. Included in Response:**
```http
HTTP/1.1 200 OK
X-Request-ID: custom-req-123
Content-Type: application/json
```

**4. Included in Error Responses:**
```json
{
  "error": {
    "message": "Error message",
    "request_id": "custom-req-123"
  }
}
```

**5. Logged Throughout Request:**
```
Request started | ID: custom-req-123 | POST /api/v1/leads
Lead created | ID: abc123 | Email: john@example.com
Request completed | ID: custom-req-123 | Status: 201 | Duration: 45ms
```

### Middleware Configuration

**Order Matters!** Middleware is applied in order from top to bottom:

```python
# In app/main.py
from app.utils.middleware import RequestLoggingMiddleware, ErrorTrackingMiddleware

app = FastAPI(...)

# 1. Request logging (outermost)
app.add_middleware(RequestLoggingMiddleware)

# 2. Error tracking
app.add_middleware(ErrorTrackingMiddleware)

# 3. CORS (after logging)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Exception Handling

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

### Base Exception

**`LeadManagementException`**

Base class for all custom exceptions with:
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

### Custom Exceptions

**LeadNotFoundException (404)**
```python
raise LeadNotFoundException(lead_id="uuid-here")
```

**DuplicateLeadException (409)**
```python
raise DuplicateLeadException(email="john@example.com")
```

**InvalidStatusTransitionException (400)**
```python
raise InvalidStatusTransitionException(
    from_status="REACHED_OUT",
    to_status="PENDING"
)
```

**FileUploadException (400/500)**
```python
raise FileUploadException(
    message="File size exceeds 5MB limit",
    status_code=400
)
```

**EmailSendException (500)**
```python
raise EmailSendException(
    recipient="user@example.com",
    reason="SMTP connection timeout"
)
```

**AuthenticationException (401)**
```python
raise AuthenticationException(message="Invalid credentials")
```

**UserNotFoundException (404)**
```python
raise UserNotFoundException(username="attorney1")
```

**DuplicateUserException (409)**
```python
raise DuplicateUserException(
    field="username",
    value="attorney1"
)
```

**InactiveUserException (403)**
```python
raise InactiveUserException(username="attorney1")
```

**ValidationException (422)**
```python
raise ValidationException(
    field="email",
    message="Invalid email format"
)
```

### Standardized Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": {
    "message": "Lead with ID abc123 not found",
    "status_code": 404,
    "timestamp": "2025-12-14T10:30:00.123456Z",
    "details": {
      "field": "value"
    },
    "request_id": "req-uuid-123"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Human-readable error description |
| `status_code` | integer | HTTP status code |
| `timestamp` | string | ISO 8601 timestamp |
| `details` | object | Optional additional context |
| `request_id` | string | Request tracking ID |

### Exception Handlers

**Custom Exception Handler:**

Handles all `LeadManagementException` subclasses:

```python
@app.exception_handler(LeadManagementException)
async def lead_management_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
                "timestamp": datetime.now(UTC).isoformat(),
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )
```

**Validation Exception Handler:**

Handles Pydantic validation errors:

```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "timestamp": "2025-12-14T10:30:00Z",
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

**HTTP Exception Handler:**

Handles standard FastAPI/Starlette HTTP exceptions:

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.detail,
            status_code=exc.status_code,
            request_id=getattr(request.state, "request_id", None)
        )
    )
```

**General Exception Handler:**

Catches all unhandled exceptions (500 errors):

```python
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "An unexpected error occurred. Please try again later.",
                "status_code": 500,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )
```

### HTTP Status Code Mapping

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

### Error Response Examples

**Lead Not Found (404):**
```json
{
  "error": {
    "message": "Lead with ID a1b2c3d4-... not found",
    "status_code": 404,
    "timestamp": "2025-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

**Duplicate Email (409):**
```json
{
  "error": {
    "message": "A lead with email john@example.com already exists",
    "status_code": 409,
    "timestamp": "2025-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

**Validation Error (422):**
```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "timestamp": "2025-12-14T10:30:00.123456Z",
    "details": {
      "validation_errors": [
        {
          "field": "body -> email",
          "message": "value is not a valid email address",
          "type": "value_error.email"
        }
      ]
    },
    "request_id": "req-12345"
  }
}
```

**Authentication Failed (401):**
```json
{
  "error": {
    "message": "Could not validate credentials",
    "status_code": 401,
    "timestamp": "2025-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

**Internal Server Error (500):**
```json
{
  "error": {
    "message": "An unexpected error occurred. Please try again later.",
    "status_code": 500,
    "timestamp": "2025-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

---

## Logging

### Features

✅ **Structured Logging** - Consistent format with timestamps and context  
✅ **Multiple Handlers** - Console, file, and error-only file handlers  
✅ **File Rotation** - Automatic log rotation (10MB max, 5 backups)  
✅ **Environment-Specific** - Different log levels per environment  
✅ **Utility Functions** - Pre-built functions for common log events  
✅ **Error Tracking** - Separate error log file with stack traces  
✅ **Third-Party Suppression** - Reduces noise from libraries in production

### Log Format

**Console Output (Simple):**
```
2025-12-14 10:30:00 | INFO     | Lead created | ID: abc123 | Email: john@example.com
```

**File Output (Detailed):**
```
2025-12-14 10:30:00 | INFO     | app.services.lead_service | lead_service.create_lead:45 | Lead created | ID: abc123 | Email: john@example.com
```

### Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| DEBUG | Detailed information | Development, troubleshooting |
| INFO | General informational | Normal operations, events |
| WARNING | Warning messages | Deprecated features, recoverable errors |
| ERROR | Error messages | Failures, exceptions |
| CRITICAL | Critical failures | System crashes, data corruption |

### Configuration

**Environment Variables:**

```env
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=development           # development, production, staging
DEBUG=True                        # Enable debug mode
```

**Log Levels by Environment:**

```python
# Development
LOG_LEVEL=DEBUG

# Staging
LOG_LEVEL=INFO

# Production
LOG_LEVEL=WARNING
```

### File Structure

```
backend-take-home/
├── logs/
│   ├── app.log          # All logs (rotated, 10MB, 5 backups)
│   ├── app.log.1        # Backup 1
│   ├── app.log.2        # Backup 2
│   ├── ...
│   ├── errors.log       # ERROR and CRITICAL only
│   ├── errors.log.1     # Error backup 1
│   └── errors.log.2     # Error backup 2
```

### Setup

**Initialize Logging:**

```python
from app.utils.logging_config import setup_logging

# In app/main.py
def create_application():
    # Initialize logging on startup
    setup_logging()
    
    app = FastAPI(...)
    return app
```

**Get Logger Instance:**

```python
from app.utils.logging_config import get_logger

# In any module
logger = get_logger(__name__)

logger.info("Application started")
logger.debug(f"Processing request for user {username}")
logger.error(f"Failed to process: {error}")
```

### Utility Functions

**Lead Operations:**

```python
from app.utils.logging_config import log_lead_creation, log_lead_status_update

# Log lead creation
log_lead_creation(
    logger=logger,
    lead_id="abc123",
    email="john@example.com"
)
# Output: Lead created | ID: abc123 | Email: john@example.com

# Log status update
log_lead_status_update(
    logger=logger,
    lead_id="abc123",
    old_status="PENDING",
    new_status="REACHED_OUT",
    user="attorney1"
)
# Output: Lead status updated | ID: abc123 | PENDING -> REACHED_OUT | User: attorney1
```

**Authentication:**

```python
from app.utils.logging_config import log_authentication_attempt

log_authentication_attempt(
    logger=logger,
    username="attorney1",
    success=True,
    ip_address="192.168.1.100"
)
# Output: Authentication SUCCESS | Username: attorney1 | IP: 192.168.1.100
```

**Email Operations:**

```python
from app.utils.logging_config import log_email_sent

log_email_sent(
    logger=logger,
    recipient="john@example.com",
    subject="Welcome to Lead Management",
    success=True
)
# Output: Email sent | To: john@example.com | Subject: Welcome to Lead Management
```

**File Operations:**

```python
from app.utils.logging_config import log_file_upload

log_file_upload(
    logger=logger,
    filename="resume.pdf",
    file_size=1048576,  # bytes
    lead_id="abc123"
)
# Output: File uploaded | Name: resume.pdf | Size: 1.00MB | Lead ID: abc123
```

**Error Logging:**

```python
from app.utils.logging_config import log_error

try:
    risky_operation()
except Exception as e:
    log_error(
        logger=logger,
        error=e,
        context="lead creation",
        include_stack=True
    )
# Output: Error in lead creation | ValueError: Invalid data
# (includes full stack trace)
```

**HTTP Requests:**

```python
from app.utils.logging_config import log_request

log_request(
    logger=logger,
    method="POST",
    path="/api/v1/leads",
    status_code=201,
    duration_ms=45.32,
    user="attorney1"
)
# Output: POST /api/v1/leads | Status: 201 | Duration: 45.32ms | User: attorney1
```

**Database Operations:**

```python
from app.utils.logging_config import log_database_operation

log_database_operation(
    logger=logger,
    operation="INSERT",
    table="leads",
    record_id="abc123",
    duration_ms=5.67
)
# Output: DB INSERT | Table: leads | ID: abc123 | Duration: 5.67ms
```

**Application Lifecycle:**

```python
from app.utils.logging_config import log_startup, log_shutdown

# On startup
log_startup(logger, environment="production", debug=False)
# Output:
# ======================================================================
# Lead Management API Starting
# Environment: production
# Debug Mode: False
# ======================================================================

# On shutdown
log_shutdown(logger)
# Output:
# ======================================================================
# Lead Management API Shutting Down
# ======================================================================
```

### Log Rotation

**Configuration:**

```python
# In app/utils/logging_config.py
RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=10 * 1024 * 1024,  # 10MB per file
    backupCount=5,               # Keep 5 backup files
    encoding="utf-8"
)
```

**Rotation Behavior:**
- Log file grows until it reaches 10MB
- When limit is reached:
  - `app.log` → `app.log.1`
  - `app.log.1` → `app.log.2`
  - ...
  - `app.log.4` → `app.log.5`
  - `app.log.5` is deleted
  - New `app.log` is created

**Total Storage:**
- Main log: 10MB
- Backups: 5 × 10MB = 50MB
- **Total: 60MB** per log type (app.log + errors.log = 120MB max)

---

## Integration

### Complete Request Flow

**1. Request Arrives:**
```
POST /api/v1/leads
X-Request-ID: req-12345
```

**2. Middleware Processing:**
```
DEBUG: Request started | ID: req-12345 | POST /api/v1/leads
```

**3. Endpoint Executes:**
```python
async def create_lead(...):
    # Business logic
    lead = lead_service.create_lead(data)
```

**4. Service Layer:**
```python
class LeadService:
    def create_lead(self, data):
        # May raise exceptions
        if self.repository.get_by_email(data.email):
            raise DuplicateLeadException(email=data.email)
        
        lead = self.repository.create(data)
        log_lead_creation(logger, lead.id, lead.email)
        return lead
```

**5. Exception Handling (if error occurs):**
```python
# Exception handler formats error
{
  "error": {
    "message": "A lead with email john@example.com already exists",
    "status_code": 409,
    "request_id": "req-12345"
  }
}
```

**6. Response Logging:**
```
INFO: POST /api/v1/leads | Status: 409 | Duration: 12.45ms | User: None
```

### Usage Examples

**In Services:**

```python
from app.utils.logging_config import get_logger, log_lead_creation, log_error
from app.utils.exceptions import DuplicateLeadException

class LeadService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
    
    async def create_lead(self, data: LeadCreate, resume: UploadFile):
        try:
            self.logger.info(f"Creating lead for {data.email}")
            
            # Check for duplicate
            existing = self.repository.get_by_email(data.email)
            if existing:
                raise DuplicateLeadException(email=data.email)
            
            # Create lead
            lead = self.repository.create(data)
            
            # Log successful creation
            log_lead_creation(
                self.logger,
                lead_id=str(lead.id),
                email=lead.email
            )
            
            return lead
            
        except Exception as e:
            log_error(
                self.logger,
                error=e,
                context="lead creation",
                include_stack=True
            )
            raise
```

**In Endpoints:**

```python
from app.utils.logging_config import get_logger
from app.utils.exceptions import LeadNotFoundException

logger = get_logger(__name__)

@router.get("/leads/{lead_id}")
async def get_lead(
    lead_id: UUID,
    db: Session = Depends(get_db)
):
    logger.debug(f"Fetching lead {lead_id}")
    
    lead = lead_service.get_lead(lead_id)
    if not lead:
        raise LeadNotFoundException(lead_id=str(lead_id))
    
    logger.info(f"Lead retrieved: {lead_id}")
    return lead
```

### Request Logging Examples

**Successful Request:**
```
2025-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | POST /api/v1/leads
2025-12-14 10:30:00 | INFO  | Lead created | ID: abc123 | Email: john@example.com
2025-12-14 10:30:00 | INFO  | POST /api/v1/leads | Status: 201 | Duration: 45.32ms | User: None
```

**Failed Request:**
```
2025-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | PATCH /api/v1/leads/abc123
2025-12-14 10:30:00 | ERROR | Request failed | ID: req-12345 | PATCH /api/v1/leads/abc123 | Duration: 12.45ms | Error: InvalidStatusTransitionException
2025-12-14 10:30:00 | ERROR | Error in PATCH /api/v1/leads/abc123 | InvalidStatusTransitionException: Invalid status transition...
```

**Authenticated Request:**
```
2025-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | GET /api/v1/leads
2025-12-14 10:30:00 | INFO  | Authentication SUCCESS | Username: attorney1 | IP: 192.168.1.100
2025-12-14 10:30:00 | INFO  | GET /api/v1/leads | Status: 200 | Duration: 23.45ms | User: attorney1
```

---

## Best Practices

### For Developers

**1. Always Include Context:**
```python
# ✅ Good
logger.info(f"Lead created | ID: {lead.id} | Email: {lead.email}")

# ❌ Bad
logger.info("Lead created")
```

**2. Use Appropriate Log Levels:**
```python
# DEBUG - Development/troubleshooting
logger.debug(f"Processing request for user {user_id}")

# INFO - Normal operations
logger.info(f"Lead status updated to {status}")

# WARNING - Recoverable issues
logger.warning(f"Rate limit approaching for user {user_id}")

# ERROR - Failures that need attention
logger.error(f"Failed to send email to {recipient}")

# CRITICAL - System failures
logger.critical(f"Database connection lost")
```

**3. Use Specific Exceptions:**
```python
# ✅ Good
raise LeadNotFoundException(lead_id=str(lead_id))

# ❌ Bad
raise Exception("Lead not found")
```

**4. Never Log Sensitive Data:**
```python
# ✅ Good
logger.info(f"User authenticated | Username: {username}")

# ❌ Bad
logger.debug(f"Password: {password}")  # Security risk!
logger.info(f"Token: {jwt_token}")     # Security risk!
```

**5. Include Request IDs:**
```python
# ✅ Good
logger.info(f"Request completed | ID: {request.state.request_id}")

# ❌ Bad (missing request ID)
logger.info("Request completed")
```

### For Clients

**1. Generate Request IDs:**
```bash
# Include X-Request-ID header
curl -H "X-Request-ID: custom-req-123" http://localhost:8000/api/v1/leads
```

**2. Check Response Headers:**
```python
response = requests.post(url, data=data)
request_id = response.headers.get("X-Request-ID")
print(f"Request ID: {request_id}")
```

**3. Include in Bug Reports:**
```
Bug Report:
Description: Failed to create lead
Request ID: req-12345
Timestamp: 2025-12-14T10:30:00Z
```

**4. Parse Error Structure:**
```python
if response.status_code >= 400:
    error = response.json()["error"]
    print(f"Error: {error['message']}")
    print(f"Request ID: {error['request_id']}")
```

### Debugging with Request IDs

**Find All Logs for a Request:**

```bash
# Search logs for specific request ID
grep "req-12345" logs/app.log

# Example output:
2025-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | POST /api/v1/leads
2025-12-14 10:30:00 | INFO  | Lead created | ID: abc123 | Email: john@example.com
2025-12-14 10:30:00 | INFO  | POST /api/v1/leads | Status: 201 | Duration: 45ms
```

**Track Request Across Services:**

If using microservices, propagate request ID:

```python
# Service A calls Service B
response = await http_client.get(
    "http://service-b/api/endpoint",
    headers={"X-Request-ID": request.state.request_id}
)
```

### Performance Monitoring

**Key Metrics Logged:**
- Request duration (time from start to finish)
- Status code distribution (success vs error rates)
- Error types (which exceptions occur most)
- Endpoint performance (which endpoints are slowest)

**Example Queries:**

```bash
# Find slow requests (>1000ms)
grep "Duration: [0-9]\{4,\}" logs/app.log

# Count errors by type
grep "ERROR" logs/errors.log | cut -d'|' -f5 | sort | uniq -c

# Find all 500 errors
grep "Status: 5[0-9][0-9]" logs/app.log
```

### Security Considerations

**What to Log:**
- ✅ User actions (login, logout, data access)
- ✅ System events (startup, shutdown, errors)
- ✅ Business operations (lead creation, status changes)
- ✅ Performance metrics (request duration, DB queries)

**What NOT to Log:**
- ❌ Passwords or password hashes
- ❌ JWT tokens or API keys
- ❌ Credit card numbers or SSNs
- ❌ Sensitive personal information
- ❌ Complete database records

---

## Related Documentation

- [API Documentation](./API.md) - Complete API reference
- [Services Documentation](./SERVICES.md) - Business logic layer
- [Database Documentation](./DATABASE.md) - Database models and repositories
- [Testing Documentation](./TESTING.md) - Exception testing strategies

---

**Middleware Version:** 1.0.0  
**Last Updated:** December 2025  
**Test Coverage:** Complete integration testing across all layers
