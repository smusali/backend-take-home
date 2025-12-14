# Database Documentation

**Version:** 1.0.0  
**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Database Models](#database-models)
3. [Database Connection](#database-connection)
4. [Database Migrations](#database-migrations)
5. [Repository Pattern](#repository-pattern)
6. [Best Practices](#best-practices)

---

## Overview

The Lead Management API uses SQLAlchemy 2.0 as the ORM with support for both SQLite (development) and PostgreSQL (production). The database layer implements a three-tier architecture: Models → Repositories → Services.

### Architecture

```
┌─────────────────────────────────────────────┐
│         Service Layer                       │
│     (Business Logic)                        │
└─────────────────┬───────────────────────────┘
                  │ uses
                  ▼
┌─────────────────────────────────────────────┐
│         Repository Layer                    │
│  ┌────────────────────────────────────┐    │
│  │      BaseRepository<T>              │    │
│  │  - create(), get(), update()        │    │
│  │  - delete(), get_multi(), count()   │    │
│  └────────┬───────────────┬─────────────┘   │
│           │               │                  │
│     ┌─────▼──────┐  ┌────▼──────────┐      │
│     │LeadRepo    │  │UserRepo       │      │
│     │+ specific  │  │+ specific     │      │
│     │  methods   │  │  methods      │      │
│     └────────────┘  └───────────────┘      │
└─────────────────┬───────────────────────────┘
                  │ uses
                  ▼
┌─────────────────────────────────────────────┐
│         Model Layer                         │
│     (SQLAlchemy ORM Models)                 │
│     - Lead Model                            │
│     - User Model                            │
└─────────────────┬───────────────────────────┘
                  │ uses
                  ▼
┌─────────────────────────────────────────────┐
│         Database                            │
│     SQLite (dev) / PostgreSQL (prod)        │
└─────────────────────────────────────────────┘
```

### Technology Stack

- **ORM**: SQLAlchemy 2.0.36
- **Migrations**: Alembic 1.14.0
- **Development DB**: SQLite 3.x
- **Production DB**: PostgreSQL 14+

---

## Database Models

### Lead Model

Located in `app/models/lead.py`

**Purpose:** Represents a prospect's submission with contact information and resume.

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `first_name` | String(100) | NOT NULL | Prospect's first name |
| `last_name` | String(100) | NOT NULL | Prospect's last name |
| `email` | String(255) | UNIQUE, NOT NULL, INDEXED | Prospect's email |
| `resume_path` | String(500) | NOT NULL | Path to resume file |
| `status` | Enum | NOT NULL, DEFAULT='PENDING', INDEXED | Lead status |
| `created_at` | DateTime | NOT NULL, INDEXED | Creation timestamp |
| `updated_at` | DateTime | NOT NULL | Last update timestamp |
| `reached_out_at` | DateTime | NULLABLE | When attorney reached out |

**Indexes:**
- Primary key on `id`
- Unique index on `email`
- Index on `status`
- Index on `created_at`
- Composite index on `(status, created_at)` for efficient filtering

**LeadStatus Enum:**
- `PENDING`: Initial state when prospect submits form
- `REACHED_OUT`: Attorney has contacted the prospect

**Example:**
```python
from app.models import Lead, LeadStatus

lead = Lead(
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    resume_path="/uploads/resumes/uuid_resume.pdf"
)
# Default status is PENDING

# Update status
lead.status = LeadStatus.REACHED_OUT
lead.reached_out_at = datetime.now(UTC)
```

### User Model

Located in `app/models/user.py`

**Purpose:** Represents attorney user accounts for authentication.

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `username` | String(50) | UNIQUE, NOT NULL, INDEXED | Username for login |
| `email` | String(255) | UNIQUE, NOT NULL, INDEXED | User's email |
| `hashed_password` | String(255) | NOT NULL | Bcrypt hashed password |
| `is_active` | Boolean | NOT NULL, DEFAULT=TRUE | Account status |
| `created_at` | DateTime | NOT NULL | Account creation timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `username`
- Unique index on `email`

**Example:**
```python
from app.models import User

user = User(
    username="attorney1",
    email="attorney@lawfirm.com",
    hashed_password="$2b$12$..."  # bcrypt hash
)
# Default is_active is True
```

### Design Decisions

**UUID Primary Keys:**
- **Security**: Non-sequential IDs prevent enumeration attacks
- **Distribution**: Can be generated client-side if needed
- **Privacy**: Doesn't leak business metrics (e.g., number of users)
- **Trade-off**: Larger storage (16 bytes vs 4/8 bytes for int)

**Enum for Status:**
- **Type Safety**: Only valid statuses allowed
- **Database Integrity**: Enforced at DB level
- **Performance**: Efficient storage and indexing
- **Clarity**: Self-documenting valid states

**Timestamps Strategy:**
- `created_at`: Audit trail, sorting, analytics
- `updated_at`: Track modifications (auto-updated)
- `reached_out_at`: Business metric (nullable for PENDING leads)

**String Lengths:**
- Names: 100 characters (sufficient for real names)
- Email: 255 characters (RFC 5321 standard)
- Username: 50 characters (typical username length)
- Resume path: 500 characters (long file paths)
- Hashed password: 255 characters (bcrypt output)

### SQLAlchemy 2.0 Features

- **Mapped columns**: Type-safe column definitions with `Mapped[Type]`
- **Declarative base**: Modern SQLAlchemy 2.0 syntax
- **Type hints**: Full typing support throughout
- **Native enums**: Enum with `native_enum=False` for SQLite compatibility

---

## Database Connection

### Core Components

#### Database Engine

Located in `app/db/database.py`

**Configuration:**
```python
pool_size=20          # Base connection pool size
max_overflow=40       # Additional connections when needed
pool_recycle=3600     # Recycle connections after 1 hour
pool_pre_ping=True    # Verify connections before use
```

**Features:**
- Automatic database URL configuration from settings
- SQLite-specific configuration (`check_same_thread=False`)
- Connection pooling for performance
- Connection pre-ping for health checks
- Connection recycling to prevent stale connections
- SQL query echo in debug mode
- Connection retry logic with event listeners

#### Session Factory

**Configuration:**
- `autocommit=False` - Manual transaction control
- `autoflush=False` - Explicit flush control
- Bound to database engine

#### FastAPI Dependency (`get_db`)

**Usage:**
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db

@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).all()
```

**Features:**
- Automatic session creation
- Automatic session cleanup
- Exception-safe (closes session even on errors)

#### Context Manager (`get_db_context`)

**Usage:**
```python
from app.db import get_db_context

with get_db_context() as db:
    leads = db.query(Lead).all()
    # Auto-commits on success
    # Auto-rolls back on exception
```

**Features:**
- Useful for scripts and background tasks
- Automatic commit on success
- Automatic rollback on exception
- Always closes session

#### Database Initialization (`init_db`)

**Usage:**
```python
from app.db import init_db

init_db()  # Creates all tables
```

**Features:**
- Creates all tables defined in models
- Retry logic (5 attempts, 2-second delay)
- Idempotent (safe to call multiple times)
- Useful for development/testing
- **Production: Use Alembic migrations instead**

#### Connection Cleanup (`close_db`)

**Usage:**
```python
from app.db import close_db

# During application shutdown
close_db()
```

**Features:**
- Disposes of engine and closes all connections
- Should be called in FastAPI shutdown event

### Connection Retry Logic

**Event Listeners:**
1. **`connect`** - Tracks connection process ID
2. **`checkout`** - Verifies connection belongs to current process
3. **Automatic failover** - Raises `DisconnectionError` for stale connections

This prevents issues with:
- Forked processes
- Stale connections
- Connection pool corruption

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db import get_db, close_db

app = FastAPI()

@app.on_event("shutdown")
def shutdown_event():
    close_db()

@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).all()
```

### Configuration

All database configuration comes from environment variables:

```bash
# .env
DATABASE_URL=sqlite:///./leads.db           # Development
# DATABASE_URL=postgresql://user:pass@host/db  # Production
DEBUG=True                                   # Enable SQL query logging
```

### Development vs Production

| Feature | Development (SQLite) | Production (PostgreSQL) |
|---------|---------------------|-------------------------|
| Connection | File-based | Network connection |
| check_same_thread | False | N/A |
| Pool size | 20 | 20 |
| Max overflow | 40 | 40 |
| Recycle time | 1 hour | 1 hour |
| Pre-ping | Enabled | Enabled |
| Echo SQL | DEBUG=True | DEBUG=False |

---

## Database Migrations

### Overview

Database schema versioning is managed by Alembic, which tracks changes and provides upgrade/downgrade paths.

### Configuration

**Files:**
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Environment setup with app integration
- `alembic/versions/` - Migration scripts

**Integration Features:**
- Imports `get_settings()` to get DATABASE_URL from app config
- Imports `Base` metadata for autogenerate support
- Sets SQLAlchemy URL dynamically from settings
- `compare_type=True` detects column type changes

### Makefile Commands

**`make migrate-up`**

Apply all pending migrations to the database.

```bash
make migrate-up
```

**Output:**
```
Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> 076f6036418b
Migrations applied successfully.
```

**`make migrate-down`**

Revert the last migration.

```bash
make migrate-down
```

**Use case:** Undo the most recent migration if something went wrong.

**`make migrate-create MSG='description'`**

Create a new migration with autogenerate.

```bash
make migrate-create MSG='Add user role field'
```

**Features:**
- Requires `MSG` parameter
- Uses `--autogenerate` to detect model changes
- Generates migration file automatically

**Output:**
```
Creating new migration: Add user role field
INFO  [alembic.autogenerate.compare] Detected added column 'users.role'
Generating alembic/versions/abc123_add_user_role_field.py ...  done
```

**`make migrate-history`**

View all migrations with details.

```bash
make migrate-history
```

**`make migrate-current`**

Show current migration revision.

```bash
make migrate-current
```

**Output:**
```
Current revision(s) for sqlite:///./leads.db:
Rev: 076f6036418b (head)
Parent: <base>
```

### Migration Workflow

#### Development Workflow

```bash
# 1. Setup project
make venv
make install
make env

# 2. Make model changes
# Edit app/models/lead.py or app/models/user.py

# 3. Generate migration
make migrate-create MSG='Add new field to Lead model'

# 4. Review the generated migration file
# Check alembic/versions/latest_file.py

# 5. Apply migration
make migrate-up

# 6. Test changes
make test

# 7. If something goes wrong, rollback
make migrate-down
```

#### Team Collaboration

```bash
# Pull latest code
git pull

# Apply any new migrations
make migrate-up

# Your database is now up to date
```

### Migration Best Practices

**Before Creating Migration:**
1. Ensure all model changes are complete
2. Review existing migrations
3. Have a `.env` file configured

**After Auto-generation:**
1. **Review the generated file** - Autogenerate isn't perfect
2. **Check upgrade()** - Verify all changes are correct
3. **Check downgrade()** - Ensure rollback works
4. **Test locally** - Apply and rollback before committing

**Production Deployment:**
1. Backup database before migration
2. Test migrations on staging first
3. Use `make migrate-up` to apply
4. Monitor for errors
5. Have rollback plan (`make migrate-down`)

### Migration File Structure

```python
# alembic/versions/076f6036418b_*.py

def upgrade() -> None:
    """Apply migration changes."""
    # Create tables
    op.create_table('leads', ...)
    
    # Create indexes
    op.create_index('ix_leads_email', ...)
    
    # Add columns (in future migrations)
    # op.add_column('leads', sa.Column('new_field', ...))

def downgrade() -> None:
    """Revert migration changes."""
    # Reverse operations in opposite order
    op.drop_index('ix_leads_email', ...)
    op.drop_table('leads')
```

### Common Migration Operations

**Add Column:**
```python
# Make model change first
class Lead(Base):
    new_field: Mapped[str] = mapped_column(String(100))

# Then generate migration
make migrate-create MSG='Add new_field to Lead'
```

**Modify Column:**
```python
# Autogenerate detects this if compare_type=True
# Change String(100) to String(200)
make migrate-create MSG='Increase field length'
```

**Add Index:**
```python
# Add index in model
__table_args__ = (
    Index('idx_new_field', 'new_field'),
)

make migrate-create MSG='Add index on new_field'
```

### Troubleshooting

**Migration Fails:**
```bash
# Check current state
make migrate-current

# View history
make migrate-history

# Rollback if needed
make migrate-down

# Fix issue and try again
make migrate-up
```

**Autogenerate Misses Changes:**
- Ensure models are imported in `app/db/base.py`
- Check `target_metadata` in `alembic/env.py`
- Verify `compare_type=True` is set

**Database Out of Sync:**
```bash
# Stamp database with current revision
source venv/bin/activate
alembic stamp head

# Or start fresh (development only!)
rm leads.db
make migrate-up
```

---

## Repository Pattern

### Overview

The repository pattern provides a clean abstraction layer between business logic and data access, improving maintainability, testability, and following SOLID principles.

### BaseRepository

Located in `app/db/repositories/base.py`

Generic base repository providing CRUD operations for any model.

**Features:**
- Generic type parameter `ModelType` for type safety
- Standard CRUD operations
- Works with any SQLAlchemy model

**Methods:**

**`create(obj_in: dict) -> ModelType`**

Create a new record.

```python
from app.db.repositories.base import BaseRepository
from app.models.lead import Lead

repo = BaseRepository(Lead, db_session)
lead = repo.create({"first_name": "John", "email": "john@example.com"})
```

**`get(id: UUID) -> Optional[ModelType]`**

Retrieve by UUID.

```python
lead = repo.get(lead_id)
if lead:
    print(lead.email)
```

**`get_multi(skip: int = 0, limit: int = 100) -> List[ModelType]`**

Paginated retrieval.

```python
leads = repo.get_multi(skip=0, limit=20)
```

**`update(id: UUID, obj_in: dict) -> Optional[ModelType]`**

Update existing record.

```python
updated = repo.update(lead_id, {"first_name": "Jane"})
```

**`delete(id: UUID) -> bool`**

Delete record.

```python
deleted = repo.delete(lead_id)
```

**`count() -> int`**

Total count.

```python
total = repo.count()
```

### LeadRepository

Located in `app/db/repositories/lead_repository.py`

Lead-specific repository extending BaseRepository.

**Additional Methods:**

**`get_by_email(email: str) -> Optional[Lead]`**

Find lead by email.

```python
from app.db.repositories.lead_repository import LeadRepository

repo = LeadRepository(Lead, db_session)
lead = repo.get_by_email("john@example.com")
```

**`get_by_status(status: LeadStatus, skip: int = 0, limit: int = 100) -> List[Lead]`**

Filter by status with pagination.

```python
from app.models.lead import LeadStatus

pending = repo.get_by_status(LeadStatus.PENDING, skip=0, limit=20)
```

**`update_status(lead_id: UUID, status: LeadStatus) -> Optional[Lead]`**

Update status and automatically set `reached_out_at` timestamp.

```python
updated = repo.update_status(lead.id, LeadStatus.REACHED_OUT)
print(f"Reached out at: {updated.reached_out_at}")
```

**Smart Features:**
- Automatically sets `reached_out_at` timestamp when status changes to `REACHED_OUT`
- Preserves timestamp if already set
- Updates `updated_at` automatically

**`get_leads_paginated(skip: int = 0, limit: int = 100, status: Optional[LeadStatus] = None, search: Optional[str] = None) -> Tuple[List[Lead], int]`**

Advanced filtering with pagination.

```python
leads, total = repo.get_leads_paginated(
    skip=0,
    limit=10,
    status=LeadStatus.PENDING,
    search="john"
)
```

**Features:**
- Case-insensitive search across first name, last name, and email
- Returns both data and total count
- Ordered by creation date (newest first)

**`get_recent_leads(limit: int = 10) -> List[Lead]`**

Most recent leads.

```python
recent = repo.get_recent_leads(limit=5)
```

**`count_by_status(status: LeadStatus) -> int`**

Count by status.

```python
pending_count = repo.count_by_status(LeadStatus.PENDING)
```

### UserRepository

Located in `app/db/repositories/user_repository.py`

User-specific repository extending BaseRepository.

**Additional Methods:**

**`get_by_username(username: str) -> Optional[User]`**

Find user by username.

```python
from app.db.repositories.user_repository import UserRepository

repo = UserRepository(User, db_session)
user = repo.get_by_username("attorney1")
```

**`get_by_email(email: str) -> Optional[User]`**

Find user by email.

```python
user = repo.get_by_email("attorney@example.com")
```

**`get_active_users(skip: int = 0, limit: int = 100) -> List[User]`**

Get only active users.

```python
active_users = repo.get_active_users(skip=0, limit=20)
```

**`deactivate_user(user_id: UUID) -> Optional[User]`**

Set `is_active` to False.

```python
repo.deactivate_user(user.id)
```

**`activate_user(user_id: UUID) -> Optional[User]`**

Set `is_active` to True.

```python
repo.activate_user(user.id)
```

### Usage Patterns

#### In FastAPI Endpoints

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.repositories import LeadRepository
from app.models.lead import Lead

@app.get("/leads")
def get_leads(
    status: Optional[LeadStatus] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    repo = LeadRepository(Lead, db)
    leads, total = repo.get_leads_paginated(
        skip=skip,
        limit=limit,
        status=status,
        search=search
    )
    return {"items": leads, "total": total}
```

#### In Service Layer

```python
class LeadService:
    def __init__(self, db: Session):
        self.lead_repo = LeadRepository(Lead, db)
    
    def create_lead(self, lead_data: dict) -> Lead:
        # Check if email exists
        existing = self.lead_repo.get_by_email(lead_data["email"])
        if existing:
            raise ValueError("Lead already exists")
        
        return self.lead_repo.create(lead_data)
```

### Design Benefits

**1. Separation of Concerns**
- Business logic doesn't know about SQL
- Database operations centralized
- Easy to swap ORM or database

**2. Type Safety**
- Generic `ModelType` parameter
- IDE autocomplete support
- Compile-time type checking

**3. DRY Principle**
- Common CRUD in BaseRepository
- No repetitive database code
- Specialized methods in subclasses

**4. Testability**
- Easy to mock repositories
- Unit tests without database
- Clear interfaces

**5. Maintainability**
- Single place for queries
- Easy to optimize queries
- Clear method signatures

---

## Best Practices

### Connection Management

**Always use dependency injection:**
```python
# Good
@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).all()

# Bad
def get_leads():
    db = SessionLocal()  # Manual session management
    return db.query(Lead).all()
```

### Transaction Management

**Let repositories handle commits:**
```python
# Good - repository commits internally
repo = LeadRepository(Lead, db)
lead = repo.create(lead_data)

# For custom workflows
try:
    lead = repo.create(lead_data)
    # Additional operations...
    db.commit()
except:
    db.rollback()
    raise
```

### Query Optimization

**Use indexed columns for filtering:**
```python
# Good - uses indexed email column
lead = repo.get_by_email("john@example.com")

# Good - uses indexed status column
pending = repo.get_by_status(LeadStatus.PENDING)

# Good - uses composite index
leads = db.query(Lead).filter(
    Lead.status == LeadStatus.PENDING
).order_by(Lead.created_at.desc()).all()
```

### Migration Management

**Always review auto-generated migrations:**
```bash
# After generating migration
make migrate-create MSG='Add new field'

# Review the file in alembic/versions/
cat alembic/versions/latest_migration.py

# Test locally
make migrate-up
make test
make migrate-down
make migrate-up
```

### Repository Usage

**Use appropriate repository methods:**
```python
# Good - use specialized methods
lead = repo.get_by_email("john@example.com")

# Less ideal - manual query
lead = db.query(Lead).filter(Lead.email == "john@example.com").first()
```

### Error Handling

**Handle database errors appropriately:**
```python
from sqlalchemy.exc import IntegrityError

try:
    repo.create({"email": "john@example.com"})
except IntegrityError:
    raise HTTPException(
        status_code=400,
        detail="Email already exists"
    )
```

---

## Related Documentation

- [API Documentation](./API.md) - API endpoint reference
- [Services Documentation](./SERVICES.md) - Business logic layer
- [Schema Documentation](./SCHEMA.md) - Data validation schemas
- [Design Documentation](./DESIGN.md) - System architecture

---

**Database Version:** 1.0.0  
**Last Updated:** December 2025  
**Test Coverage:** 57+ tests across all database components
