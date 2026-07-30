# Larp — AI-Powered Multi-Step Research Agent (Backend)

Larp is a high-performance, asynchronous backend engine for an **AI-powered Multi-Step Research Agent**. It accepts complex research queries, decomposes them into multi-step tasks, orchestrates specialized AI agents (`Planner`, `Search`, `FactChecker`, `Citation`, `Report`), enforces x402 pre-execution micropayments, streams live status updates over WebSockets, and generates multi-format research reports (Markdown, styled HTML5, printable PDF) with historical revision versioning.

---

## 🚀 Key Features

* **Clean 5-Tier Architecture**: Unidirectionally decoupled layers (`Router` $\rightarrow$ `Middleware` $\rightarrow$ `Service` $\rightarrow$ `Repository` $\rightarrow$ `Database / Redis`).
* **Async PostgreSQL 16 & SQLAlchemy 2.0**: Generic `BaseRepository[T]` with B-Tree compound indexing (`user_id, created_at`, `job_id, step_number`).
* **JWT Authentication & RBAC**: Access & refresh token rotation (`HS256`), Bcrypt password hashing, and Redis JTI revocation blacklist.
* **Real-Time WebSocket Streaming**: PubSub channel streaming (`research:{job_id}`) powered by Redis PubSub.
* **Resilient Multi-Agent Pipeline (`AgentManager`)**: 3x retries with exponential backoff ($0.5\text{s} \rightarrow 1.0\text{s} \rightarrow 2.0\text{s}$), non-blocking 30s timeouts (`asyncio.wait_for`), and per-agent fallback handlers.
* **Granular Execution Logging**: Step-level metrics storing `execution_time_ms`, `cost_usd`, `error_message`, and `status`.
* **x402 Micropayment Protocol**: Pre-execution `PaymentMiddleware` checking user budget and returning HTTP `402 Payment Required` on budget exhaustion.
* **Multi-Format Report Exports**: Direct Markdown download, styled HTML5 browser rendering, printable PDF bytes, and historical versioning (`version`, `is_latest`).
* **Containerized Deployment**: Multi-stage `Dockerfile`, `docker-compose.yml`, Railway configuration (`railway.json`), and `/api/v1/health` probes.

---

## 🛠 Tech Stack

* **Core**: Python 3.12, FastAPI, Uvicorn (ASGI)
* **Database**: PostgreSQL 16, Async SQLAlchemy 2.0, Asyncpg, Alembic Migrations
* **Cache & PubSub**: Redis 7, `redis.asyncio`
* **Security & Auth**: PyJWT, Passlib (Bcrypt), OAuth2 Bearer
* **Containerization & Cloud**: Docker, Docker Compose, Railway

---

## 📦 Project Structure

```
backend/
├── alembic/                      # Alembic database migration scripts
│   └── versions/                 # Versioned schema migration files
├── app/
│   ├── agents/                   # LangGraph Abstract Agent Interfaces & Mock Fallbacks
│   │   ├── base.py               # BaseAgentInterface & BaseAgentState
│   │   ├── planner.py            # PlannerAgentInterface
│   │   ├── search.py             # SearchAgentInterface
│   │   ├── fact_checker.py       # FactCheckerAgentInterface
│   │   ├── citation.py           # CitationAgentInterface
│   │   ├── report.py             # ReportAgentInterface
│   │   └── mock_agents.py        # Offline Mock Agent Implementations
│   ├── api/v1/endpoints/         # REST API Route Handlers
│   │   ├── health.py             # Health Check Probe (/health)
│   │   ├── auth.py               # Authentication Routes (/register, /login, /refresh, /logout)
│   │   ├── users.py              # User Management & Profile Routes
│   │   ├── research.py           # Research Job Creation, History, Exports (/research)
│   │   ├── reports.py            # Report Exports & Revision History (/reports)
│   │   ├── agents.py             # Agent Task Execution Logging (/agents)
│   │   └── websockets.py         # Real-Time WebSocket Streaming Channel (/ws)
│   ├── core/                     # Security, Logging, Exceptions & WebSockets
│   ├── middleware/               # CORS, GZip, Correlation ID, Rate Limiter, Auth, Payment
│   ├── models/                   # Async SQLAlchemy 2.0 Models (7 tables)
│   ├── repositories/             # Repository Pattern Data Access Layer
│   ├── schemas/                  # Pydantic Schemas for Requests & Responses
│   ├── services/                 # Business Logic Services (Research, User, Agent, Report, Payment)
│   ├── utils/                    # Resilience Engine (Retries, Timeouts, Fallbacks)
│   ├── database.py               # Async SQLAlchemy Engine & QueuePool Connection Pool
│   ├── dependencies.py           # Dependency Injection Factories
│   ├── main.py                   # FastAPI Application Factory
│   └── settings.py               # Pydantic Settings & Environment Loading
├── tests/                        # Pytest Test Suite
├── Dockerfile                    # Multi-stage Production Docker Image
├── docker-compose.yml            # Local Multi-Container Stack (API, PostgreSQL, Redis)
├── entrypoint.sh                 # Docker Startup Script with Auto-Alembic Migrations
├── railway.json                  # Railway Cloud Deployment Configuration
└── requirements.txt              # Production Dependencies
```

---

## ⚡ Quick Start (Local Docker Compose)

1. Clone repository & copy `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Build and start containers:
   ```bash
   cd backend
   docker compose up --build -d
   ```

3. Access local endpoints:
   * **Swagger API Docs**: `http://localhost:8000/docs`
   * **ReDoc Documentation**: `http://localhost:8000/redoc`
   * **OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`
   * **Health Check**: `http://localhost:8000/api/v1/health`

---

## 📄 Key Environment Variables

| Variable | Description | Example / Default |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection URL | `postgresql+asyncpg://user:password@postgres:5432/researchdb` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `JWT_SECRET` | Secret key for signing JWT tokens | `min_32_bytes_random_secret_key` |
| `JWT_ALGORITHM` | Signature algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifespan | `7` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## 🧪 Running Unit & Integration Tests

```bash
pip install -r requirements.txt
pytest
```
