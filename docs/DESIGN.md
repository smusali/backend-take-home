# System Design Document

## Lead Management Application

**Version:** 1.0.0  
**Date:** December 14, 2025  
**Author:** Samir Musali

---

## Summary

This document provides a comprehensive technical design specification for the Lead Management API, a production-ready FastAPI application that enables legal professionals to collect and manage prospect information through a public submission form and an authenticated internal dashboard.

The system implements a three-tier architecture with clear separation of concerns, following modern best practices for security, scalability, and maintainability. Built with FastAPI, SQLAlchemy, and JWT authentication, the application handles lead submissions with resume uploads, automated email notifications, and secure lead management workflows.

**Key Technical Highlights:**
- **Framework**: FastAPI with async/await for high performance
- **Architecture**: Three-tier layered architecture (API, Service, Repository)
- **Database**: SQLAlchemy ORM with Alembic migrations
- **Security**: JWT authentication, bcrypt password hashing, comprehensive input validation
- **Email**: Async SMTP with Jinja2 templates
- **Testing**: 220+ tests with >95% coverage
- **Documentation**: Auto-generated OpenAPI/Swagger documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Technology Stack](#technology-stack)
4. [Database Design](#database-design)
5. [API Design](#api-design)
6. [Lead State Machine](#lead-state-machine)
7. [Authentication & Authorization](#authentication--authorization)
8. [File Storage Strategy](#file-storage-strategy)
9. [Email Service Integration](#email-service-integration)
10. [Security Considerations](#security-considerations)
11. [Scalability & Performance](#scalability--performance)
12. [Error Handling](#error-handling)

---

## Overview

### Purpose

This application provides a lead management system for legal professionals to collect and manage prospect information through a public submission form and an internal authenticated dashboard.

### Key Features

- **Public Lead Submission**: Prospects can submit their information (name, email, resume) through a publicly accessible form
- **Email Notifications**: Automatic email notifications sent to both prospect and attorney upon submission
- **Internal Dashboard**: Authenticated interface for attorneys to view and manage leads
- **Lead Status Management**: Track lead progression from PENDING to REACHED_OUT status
- **Resume Storage**: Secure file storage for uploaded resumes

### System Requirements

- Accept lead submissions from public users
- Validate and store lead data securely
- Send confirmation emails to prospects
- Notify attorneys of new leads
- Provide authenticated access to lead management
- Support lead status transitions
- Enable resume file downloads

---

## Architecture Design

### High-Level Architecture

The application follows a **three-tier architecture** pattern, separating concerns into distinct layers:
```mermaid
graph TB
    subgraph "Client Layer"
        PC[Public Client]
        AC[Attorney Client]
    end
    
    subgraph "API Layer (FastAPI)"
        PE[Public Endpoints]
        AE[Auth Endpoints]
        LE[Protected Lead Endpoints]
    end
    
    subgraph "Business Logic Layer"
        LS[Lead Service]
        AS[Auth Service]
        FS[File Service]
        ES[Email Service]
    end
    
    subgraph "Data Access Layer"
        LR[Lead Repository]
        UR[User Repository]
        BR[Base Repository]
    end
    
    subgraph "Storage Layer"
        DB[(SQLAlchemy Database)]
        DISK[File Storage]
    end
    
    subgraph "External Services"
        SMTP[SMTP Server]
    end
    
    PC --> PE
    AC --> AE
    AC --> LE
    
    PE --> LS
    AE --> AS
    LE --> LS
    
    LS --> LR
    LS --> FS
    LS --> ES
    AS --> UR
    
    LR --> BR
    UR --> BR
    BR --> DB
    
    FS --> DISK
    ES --> SMTP

    style PC fill:#90EE90,stroke:#333,stroke-width:2px,color:#000
    style AC fill:#87CEEB,stroke:#333,stroke-width:2px,color:#000
    style PE fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    style AE fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    style LE fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    style LS fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style AS fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style FS fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style ES fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style LR fill:#e6e6e6,stroke:#333,stroke-width:2px,color:#000
    style UR fill:#e6e6e6,stroke:#333,stroke-width:2px,color:#000
    style BR fill:#e6e6e6,stroke:#333,stroke-width:2px,color:#000
    style DB fill:#DDA0DD,stroke:#333,stroke-width:2px,color:#000
    style DISK fill:#f0f0f0,stroke:#333,stroke-width:2px,color:#000
    style SMTP fill:#FFA07A,stroke:#333,stroke-width:2px,color:#000
```

### Architecture Layers

#### 1. API Layer (Presentation)
- **Responsibility**: Handle HTTP requests/responses, input validation, authentication
- **Technology**: FastAPI with Pydantic schemas
- **Components**:
  - Public endpoints (lead submission)
  - Authentication endpoints (login, registration)
  - Protected endpoints (lead management)

#### 2. Business Logic Layer (Service)
- **Responsibility**: Implement business rules, orchestrate workflows, coordinate between components
- **Components**:
  - **Lead Service**: Manages lead creation, retrieval, and updates
  - **Auth Service**: Handles user authentication and token management
  - **File Service**: Manages resume upload, storage, and retrieval
  - **Email Service**: Sends notifications to prospects and attorneys

#### 3. Data Access Layer (Repository)
- **Responsibility**: Abstract database operations, provide clean data access interface
- **Pattern**: Repository pattern with generic base repository
- **Components**:
  - **Base Repository**: Generic CRUD operations
  - **Lead Repository**: Lead-specific queries (by status, pagination, etc.)
  - **User Repository**: User authentication queries

### Design Principles

1. **Separation of Concerns**: Each layer has a distinct responsibility
2. **Dependency Inversion**: Higher layers depend on abstractions, not concrete implementations
3. **Single Responsibility**: Each service/repository handles one domain
4. **Don't Repeat Yourself (DRY)**: Common functionality in base classes
5. **RESTful Design**: API follows REST principles with proper HTTP methods and status codes

---

## Technology Stack

### Core Framework

#### FastAPI
- **Async Support**: Native async/await for non-blocking I/O operations (email sending, file I/O)
- **Auto Documentation**: Automatic OpenAPI (Swagger) documentation generation
- **Data Validation**: Built-in Pydantic integration for request/response validation
- **Performance**: One of the fastest Python frameworks (comparable to Node.js)
- **Type Safety**: First-class support for Python type hints
- **Modern**: Built on modern Python standards (Python 3.13+)

### Database & ORM

#### SQLAlchemy 2.0
- **ORM Flexibility**: Supports both ORM and Core for different use cases
- **Database Agnostic**: Easy migration from SQLite (dev) to PostgreSQL (production)
- **Type Safety**: Full support for modern Python type hints
- **Migration Support**: Seamless integration with Alembic
- **Connection Pooling**: Built-in connection management for scalability

#### Database Choice
- **Development**: SQLite
  - Zero configuration
  - File-based, easy setup
  - Perfect for local development and testing
  
- **Production**: PostgreSQL
  - ACID compliance
  - Advanced features (JSON, full-text search)
  - Excellent performance at scale
  - Robust community and tooling

#### Alembic
- **Version Control**: Database schema versioning
- **Migration Management**: Safe, reversible schema changes
- **Team Collaboration**: Shared migration history
- **Environment Support**: Different migrations per environment

### Authentication & Security

#### JWT (JSON Web Tokens) with python-jose
- **Stateless**: No server-side session storage required
- **Scalable**: Works well with horizontal scaling
- **Standard**: Industry-standard authentication mechanism
- **Flexible**: Easy to add custom claims
- **Secure**: Cryptographically signed tokens

#### Passlib with bcrypt
- **Security**: Industry-standard password hashing
- **Adaptive**: Configurable work factor for future-proofing
- **Protection**: Resistant to rainbow table attacks
- **Salting**: Automatic salt generation

### File Handling

#### python-multipart
- **Multipart Forms**: Native support for file uploads
- **Streaming**: Memory-efficient file processing
- **FastAPI Integration**: Native FastAPI support

### Email Service

#### aiosmtplib
- **Async**: Non-blocking email sending
- **Performance**: Doesn't block request processing
- **Standard**: SMTP protocol support
- **Flexibility**: Works with any SMTP server

#### Jinja2
- **Templates**: Clean email template management
- **Dynamic Content**: Easy variable substitution
- **Reusability**: Template inheritance and composition
- **Security**: Auto-escaping for XSS prevention

### Testing

#### pytest
- **Simplicity**: Clean, readable test syntax
- **Fixtures**: Powerful dependency injection for tests
- **Plugins**: Extensive plugin ecosystem
- **Async Support**: Native async test support

#### httpx
**Justification:**
- **Async**: Async client for testing FastAPI
- **FastAPI Integration**: Official FastAPI testing recommendation
- **HTTP/2 Support**: Modern protocol support

---

## Database Design

### Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ LEAD : manages
    
    USER {
        uuid id PK
        string username UK
        string email UK
        string hashed_password
        boolean is_active
        datetime created_at
    }
    
    LEAD {
        uuid id PK
        string first_name
        string last_name
        string email UK
        string resume_path
        enum status
        datetime created_at
        datetime updated_at
        datetime reached_out_at
    }
```

### Schema Details

#### Lead Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the lead |
| `first_name` | VARCHAR(100) | NOT NULL | Prospect's first name |
| `last_name` | VARCHAR(100) | NOT NULL | Prospect's last name |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Prospect's email address |
| `resume_path` | VARCHAR(500) | NOT NULL | Path to stored resume file |
| `status` | ENUM | NOT NULL, DEFAULT 'PENDING' | Current lead status |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When the lead was created |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |
| `reached_out_at` | TIMESTAMP | NULLABLE | When attorney marked as reached out |

**Indexes:**
- `idx_lead_email` on `email` (for duplicate checking)
- `idx_lead_status` on `status` (for filtering)
- `idx_lead_created_at` on `created_at` (for sorting/pagination)

#### User Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the user |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE | Attorney username |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Attorney email address |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |

**Indexes:**
- `idx_user_username` on `username` (for login lookups)
- `idx_user_email` on `email` (for email lookups)

### Design Decisions

#### UUID for Primary Keys
**Why:**
- **Security**: Non-sequential IDs prevent enumeration attacks
- **Distribution**: Can be generated client-side if needed
- **Merging**: No conflicts when merging databases
- **Privacy**: Doesn't leak business information (e.g., number of users)

**Trade-offs:**
- Larger storage (16 bytes vs 4/8 bytes for int)
- Slightly slower joins (acceptable for this scale)

#### ENUM for Status Field
- **Data Integrity**: Only valid statuses allowed at database level
- **Type Safety**: Application-level type checking
- **Performance**: Efficient storage and indexing
- **Clarity**: Self-documenting valid states

#### Timestamps Strategy
- `created_at`: Audit trail, sorting, analytics
- `updated_at`: Track modifications, cache invalidation
- `reached_out_at`: Business metric, nullable for PENDING leads

#### Email Uniqueness Constraint
**Why:**
- **Business Logic**: One lead per email address
- **User Experience**: Prevents duplicate submissions
- **Data Quality**: Maintains data integrity

---

## API Design

### REST Principles

The API follows RESTful design principles:

1. **Resource-Based URLs**: `/api/v1/leads/{id}`
2. **HTTP Methods**: GET, POST, PATCH for appropriate operations
3. **Status Codes**: Meaningful HTTP status codes
4. **Stateless**: Each request contains all necessary information
5. **JSON Format**: Consistent JSON request/response bodies
6. **Versioning**: `/api/v1/` prefix for future compatibility

### API Endpoints

```mermaid
graph LR
    subgraph Public
        A[POST /api/v1/leads]
    end
    
    subgraph Authentication
        B[POST /api/v1/auth/login]
        C[POST /api/v1/auth/register]
        D[GET /api/v1/auth/me]
    end
    
    subgraph Protected
        E[GET /api/v1/leads]
        F[GET /api/v1/leads/:id]
        G[PATCH /api/v1/leads/:id]
        H[GET /api/v1/leads/:id/resume]
    end
    
    style A fill:#90EE90,stroke:#333,stroke-width:2px,color:#000
    style B fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    style C fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    style D fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    style E fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#fff
    style F fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#fff
    style G fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#fff
    style H fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#fff
```

### Endpoint Specifications

#### 1. Create Lead (Public)

**Endpoint:** `POST /api/v1/leads`  
**Authentication:** None (Public)  
**Content-Type:** `multipart/form-data`
**Request Body:**
```json
{
  "first_name": "string (1-100 chars, required)",
  "last_name": "string (1-100 chars, required)",
  "email": "string (valid email, required)",
  "resume": "file (PDF/DOC/DOCX, max 5MB, required)"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "status": "PENDING",
  "created_at": "timestamp",
  "message": "Lead submitted successfully. Confirmation email sent."
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors
- `409 Conflict`: Email already exists
- `413 Payload Too Large`: File too large
- `415 Unsupported Media Type`: Invalid file type
- `500 Internal Server Error`: Server error

---

#### 2. User Login

**Endpoint:** `POST /api/v1/auth/login`  
**Authentication:** None  
**Content-Type:** `application/x-www-form-urlencoded`
**Request Body:**
```
username=string&password=string
```

**Response:** `200 OK`
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 1440
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `422 Unprocessable Entity`: Missing fields

---

#### 3. User Registration

**Endpoint:** `POST /api/v1/auth/register`  
**Authentication:** None (or Admin-only in production)  
**Content-Type:** `application/json`
**Request Body:**
```json
{
  "username": "string (3-50 chars, required)",
  "email": "string (valid email, required)",
  "password": "string (min 8 chars, required)"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "is_active": true,
  "created_at": "timestamp"
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors
- `409 Conflict`: Username or email already exists

---

#### 4. Get Current User

**Endpoint:** `GET /api/v1/auth/me`  
**Authentication:** Required (Bearer Token)
**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "is_active": true
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

---

#### 5. List Leads (Protected)

**Endpoint:** `GET /api/v1/leads`  
**Authentication:** Required (Bearer Token)
**Query Parameters:**
- `page` (integer, default: 1): Page number
- `size` (integer, default: 50, max: 100): Items per page
- `status` (enum, optional): Filter by status (PENDING, REACHED_OUT)
- `sort_by` (string, default: created_at): Sort field
- `sort_order` (string, default: desc): Sort direction (asc, desc)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "status": "PENDING",
      "created_at": "timestamp",
      "updated_at": "timestamp",
      "reached_out_at": "timestamp or null"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 50,
  "pages": 3
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `422 Unprocessable Entity`: Invalid query parameters

---

#### 6. Get Lead by ID (Protected)

**Endpoint:** `GET /api/v1/leads/{lead_id}`  
**Authentication:** Required (Bearer Token)
**Response:** `200 OK`
```json
{
  "id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "resume_path": "string",
  "status": "PENDING",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "reached_out_at": "timestamp or null"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `404 Not Found`: Lead not found
- `422 Unprocessable Entity`: Invalid UUID format

---

#### 7. Update Lead Status (Protected)

**Endpoint:** `PATCH /api/v1/leads/{lead_id}`  
**Authentication:** Required (Bearer Token)  
**Content-Type:** `application/json`
**Request Body:**
```json
{
  "status": "REACHED_OUT"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "status": "REACHED_OUT",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "reached_out_at": "timestamp"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid status transition
- `401 Unauthorized`: Invalid or expired token
- `404 Not Found`: Lead not found
- `422 Unprocessable Entity`: Invalid request body

---

#### 8. Download Resume (Protected)

**Endpoint:** `GET /api/v1/leads/{lead_id}/resume`  
**Authentication:** Required (Bearer Token)
**Response:** `200 OK`
- **Content-Type**: `application/pdf` or `application/msword` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition**: `attachment; filename="firstname_lastname_resume.pdf"`
- **Body**: Binary file content

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `404 Not Found`: Lead or file not found
- `500 Internal Server Error`: File read error

---

### API Versioning Strategy

**Current:** `/api/v1/`
**Future Considerations:**
- Version in URL path (current approach)
- Allows running multiple versions simultaneously
- Clear migration path for clients
- Version deprecation policy: N-1 support (latest + previous version)

---

## Lead State Machine

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> PENDING: Lead Created
    PENDING --> REACHED_OUT: Attorney marks as reached out
    REACHED_OUT --> PENDING: Attorney can revert if needed
    REACHED_OUT --> [*]: Optional End State
    
    note right of PENDING
        Initial state when
        prospect submits form.
        Emails sent to both
        prospect and attorney.
    end note
    
    note right of REACHED_OUT
        Attorney has contacted
        the prospect.
        Timestamp recorded.
        Can be reverted to PENDING.
    end note
```

### State Definitions

#### PENDING
- **Description**: Lead has been submitted but attorney has not yet reached out
- **Entry Actions**:
  - Create lead record in database
  - Store resume file
  - Send confirmation email to prospect
  - Send notification email to attorney
  - Set `created_at` timestamp
  - Set `updated_at` timestamp
- **Valid Transitions**: Can transition to REACHED_OUT
- **Business Rules**:
  - All new leads start in this state
  - Cannot be created directly in REACHED_OUT state
  - Email must be unique across all leads
  - Can be transitioned back from REACHED_OUT if needed

#### REACHED_OUT
- **Description**: Attorney has made contact with the prospect
- **Entry Actions**:
  - Update `status` to REACHED_OUT
  - Set `reached_out_at` timestamp
  - Update `updated_at` timestamp
- **Valid Transitions**: Can transition back to PENDING
- **Business Rules**:
  - Can only be set by authenticated attorney
  - Can transition back to PENDING if attorney needs to revert
  - Timestamp records when attorney first reached out

### State Transition Validation

```python
# Valid transitions (bidirectional for flexibility)
VALID_TRANSITIONS = {
    LeadStatus.PENDING: [LeadStatus.REACHED_OUT],
    LeadStatus.REACHED_OUT: [LeadStatus.PENDING],  # Allow revert
}

def validate_transition(current_status, new_status):
    """Validate if state transition is allowed."""
    if new_status not in VALID_TRANSITIONS[current_status]:
        raise InvalidStatusTransitionException(
            f"Cannot transition from {current_status} to {new_status}"
        )
```

### Future State Considerations

If business requirements expand, potential additional states:

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> IN_REVIEW: Attorney reviewing
    IN_REVIEW --> REACHED_OUT: Contact made
    IN_REVIEW --> REJECTED: Not qualified
    REACHED_OUT --> QUALIFIED: Interested
    REACHED_OUT --> NOT_INTERESTED: Not interested
    QUALIFIED --> [*]
    REJECTED --> [*]
    NOT_INTERESTED --> [*]
```

*Note: Current implementation uses simple two-state model per requirements.*

---

## Authentication & Authorization

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Server
    participant AUTH as Auth Service
    participant DB as Database
    
    Note over C,DB: Login Flow
    
    C->>API: POST /auth/login {username, password}
    API->>AUTH: Authenticate user
    AUTH->>DB: Query user by username
    DB-->>AUTH: User record
    AUTH->>AUTH: Verify password hash
    AUTH->>AUTH: Generate JWT token
    AUTH-->>API: Token + user info
    API-->>C: {access_token, token_type, expires_in}
    
    Note over C,DB: Authenticated Request Flow
    
    C->>API: GET /leads (Authorization: Bearer <token>)
    API->>AUTH: Verify JWT token
    AUTH->>AUTH: Decode & validate token
    AUTH-->>API: User identity
    API->>API: Process request
    API-->>C: Response data
```

### JWT Token Structure

**Claims:**
```json
{
  "sub": "user_id (UUID)",
  "username": "attorney_username",
  "exp": "expiration_timestamp",
  "iat": "issued_at_timestamp",
  "type": "access"
}
```

**Configuration:**
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Secret Key**: Environment variable (`SECRET_KEY`)
- **Token Type**: Bearer

### Password Security

**Hashing Strategy:**
- **Algorithm**: bcrypt
- **Rounds**: 12 (configurable)
- **Salt**: Automatic, unique per password
- **Storage**: Store only hashed password, never plaintext

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter (recommended)
- At least one lowercase letter (recommended)
- At least one number (recommended)
- At least one special character (recommended)

*Note: Complexity requirements can be enforced in Pydantic schema validators.*

### Authorization Model

**Current Model**: Role-Based Access Control (RBAC) - Simple
**Roles:**
1. **Public** (Unauthenticated)
   - Can submit leads
   - No access to lead management

2. **Attorney** (Authenticated)
   - Can view all leads
   - Can update lead status
   - Can download resumes

**Future Considerations:**
- Multiple attorney accounts
- Admin role for user management
- Permissions per lead (if needed)
- Rate limiting per user

### Security Headers

```python
# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",  # Development frontend
    "https://yourdomain.com"  # Production frontend
]

# Security Headers
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

---

## File Storage Strategy

### Storage Architecture

```mermaid
graph TB
    A[Client Upload] --> B[API Endpoint]
    B --> C{Validate File}
    C -->|Invalid| D[Return 400 Error]
    C -->|Valid| E[Generate Unique Filename]
    E --> F[Save to Disk]
    F --> G[Store Path in Database]
    G --> H[Return Success]
    
    I[Client Download] --> J[API Endpoint]
    J --> K{Authenticate}
    K -->|Fail| L[Return 401 Error]
    K -->|Success| M[Get Lead from DB]
    M --> N{File Exists?}
    N -->|No| O[Return 404 Error]
    N -->|Yes| P[Stream File to Client]
```

### File Naming Strategy

**Format:**
```
{uuid}_{sanitized_filename}{extension}
```

**Example:**
```
a7b3c9d2-4e5f-6789-0123-456789abcdef_john_doe_resume.pdf
```

**Implementation Details:**
- UUID v4 for guaranteed uniqueness
- Base filename sanitized (alphanumeric, dots, dashes, underscores only)
- Filename truncated to 50 characters max
- File extension preserved and normalized to lowercase
- Path traversal characters removed

**Benefits:**
- **Uniqueness**: UUID prevents collisions
- **Security**: Sanitized filename prevents directory traversal and injection attacks
- **User-Friendly**: Original filename partially preserved for identification
- **Compatibility**: Safe across all filesystems

### File Validation

**Allowed Types:**
- `application/pdf` (.pdf)
- `application/msword` (.doc)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (.docx)

**Validation Steps:**
1. **MIME Type**: Check Content-Type header
2. **File Extension**: Verify file extension
3. **File Size**: Maximum 5MB
4. **Magic Bytes**: Verify actual file type (optional, recommended for production)

**Code Example:**
```python
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

### Storage Location

**Development:**
```
{PROJECT_ROOT}/uploads/resumes/
```

**Production Considerations:**
- Local disk (current implementation)
- Network-attached storage (NAS)
- Object storage (S3, Google Cloud Storage, Azure Blob)
- CDN for serving files

### File Security

**Upload Security:**
- Validate file type before saving
- Sanitize filenames (remove ../, special characters)
- Store outside web root
- Implement virus scanning (production)
- Rate limit uploads

**Download Security:**
- Require authentication
- Verify user has access to lead
- Prevent directory traversal attacks
- Set appropriate Content-Disposition header
- Log access for audit trail

### Cleanup Strategy

**Orphaned Files:**
- Background job to identify files without database records
- Retention policy for deleted leads
- Archive old leads before deletion

**Disk Space Management:**
- Monitor disk usage
- Implement size quotas
- Automated cleanup of old files
- Compression for archived files

---

## Email Service Integration

### Email Flow

```mermaid
sequenceDiagram
    participant P as Prospect
    participant API as API Server
    participant LS as Lead Service
    participant ES as Email Service
    participant SMTP as SMTP Server
    participant A as Attorney
    
    P->>API: Submit Lead Form
    API->>LS: Create Lead
    LS->>ES: Send Emails
    
    par Prospect Email
        ES->>SMTP: Send Confirmation
        SMTP->>P: Confirmation Email
    and Attorney Email
        ES->>SMTP: Send Notification
        SMTP->>A: New Lead Alert
    end
    
    ES-->>LS: Email Status
    LS-->>API: Lead Created
    API-->>P: Success Response
```

### Email Templates

#### 1. Prospect Confirmation Email

**Template:** `app/templates/prospect_confirmation.html`  
**Subject:** Thank you for your submission  
**Design:** Professional, clean HTML email with responsive styling  
**Key Elements:**
- Green-themed header with checkmark indicating successful submission
- Personalized greeting with prospect's name
- Submission reference ID (lead UUID) for tracking
- "What Happens Next?" section with clear timeline:
  - Review by attorney team
  - Contact within 3-5 business days
  - Next steps discussion
- Professional signature with company name
- Mobile-responsive design with modern CSS
- Automated disclaimer in footer

**Template Variables:**
- `prospect_name`: Prospect's full name
- `company_name`: Business name from config
- `lead_id`: Unique lead identifier for reference

#### 2. Attorney Notification Email

**Template:** `app/templates/attorney_notification.html`  
**Subject:** New Lead Submission - [Prospect Name]  
**Design:** Action-oriented alert email with prominent call-to-action  
**Key Elements:**
- Blue-themed alert header with "NEW LEAD" badge
- Bell icon for visual attention
- Structured lead details section with key information:
  - Prospect's full name (emphasized)
  - Email address (clickable mailto link)
  - Resume filename
  - Lead ID (monospace reference format)
  - Current status (PENDING, highlighted in orange)
- Prominent "View Lead in Dashboard" button linking to dashboard
- Action required info box with timing expectations
- Professional footer with system information
- Mobile-responsive design

**Template Variables:**
- `prospect_name`: Prospect's full name
- `prospect_email`: Contact email address
- `resume_filename`: Name of uploaded resume file
- `lead_id`: Unique lead identifier
- `dashboard_url`: URL to the internal dashboard

**Note:** Resume file is referenced but not attached in current implementation (can be downloaded from dashboard)

### SMTP Configuration

**Environment Variables:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME="Lead Management System"
ATTORNEY_EMAIL=attorney@yourdomain.com
```

**Supported SMTP Servers:**
- Gmail (with App Password)
- SendGrid
- AWS SES
- Mailgun
- Custom SMTP server

### Error Handling

**Email Sending Strategy:**
- **Async**: Non-blocking email sending
- **Retry Logic**: 3 attempts with exponential backoff
- **Fallback**: Log failure but don't block lead creation
- **Monitoring**: Log all email attempts and failures

**Error Scenarios:**
1. **SMTP Connection Failure**
   - Retry with backoff
   - Log error
   - Don't fail lead creation
2. **Invalid Recipient**
   - Log error
   - Alert admin
   - Continue processing
3. **Template Rendering Error**
   - Use fallback plain text
   - Log error
   - Alert developer

### Email Best Practices

1. **HTML + Plain Text**: Provide both versions
2. **Unsubscribe Link**: For transactional emails (if needed)
3. **Personalization**: Use recipient name
4. **Mobile-Friendly**: Responsive email templates
5. **SPF/DKIM**: Proper email authentication
6. **Rate Limiting**: Prevent abuse

---

## Security Considerations

### Input Validation

**API Level:**
- Pydantic schemas validate all inputs
- Type checking for all fields
- Length constraints (min/max)
- Email format validation
- File type and size validation

**Database Level:**
- Unique constraints
- NOT NULL constraints
- Foreign key constraints
- Check constraints for enums

### SQL Injection Prevention

**Strategy:**
- **SQLAlchemy ORM**: Automatic parameterization
- **Never use raw SQL with user input**
- **Prepared statements**: For complex queries
- **Input validation**: Additional layer of protection

**Example (Safe):**
```python
# SQLAlchemy automatically parameterizes
lead = db.query(Lead).filter(Lead.email == user_input).first()
```

**Example (Unsafe - Avoided):**
```python
# NEVER DO THIS
query = f"SELECT * FROM leads WHERE email = '{user_input}'"
```

### Cross-Site Scripting (XSS) Prevention

**API Protection:**
- FastAPI returns JSON by default (not HTML)
- No direct HTML rendering in API
- Content-Type headers properly set

**Email Templates:**
- Jinja2 auto-escaping enabled
- Sanitize user input in templates
- Use `| safe` filter only for trusted content

### Cross-Site Request Forgery (CSRF)

**Protection:**
- JWT tokens in Authorization header (not cookies)
- SameSite cookie attribute (if using cookies)
- Origin header validation
- CORS properly configured

### Authentication Security

**Token Security:**
- Use strong SECRET_KEY (min 256 bits)
- Rotate secret keys periodically
- Short token expiration (24 hours)
- HTTPS only in production
- Secure token storage (client-side)

**Password Security:**
- bcrypt with sufficient rounds
- No password in logs or errors
- Secure password reset flow
- Account lockout after failed attempts (future)

### File Upload Security

**Validation:**
- Strict file type checking
- File size limits
- Filename sanitization
- Virus scanning (production)

**Storage:**
- Files outside web root
- No direct file serving
- Authenticated access only
- Path traversal prevention

### API Security

**Rate Limiting:**
- Per IP address
- Per authenticated user
- Different limits for public vs. authenticated
- Sliding window algorithm

**Request Size Limits:**
- Maximum request body size
- Maximum file size
- Maximum JSON depth
- Maximum array length

### Data Privacy

**GDPR Compliance:**
- Data minimization (only required fields)
- User consent (terms acceptance)
- Right to deletion (admin function)
- Data export capability
- Audit logging

**PII Protection:**
- Encrypted at rest (database encryption)
- Encrypted in transit (HTTPS/TLS)
- Access logging
- Role-based access
- Data retention policies

### Security Headers

```python
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

### Dependency Security

**Practices:**
- Pin dependency versions
- Regular security audits (`pip-audit`)
- Automated vulnerability scanning
- Keep dependencies updated
- Monitor security advisories

---

## Scalability & Performance

### Current Architecture Scalability

**Single-Server Deployment:**
- Suitable for initial launch
- Handles 100-1000 leads/day
- FastAPI async handles concurrent requests
- Database connection pooling

### Horizontal Scaling Strategy

```mermaid
graph TB
    LB[Load Balancer]
    
    subgraph "Application Tier"
        API1[API Server 1]
        API2[API Server 2]
        API3[API Server N]
    end
    
    subgraph "Database Tier"
        PRIMARY[(Primary DB)]
        REPLICA1[(Read Replica 1)]
        REPLICA2[(Read Replica 2)]
    end
    
    subgraph "Storage Tier"
        S3[Object Storage / S3]
    end
    
    subgraph "Cache Tier"
        REDIS[Redis Cache]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> PRIMARY
    API2 --> PRIMARY
    API3 --> PRIMARY
    
    API1 --> REPLICA1
    API2 --> REPLICA2
    API3 --> REPLICA1
    
    API1 --> S3
    API2 --> S3
    API3 --> S3
    
    API1 --> REDIS
    API2 --> REDIS
    API3 --> REDIS
    
    PRIMARY --> REPLICA1
    PRIMARY --> REPLICA2
```

### Performance Optimizations

#### Database Optimizations

**Indexing:**
- Index on `lead.email` (unique lookups)
- Index on `lead.status` (filtering)
- Index on `lead.created_at` (sorting)
- Composite index on `(status, created_at)` for common queries

**Query Optimization:**
- Eager loading for relationships (if added)
- Pagination for list queries
- Select only needed columns
- Query result caching

**Connection Pooling:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Base pool size
    max_overflow=40,     # Additional connections
    pool_timeout=30,     # Connection timeout
    pool_recycle=3600    # Recycle connections
)
```

#### Application Optimizations

**Async Operations:**
- Async email sending (non-blocking)
- Async file I/O for large files
- Async database queries (with async SQLAlchemy)

**Caching Strategy:**
```python
# Redis cache for read-heavy data
- User session data (JWT validation)
- Lead list queries (with short TTL)
- Configuration settings
- Rate limit counters
```

**Response Compression:**
- Gzip compression for JSON responses
- Reduces bandwidth usage
- Faster response times

#### File Storage Optimization

**Current (Development):**
- Local disk storage
- Direct file serving

**Production Recommendations:**
- **Object Storage** (S3, GCS, Azure Blob)
  - Unlimited scalability
  - High availability
  - Geographic distribution
  - Cost-effective
  
- **CDN** for file serving
  - Edge caching
  - Reduced latency
  - Lower server load

### Load Handling

**Expected Load:**
| Metric | Development | Production (Year 1) |
|--------|-------------|---------------------|
| Leads/day | 10-50 | 100-500 |
| Concurrent users | 1-5 | 10-50 |
| API requests/sec | 1-10 | 50-200 |
| Database size | < 1 GB | 1-10 GB |
| File storage | < 10 GB | 50-200 GB |

**Capacity Planning:**
- Monitor key metrics (response time, error rate, throughput)
- Set up alerts for high load
- Vertical scaling (CPU/RAM) before horizontal
- Horizontal scaling for high availability

### Monitoring & Observability

**Application Metrics:**
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Active connections

**Business Metrics:**
- Leads created per hour
- Email delivery rate
- Status transition frequency
- User login frequency

**Infrastructure Metrics:**
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Database connections

**Logging:**
- Structured logging (JSON)
- Log aggregation (ELK, Datadog, CloudWatch)
- Error tracking (Sentry)
- Request tracing (distributed tracing)

### Future Scaling Considerations

**Database Scaling:**
1. Read replicas for read-heavy workloads
2. Sharding by date or lead ID
3. Archive old leads to separate database
4. Consider NoSQL for analytics

**Application Scaling:**
1. Containerization (Docker)
2. Orchestration (Kubernetes)
3. Auto-scaling policies
4. Blue-green deployments

**Background Jobs:**
1. Task queue (Celery, RQ)
2. Async workers for emails
3. Scheduled jobs for cleanup
4. Background data processing

---

## Error Handling

### Error Response Format

**Standard Error Response:**
```json
{
  "detail": "Human-readable error message",
  "error_code": "LEAD_EMAIL_DUPLICATE",
  "timestamp": "2025-12-14T10:30:00Z",
  "request_id": "uuid",
  "field_errors": {
    "email": ["Email already exists"],
    "file": ["File size exceeds 5MB"]
  }
}
```

### HTTP Status Codes

| Code | Usage | Example |
|------|-------|---------|
| 200 | Success | GET request successful |
| 201 | Created | Lead created successfully |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Lead not found |
| 409 | Conflict | Duplicate email |
| 413 | Payload Too Large | File too large |
| 415 | Unsupported Media Type | Invalid file type |
| 422 | Unprocessable Entity | Invalid request body |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Database connection failure |

### Custom Exceptions

```python
class LeadNotFoundException(HTTPException):
    """Raised when lead is not found."""
    status_code = 404
    detail = "Lead not found"

class DuplicateLeadException(HTTPException):
    """Raised when email already exists."""
    status_code = 409
    detail = "A lead with this email already exists"

class InvalidStatusTransitionException(HTTPException):
    """Raised for invalid status transitions."""
    status_code = 400
    detail = "Invalid status transition"

class FileUploadException(HTTPException):
    """Raised for file upload errors."""
    status_code = 400
    detail = "File upload failed"

class EmailSendException(Exception):
    """Raised when email sending fails."""
    # Don't fail the request, just log
```

### Error Logging

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General information (requests, actions)
- `WARNING`: Recoverable errors (email send failure)
- `ERROR`: Unrecoverable errors (database connection)
- `CRITICAL`: System-level failures

**Logging Strategy:**
```python
import logging

logger = logging.getLogger(__name__)

# Log format
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Log all errors with stack trace
logger.error(f"Failed to create lead", exc_info=True, extra={
    "email": email,
    "request_id": request_id
})
```

---

## Appendix

### Technology Versions

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.13.5 | Runtime environment |
| FastAPI | 0.115.6 | Web framework |
| SQLAlchemy | 2.0.36 | ORM and database toolkit |
| Alembic | 1.14.0 | Database migrations |
| Pydantic | 2.10.6 | Data validation and settings |
| uvicorn | 0.34.0 | ASGI server |
| python-jose | 3.4.0 | JWT token handling |
| passlib | 1.7.4 | Password hashing |
| bcrypt | 4.2.1 | Password hashing algorithm |
| aiosmtplib | 3.0.2 | Async SMTP client |
| Jinja2 | 3.1.5 | Email template engine |
| SQLite | 3.x | Development database |
| PostgreSQL | 14+ | Production database (recommended) |

### Configuration Management

**Environment Variables:**
All configuration via `.env` file (not committed to git)

**Required Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Security
SECRET_KEY=your-256-bit-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
ATTORNEY_EMAIL=attorney@yourdomain.com

# File Storage
UPLOAD_DIR=./uploads/resumes
MAX_FILE_SIZE=5242880

# Application
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

### Development vs. Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Database | SQLite | PostgreSQL |
| Debug Mode | Enabled | Disabled |
| HTTPS | Optional | Required |
| Secret Key | Simple | Complex (256-bit) |
| CORS | Permissive | Restrictive |
| Logging | Console | File + Service |
| Email | Local SMTP | Production SMTP |
| File Storage | Local disk | S3 / Cloud Storage |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-14 | Samir Musali | Initial System Design and Architecture Document |

---

**End of Document**
