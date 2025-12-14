# Database Migrations

## ✅ Completed: Section 2.3 Database Migrations

### Files Created/Modified

1. **`alembic.ini`** - Alembic configuration file
2. **`alembic/env.py`** - Alembic environment setup with app integration
3. **`alembic/versions/ce27423da2f4_*.py`** - Initial migration (auto-generated)
4. **`Makefile`** - Added 5 migration commands

### Alembic Configuration

#### **`alembic/env.py`** Features:

✅ **Application Integration:**
- Imports `get_settings()` to get DATABASE_URL from app config
- Imports `Base` metadata for autogenerate support
- Sets SQLAlchemy URL dynamically from settings

✅ **Autogenerate Support:**
- `target_metadata = Base.metadata` enables model detection
- `compare_type=True` detects column type changes
- Automatically detects table/column/index changes

✅ **Offline & Online Modes:**
- Offline: SQL script generation
- Online: Direct database execution

#### **`alembic.ini`** Configuration:

- Database URL loaded from app settings (not hardcoded)
- `prepend_sys_path = .` for module imports
- Standard logging configuration

### Initial Migration

**File:** `alembic/versions/ce27423da2f4_initial_migration_create_leads_and_.py`

**Auto-detected Changes:**
- ✅ Created `leads` table with all fields
- ✅ Created `users` table with all fields
- ✅ Created all indexes:
  - `ix_leads_email` (unique)
  - `ix_leads_status`
  - `ix_leads_created_at`
  - `ix_leads_id`
  - `idx_lead_status_created` (composite)
  - `ix_users_username` (unique)
  - `ix_users_email` (unique)
  - `ix_users_id`
- ✅ Created enum type for LeadStatus
- ✅ Proper upgrade() and downgrade() functions

### Makefile Migration Commands

#### **1. `make migrate-up`**
Apply all pending migrations to the database.

```bash
make migrate-up
```

**Output:**
```
Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade  -> ce27423da2f4
Migrations applied successfully.
```

#### **2. `make migrate-down`**
Revert the last migration.

```bash
make migrate-down
```

**Use case:** Undo the most recent migration if something went wrong.

#### **3. `make migrate-create MSG='description'`**
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

#### **4. `make migrate-history`**
View all migrations with details.

```bash
make migrate-history
```

**Output:**
```
ce27423da2f4 -> (head), Initial migration: create leads and users tables
```

#### **5. `make migrate-current`**
Show current migration revision.

```bash
make migrate-current
```

**Output:**
```
Current revision(s) for sqlite:///./leads.db:
Rev: ce27423da2f4 (head)
Parent: <base>
Path: .../alembic/versions/ce27423da2f4_initial_migration_create_leads_and_.py
```

### Migration Workflow

#### **Development Workflow:**

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
make unittest

# 7. If something goes wrong, rollback
make migrate-down
```

#### **Team Collaboration:**

```bash
# Pull latest code
git pull

# Apply any new migrations
make migrate-up

# Your database is now up to date
```

### Migration Best Practices

#### **Before Creating Migration:**
1. ✅ Ensure all model changes are complete
2. ✅ Review existing migrations
3. ✅ Have a `.env` file configured

#### **After Auto-generation:**
1. ✅ **Review the generated file** - Autogenerate isn't perfect
2. ✅ **Check upgrade()** - Verify all changes are correct
3. ✅ **Check downgrade()** - Ensure rollback works
4. ✅ **Test locally** - Apply and rollback before committing

#### **Production Deployment:**
1. ✅ Backup database before migration
2. ✅ Test migrations on staging first
3. ✅ Use `make migrate-up` to apply
4. ✅ Monitor for errors
5. ✅ Have rollback plan (`make migrate-down`)

### Migration File Structure

```python
# alembic/versions/ce27423da2f4_*.py

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

#### **Add Column:**
```python
# Make model change first
class Lead(Base):
    new_field: Mapped[str] = mapped_column(String(100))

# Then generate migration
make migrate-create MSG='Add new_field to Lead'
```

#### **Modify Column:**
```python
# Autogenerate detects this if compare_type=True
# Change String(100) to String(200)
make migrate-create MSG='Increase field length'
```

#### **Add Index:**
```python
# Add index in model
__table_args__ = (
    Index('idx_new_field', 'new_field'),
)

make migrate-create MSG='Add index on new_field'
```

### Troubleshooting

#### **Migration Fails:**
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

#### **Autogenerate Misses Changes:**
- Ensure models are imported in `app/db/base.py`
- Check `target_metadata` in `alembic/env.py`
- Verify `compare_type=True` is set

#### **Database Out of Sync:**
```bash
# Stamp database with current revision
source venv/bin/activate
alembic stamp head

# Or start fresh (development only!)
rm leads.db
make migrate-up
```

### SQLite vs PostgreSQL

#### **Development (SQLite):**
- Simple file-based database
- No server needed
- Good for local development
- Some limitations (ALTER TABLE)

#### **Production (PostgreSQL):**
- Full-featured database
- Better performance
- Supports all migration operations
- Change `DATABASE_URL` in `.env`:
  ```
  DATABASE_URL=postgresql://user:pass@localhost/dbname
  ```

### Migration Testing

```bash
# Apply migration
make migrate-up

# Run tests
make unittest

# Check migration is reversible
make migrate-down

# Re-apply
make migrate-up
```

### Summary

**Section 2.3: Database Migrations** provides:

✅ **Alembic Integration** - Configured with app settings  
✅ **Autogenerate** - Automatic migration generation  
✅ **Initial Migration** - Leads and users tables created  
✅ **Makefile Commands** - 5 convenient migration commands  
✅ **Version Control** - All migrations tracked in `alembic/versions/`  
✅ **Reversible** - All migrations have upgrade/downgrade  
✅ **Production Ready** - Works with SQLite and PostgreSQL  

### Next Steps

Migrations are ready for:
1. ✅ Repository pattern implementation (Section 2.4)
2. ✅ Future model changes (auto-detected)
3. ✅ Team collaboration (shared migrations)
4. ✅ Production deployment (tested and reversible)
