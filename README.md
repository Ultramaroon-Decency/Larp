# Larp — Multi-Step Research Agent

> AI-powered research orchestrator that decomposes queries, searches the web, fact-checks findings, and generates cited reports — with autonomous x402 micropayments at each step.

---

## Repository Layout

```
Larp/
├── Larp-Frontend/   # React + TypeScript UI + Express/SSE orchestration server
├── Larp-Backend/    # FastAPI backend — auth, agents, DB, WebSocket streaming
└── LarpAi/          # Lightweight AI pipeline agent (standalone FastAPI service)
```

---

## Frontend — `Larp-Frontend/research-lab/`

**Stack:** React 18, TypeScript, Tailwind CSS v4, Vite, Express, SSE

### What it does
- Accepts a research query and mode (Quick Scan / Deep Dive)
- Opens an SSE connection and runs a **5-step pipeline** in real time:
  1. **Decompose** — Groq (Llama 3) breaks the query into 3 sub-questions
  2. **Search** — Tavily AI fetches live web results per sub-question
  3. **Fact-Check** — Groq cross-references results and extracts verified claims
  4. **Enrich** — Wikipedia REST API adds academic context for key entities
  5. **Synthesize** — Groq compiles a full cited research report
- Simulates x402 USDC micropayments for each API call
- Displays live pipeline progress, payment receipts, and the final report

### Setup

```bash
cd Larp-Frontend/research-lab
npm install
```

Create `.env.local`:
```env
GROQ_API_KEY=gsk_...          # console.groq.com (free)
TAVILY_API_KEY=tvly-...       # app.tavily.com (free, optional)
AGENT_WALLET_PRIVATE_KEY=     # leave blank for simulation mode
```

```bash
npm run dev
# http://localhost:3000
```

### Key env variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq LLM API key — free at [console.groq.com](https://console.groq.com) |
| `TAVILY_API_KEY` | Optional | Real web search — falls back to model knowledge if absent |
| `AGENT_WALLET_PRIVATE_KEY` | Optional | EVM key for real x402 payments; blank = simulation |

---

## Backend — `Larp-Backend/backend/`

**Stack:** Python 3.12, FastAPI, PostgreSQL 16, Redis 7, SQLAlchemy 2.0, Docker

### What it does
- REST + WebSocket API for research job management
- Orchestrates 5 AI agents: `Planner → Search → FactChecker → Citation → Report`
- Streams live job status over WebSocket (Redis PubSub)
- JWT authentication with refresh token rotation and Redis revocation blacklist
- x402 `PaymentMiddleware` enforces per-user budget before job execution
- Exports reports as Markdown, HTML, or PDF with revision history

### Setup

```bash
cd Larp-Backend/backend
cp .env.example .env        # fill in DATABASE_URL, REDIS_URL, JWT_SECRET
docker compose up --build -d
# Swagger docs at http://localhost:8000/docs
```

### Key env variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@postgres:5432/researchdb` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `JWT_SECRET` | Random 32+ byte secret |
| `LOG_LEVEL` | `INFO` |

### Key API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/login` | Get JWT tokens |
| `POST` | `/api/v1/research` | Start a research job |
| `GET` | `/api/v1/research/{id}` | Poll job status |
| `GET` | `/api/v1/reports/{id}` | Fetch final report |
| `WS` | `/api/v1/ws/{job_id}` | Real-time progress stream |

---

## AI Agent — `LarpAi/`

**Stack:** Python, FastAPI, httpx, in-memory TTL cache

### What it does
Standalone lightweight research orchestration service — no GPU, no Docker required:
- **Planner Agent** — decomposes a query into a DAG of concurrent tasks
- **Executor** — runs tasks via `asyncio.gather`
- **Memory Layer** — TTL cache prevents duplicate API calls
- **Tool Services** — web search, fact extraction, summarization, citation
- **Payment Agent** — handles x402 HTTP 402 intercepts and auto-retries
- **Report Generator** — renders a cited Markdown report

### Setup

```bash
cd LarpAi
pip install -r requirements.txt
cp .env.example .env
uvicorn research_agent.app.main:app --reload
```

### Key API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | System status |
| `POST` | `/api/v1/plan` | Decompose query into execution plan |
| `POST` | `/api/v1/execute` | Execute a plan |
| `POST` | `/api/v1/aggregate` | Aggregate findings |
| `POST` | `/api/v1/report` | Full end-to-end: plan → execute → report |
| `GET/POST` | `/api/v1/stream/research` | SSE live progress stream |

---

## x402 Payments

All three components implement the **x402 micropayment protocol**:
- Each API call is treated as a paid service (e.g. 0.0008 USDC per LLM call)
- The agent wallet intercepts HTTP 402 responses, constructs a payment header, and retries
- Without `AGENT_WALLET_PRIVATE_KEY`, payments run in **simulation mode** — the full pipeline executes and receipts are generated with mock transaction hashes

---

## Running Everything Together

| Service | Port | Start command |
|---|---|---|
| Frontend + Orchestrator | `3000` | `npm run dev` in `Larp-Frontend/research-lab/` |
| Backend API | `8000` | `docker compose up` in `Larp-Backend/backend/` |
| AI Agent | `8001` | `uvicorn ... --port 8001` in `LarpAi/` |
