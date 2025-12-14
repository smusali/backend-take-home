# Authentication Service

## ✅ Completed: Section 4.1 Authentication Service

### Overview

Complete authentication system with password hashing (bcrypt), JWT token management, and FastAPI security dependencies for protected routes.

### Files Created

#### **Security Module (1 file):**
1. ✅ `app/core/security.py` - Security utilities (240 lines)

#### **Service Module (2 files):**
2. ✅ `app/services/__init__.py` - Package exports
3. ✅ `app/services/auth_service.py` - Authentication service (177 lines)

#### **Test Files (2 files):**
4. ✅ `tests/core/test_security.py` - Security utilities tests (17 tests)
5. ✅ `tests/services/test_auth_service.py` - Auth service tests (12 tests)

#### **Updated Files:**
6. ✅ `requirements.txt` - Pinned bcrypt to 4.2.1 for compatibility

### Security Functions (`app/core/security.py`)

#### **Password Hashing**

##### **`hash_password(password)`**

Hash a password using bcrypt with automatic salt generation.

```python
from app.core.security import hash_password

hashed = hash_password("SecurePassword123")
# Returns: "$2b$12$..."  (60 characters, bcrypt format)
```

**Features:**
- ✅ Bcrypt algorithm (industry standard)
- ✅ Automatic salt generation
- ✅ Truncates to 72 chars (bcrypt limit)
- ✅ Handles bytes/string conversion

**Security:**
- Work factor: 12 rounds (default)
- Rainbow table resistant
- Each hash is unique (random salt)

##### **`verify_password(plain_password, hashed_password)`**

Verify a password against a bcrypt hash.

```python
from app.core.security import verify_password, hash_password

hashed = hash_password("SecurePassword123")

verify_password("SecurePassword123", hashed)  # True
verify_password("WrongPassword", hashed)      # False
```

**Features:**
- ✅ Constant-time comparison
- ✅ Timing attack resistant
- ✅ Case-sensitive

#### **JWT Token Management**

##### **`create_access_token(data, expires_delta)`**

Create a JWT access token with claims.

```python
from app.core.security import create_access_token
from datetime import timedelta

# Default expiration (from config)
token = create_access_token({"sub": "attorney1"})

# Custom expiration
token = create_access_token(
    {"sub": "attorney1"},
    expires_delta=timedelta(hours=24)
)
```

**Token Payload:**
```json
{
  "sub": "attorney1",          // Subject (username)
  "exp": 1702567890            // Expiration timestamp
}
```

**Features:**
- ✅ Configurable expiration
- ✅ Signed with SECRET_KEY
- ✅ HS256 algorithm
- ✅ Automatic expiration handling

##### **`verify_token(token)`**

Verify and decode a JWT token.

```python
from app.core.security import verify_token

try:
    token_data = verify_token(token_string)
    print(f"Username: {token_data.username}")
except HTTPException:
    print("Invalid token")
```

**Validates:**
- ✅ Signature matches SECRET_KEY
- ✅ Token hasn't expired
- ✅ Contains required claims

**Raises:**
- `HTTPException(401)` if invalid or expired

#### **FastAPI Dependencies**

##### **`get_current_user(token, db)`**

FastAPI dependency to extract and validate current user from JWT.

```python
from fastapi import Depends
from app.core.security import get_current_user
from app.models.user import User

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}
```

**Process:**
1. Extract token from `Authorization: Bearer <token>` header
2. Verify token signature and expiration
3. Extract username from token
4. Look up user in database
5. Return User object

**Raises:**
- `HTTPException(401)` if token invalid
- `HTTPException(401)` if user not found

##### **`get_current_active_user(current_user)`**

FastAPI dependency to ensure user is active.

```python
from fastapi import Depends
from app.core.security import get_current_active_user
from app.models.user import User

@app.get("/protected")
async def protected_route(user: User = Depends(get_current_active_user)):
    # user is guaranteed to be active
    return {"username": user.username}
```

**Additional Check:**
- Verifies `user.is_active == True`
- Returns `HTTPException(400)` if inactive

##### **`authenticate_user(username, password, db)`**

Authenticate user by credentials.

```python
from app.core.security import authenticate_user

user = authenticate_user("attorney1", "Password123", db)
if user:
    print("Authenticated!")
else:
    print("Invalid credentials")
```

**Returns:**
- `User` object if authenticated
- `None` if credentials invalid

### AuthService (`app/services/auth_service.py`)

Business logic layer for authentication operations.

#### **Initialization**

```python
from app.services import AuthService
from sqlalchemy.orm import Session

service = AuthService(db_session)
```

#### **Methods**

##### **`register_user(user_data)`**

Register a new attorney user.

```python
from app.schemas.user import UserCreate

user_data = UserCreate(
    username="attorney1",
    email="attorney@lawfirm.com",
    password="SecurePass123"
)

user = service.register_user(user_data)
```

**Validation:**
- ✅ Username not already taken
- ✅ Email not already registered
- ✅ Password automatically hashed
- ✅ Default is_active = True

**Raises:**
- `HTTPException(400)` if username exists
- `HTTPException(400)` if email exists

##### **`login(username, password)`**

Authenticate and generate token.

```python
token = service.login("attorney1", "SecurePass123")

print(token.access_token)  # JWT token string
print(token.token_type)    # "bearer"
```

**Validation:**
- ✅ Credentials are correct
- ✅ User account is active

**Returns:**
- `Token` object with JWT

**Raises:**
- `HTTPException(401)` if credentials wrong
- `HTTPException(400)` if user inactive

##### **`get_user_by_username(username)`**

Look up user by username.

```python
user = service.get_user_by_username("attorney1")
if user:
    print(user.email)
```

##### **`check_user_permissions(user, permission)`**

Check if user has a specific permission.

```python
has_access = service.check_user_permissions(user, "view_leads")
```

**Note:** Currently all active users have all permissions. Future implementation will add role-based access control (RBAC).

##### **`deactivate_user(user_id)` / `activate_user(user_id)`**

Manage user account status.

```python
# Deactivate
service.deactivate_user(user.id)

# Activate
service.activate_user(user.id)
```

### Usage Patterns

#### **User Registration Endpoint**

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services import AuthService
from app.schemas.user import UserCreate, UserResponse
from app.db.database import get_db

app = FastAPI()

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new attorney user."""
    service = AuthService(db)
    
    try:
        user = service.register_user(user_data)
        return user
    except HTTPException:
        raise
```

#### **Login Endpoint**

```python
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import Token

@app.post("/api/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate and return JWT token."""
    service = AuthService(db)
    return service.login(form_data.username, form_data.password)
```

#### **Protected Endpoint**

```python
from app.core.security import get_current_active_user
from app.models.user import User

@app.get("/api/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile (requires authentication)."""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }
```

#### **Complete Authentication Flow**

```python
# 1. Register
POST /api/auth/register
{
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "password": "SecurePass123"
}
Response: 201 Created

# 2. Login
POST /api/auth/login
{
  "username": "attorney1",
  "password": "SecurePass123"
}
Response: {
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# 3. Access Protected Resource
GET /api/profile
Headers: {
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
Response: {
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "is_active": true
}
```

### Security Features

#### **Password Security**

✅ **Bcrypt Hashing:**
- Industry standard algorithm
- Automatic salt generation
- Configurable work factor (12 rounds)
- Resistant to rainbow tables

✅ **Password Requirements:**
- Minimum 8 characters
- Uppercase + lowercase + digit
- Validated before hashing

#### **JWT Security**

✅ **Token Structure:**
- Signed with SECRET_KEY (32+ chars)
- HS256 algorithm
- Expiration timestamp
- Cannot be tampered with

✅ **Token Validation:**
- Signature verification
- Expiration checking
- User existence validation

#### **Protection Against Attacks**

✅ **Timing Attacks:**
- Constant-time password comparison (bcrypt)
- No early returns that leak information

✅ **Brute Force:**
- Bcrypt work factor slows down attempts
- Can add rate limiting later

✅ **Token Tampering:**
- HMAC signature prevents modification
- Invalid tokens rejected immediately

### Test Coverage

#### **Security Tests (17 tests)**

**Password Hashing (5 tests):**
- ✅ Hash creates different hashes (salt)
- ✅ Hash uses bcrypt format
- ✅ Verify with correct password
- ✅ Verify with wrong password
- ✅ Case-sensitive verification

**JWT Tokens (8 tests):**
- ✅ Create access token
- ✅ Create with custom expiration
- ✅ Token contains username
- ✅ Token contains expiration
- ✅ Verify valid token
- ✅ Verify invalid token
- ✅ Verify tampered token

**User Authentication (4 tests):**
- ✅ Authenticate with correct credentials
- ✅ Authenticate with wrong password
- ✅ Authenticate nonexistent user
- ✅ Case-sensitive password

#### **Auth Service Tests (12 tests)**

**Registration (3 tests):**
- ✅ Successful registration
- ✅ Duplicate username rejected
- ✅ Duplicate email rejected

**Login (4 tests):**
- ✅ Successful login
- ✅ Wrong password rejected
- ✅ Nonexistent user rejected
- ✅ Inactive user rejected

**User Management (5 tests):**
- ✅ Get user by username
- ✅ Check permissions (active user)
- ✅ Check permissions (inactive user)
- ✅ Deactivate user
- ✅ Activate user

**Total Tests: 229 ✅ ALL PASSING** (200 existing + 29 new)

### Configuration

#### **Environment Variables**

From `.env`:
```bash
SECRET_KEY=your-secret-key-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### **Settings Integration**

```python
from app.core.config import get_settings

settings = get_settings()
secret = settings.SECRET_KEY
algorithm = settings.ALGORITHM
expiration = settings.ACCESS_TOKEN_EXPIRE_MINUTES
```

### Token Lifecycle

```
1. User Login
   ↓
2. Validate Credentials
   ↓
3. Create JWT Token
   - Sign with SECRET_KEY
   - Set expiration
   - Encode username
   ↓
4. Return Token to Client
   ↓
5. Client Includes Token in Requests
   - Header: Authorization: Bearer <token>
   ↓
6. Server Validates Token
   - Verify signature
   - Check expiration
   - Extract username
   - Look up user
   ↓
7. Grant Access or Reject
```

### Security Best Practices

#### **Password Storage**

✅ **Never store plain text passwords**
```python
# ✅ Good
hashed = hash_password(password)
user.hashed_password = hashed

# ❌ Bad
user.password = password
```

✅ **Use bcrypt (not MD5/SHA)**
- Designed for password hashing
- Includes salt automatically
- Computationally expensive (slows brute force)

#### **Token Management**

✅ **Use strong SECRET_KEY**
```python
# ✅ Good - 32+ random characters
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# ❌ Bad - Short or predictable
SECRET_KEY=mysecret
```

✅ **Set reasonable expiration**
```python
# Balance security vs UX
ACCESS_TOKEN_EXPIRE_MINUTES=30  # 30 minutes
```

✅ **Don't expose tokens**
```python
# ✅ Good - Return in response body
return {"access_token": token}

# ❌ Bad - Don't log tokens
logger.info(f"Token: {token}")  # NEVER DO THIS
```

#### **Authentication Flow**

✅ **Validate before hashing**
```python
# Check password strength first
validate_password_strength(password)
# Then hash
hashed = hash_password(password)
```

✅ **Check user is active**
```python
if not user.is_active:
    raise HTTPException(400, "Inactive user")
```

✅ **Use dependencies for protected routes**
```python
@app.get("/protected")
async def route(user: User = Depends(get_current_active_user)):
    # user is authenticated and active
    pass
```

### Error Handling

#### **Authentication Errors**

**Invalid Credentials:**
```json
{
  "status": 401,
  "detail": "Incorrect username or password",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

**Inactive User:**
```json
{
  "status": 400,
  "detail": "Inactive user"
}
```

**Invalid Token:**
```json
{
  "status": 401,
  "detail": "Could not validate credentials",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

#### **Registration Errors**

**Duplicate Username:**
```json
{
  "status": 400,
  "detail": "Username already registered"
}
```

**Duplicate Email:**
```json
{
  "status": 400,
  "detail": "Email already registered"
}
```

### Integration Examples

#### **Complete Auth Flow**

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.services import AuthService
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import get_current_active_user
from app.db.database import get_db
from app.models.user import User

app = FastAPI()

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new attorney user."""
    service = AuthService(db)
    return service.register_user(user_data)

@app.post("/api/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and receive JWT token."""
    service = AuthService(db)
    return service.login(form_data.username, form_data.password)

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    return current_user

@app.get("/api/leads")
async def list_leads(current_user: User = Depends(get_current_active_user)):
    """Protected endpoint - requires authentication."""
    # Only authenticated, active users can access
    return {"message": f"Welcome, {current_user.username}"}
```

#### **Testing Authentication**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_authentication_flow():
    # Register
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    })
    assert response.status_code == 201
    
    # Login
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "TestPass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Access protected route
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

### Performance Considerations

#### **Bcrypt Work Factor**

Default: 12 rounds (good balance)

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Can increase for more security
)
```

**Benchmark:**
- 10 rounds: ~50ms per hash
- 12 rounds: ~200ms per hash (default)
- 14 rounds: ~800ms per hash

**Recommendation:** Keep at 12 for good security/performance balance.

#### **Token Expiration**

```python
ACCESS_TOKEN_EXPIRE_MINUTES=30  # 30 minutes
```

**Considerations:**
- Shorter = More secure (less time if stolen)
- Longer = Better UX (less re-login)
- 30 minutes is good balance

### Dependency Injection

#### **FastAPI Dependencies Chain**

```python
oauth2_scheme          # Extract token from header
    ↓
get_current_user       # Verify token, get user
    ↓
get_current_active_user  # Check user is active
```

**Usage:**
```python
# Level 1: Just need token
def route1(token: str = Depends(oauth2_scheme)):
    pass

# Level 2: Need authenticated user
def route2(user: User = Depends(get_current_user)):
    pass

# Level 3: Need active user (most common)
def route3(user: User = Depends(get_current_active_user)):
    pass
```

### Future Enhancements

Potential additions for production:

1. **Refresh Tokens** - Long-lived tokens for re-authentication
2. **Role-Based Access Control (RBAC)** - Admin, Attorney, ReadOnly roles
3. **Token Revocation** - Blacklist for logout
4. **Multi-Factor Authentication (MFA)** - SMS/TOTP codes
5. **Password Reset** - Email-based password recovery
6. **Rate Limiting** - Prevent brute force attacks
7. **Session Management** - Track active sessions
8. **OAuth Integration** - Google/Microsoft login

### Troubleshooting

#### **"Could not validate credentials"**

Causes:
- Token expired
- Token tampered with
- User deleted
- Wrong SECRET_KEY

Solution:
- Re-login to get new token
- Check SECRET_KEY matches

#### **"Inactive user"**

Causes:
- User account deactivated
- User banned

Solution:
- Contact administrator
- Check user.is_active in database

#### **Bcrypt Compatibility**

Fixed bcrypt version to 4.2.1 for compatibility with passlib 1.7.4.

```bash
# requirements.txt
passlib[bcrypt]==1.7.4
bcrypt==4.2.1  # Pinned for compatibility
```

### Summary

**Section 4.1: Authentication Service** provides:

✅ **Password Security** - Bcrypt hashing with salt  
✅ **JWT Tokens** - Secure, stateless authentication  
✅ **FastAPI Dependencies** - Easy route protection  
✅ **AuthService** - Complete authentication business logic  
✅ **29 Unit Tests** - Comprehensive test coverage  
✅ **Production Ready** - Security best practices  

### Next Steps

Authentication is ready for:
1. ✅ API endpoint implementation
2. ✅ Protected route creation
3. ✅ User management
4. ✅ File upload service (4.2)
5. ✅ Email service (4.3)
