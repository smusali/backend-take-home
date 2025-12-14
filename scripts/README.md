# Database Seeding Scripts

This directory contains scripts for initializing and managing database data.

## Scripts

### seed_db.py

Creates the initial admin user account for accessing the attorney dashboard.

**Usage:**
```bash
make seed-db
# or directly:
python scripts/seed_db.py
```

**Default Credentials:**
- Username: `admin`
- Email: `admin@leadmanagement.local`
- Password: `Admin123!SecurePassword`

**Important:** Change the default password after first login!

The script will skip creation if the admin user already exists.

### create_user.py

Creates a new attorney user account with custom credentials.

**Usage:**
```bash
make create-user USERNAME=attorney1 EMAIL=attorney1@firm.com PASSWORD=SecurePass123
# or directly:
python scripts/create_user.py attorney1 attorney1@firm.com SecurePass123
```

**Requirements:**
- **Username:** 3-50 characters, alphanumeric with underscores or hyphens
- **Email:** Valid email format
- **Password:** Minimum 8 characters, must include:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit

**Examples:**
```bash
# Create attorney user
make create-user USERNAME=jsmith EMAIL=jsmith@lawfirm.com PASSWORD=Attorney2024!

# Create another user
make create-user USERNAME=mjones EMAIL=mjones@lawfirm.com PASSWORD=Secure123Pass
```

The script will fail if a user with the same username or email already exists.

## Prerequisites

Before running these scripts:

1. **Environment Setup:**
   ```bash
   make venv
   make install
   make env
   ```

2. **Database Migrations:**
   ```bash
   make migrate-up
   ```

3. **Configuration:**
   Ensure `.env` file is configured with proper database settings.

## Typical Setup Flow

```bash
# 1. Initial setup
make venv
make install
make env

# 2. Configure .env file with your settings
# Edit .env file as needed

# 3. Run migrations
make migrate-up

# 4. Seed initial admin user
make seed-db

# 5. (Optional) Create additional users
make create-user USERNAME=attorney1 EMAIL=attorney1@firm.com PASSWORD=SecurePass123
```

## Error Handling

Both scripts include comprehensive error handling:

- **Duplicate Users:** Scripts check for existing usernames and emails
- **Validation:** Input validation for usernames, emails, and passwords
- **Database Errors:** Clear error messages for database connection issues
- **Graceful Exit:** Proper cleanup on keyboard interrupts

## Security Notes

- Passwords are hashed using bcrypt before storage
- Default admin credentials should be changed immediately
- Strong password requirements are enforced for new users
- Never commit actual passwords to version control
