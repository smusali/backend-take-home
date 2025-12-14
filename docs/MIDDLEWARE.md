# API Error Responses & Middleware Documentation

## Overview

The Lead Management API implements comprehensive error response standardization and request/response logging middleware for complete observability and consistent error handling.

## Standardized Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": {
    "message": "Lead with ID abc123 not found",
    "status_code": 404,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "details": {
      "field": "value"
    },
    "request_id": "req-uuid-123"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Human-readable error description |
| `status_code` | integer | HTTP status code |
| `timestamp` | string | ISO 8601 timestamp |
| `details` | object | Optional additional context |
| `request_id` | string | Request tracking ID |

## Request/Response Logging Middleware

### RequestLoggingMiddleware

Automatically logs all HTTP requests with timing and context.

**Features:**
- ✅ Request ID generation/tracking
- ✅ Request timing (duration in milliseconds)
- ✅ User identification (if authenticated)
- ✅ Method and path logging
- ✅ Status code tracking
- ✅ Error context on failures

**Example Log Output:**
```
2024-12-14 10:30:00 | INFO | POST /api/v1/leads | Status: 201 | Duration: 45.32ms | User: attorney1
```

### ErrorTrackingMiddleware

Tracks and logs application errors during request processing.

**Features:**
- ✅ Unhandled exception logging
- ✅ 4xx client error warnings
- ✅ 5xx server error alerts
- ✅ Full stack traces
- ✅ Error context preservation

**Example Log Output:**
```
2024-12-14 10:30:00 | ERROR | Unhandled exception | POST /api/v1/leads | Error: ValidationError: Invalid data
```

## Request ID Tracking

### What is a Request ID?

A unique identifier for each HTTP request used for:
- Distributed tracing across services
- Correlating logs for a single request
- Debugging issues with specific requests
- Performance monitoring

### How It Works

1. **Client Provides ID (Optional)**:
   ```bash
   curl -H "X-Request-ID: custom-req-123" http://localhost:8000/api/v1/leads
   ```

2. **Auto-Generated if Missing**:
   ```python
   # Middleware generates UUID if header not present
   request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
   ```

3. **Included in Response**:
   ```http
   HTTP/1.1 200 OK
   X-Request-ID: custom-req-123
   Content-Type: application/json
   ```

4. **Included in Error Responses**:
   ```json
   {
     "error": {
       "message": "Error message",
       "request_id": "custom-req-123"
     }
   }
   ```

5. **Logged Throughout Request**:
   ```
   Request started | ID: custom-req-123 | POST /api/v1/leads
   Lead created | ID: abc123 | Email: john@example.com
   Request completed | ID: custom-req-123 | Status: 201 | Duration: 45ms
   ```

## Middleware Stack

Middleware is applied in order from top to bottom:

```
Request Flow:
  1. RequestLoggingMiddleware  ← Logs request start, adds request ID
  2. ErrorTrackingMiddleware   ← Tracks errors and warnings
  3. CORSMiddleware            ← Handles CORS
  4. Exception Handlers        ← Formats errors
  5. API Router                ← Your endpoints
  
Response Flow:
  5. API Router                → Returns response
  4. Exception Handlers        → Catches exceptions
  3. CORSMiddleware            → Adds CORS headers
  2. ErrorTrackingMiddleware   → Logs error status codes
  1. RequestLoggingMiddleware  → Logs completion, adds request ID
```

## Error Response Examples

### Lead Not Found (404)
```json
{
  "error": {
    "message": "Lead with ID a1b2c3d4-... not found",
    "status_code": 404,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

### Duplicate Email (409)
```json
{
  "error": {
    "message": "A lead with email john@example.com already exists",
    "status_code": 409,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

### Validation Error (422)
```json
{
  "error": {
    "message": "Validation error",
    "status_code": 422,
    "timestamp": "2024-12-14T10:30:00.123456Z",
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

### Invalid Status Transition (400)
```json
{
  "error": {
    "message": "Invalid status transition from REACHED_OUT to PENDING. Status can only progress forward, not backward.",
    "status_code": 400,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

### Authentication Failed (401)
```json
{
  "error": {
    "message": "Could not validate credentials",
    "status_code": 401,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

### Internal Server Error (500)
```json
{
  "error": {
    "message": "An unexpected error occurred. Please try again later.",
    "status_code": 500,
    "timestamp": "2024-12-14T10:30:00.123456Z",
    "request_id": "req-12345"
  }
}
```

## Request Logging Examples

### Successful Request
```
2024-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | POST /api/v1/leads
2024-12-14 10:30:00 | INFO  | Lead created | ID: abc123 | Email: john@example.com
2024-12-14 10:30:00 | INFO  | POST /api/v1/leads | Status: 201 | Duration: 45.32ms | User: None
```

### Failed Request
```
2024-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | PATCH /api/v1/leads/abc123
2024-12-14 10:30:00 | ERROR | Request failed | ID: req-12345 | PATCH /api/v1/leads/abc123 | Duration: 12.45ms | Error: InvalidStatusTransitionException
2024-12-14 10:30:00 | ERROR | Error in PATCH /api/v1/leads/abc123 | InvalidStatusTransitionException: Invalid status transition...
```

### Authenticated Request
```
2024-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | GET /api/v1/leads
2024-12-14 10:30:00 | INFO  | Authentication SUCCESS | Username: attorney1 | IP: 192.168.1.100
2024-12-14 10:30:00 | INFO  | GET /api/v1/leads | Status: 200 | Duration: 23.45ms | User: attorney1
```

## Integration with Error Handling

### How It Works Together

1. **Request Arrives**
   - RequestLoggingMiddleware logs request start
   - Request ID generated/extracted

2. **Request Processing**
   - Endpoint logic executes
   - Services log business operations
   - Custom exceptions may be raised

3. **Exception Occurs**
   - Exception handler catches it
   - Formats error response with request ID
   - ErrorTrackingMiddleware logs the error

4. **Response Sent**
   - RequestLoggingMiddleware logs completion
   - Request ID included in response headers
   - Client receives consistent error format

### Example Flow

```python
# 1. Request arrives
POST /api/v1/leads

# 2. Middleware logs
DEBUG: Request started | ID: req-12345 | POST /api/v1/leads

# 3. Endpoint executes
async def create_lead(...):
    # 4. Service raises exception
    raise DuplicateLeadException(email="john@example.com")

# 5. Exception handler formats error
{
  "error": {
    "message": "A lead with email john@example.com already exists",
    "status_code": 409,
    "request_id": "req-12345"
  }
}

# 6. Middleware logs completion
ERROR: Request failed | ID: req-12345 | POST /api/v1/leads | Duration: 12ms
INFO: POST /api/v1/leads | Status: 409 | Duration: 12.45ms
```

## Configuration

### Middleware Order (Important!)

```python
# In app/main.py
app = FastAPI(...)

# 1. Request logging (outermost)
app.add_middleware(RequestLoggingMiddleware)

# 2. Error tracking
app.add_middleware(ErrorTrackingMiddleware)

# 3. CORS (after logging)
app.add_middleware(CORSMiddleware, ...)

# 4. Exception handlers
register_exception_handlers(app)
```

### Environment Variables

```env
# Enable/disable debug mode
DEBUG=True

# Set log level
LOG_LEVEL=INFO

# Environment name
ENVIRONMENT=development
```

## Best Practices

### For Developers

1. **Always Include Context**: Use f-strings with relevant IDs and details
2. **Use Request IDs**: Include in logs for correlation
3. **Log at Appropriate Levels**: DEBUG for development, INFO for production
4. **Don't Log Sensitive Data**: Never log passwords, tokens, or PII
5. **Include Duration**: Always log operation timing

### For Clients

1. **Generate Request IDs**: Send `X-Request-ID` header for tracking
2. **Check Response Headers**: Read `X-Request-ID` from responses
3. **Include in Bug Reports**: Provide request ID when reporting issues
4. **Monitor Status Codes**: Handle errors based on status code
5. **Parse Error Structure**: Use consistent error format

## Debugging with Request IDs

### Find All Logs for a Request

```bash
# Search logs for specific request ID
grep "req-12345" logs/app.log

# Example output:
2024-12-14 10:30:00 | DEBUG | Request started | ID: req-12345 | POST /api/v1/leads
2024-12-14 10:30:00 | INFO  | Lead created | ID: abc123 | Email: john@example.com
2024-12-14 10:30:00 | INFO  | POST /api/v1/leads | Status: 201 | Duration: 45ms
```

### Track Request Across Services

If using microservices, propagate request ID:

```python
# Service A calls Service B
response = await http_client.get(
    "http://service-b/api/endpoint",
    headers={"X-Request-ID": request.state.request_id}
)
```

## Performance Monitoring

### Key Metrics Logged

- **Request Duration**: Time from start to finish
- **Status Code Distribution**: Success vs error rates
- **Error Types**: Which exceptions occur most
- **Endpoint Performance**: Which endpoints are slowest

### Example Queries

```bash
# Find slow requests (>1000ms)
grep "Duration: [0-9]\{4,\}" logs/app.log

# Count errors by type
grep "ERROR" logs/errors.log | cut -d'|' -f5 | sort | uniq -c

# Find all 500 errors
grep "Status: 5[0-9][0-9]" logs/app.log
```

## Related Documentation

- [Exception Handling](./EXCEPTION_HANDLING.md) - Custom exceptions
- [Logging](./LOGGING.md) - Logging configuration
- [API Overview](./API_OVERVIEW.md) - Complete API reference
