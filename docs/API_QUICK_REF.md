# API Quick Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Endpoints at a Glance

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/leads` | No | Submit new lead |
| `POST` | `/auth/register` | No | Register attorney |
| `POST` | `/auth/login` | No | Get JWT token |
| `GET` | `/auth/me` | Yes | Current user profile |
| `GET` | `/leads` | Yes | List/filter leads |
| `GET` | `/leads/{id}` | Yes | Get lead details |
| `PATCH` | `/leads/{id}` | Yes | Update lead status |
| `GET` | `/leads/{id}/resume` | Yes | Download resume |
| `GET` | `/health` | No | Health check |

## Authentication Header

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Common Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `500` - Server Error

## Lead Status Values

- `PENDING` - Initial state
- `REACHED_OUT` - Attorney contacted prospect

## Quick Commands

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","email":"user@example.com","password":"Pass123!"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user1&password=Pass123!"
```

### Submit Lead
```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john@example.com" \
  -F "resume=@resume.pdf"
```

### Get Leads
```bash
curl http://localhost:8000/api/v1/leads?page=1&status=PENDING \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Status
```bash
curl -X PATCH http://localhost:8000/api/v1/leads/{id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"REACHED_OUT"}'
```

## Environment Setup

```bash
# Create .env file
cp .env.example .env

# Activate virtual environment
source venv/bin/activate

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Interactive Docs

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

For detailed documentation, see [API_OVERVIEW.md](./API_OVERVIEW.md)
