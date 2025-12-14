# Testing Infrastructure Documentation

## Overview

Comprehensive testing suite covering unit tests, integration tests, and end-to-end tests for the Lead Management API.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── pytest.ini               # Pytest configuration
├── unit/                    # Unit tests (isolated component testing)
│   ├── test_models.py       # Database model tests
│   ├── test_schemas.py      # Pydantic schema validation tests
│   ├── test_services.py     # Business logic service tests
│   └── test_utils.py        # Utility function tests
├── integration/             # Integration tests (API endpoint testing)
│   ├── test_api_auth.py     # Authentication endpoint tests
│   ├── test_api_protected.py # Protected endpoint tests
│   └── test_api_public.py   # Public endpoint tests
└── e2e/                     # End-to-end tests (complete workflows)
    └── test_lead_workflow.py # Complete user journey tests
```

## Running Tests

### Run All Tests
```bash
make test
```

### Run Unit Tests Only
```bash
make unit-test
```

### Run Integration Tests Only
```bash
make integration-test
```

### Run End-to-End Tests Only
```bash
make e2e-test
```

### Run Tests with Coverage
```bash
make test-coverage
```

## Test Categories

### Unit Tests (131 tests)

**Models** (`test_models.py`) - 17 tests
- Lead model creation and defaults
- User model creation and defaults
- Unique constraint validation
- Status transitions
- Timestamp tracking
- String representations

**Schemas** (`test_schemas.py`) - 41 tests
- Pydantic validation for all schemas
- Email normalization
- Name sanitization
- XSS prevention
- Password strength validation
- LeadStatus enum operations
- Pagination metadata

**Services** (`test_services.py`) - 39 tests
- LeadService: CRUD operations, pagination, filtering
- AuthService: Registration, login, user management
- FileService: File upload, validation, retrieval
- EmailService: Email sending with retry logic

**Utils** (`test_utils.py`) - 41 tests
- File validation (size, extension, MIME type)
- Text sanitization and validation
- Email format validation
- Password strength checking
- Status transition validation
- Security functions (hashing, JWT)

### Integration Tests (73 tests)

**Authentication API** (`test_api_auth.py`) - 29 tests
- User registration with validation
- User login and token generation
- Token validation (valid, invalid, expired, malformed)
- Current user profile retrieval
- Unauthorized access handling

**Protected API** (`test_api_protected.py`) - 31 tests
- Lead listing with pagination
- Lead filtering by status
- Lead sorting
- Lead detail retrieval
- Lead status updates
- Resume download
- Authentication requirements
- Authorization checks

**Public API** (`test_api_public.py`) - 17 tests
- Lead creation with file upload
- Multiple file format support (PDF, DOC, DOCX)
- Duplicate email detection
- Field validation
- Input sanitization
- Email normalization
- XSS prevention

### End-to-End Tests (24 tests)

**Lead Submission Workflow** (`test_lead_workflow.py`)
- Complete lead submission flow
- Multiple file type support
- Duplicate email rejection
- Invalid file type handling

**Lead Management Workflow**
- Complete management flow (list, view, update)
- Filtering and pagination
- Unauthorized access prevention

**Status Transition Workflow**
- Valid status transitions
- Invalid status rejection
- Transition persistence

**File Storage Workflow**
- Upload and retrieval
- File persistence on filesystem
- Unique filename generation

**Authentication Workflow**
- Registration and login flow
- Protected endpoint authentication
- Invalid credential rejection

**Error Scenarios**
- Missing required fields
- Invalid email format
- Non-existent lead access
- Malformed UUID handling
- Large file rejection

**Complete User Journeys**
- Prospect to reached-out workflow
- Multiple attorneys collaboration

## Test Fixtures

### Database Fixtures
- `test_settings`: Test configuration overrides
- `db_engine`: SQLite in-memory database engine
- `db_session`: Isolated database session per test
- `reset_db_state`: Automatic cleanup between tests

### API Client Fixtures
- `client`: Synchronous test client
- `async_client`: Asynchronous test client

### Authentication Fixtures
- `sample_user_data`: User data factory
- `create_user`: User creation helper
- `test_user`: Pre-created test user
- `auth_token`: JWT authentication token
- `auth_headers`: Authentication headers

### Data Fixtures
- `sample_lead_data`: Lead data factory
- `create_lead`: Lead creation helper
- `sample_leads`: Multiple test leads

### File Upload Fixtures
- `temp_upload_dir`: Temporary upload directory
- `mock_resume_file`: Mock UploadFile helper

### Mock Fixtures
- `mock_email_service`: Email service mock
- `mock_file_service`: File service mock
- `mock_smtp`: SMTP connection mock

## Test Configuration

### pytest.ini
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function

testpaths = tests

python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    asyncio: mark test as an async test
    unit: mark test as a unit test
    integration: mark test as an integration test
    e2e: mark test as an end-to-end test

addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
```

## Test Coverage

Target: 90%+ code coverage

Key areas covered:
- ✅ All API endpoints
- ✅ All service layer logic
- ✅ All data validation
- ✅ All authentication flows
- ✅ All file operations
- ✅ All error scenarios
- ✅ Complete user workflows

## Best Practices

1. **Test Isolation**: Each test is independent and doesn't affect others
2. **Fixtures**: Reusable test setup using pytest fixtures
3. **Mocking**: External dependencies (email, SMTP) are mocked
4. **Cleanup**: Automatic cleanup after each test
5. **Descriptive Names**: Clear test method names describing what's tested
6. **Assertions**: Multiple assertions to verify complete behavior
7. **Error Testing**: Comprehensive error scenario coverage
8. **Documentation**: Docstrings explaining test purpose

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=xml

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

## Common Test Patterns

### Testing API Endpoints
```python
def test_endpoint(client, auth_headers):
    response = client.get("/api/v1/endpoint", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Testing with Database
```python
def test_with_db(db_session, create_lead):
    lead = create_lead(email="test@example.com")
    assert lead.id is not None
    assert lead.email == "test@example.com"
```

### Testing File Upload
```python
def test_file_upload(client, temp_upload_dir):
    response = client.post(
        "/api/v1/leads",
        data={"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
        files={"resume": ("resume.pdf", BytesIO(b"content"), "application/pdf")}
    )
    assert response.status_code == 201
```

### Testing Authentication
```python
def test_protected_endpoint(client, auth_headers):
    response = client.get("/api/v1/protected", headers=auth_headers)
    assert response.status_code == 200
```

## Debugging Tests

### Run single test
```bash
pytest tests/unit/test_models.py::TestLeadModel::test_create_lead -v
```

### Run with detailed output
```bash
pytest tests/ -vv --tb=long
```

### Run with print statements
```bash
pytest tests/ -v -s
```

### Run failed tests only
```bash
pytest tests/ --lf
```

## Maintenance

- Update fixtures when models change
- Add tests for new features
- Update mocks when external services change
- Review and update test data regularly
- Keep test coverage above 90%
