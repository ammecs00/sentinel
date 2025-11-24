# Sentinel Backend - Employee Monitoring System

Secure backend API for employee monitoring and activity tracking with PostgreSQL database.

## Features

- ✅ JWT-based authentication with secure password policies
- ✅ API key management for client authorization
- ✅ PostgreSQL database with proper indexing
- ✅ Activity tracking and categorization
- ✅ Client management and monitoring
- ✅ Rate limiting and security middleware
- ✅ Employee consent tracking
- ✅ Data retention policies
- ✅ Comprehensive API documentation
- ✅ Docker support

## Security Features

- Strong password requirements (8+ chars, uppercase, lowercase, numbers, special chars)
- Bcrypt password hashing
- JWT tokens with expiration
- API key authentication for monitoring clients
- Rate limiting per IP
- Failed login attempt tracking
- HTTPS enforcement (production)
- CORS configuration
- SQL injection protection (SQLAlchemy ORM)

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional, for rate limiting)

## Installation

### Local Development

1. **Clone repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Setup database**
```bash
# Create PostgreSQL database
createdb sentinel_db

# Run migrations
alembic upgrade head
```

6. **Run application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env with secure values
```

2. **Generate secure secrets**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Use output for SECRET_KEY and passwords
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Run migrations**
```bash
docker-compose exec backend alembic upgrade head
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key (32+ chars) | Required |
| `INITIAL_ADMIN_PASSWORD` | Admin password | Required |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `ACTIVITY_RETENTION_DAYS` | Days to keep activities | `90` |
| `REQUIRE_EMPLOYEE_CONSENT` | Require consent for monitoring | `true` |

### Database Setup

**PostgreSQL Connection String Format:**
```
postgresql://username:password@host:port/database
```

**Example:**
```
postgresql://sentinel_user:secure_password@localhost:5432/sentinel_db
```

## API Documentation

Once running, access API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Authentication

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "force_password_change": false
}
```

### API Key Creation
```bash
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Client"}'
```

### Activity Reporting (from monitoring clients)
```bash
curl -X POST http://localhost:8000/api/v1/activities/report \
  -H "X-API-Key: sk_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "client-001",
    "active_window": "Visual Studio Code",
    "processes": [...],
    "system_metrics": {...}
  }'
```

## Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## Maintenance

### Cleanup Old Activities
```bash
curl -X POST "http://localhost:8000/api/v1/activities/cleanup?days=90" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Database Backup
```bash
pg_dump -U sentinel_user sentinel_db > backup_$(date +%Y%m%d).sql
```

### Log Rotation

Logs are stored in `app.log`. Configure logrotate:
```bash
/path/to/app.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

## Security Best Practices

1. **Change default credentials immediately**
2. **Use strong SECRET_KEY (32+ random characters)**
3. **Enable HTTPS in production** (`REQUIRE_HTTPS=true`)
4. **Restrict CORS origins** (no wildcards in production)
5. **Use environment-specific .env files**
6. **Regularly update dependencies**
7. **Monitor failed login attempts**
8. **Implement database backups**
9. **Use rate limiting**
10. **Keep audit logs**

## Compliance

### GDPR/CCPA Compliance

- **Employee Consent**: Set `REQUIRE_EMPLOYEE_CONSENT=true`
- **Data Retention**: Configure `ACTIVITY_RETENTION_DAYS`
- **Data Access**: Employees can request their data via admin
- **Data Deletion**: Admin can delete client data

### Audit Logging

All actions are logged when `ENABLE_AUDIT_LOGGING=true`:
- User logins
- Password changes
- API key creation/revocation
- Client registration
- Activity reporting

## Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -U sentinel_user -d sentinel_db
```

### Migration Errors
```bash
# Reset migrations (DEVELOPMENT ONLY)
alembic downgrade base
alembic upgrade head
```

### High Memory Usage
```bash
# Reduce connection pool size in .env
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## License

Proprietary - Employee Monitoring System

## Support

For issues and questions:
- Check documentation: `/docs`
- Review logs: `app.log`
- Database logs: PostgreSQL logs

## Version

Current Version: 2.0.0