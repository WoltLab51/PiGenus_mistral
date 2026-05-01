# PiGenus API Documentation

## Base URL
```
http://<pigenus-host>:8000
```

---

## Authentication

All endpoints (except `/health` and `/auth/token`) require a JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### Get Token
```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=<username>&password=<password>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Endpoints

### Health

#### Check System Health
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-01T09:00:00Z",
  "details": {
    "database": "healthy",
    "disk": {
      "status": "healthy",
      "free_mb": 12345
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 45.2
    }
  }
}
```

---

### Workers

#### Register Worker
```
POST /workers/register
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "my-worker",
  "capabilities": {
    "gpu": false,
    "cpu_cores": 8,
    "memory_gb": 16
  }
}
```

**Response:**
```json
{
  "id": 1,
  "name": "my-worker",
  "capabilities": {"gpu": false, "cpu_cores": 8, "memory_gb": 16},
  "status": "online",
  "last_heartbeat": "2026-05-01T09:00:00Z",
  "owner_id": 1
}
```

#### Worker Heartbeat
```
POST /workers/heartbeat
Authorization: Bearer <token>
Content-Type: application/json

{
  "worker_id": 1
}
```

**Response:** Same as register, with updated `last_heartbeat`.

#### List Workers
```
GET /workers/list
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "my-worker",
    "capabilities": {...},
    "status": "online",
    "last_heartbeat": "2026-05-01T09:00:00Z",
    "owner_id": 1
  }
]
```

---

### Jobs

#### Submit Job
```
POST /jobs/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "task": {
    "type": "inference",
    "model": "mistral-7b",
    "prompt": "Hello, world!"
  },
  "priority": 1
}
```

**Response:**
```json
{
  "id": 1,
  "task": {"type": "inference", "model": "mistral-7b", "prompt": "Hello, world!"},
  "status": "pending",
  "priority": 1,
  "created_at": "2026-05-01T09:00:00Z",
  "leased_at": null,
  "completed_at": null,
  "worker_id": null,
  "result": null
}
```

#### Lease Job
```
GET /jobs/lease?worker_id=1
Authorization: Bearer <token>
```

**Response:**
```json
{
  "job": {
    "id": 1,
    "task": {...},
    "status": "leased",
    "priority": 1,
    "created_at": "2026-05-01T09:00:00Z",
    "leased_at": "2026-05-01T09:01:00Z",
    "completed_at": null,
    "worker_id": 1,
    "result": null
  },
  "lease_expires_at": "2026-05-01T09:02:00Z"
}
```

#### Acknowledge Job
```
POST /jobs/1/ack
Authorization: Bearer <token>
Content-Type: application/json

{
  "result": {
    "output": "Hello, world!",
    "time": 0.5
  }
}
```

**Response:**
```json
{
  "status": "acknowledged",
  "job_id": 1
}
```

#### Fail Job
```
POST /jobs/1/fail
Authorization: Bearer <token>
Content-Type: application/json

{
  "error": "Model not found"
}
```

**Response:**
```json
{
  "status": "failed",
  "job_id": 1,
  "error": "Model not found"
}
```

#### List Jobs
```
GET /jobs/list?status=pending
Authorization: Bearer <token>
```

**Response:** Array of job objects.

---

### Memory

#### Set Memory Item
```
POST /memory/set
Authorization: Bearer <token>
Content-Type: application/json

{
  "key": "user_preferences",
  "value": {
    "theme": "dark",
    "language": "de"
  }
}
```

**Response:**
```json
{
  "key": "user_preferences",
  "value": {"theme": "dark", "language": "de"},
  "created_at": "2026-05-01T09:00:00Z",
  "updated_at": "2026-05-01T09:00:00Z"
}
```

#### Get Memory Item
```
GET /memory/get/user_preferences
Authorization: Bearer <token>
```

**Response:** Same as set, or `null` if not found.

#### List Memory Items
```
GET /memory/list
Authorization: Bearer <token>
```

**Response:** Array of all memory items for the user.

---

### Admin

#### System Status
```
GET /admin/status
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "workers": [
    {
      "worker_id": 1,
      "name": "my-worker",
      "status": "online",
      "last_heartbeat": "2026-05-01T09:00:00Z",
      "owner": "admin"
    }
  ],
  "jobs": [
    {
      "job_id": 1,
      "status": "completed",
      "priority": 1,
      "created_at": "2026-05-01T09:00:00Z",
      "worker_id": 1
    }
  ],
  "pending_jobs": 0,
  "running_jobs": 0,
  "completed_jobs": 1,
  "failed_jobs": 0,
  "total_workers": 1,
  "online_workers": 1
}
```

#### Audit Logs
```
GET /admin/audit-logs?limit=50
Authorization: Bearer <admin-token>
```

**Response:** Array of audit log entries.

#### List Users
```
GET /admin/users
Authorization: Bearer <admin-token>
```

**Response:** Array of user objects.

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "timestamp": "2026-05-01T09:00:00Z"
}
```

### Common Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Could not validate credentials` | Invalid or missing JWT token |
| 403 | `Not authorized` | User doesn't have permission |
| 404 | `Not found` | Resource doesn't exist |
| 422 | `Validation Error` | Invalid request data |
| 500 | `Internal Server Error` | Unexpected server error |

---

## Rate Limiting

Rate limiting is planned for future versions. Current limits:
- No hard limits in MVP
- Recommended: Implement at reverse proxy level (nginx)

---

## API Versioning

Current version: `v0.1.0`

Versioning strategy:
- URL path: `/v1/...` (future)
- Currently: No version in path (MVP)

---

## OpenAPI/Swagger

Interactive API documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`
