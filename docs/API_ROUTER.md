# API Router Configuration Documentation

## Overview

The API router configuration establishes the complete routing structure for the Lead Management API, organizing endpoints by functionality and access level.

## Architecture

### Three-Layer Routing Structure

```
app (FastAPI instance)
└── /api/v1 (API versioning prefix)
    ├── /leads (POST) - Public lead submission
    ├── /auth/register (POST) - User registration
    ├── /auth/login (POST) - User authentication
    ├── /auth/me (GET) - Current user profile
    ├── /leads (GET) - List leads [Protected]
    ├── /leads/{id} (GET) - Get lead details [Protected]
    ├── /leads/{id} (PATCH) - Update lead status [Protected]
    └── /leads/{id}/resume (GET) - Download resume [Protected]
```

## File Structure

### app/api/v1/api.py

Main API router that combines all endpoint modules:

```python
api_router = APIRouter()

# Public endpoints - No authentication
api_router.include_router(
    public.router,
    prefix="",
    tags=["public"]
)

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Protected endpoints - JWT required
api_router.include_router(
    leads.router,
    prefix="/leads",
    tags=["leads"]
)
```

**Design Decisions:**
- Public endpoints have no prefix for clean URLs
- Auth endpoints grouped under `/auth`
- Protected lead management under `/leads`
- OpenAPI tags for logical grouping in documentation

### app/main.py

FastAPI application factory with full configuration:

```python
def create_application() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="Lead Management API",
        description="API for managing attorney lead submissions",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(CORSMiddleware, ...)
    
    # Include versioned API
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy"}
    
    return app

app = create_application()
```

**Features:**
- Factory pattern for testability
- Environment-based CORS configuration
- API versioning via `/api/v1` prefix
- OpenAPI documentation at `/docs`
- Health check endpoint
- Centralized settings management

## Endpoint Organization

### Public Endpoints (No Auth)
- `POST /api/v1/leads` - Submit new lead with resume

### Authentication Endpoints
- `POST /api/v1/auth/register` - Create attorney account
- `POST /api/v1/auth/login` - Get JWT token
- `GET /api/v1/auth/me` - Get current user (requires auth)

### Protected Endpoints (JWT Required)
- `GET /api/v1/leads` - List/filter/sort leads
- `GET /api/v1/leads/{id}` - Get lead details
- `PATCH /api/v1/leads/{id}` - Update lead status
- `GET /api/v1/leads/{id}/resume` - Download resume file

### Utility Endpoints
- `GET /health` - Health check (no auth)

## Middleware Configuration

### CORS Middleware
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),  # From environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Configuration:**
- Origins from `CORS_ORIGINS` environment variable
- Supports credentials for cookie-based auth
- Permissive methods/headers for development

## OpenAPI Documentation

### Interactive Documentation

**Swagger UI:** `http://localhost:8000/docs`
- Interactive API testing
- OAuth2 authorization support
- Request/response examples
- Schema definitions

**ReDoc:** `http://localhost:8000/redoc`
- Clean, readable documentation
- Hierarchical organization
- Search functionality

**OpenAPI JSON:** `http://localhost:8000/openapi.json`
- Machine-readable API spec
- Client code generation
- API gateway integration

### OpenAPI Tags

Endpoints are organized by tags:
- **public** - Public lead submission
- **authentication** - User registration and login
- **leads** - Protected lead management
- **health** - System health check

## API Versioning Strategy

### Current Version: v1

All endpoints prefixed with `/api/v1` for version control:

```
/api/v1/leads          ✓ Current
/api/v2/leads          Future version
```

**Benefits:**
- Backward compatibility
- Gradual migration
- Multiple versions can coexist
- Clear deprecation path

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Gunicorn

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Configuration

### Environment Variables

Required for proper routing:
```env
# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"attorney1","email":"test@example.com","password":"Test123!"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=Test123!"
```

### Access Protected Endpoint
```bash
curl http://localhost:8000/api/v1/leads \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Router Hierarchy

```
FastAPI App
├── Middleware Layer
│   └── CORS
├── Root Routes
│   └── GET /health
└── API Router (/api/v1)
    ├── Public Router
    │   └── POST /leads
    ├── Auth Router (/auth)
    │   ├── POST /register
    │   ├── POST /login
    │   └── GET /me
    └── Leads Router (/leads)
        ├── GET /
        ├── GET /{id}
        ├── PATCH /{id}
        └── GET /{id}/resume
```

## Best Practices Implemented

1. **Separation of Concerns**: Each router handles distinct functionality
2. **API Versioning**: Future-proof with `/api/v1` prefix
3. **Factory Pattern**: `create_application()` for testability
4. **Environment Config**: Settings from environment variables
5. **OpenAPI Integration**: Automatic documentation generation
6. **CORS Configuration**: Secure cross-origin requests
7. **Health Checks**: Monitoring endpoint for load balancers
8. **Logical Grouping**: Tags for organized documentation

## Related Documentation

- [Public API](./PUBLIC_API.md) - Public lead submission
- [Protected API](./PROTECTED_API.md) - Attorney dashboard endpoints
- [Auth API](./AUTH_API.md) - Authentication and registration
- [Design Document](./DESIGN.md) - System architecture
