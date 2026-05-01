# PiGenus

**Private Orchestration Node for the GENUS Ecosystem**

PiGenus is a **persistent orchestration node** designed to run on a **Raspberry Pi 5** as the core infrastructure component for the GENUS ecosystem. It provides:

- **Long-term memory and persistence** (sessions, messages, tasks, memory)
- **Task queue and job lifecycle management**
- **Worker coordination** (laptops, workstations, cloud workers)
- **Secure remote private access** (Tailscale/WireGuard ready)
- **Administration and monitoring**
- **Nightly maintenance workflows** (backup, cleanup, summarization)
- **Development workflow orchestration** (GitHub/coding agents integration)

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/WoltLab51/PiGenus_mistral.git
cd PiGenus_mistral
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings (SECRET_KEY, DATABASE_URL, etc.)
```

### 4. Initialize Database
```bash
python scripts/init_db.py
```

### 5. Run PiGenus
```bash
uvicorn api.main:app --reload
```

### 6. Deploy with systemd (Production)
```bash
# Copy systemd services
sudo cp systemd/pigenus.service /etc/systemd/system/
sudo cp systemd/pigenus-scheduler.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable pigenus
sudo systemctl enable pigenus-scheduler
sudo systemctl start pigenus
sudo systemctl start pigenus-scheduler
```

---

## 📡 API Documentation

The API is available at:
- **Swagger UI**: `http://<host>:8000/docs`
- **ReDoc**: `http://<host>:8000/redoc`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/token` | POST | Generate JWT token |
| `/workers/register` | POST | Register a worker |
| `/workers/heartbeat` | POST | Worker heartbeat |
| `/workers/list` | GET | List all workers |
| `/jobs/submit` | POST | Submit a job |
| `/jobs/lease` | GET | Lease a job |
| `/jobs/{id}/ack` | POST | Acknowledge job completion |
| `/jobs/{id}/fail` | POST | Report job failure |
| `/memory/get/{key}` | GET | Retrieve memory item |
| `/memory/set` | POST | Store memory item |
| `/admin/status` | GET | Admin status (workers, jobs, metrics) |

---

## 📂 Project Structure

```
pigenus/
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt
│
├── api/
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── auth.py               # JWT authentication
│   ├── dependencies.py       # Dependencies (DB session)
│   ├── middleware.py         # Rate limiting, logging
│   └── endpoints/
│       ├── __init__.py
│       ├── health.py         # /health
│       ├── auth.py           # /auth/token
│       ├── workers.py        # /workers/*
│       ├── jobs.py           # /jobs/*
│       ├── memory.py         # /memory/*
│       └── admin.py          # /admin/*
│
├── core/
│   ├── __init__.py
│   ├── config.py             # Settings (Pydantic)
│   ├── job_manager.py        # Job lifecycle
│   ├── worker_manager.py     # Worker coordination
│   └── scheduler.py          # Nightly jobs (APScheduler)
│
├── db/
│   ├── __init__.py
│   ├── database.py           # SQLite connection
│   └── models.py             # SQLModel entities
│
├── models/
│   ├── __init__.py
│   ├── schemas.py            # Pydantic schemas
│   └── enums.py              # Status enums
│
├── workers/
│   ├── __init__.py
│   └── client.py             # Worker client (for testing)
│
├── memory/
│   ├── __init__.py
│   ├── storage.py            # Memory storage (SQLite)
│   └── summarizer.py         # Session summarization
│
├── security/
│   ├── __init__.py
│   ├── tokens.py             # JWT token management
│   └── validation.py         # Input validation
│
├── services/
│   ├── __init__.py
│   ├── audit.py              # Audit logs
│   └── backup.py             # Backup logic
│
├── monitoring/
│   ├── __init__.py
│   ├── health.py             # Health checks
│   └── metrics.py            # Prometheus metrics
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # pytest fixtures
│   ├── test_api.py           # API tests
│   ├── test_core.py          # Core logic tests
│   └── test_db.py            # DB tests
│
├── docs/
│   ├── architecture.md       # Architecture documentation
│   ├── api.md                # API documentation
│   └── deployment.md         # Deployment guide
│
├── scripts/
│   ├── init_db.py            # DB initialization
│   └── nightly_jobs.sh       # Cron jobs (backup)
│
└── systemd/
    ├── pigenus.service       # Main service
    └── pigenus-scheduler.service  # Scheduler service
```

---

## 🔧 Development

### Run Tests
```bash
pytest -v
```

### Code Quality
```bash
black .
isort .
flake8
```

---

## 🔒 Security

- **Token Authentication**: All endpoints (except `/health`) require a JWT token.
- **Input Validation**: All requests are validated with Pydantic.
- **Rate Limiting**: Ready for implementation (see `api/middleware.py`).
- **Secrets**: Loaded only via environment variables or config files.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
