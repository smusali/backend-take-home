# Docker Deployment Guide

This guide explains how to run the Lead Management API using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- At least 2GB of available RAM
- SMTP credentials for email notifications

## Quick Start

### 1. Environment Configuration

Create a `.env` file in the project root with your configuration:

```bash
# Copy from example
cp .env.example .env

# Edit with your values
nano .env
```

**Important**: Update these required environment variables:

```env
# Security (REQUIRED)
SECRET_KEY=your-secure-secret-key-at-least-32-characters-long

# SMTP Configuration (REQUIRED)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
ATTORNEY_EMAIL=attorney@yourdomain.com
```

### 2. Start Services

```bash
docker-compose up -d
```

This will:
- Build the API application image
- Start PostgreSQL database
- Start the API service
- Create necessary volumes and networks

### 3. Initialize Database

Run database migrations:

```bash
docker-compose exec api alembic upgrade head
```

### 4. Create Admin User (Optional)

```bash
docker-compose exec api python -c "
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
user = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('ChangeMe123!')
)
db.add(user)
db.commit()
print('Admin user created: username=admin, password=ChangeMe123!')
"
```

### 5. Access the Application

- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Docker Compose Services

### API Service

- **Image**: Built from local Dockerfile
- **Port**: 8000:8000
- **Environment**: Production mode by default
- **Volumes**: `./uploads:/app/uploads` for resume storage
- **Dependencies**: PostgreSQL database

### Database Service

- **Image**: postgres:16-alpine
- **Port**: 5432:5432
- **User**: leaduser
- **Password**: leadpassword
- **Database**: leaddb
- **Volume**: `postgres_data` for data persistence

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# Database only
docker-compose logs -f db
```

### Stop Services

```bash
docker-compose stop
```

### Restart Services

```bash
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Stop and Remove Everything

```bash
docker-compose down
```

### Stop and Remove Everything Including Volumes

```bash
docker-compose down -v
```

### Rebuild Images

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Access Container Shell

```bash
# API container
docker-compose exec api /bin/bash

# Database container
docker-compose exec db /bin/bash
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U leaduser -d leaddb

# Run migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history
```

## Environment Variables

The following environment variables can be configured in `.env`:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (min 32 chars) | `openssl rand -hex 32` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_USERNAME` | SMTP authentication username | `your-email@gmail.com` |
| `SMTP_PASSWORD` | SMTP authentication password | `your-app-password` |
| `SMTP_FROM_EMAIL` | Email sender address | `noreply@example.com` |
| `ATTORNEY_EMAIL` | Attorney notification email | `attorney@example.com` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiry (24h) |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_FROM_NAME` | `Lead Management System` | Email sender name |
| `MAX_FILE_SIZE` | `5242880` | Max file size (5MB) |
| `ENVIRONMENT` | `production` | Environment name |
| `DEBUG` | `False` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

## Volume Management

### Uploads Volume

Resume files are stored in `./uploads` on the host, mounted to `/app/uploads` in the container.

```bash
# Backup uploads
tar -czf uploads-backup.tar.gz uploads/

# Restore uploads
tar -xzf uploads-backup.tar.gz
```

### Database Volume

PostgreSQL data is stored in the `postgres_data` Docker volume.

```bash
# Backup database
docker-compose exec db pg_dump -U leaduser leaddb > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U leaduser -d leaddb

# View volume info
docker volume inspect backend-take-home_postgres_data
```

## Health Checks

### API Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### Database Health Check

```bash
docker-compose exec db pg_isready -U leaduser -d leaddb
```

## Troubleshooting

### API Service Won't Start

Check logs:
```bash
docker-compose logs api
```

Common issues:
- Missing `.env` file: Copy from `.env.example`
- Invalid SECRET_KEY: Must be at least 32 characters
- Database not ready: Wait for health check to pass

### Database Connection Issues

Verify database is running:
```bash
docker-compose ps db
```

Check database logs:
```bash
docker-compose logs db
```

Test connection:
```bash
docker-compose exec db psql -U leaduser -d leaddb -c "SELECT 1;"
```

### Port Already in Use

If port 8000 or 5432 is already in use, modify `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "8080:8000"  # Use port 8080 instead
  db:
    ports:
      - "5433:5432"  # Use port 5433 instead
```

### Cannot Write to Uploads Directory

Ensure uploads directory has correct permissions:
```bash
chmod -R 755 uploads
```

### Out of Disk Space

Clean up Docker resources:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

## Production Deployment

### Security Considerations

1. **Generate Strong Secret Key**:
```bash
openssl rand -hex 32
```

2. **Use Environment-Specific Credentials**:
- Don't commit `.env` to version control
- Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

3. **Configure HTTPS**:
- Use a reverse proxy (Nginx, Traefik)
- Obtain SSL certificates (Let's Encrypt)

4. **Update Database Credentials**:
- Change default PostgreSQL password
- Restrict database access

5. **Set Proper CORS Origins**:
```env
CORS_ORIGINS=https://yourdomain.com
```

### Scaling the Application

Increase API replicas:

```yaml
services:
  api:
    deploy:
      replicas: 3
```

Or use Docker Swarm/Kubernetes for production orchestration.

### Monitoring

Add monitoring services to `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus
    # ... configuration

  grafana:
    image: grafana/grafana
    # ... configuration
```

## Development with Docker

### Using Local Code Changes

Mount source code as volume:

```yaml
services:
  api:
    volumes:
      - ./app:/app/app
      - ./uploads:/app/uploads
```

### Running Tests in Container

```bash
# Install dev dependencies
docker-compose exec api pip install -r requirements-dev.txt

# Run tests
docker-compose exec api pytest tests/ -v

# Run with coverage
docker-compose exec api pytest tests/ --cov=app --cov-report=term-missing
```

## Performance Tuning

### Increase Workers

Modify the CMD in Dockerfile:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Database Connection Pool

Adjust PostgreSQL settings in `docker-compose.yml`:

```yaml
services:
  db:
    environment:
      - POSTGRES_MAX_CONNECTIONS=100
    command:
      - "postgres"
      - "-c"
      - "max_connections=100"
      - "-c"
      - "shared_buffers=256MB"
```

## Backup and Restore

### Full System Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker-compose exec -T db pg_dump -U leaduser leaddb > "$BACKUP_DIR/database.sql"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads.tar.gz" uploads/

# Backup .env
cp .env "$BACKUP_DIR/.env"

echo "Backup completed: $BACKUP_DIR"
```

### Full System Restore

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

# Restore database
cat "$BACKUP_DIR/database.sql" | docker-compose exec -T db psql -U leaduser -d leaddb

# Restore uploads
tar -xzf "$BACKUP_DIR/uploads.tar.gz"

# Restore .env
cp "$BACKUP_DIR/.env" .env

echo "Restore completed from: $BACKUP_DIR"
```

## Upgrading

### Application Updates

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### Database Updates

```bash
# Backup first
docker-compose exec db pg_dump -U leaduser leaddb > backup.sql

# Update PostgreSQL version in docker-compose.yml
# Then rebuild
docker-compose down
docker-compose up -d
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

## Support

For issues with Docker deployment, check:
1. Docker logs: `docker-compose logs`
2. Container status: `docker-compose ps`
3. Network connectivity: `docker network inspect backend-take-home_lead-network`
4. Volume mounts: `docker volume ls`
