# Lead Management API

A production-ready FastAPI application for managing attorney lead submissions with resume uploads, email notifications, and authenticated lead management dashboard.

## Features

### Public Features
- **Lead Submission Form**: Public endpoint for prospects to submit their information
- **Resume Upload**: Secure file upload with validation (PDF, DOC, DOCX, max 5MB)
- **Email Notifications**: Automatic confirmation emails to prospects and notification emails to attorneys
- **Input Validation**: Comprehensive validation for names, emails, and file uploads

### Protected Features (Attorney Dashboard)
- **Lead Management**: View, filter, and update lead statuses
- **Status Tracking**: Lead status transitions from PENDING to REACHED_OUT
- **Resume Download**: Secure access to uploaded resume files
- **Pagination & Filtering**: Efficient lead browsing with pagination and status filtering
- **JWT Authentication**: Secure token-based authentication for attorneys

## Technology Stack

- **Framework**: FastAPI 0.115.6 (async web framework with automatic API documentation)
- **ORM**: SQLAlchemy 2.0.36 (database abstraction layer)
- **Migrations**: Alembic 1.14.0 (database schema versioning)
- **Validation**: Pydantic 2.10.6 (data validation and settings management)
- **Authentication**: JWT tokens with python-jose and bcrypt password hashing
- **Email**: aiosmtplib 3.0.2 (async SMTP client)
- **Testing**: pytest with httpx (async test client)
- **Server**: uvicorn 0.34.0 (ASGI server)

## Prerequisites

### Option 1: Local Development
- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- SMTP server access for email notifications (Gmail, SendGrid, etc.)

### Option 2: Docker Deployment (Recommended)
- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- At least 2GB of available RAM
- SMTP server access for email notifications

## Quick Start

### Option 1: Docker Deployment (Recommended)

Docker provides a complete, isolated environment with PostgreSQL database and all dependencies.

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd backend-take-home
```

#### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration (REQUIRED: SECRET_KEY, SMTP settings)
```

#### 3. Start Services

```bash
docker-compose up -d
```

#### 4. Initialize Database

```bash
docker-compose exec api alembic upgrade head
```

#### 5. Seed Initial Data

```bash
docker-compose exec api python scripts/seed_db.py
```

This creates an initial admin user. Default credentials will be printed to the console.

#### 6. Access the Application

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

For detailed Docker documentation, see [docs/DOCKER.md](docs/DOCKER.md).

### Option 2: Local Development

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd backend-take-home
```

#### 2. Set Up Virtual Environment

```bash
make venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
make install
```

#### 4. Configure Environment Variables

```bash
make env
```

This creates a `.env` file from `.env.example`. Edit the `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./leads.db

# Security Configuration
# Generate a secure SECRET_KEY with:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=<your-generated-secure-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMTP Configuration (Required for email notifications)
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
- **SECRET_KEY is REQUIRED**: Generate a secure key (minimum 32 characters) using:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  # or
  openssl rand -hex 32
  ```
- The application will **fail to start** with insecure default values
- Use environment-specific SMTP credentials
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)

#### 5. Initialize Database

```bash
make migrate-up
```

This runs Alembic migrations to create the database schema with `leads` and `users` tables.

#### 6. Seed Initial Data

```bash
make seed-db
```

This creates an initial admin user for accessing the attorney dashboard. Default credentials will be printed to the console.

#### 7. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
backend-take-home/
├── app/                          # Main application code
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API endpoints
│   │   └── v1/                   # API version 1
│   │       ├── api.py            # API router configuration
│   │       └── endpoints/        # Endpoint modules
│   │           ├── auth.py       # Authentication endpoints
│   │           ├── leads.py      # Protected lead management endpoints
│   │           └── public.py     # Public lead submission endpoint
│   ├── core/                     # Core configuration
│   │   ├── config.py             # Settings and environment variables
│   │   └── security.py           # JWT and password hashing utilities
│   ├── db/                       # Database layer
│   │   ├── base.py               # SQLAlchemy base and model imports
│   │   ├── database.py           # Database connection and session management
│   │   └── repositories/         # Repository pattern implementation
│   │       ├── base.py           # Generic CRUD repository
│   │       ├── lead_repository.py    # Lead-specific queries
│   │       └── user_repository.py    # User-specific queries
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── lead.py               # Lead model
│   │   └── user.py               # User model
│   ├── schemas/                  # Pydantic schemas for validation
│   │   ├── enums.py              # Enum definitions (LeadStatus)
│   │   ├── lead.py               # Lead request/response schemas
│   │   ├── user.py               # User and token schemas
│   │   └── validators.py         # Custom validation functions
│   ├── services/                 # Business logic layer
│   │   ├── auth_service.py       # Authentication and user management
│   │   ├── email_service.py      # Email notification service
│   │   ├── file_service.py       # File upload and storage service
│   │   └── lead_service.py       # Lead management business logic
│   ├── templates/                # Email templates (Jinja2)
│   │   ├── attorney_notification.html
│   │   └── prospect_confirmation.html
│   └── utils/                    # Utility modules
│       ├── exception_handlers.py # Global exception handlers
│       ├── exceptions.py         # Custom exception classes
│       ├── logging_config.py     # Logging configuration
│       └── middleware.py         # Request logging and error tracking
├── tests/                        # Test suite
│   ├── conftest.py               # Test fixtures and configuration
│   ├── unit/                     # Unit tests (131 tests)
│   ├── integration/              # Integration tests (73 tests)
│   └── e2e/                      # End-to-end tests (16 tests)
├── scripts/                      # Database seeding and management scripts
│   ├── seed_db.py                # Create initial admin user
│   ├── create_user.py            # Create additional attorney users
│   └── README.md                 # Scripts documentation
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration scripts
│   └── env.py                    # Alembic environment configuration
├── docs/                         # Documentation
├── .env.example                  # Environment variable template
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── Makefile                      # Development automation commands
├── alembic.ini                   # Alembic configuration
└── pytest.ini                    # Pytest configuration
```

## API Documentation

### Public Endpoints (No Authentication Required)

#### Submit Lead
```http
POST /api/v1/leads
Content-Type: multipart/form-data

Parameters:
- first_name: string (required, 1-100 chars)
- last_name: string (required, 1-100 chars)
- email: string (required, valid email)
- resume: file (required, PDF/DOC/DOCX, max 5MB)

Response: 201 Created
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "status": "PENDING",
  "created_at": "2025-12-14T10:30:00Z"
}
```

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "attorney1",
  "email": "attorney@example.com",
  "password": "SecurePassword123!"
}

Response: 201 Created
{
  "message": "User registered successfully",
  "username": "attorney1"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=attorney1&password=SecurePassword123!

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>

Response: 200 OK
{
  "id": "uuid",
  "username": "attorney1",
  "email": "attorney@example.com",
  "is_active": true
}
```

### Protected Endpoints (Authentication Required)

All protected endpoints require an `Authorization: Bearer <token>` header.

#### List Leads
```http
GET /api/v1/leads?page=1&size=10&status=PENDING&sort_by=created_at&sort_desc=true
Authorization: Bearer <token>

Response: 200 OK
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

#### Get Lead Details
```http
GET /api/v1/leads/{lead_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_path": "path/to/resume.pdf",
  "status": "PENDING",
  "created_at": "2025-12-14T10:30:00Z",
  "updated_at": "2025-12-14T10:30:00Z",
  "reached_out_at": null
}
```

#### Update Lead Status
```http
PATCH /api/v1/leads/{lead_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "REACHED_OUT"
}

Response: 200 OK
{
  "id": "uuid",
  "status": "REACHED_OUT",
  "reached_out_at": "2025-12-14T11:00:00Z"
}
```

#### Download Resume
```http
GET /api/v1/leads/{lead_id}/resume
Authorization: Bearer <token>

Response: 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="resume.pdf"

<binary file content>
```

For complete API documentation with interactive examples, visit http://localhost:8000/docs after starting the application.

## Database Schema

### Leads Table
- `id`: UUID (primary key)
- `first_name`: String (required)
- `last_name`: String (required)
- `email`: String (unique, required, indexed)
- `resume_path`: String (required)
- `status`: Enum [PENDING, REACHED_OUT] (indexed)
- `created_at`: DateTime (indexed)
- `updated_at`: DateTime
- `reached_out_at`: DateTime (nullable)

### Users Table
- `id`: UUID (primary key)
- `username`: String (unique, required)
- `email`: String (unique, required)
- `hashed_password`: String (required)
- `is_active`: Boolean (default: true)
- `created_at`: DateTime

## Testing

The project includes comprehensive test coverage with 220 tests across unit, integration, and end-to-end testing.

### Run All Tests
```bash
make test
```

### Run Specific Test Suites
```bash
make unit-test          # Run unit tests only (131 tests)
make integration-test   # Run integration tests only (73 tests)
make e2e-test          # Run end-to-end tests only (16 tests)
```

### Test Coverage Report
```bash
make test-coverage
```

This generates:
- Terminal output with coverage percentages
- HTML report at `htmlcov/index.html`

**Current Test Coverage:**
- **Unit Tests**: 131 tests covering models, schemas, services, and utilities
- **Integration Tests**: 73 tests covering all API endpoints
- **E2E Tests**: 16 tests covering complete user workflows
- **Total Coverage**: >95% code coverage

### Test Structure

```
tests/
├── unit/
│   ├── test_models.py      # Database model tests
│   ├── test_schemas.py     # Validation schema tests
│   ├── test_services.py    # Business logic tests
│   └── test_utils.py       # Utility function tests
├── integration/
│   ├── test_api_auth.py       # Authentication endpoint tests
│   ├── test_api_protected.py  # Protected endpoint tests
│   └── test_api_public.py     # Public endpoint tests
└── e2e/
    └── test_lead_workflow.py  # Complete workflow tests
```

## Database Migrations

### View Migration Status
```bash
make migrate-current    # Show current migration version
make migrate-history    # Show all migrations
```

### Apply Migrations
```bash
make migrate-up         # Apply all pending migrations
```

### Rollback Migrations
```bash
make migrate-down       # Rollback one migration
```

### Create New Migration
```bash
make migrate-create MSG="description of changes"
```

Alembic automatically detects model changes and generates migration scripts.

## Database Seeding

After running migrations, you need to create an initial admin user to access the attorney dashboard.

### Create Initial Admin User
```bash
make seed-db
```

This creates a default admin account with the following credentials:
- **Username:** `admin`
- **Email:** `admin@leadmanagement.local`
- **Password:** `Admin123!SecurePassword`

**Important:** Change the default password after your first login!

### Create Additional Users
```bash
make create-user USERNAME=attorney1 EMAIL=attorney1@firm.com PASSWORD=SecurePass123
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Username Requirements:**
- 3-50 characters
- Alphanumeric with underscores or hyphens only

The script will validate all inputs and prevent duplicate usernames or emails.

For more details on seeding scripts, see [scripts/README.md](scripts/README.md).

## Development Workflow

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Make Code Changes
Edit files in the `app/` directory following the existing architecture patterns.

### 3. Run Tests
```bash
make test               # Run all tests
make test-coverage      # Run tests with coverage report
```

### 4. Check Code Quality
```bash
# Format code (optional)
black app/ tests/

# Check style (optional)
flake8 app/ tests/
```

### 5. Database Changes
If you modified models:
```bash
make migrate-create MSG="description of model changes"
make migrate-up
```

### 6. Clean Up
```bash
make clean              # Remove generated files and caches
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./leads.db` | Database connection string |
| `SECRET_KEY` | **Yes** | **None** | JWT signing key (min 32 chars, must be securely generated) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Token expiry time (24 hours) |
| `SMTP_HOST` | Yes | - | SMTP server hostname |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USERNAME` | Yes | - | SMTP authentication username |
| `SMTP_PASSWORD` | Yes | - | SMTP authentication password |
| `SMTP_FROM_EMAIL` | Yes | - | Email sender address |
| `SMTP_FROM_NAME` | No | `Lead Management System` | Email sender name |
| `ATTORNEY_EMAIL` | Yes | - | Email address to receive lead notifications |
| `UPLOAD_DIR` | No | `./uploads/resumes` | Directory for resume storage |
| `MAX_FILE_SIZE` | No | `5242880` | Maximum file size in bytes (5MB) |
| `ENVIRONMENT` | No | `development` | Environment name (development/production) |
| `DEBUG` | No | `True` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins (comma-separated) |

## Security Features

### Authentication
- JWT token-based authentication
- bcrypt password hashing with salt
- Token expiration and validation
- Secure token storage recommendations

### Input Validation
- Pydantic schema validation for all inputs
- Email format validation
- File type and size validation
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via input sanitization

### File Upload Security
- Allowed file types: PDF, DOC, DOCX
- Maximum file size: 5MB (configurable)
- Unique filename generation (UUID)
- MIME type validation
- Secure file storage outside web root

### CORS Configuration
- Configurable allowed origins
- Credentials support
- Preflight request handling

### Rate Limiting
- Middleware-based request tracking
- Error logging and monitoring

## Production Deployment

### Docker Deployment (Recommended)

The application includes production-ready Docker configuration with PostgreSQL database.

#### Quick Deploy

```bash
# Configure environment
cp .env.example .env
# Edit .env with production values

# Generate secure secret key
SECRET_KEY=$(openssl rand -hex 32)
# Add to .env

# Start services
docker-compose up -d

# Initialize database
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f
```

#### Production Checklist

1. **Security**:
   - **Generate secure `SECRET_KEY`**: 
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Set `ENVIRONMENT=production` and `DEBUG=False`
   - Change default PostgreSQL credentials in `docker-compose.yml`
   - Configure proper CORS origins
   - Set up HTTPS with reverse proxy (Nginx, Traefik)

2. **Database**:
   - Backup strategy: `docker-compose exec db pg_dump -U leaduser leaddb > backup.sql`
   - Configure PostgreSQL connection pool settings
   - Set up automated backups

3. **Monitoring**:
   - Health check: http://your-domain.com/health
   - Container logs: `docker-compose logs -f`
   - Database monitoring: `docker-compose exec db pg_isready`

4. **Scaling**:
   - Increase uvicorn workers in Dockerfile
   - Use Docker Swarm or Kubernetes for orchestration
   - Set up load balancer for multiple API replicas

For complete Docker documentation, see [docs/DOCKER.md](docs/DOCKER.md).

### Manual Deployment (Alternative)

#### Environment Setup
1. Set `ENVIRONMENT=production` in `.env`
2. Set `DEBUG=False`
3. **Generate a secure `SECRET_KEY`** (required, will fail if using default):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
4. Use PostgreSQL instead of SQLite:
   ```
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```
5. Configure production SMTP service
6. Set up HTTPS/SSL certificates
7. Configure proper CORS origins

#### Database Migration
```bash
# On production server
source venv/bin/activate
make migrate-up
```

#### Running in Production
```bash
# Using uvicorn with proper workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Troubleshooting

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
rm leads.db
make migrate-up
```

### Email Not Sending
- Verify SMTP credentials in `.env`
- Check firewall/network settings
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Check logs for detailed error messages

### Import Errors
```bash
# Reinstall dependencies
make clean
make install
```

### Permission Issues with Uploads
```bash
# Ensure upload directory is writable
mkdir -p uploads/resumes
chmod -R 755 uploads
```

## Development Commands (Makefile)

### Local Development

| Command | Description |
|---------|-------------|
| `make env` | Create `.env` from `.env.example` |
| `make venv` | Create Python virtual environment |
| `make install` | Install dependencies |
| `make test` | Run all tests |
| `make unit-test` | Run unit tests only |
| `make integration-test` | Run integration tests only |
| `make e2e-test` | Run end-to-end tests only |
| `make test-coverage` | Run tests with coverage report |
| `make migrate-up` | Apply database migrations |
| `make migrate-down` | Rollback last migration |
| `make migrate-create MSG="description"` | Create new migration |
| `make migrate-current` | Show current migration version |
| `make migrate-history` | Show migration history |
| `make clean` | Remove generated files and caches |

### Docker Commands

| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker images |
| `make docker-up` | Start all Docker services |
| `make docker-down` | Stop Docker services |
| `make docker-logs` | View logs from all services |
| `make docker-restart` | Restart Docker services |
| `make docker-clean` | Stop and remove all containers and volumes |

## Additional Documentation

Comprehensive documentation is available in the `docs/` directory:

- **DESIGN.md**: Architecture and design decisions
- **API_OVERVIEW.md**: Detailed API endpoint documentation
- **TESTING.md**: Testing strategy and test coverage
- **DATABASE_MODELS.md**: Database schema details
- **AUTHENTICATION.md**: Authentication flow and security
- **EMAIL_SERVICE.md**: Email notification implementation
- **FILE_STORAGE.md**: File upload and storage strategy

## Architecture Highlights

### Three-Tier Architecture
1. **API Layer** (FastAPI): HTTP request/response handling, validation
2. **Service Layer**: Business logic, workflow orchestration
3. **Data Layer** (Repository Pattern): Database operations abstraction

### Design Patterns
- **Repository Pattern**: Clean data access abstraction
- **Dependency Injection**: FastAPI's dependency system
- **Service Layer Pattern**: Separation of business logic
- **Schema Validation**: Pydantic models for type safety

### Key Features
- **Async/Await**: Non-blocking I/O for email and file operations
- **Type Hints**: Full type safety throughout codebase
- **Automatic Documentation**: OpenAPI/Swagger generation
- **Database Migrations**: Version-controlled schema changes
- **Comprehensive Logging**: Structured logging with request tracking
- **Exception Handling**: Standardized error responses

## License

This project is proprietary and confidential. All rights reserved.

## Support

For issues, questions, or contributions, please contact the development team or create an issue in the repository.

---

**Built with FastAPI, SQLAlchemy, and modern Python best practices.**
