# Logging Configuration Documentation

## Overview

The Lead Management API implements a comprehensive logging system with structured logging, file rotation, environment-specific configuration, and utility functions for consistent logging across the application.

## Features

✅ **Structured Logging** - Consistent format with timestamps and context  
✅ **Multiple Handlers** - Console, file, and error-only file handlers  
✅ **File Rotation** - Automatic log rotation (10MB max, 5 backups)  
✅ **Environment-Specific** - Different log levels per environment  
✅ **Utility Functions** - Pre-built functions for common log events  
✅ **Error Tracking** - Separate error log file with stack traces  
✅ **Third-Party Suppression** - Reduces noise from libraries in production  

## Log Format

### Console Output (Simple)
```
2024-12-14 10:30:00 | INFO     | Lead created | ID: abc123 | Email: john@example.com
```

### File Output (Detailed)
```
2024-12-14 10:30:00 | INFO     | app.services.lead_service | lead_service.create_lead:45 | Lead created | ID: abc123 | Email: john@example.com
```

## Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| DEBUG | Detailed information | Development, troubleshooting |
| INFO | General informational | Normal operations, events |
| WARNING | Warning messages | Deprecated features, recoverable errors |
| ERROR | Error messages | Failures, exceptions |
| CRITICAL | Critical failures | System crashes, data corruption |

## Configuration

### Environment Variables

```env
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=development           # development, production, staging
DEBUG=True                        # Enable debug mode
```

### Log Levels by Environment

```python
# Development
LOG_LEVEL=DEBUG

# Staging
LOG_LEVEL=INFO

# Production
LOG_LEVEL=WARNING
```

## File Structure

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

## Setup

### Initialize Logging

```python
from app.utils.logging_config import setup_logging

# In app/main.py
def create_application():
    # Initialize logging on startup
    setup_logging()
    
    app = FastAPI(...)
    return app
```

### Get Logger Instance

```python
from app.utils.logging_config import get_logger

# In any module
logger = get_logger(__name__)

logger.info("Application started")
logger.debug(f"Processing request for user {username}")
logger.error(f"Failed to process: {error}")
```

## Utility Functions

### Lead Operations

#### Log Lead Creation
```python
from app.utils.logging_config import log_lead_creation

log_lead_creation(
    logger=logger,
    lead_id="abc123",
    email="john@example.com"
)
# Output: Lead created | ID: abc123 | Email: john@example.com
```

#### Log Status Update
```python
from app.utils.logging_config import log_lead_status_update

log_lead_status_update(
    logger=logger,
    lead_id="abc123",
    old_status="PENDING",
    new_status="REACHED_OUT",
    user="attorney1"
)
# Output: Lead status updated | ID: abc123 | PENDING -> REACHED_OUT | User: attorney1
```

### Authentication

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

### Email Operations

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

### File Operations

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

### Error Logging

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

### HTTP Requests

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

### Database Operations

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

### Application Lifecycle

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

## Usage Examples

### In Services

```python
from app.utils.logging_config import get_logger, log_lead_creation, log_error

class LeadService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
    
    async def create_lead(self, data: LeadCreate, resume: UploadFile):
        try:
            self.logger.info(f"Creating lead for {data.email}")
            
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

### In Endpoints

```python
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

@router.post("/leads")
async def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"Received lead submission from {email}")
    
    try:
        lead_service = LeadService(db)
        lead = await lead_service.create_lead(
            LeadCreate(first_name=first_name, last_name=last_name, email=email),
            resume
        )
        
        logger.info(f"Lead created successfully: {lead.id}")
        return lead
        
    except Exception as e:
        logger.error(f"Failed to create lead: {e}")
        raise
```

## Log Rotation

### Configuration

```python
# In app/utils/logging_config.py
RotatingFileHandler(
    filename="logs/app.log",
    maxBytes=10 * 1024 * 1024,  # 10MB per file
    backupCount=5,               # Keep 5 backup files
    encoding="utf-8"
)
```

### Rotation Behavior

- Log file grows until it reaches 10MB
- When limit is reached:
  - `app.log` → `app.log.1`
  - `app.log.1` → `app.log.2`
  - ...
  - `app.log.4` → `app.log.5`
  - `app.log.5` is deleted
  - New `app.log` is created

### Total Storage

- Main log: 10MB
- Backups: 5 × 10MB = 50MB
- **Total: 60MB** per log type (app.log + errors.log = 120MB max)

## Environment-Specific Configuration

### Development

```python
# More verbose logging
LOG_LEVEL=DEBUG

# All third-party logs visible
uvicorn, fastapi, sqlalchemy logs at DEBUG level
```

### Production

```python
# Less verbose logging
LOG_LEVEL=WARNING

# Suppressed third-party logs
uvicorn, fastapi, sqlalchemy logs at WARNING level
```

## Performance Considerations

### Best Practices

1. **Use Appropriate Levels**: DEBUG for development, INFO/WARNING for production
2. **Lazy Evaluation**: Use f-strings for efficiency
3. **Avoid Sensitive Data**: Never log passwords, tokens, or PII
4. **Structured Messages**: Use consistent format with key-value pairs
5. **Context-Rich Logs**: Include relevant IDs and metadata

### Example - Good vs Bad

❌ **Bad:**
```python
logger.info("User logged in")  # Missing context
logger.debug(f"Password: {password}")  # Security risk!
```

✅ **Good:**
```python
logger.info(f"User logged in | Username: {username} | IP: {ip}")
logger.debug("Authentication attempt validated")
```

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify `logs/` directory exists
3. Check file permissions
4. Ensure logging is initialized before use

### Excessive Log Size

1. Lower log level in production
2. Adjust `maxBytes` in RotatingFileHandler
3. Reduce `backupCount`
4. Implement log cleanup scripts

### Missing Stack Traces

```python
# Use exc_info=True for full stack traces
logger.error("Error occurred", exc_info=True)

# Or use the utility function
log_error(logger, error=e, include_stack=True)
```

## Monitoring Integration

### Log Aggregation

Logs are compatible with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **CloudWatch**
- **Datadog**
- **Grafana Loki**

### Example: Send to CloudWatch

```python
import watchtower

cloudwatch_handler = watchtower.CloudWatchLogHandler()
logger.addHandler(cloudwatch_handler)
```

## Security Considerations

### What to Log

✅ User actions (login, logout, data access)  
✅ System events (startup, shutdown, errors)  
✅ Business operations (lead creation, status changes)  
✅ Performance metrics (request duration, DB queries)  

### What NOT to Log

❌ Passwords or password hashes  
❌ JWT tokens or API keys  
❌ Credit card numbers or SSNs  
❌ Sensitive personal information  
❌ Complete database records  

## Related Documentation

- [Exception Handling](./EXCEPTION_HANDLING.md) - Error handling system
- [API Overview](./API_OVERVIEW.md) - API endpoints
- [Configuration](./ENVIRONMENT_SETUP.md) - Environment setup
