# Authentication Endpoints Documentation

## Overview

Authentication endpoints handle user registration, login, and profile management using JWT tokens.

## Endpoints

### POST /api/v1/auth/register

Register a new attorney user account.

**Request Body:**
```json
{
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "password": "SecurePassword123!"
}
```

**Validation:**
- Username: 3-50 characters, alphanumeric and underscores
- Email: Valid email format
- Password: Minimum 8 characters with uppercase, lowercase, and digit

**Response (201 Created):**
```json
{
  "id": "uuid",
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "is_active": true,
  "created_at": "2024-12-14T10:00:00Z"
}
```

**Errors:**
- `409 Conflict`: Username or email already exists
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Registration failed

---

### POST /api/v1/auth/login

Authenticate and receive a JWT token.

**Request Body (OAuth2 Form):**
```
username: attorney1
password: SecurePassword123!
```

**Note:** Uses OAuth2 password flow for OpenAPI compatibility.

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Details:**
- Algorithm: HS256
- Expiration: 30 minutes (default)
- Claim: `sub` contains username

**Errors:**
- `401 Unauthorized`: Invalid credentials
- `500 Internal Server Error`: Login failed

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=attorney1&password=SecurePassword123!"
```

---

### GET /api/v1/auth/me

Get current authenticated user's profile.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "username": "attorney1",
  "email": "attorney@lawfirm.com",
  "is_active": true,
  "created_at": "2024-12-14T10:00:00Z"
}
```

**Errors:**
- `401 Unauthorized`: Invalid or missing token
- `400 Bad Request`: Inactive user

**Example (curl):**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <jwt_token>"
```

---

## Authentication Flow

```
1. Register (optional)
   POST /api/v1/auth/register
   └─> Returns user profile

2. Login
   POST /api/v1/auth/login
   └─> Returns JWT token

3. Access Protected Resources
   Add header: Authorization: Bearer <token>
   └─> Access /api/v1/leads/* endpoints

4. Check Profile (optional)
   GET /api/v1/auth/me
   └─> Returns current user info
```

## Token Usage

Once you receive a token from `/auth/login`, include it in all protected endpoint requests:

```http
GET /api/v1/leads HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Security Features

- **Password Hashing**: Bcrypt with automatic salt generation
- **JWT Tokens**: Signed with HS256 algorithm
- **Token Expiration**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Password Validation**: Enforces strength requirements
- **Active User Check**: Inactive users cannot access protected resources
- **Unique Constraints**: Username and email must be unique

## Configuration

Environment variables for authentication:

```env
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Integration with OpenAPI

The `/auth/login` endpoint uses OAuth2PasswordBearer, making it compatible with the interactive OpenAPI documentation at `/docs`. You can:

1. Click "Authorize" button in Swagger UI
2. Enter username and password
3. Token is automatically included in subsequent requests

## Related Documentation

- [Security Module](./AUTHENTICATION.md) - Core security functions
- [Protected Endpoints](./PROTECTED_API.md) - JWT-protected lead management
- [User Service](./AUTHENTICATION.md) - User management business logic
