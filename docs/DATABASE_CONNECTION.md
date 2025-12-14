# Database Connection Setup

## ✅ Completed: Section 2.2 Database Connection Setup

### Files Created

1. **`app/db/database.py`** - Database engine, session factory, and dependencies
2. **`tests/db/test_database.py`** - Comprehensive database connection tests

### Files Updated

3. **`app/db/base.py`** - Added model imports for Alembic
4. **`app/db/__init__.py`** - Export all database utilities

### Core Components

#### Database Engine (`create_db_engine`)

**Features:**
- ✅ Automatic database URL configuration from settings
- ✅ SQLite-specific configuration (`check_same_thread=False`)
- ✅ Connection pooling (pool_size=20, max_overflow=40)
- ✅ Connection pre-ping for health checks
- ✅ Connection recycling (1 hour)
- ✅ SQL query echo in debug mode
- ✅ Connection retry logic with event listeners
- ✅ Disconnection error handling

**Pool Configuration:**
```python
pool_size=20          # Base connection pool size
max_overflow=40       # Additional connections when needed
pool_recycle=3600     # Recycle connections after 1 hour
pool_pre_ping=True    # Verify connections before use
```

#### Session Factory (`create_session_factory`)

**Configuration:**
- ✅ `autocommit=False` - Manual transaction control
- ✅ `autoflush=False` - Explicit flush control
- ✅ Bound to database engine

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
- ✅ Automatic session creation
- ✅ Automatic session cleanup
- ✅ Exception-safe (closes session even on errors)

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
- ✅ Useful for scripts and background tasks
- ✅ Automatic commit on success
- ✅ Automatic rollback on exception
- ✅ Always closes session

#### Database Initialization (`init_db`)

**Usage:**
```python
from app.db import init_db

init_db()  # Creates all tables
```

**Features:**
- ✅ Creates all tables defined in models
- ✅ Retry logic (5 attempts, 2-second delay)
- ✅ Idempotent (safe to call multiple times)
- ✅ Useful for development/testing
- ⚠️ **Production: Use Alembic migrations instead**

#### Connection Cleanup (`close_db`)

**Usage:**
```python
from app.db import close_db

# During application shutdown
close_db()
```

**Features:**
- ✅ Disposes of engine and closes all connections
- ✅ Should be called in FastAPI shutdown event

### Connection Retry Logic

**Event Listeners:**
1. **`connect`** - Tracks connection process ID
2. **`checkout`** - Verifies connection belongs to current process
3. **Automatic failover** - Raises `DisconnectionError` for stale connections

This prevents issues with:
- Forked processes
- Stale connections
- Connection pool corruption

### Test Coverage

**20 comprehensive tests** covering:

#### Engine Tests (3 tests)
- ✅ Engine creation
- ✅ Connection establishment
- ✅ Pool configuration

#### Session Factory Tests (4 tests)
- ✅ Factory creation
- ✅ Session creation
- ✅ Autocommit disabled
- ✅ Autoflush disabled

#### Dependency Injection Tests (3 tests)
- ✅ Yields valid session
- ✅ Closes session after use
- ✅ Can query database

#### Context Manager Tests (3 tests)
- ✅ Provides valid session
- ✅ Commits on success
- ✅ Rolls back on exception

#### Initialization Tests (2 tests)
- ✅ Creates all tables
- ✅ Idempotent operation

#### Integration Tests (2 tests)
- ✅ Lead model database operations
- ✅ User model database operations

### Global Instances

```python
from app.db import engine, SessionLocal

# Engine - Single global instance
engine = create_db_engine()

# Session Factory - Single global factory
SessionLocal = create_session_factory(engine)
```

These are created once at module import and reused throughout the application.

### FastAPI Integration Example

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

All database configuration comes from environment variables via settings:

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

### Best Practices Implemented

✅ **Connection Pooling** - Reuse connections for performance  
✅ **Pre-ping** - Verify connections before use  
✅ **Recycling** - Prevent stale connections  
✅ **Event Listeners** - Handle process forks  
✅ **Retry Logic** - Handle temporary failures  
✅ **Context Managers** - Safe resource cleanup  
✅ **Dependency Injection** - FastAPI integration  
✅ **Global Instances** - Single engine and factory  

### Performance Characteristics

**Connection Pool:**
- Initial: 20 connections ready
- Peak: Up to 60 connections (20 + 40 overflow)
- Reuse: Connections recycled after 1 hour
- Verification: Pre-ping on checkout

**Session Lifecycle:**
- Created on demand
- Closed automatically
- Transactions explicit (no autocommit)
- Flushes explicit (no autoflush)

### Testing

Run database tests:

```bash
pytest tests/db/ -v
```

Expected: **20 tests passing**

Run all tests:

```bash
make unittest
```

Expected: **55 tests passing** (16 config + 23 models + 16 database + 20 database connection)

### Next Steps

This database connection setup is ready for:
1. ✅ Alembic migration initialization (Section 2.3)
2. ✅ Repository pattern implementation (Section 2.4)
3. ✅ Service layer usage (Milestone 4)
4. ✅ API endpoint integration (Milestone 5)
