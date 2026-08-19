# Larp — AI Research Agent

> Full-stack AI research assistant that decomposes queries, searches the web, verifies facts, and generates comprehensive cited academic reports — all streamed in real-time.

![Stack](https://img.shields.io/badge/React_18-TypeScript-blue?logo=react)
![Stack](https://img.shields.io/badge/FastAPI-Python_3.12-green?logo=fastapi)
![Stack](https://img.shields.io/badge/PostgreSQL_16-Database-blue?logo=postgresql)
![Stack](https://img.shields.io/badge/Tailwind_CSS_v4-Styling-blue?logo=tailwindcss)

---

## How It Works

Larp runs a **5-agent AI pipeline** to turn any research question into a structured academic report:

```
User Query → Planner → Search → Fact Checker → Citation → Report
```

1. **Planner Agent** — Decomposes the query into parallel sub-tasks using Groq LLM
2. **Search Agent** — Deep-searches the web via Tavily across all sub-tasks concurrently
3. **Fact Checker Agent** — Verifies extracted claims and assigns confidence scores
4. **Citation Agent** — Formats inline `[1]`, `[2]` academic-style citations
5. **Report Agent** — Synthesizes a full Markdown report using NVIDIA GPT-OSS 120B (with multi-provider fallback)

All progress is streamed live to the frontend via WebSocket.

---

## Architecture

```
Larp/
├── Larp-Frontend/research-lab/   # React + TypeScript + Tailwind v4 + Vite
├── Larp-Backend/backend/         # FastAPI + PostgreSQL + Redis + WebSocket
└── LarpAi/                       # Core AI agent classes (imported by backend)
```

### Data Flow

```
Frontend (React)                  Backend (FastAPI)              AI Agents (Python)
┌─────────────┐    POST /research ┌──────────────┐   in-memory  ┌──────────────┐
│  Chat UI    │ ───────────────→  │ AgentManager │ ──────────→  │ PlannerAgent │
│  WebSocket  │ ←─── WS stream ── │ Redis PubSub │              │ SearchAgent  │
│  Markdown   │                   │ PostgreSQL   │              │ ReportAgent  │
└─────────────┘                   └──────────────┘              └──────────────┘
```

- Frontend proxies `/api` to backend on port `8000`
- Backend executes the AI agent pipeline as an async background task
- Progress updates stream via Redis PubSub → WebSocket
- Final report is persisted in PostgreSQL and rendered as Markdown in the frontend

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Tailwind CSS v4, Vite, react-markdown |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, httpx |
| **Database** | PostgreSQL 16 (async), Redis 7 (PubSub + caching) |
| **AI/LLM** | NVIDIA API (GPT-OSS 120B/20B), Groq (Llama 3.3), Tavily Search |
| **Auth** | JWT with refresh token rotation, Redis revocation blacklist |

---

## Quick Start

### Prerequisites

- **Node.js** ≥ 18 and **npm**
- **Python** 3.12+ and **pip**
- **PostgreSQL** 16 running locally (or Docker)
- **Redis** 7 running locally (or Docker)

### 1. Clone

```bash
git clone https://github.com/Ultramaroon-Decency/Larp.git
cd Larp
```

### 2. Backend Setup

```bash
cd Larp-Backend/backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create `.env`:
```env
# Application
APP_NAME="Research Agent API"
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/researchdb

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET_KEY=your-random-secret-key-here

# AI API Keys
NVIDIA_API_KEY=nvapi-...      # NVIDIA API (GPT-OSS 120B/20B)
GROQ_API_KEY=gsk_...          # Groq (Planner Agent — free at console.groq.com)
TAVILY_API_KEY=tvly-...       # Tavily Search (free at app.tavily.com)
```

Start the backend:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd Larp-Frontend/research-lab
npm install
npm run dev
# → http://localhost:5173
```

### 4. Run Together

| Service | Port | Command |
|---------|------|---------|
| Backend API | `8000` | `python -m uvicorn app.main:app --reload --port 8000` |
| Frontend | `5173` | `npm run dev` in `Larp-Frontend/research-lab/` |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/login` | Get JWT tokens |
| `POST` | `/api/v1/research/` | Start a research job |
| `GET` | `/api/v1/research/{id}` | Get job status |
| `GET` | `/api/v1/reports/{id}` | Fetch final report |
| `WS` | `/api/v1/ws/research/{job_id}` | Real-time progress stream |

---

## LLM Provider Cascade

The Report Agent tries multiple LLM providers in order — the first successful response is used:

| Priority | Provider | Model | Timeout |
|----------|----------|-------|---------|
| 1 | **NVIDIA** | `openai/gpt-oss-120b` | 180s |
| 2 | NVIDIA | `openai/gpt-oss-20b` | 45s |
| 3 | Groq | `llama-3.3-70b-versatile` | 60s |
| 4 | Gemini | `gemini-2.0-flash` | 60s |
| 5 | OpenAI | `gpt-4o-mini` | 60s |
| 6 | OpenRouter | `auto` | 60s |
| 7 | Fallback | Template synthesizer | instant |

Only `NVIDIA_API_KEY`, `GROQ_API_KEY`, and `TAVILY_API_KEY` are required. All other provider keys are optional fallbacks.

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `NVIDIA_API_KEY` | NVIDIA API key for report generation (GPT-OSS models) |
| `GROQ_API_KEY` | Groq API key for planning and fact-checking |
| `TAVILY_API_KEY` | Tavily API key for web search |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | Secret for JWT token signing |

### Optional

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key (fallback report provider) |
| `OPENAI_API_KEY` | OpenAI API key (fallback report provider) |
| `OPENROUTER_API_KEY` | OpenRouter API key (fallback report provider) |
| `AGENT_WALLET_PRIVATE_KEY` | EVM wallet key for x402 payments (blank = simulation) |

---

## x402 Micropayments

Larp implements the **x402 micropayment protocol**:
- Each API call is treated as a paid service (e.g., 0.0008 USDC per LLM call)
- The agent wallet intercepts HTTP 402 responses, constructs a payment header, and retries
- Without `AGENT_WALLET_PRIVATE_KEY`, payments run in **simulation mode** — the pipeline executes normally and generates mock transaction receipts

---

## Project Structure

```
Larp-Backend/backend/
├── app/
│   ├── agents/              # AI agent implementations
│   │   ├── real_agents.py   # NVIDIA/Groq/Gemini multi-provider agents
│   │   ├── planner.py       # Query decomposition
│   │   ├── search.py        # Web search interface
│   │   ├── fact_checker.py  # Fact verification
│   │   ├── citation.py      # Citation formatting
│   │   └── report.py        # Report generation interface
│   ├── api/v1/endpoints/    # REST + WebSocket endpoints
│   ├── core/                # Logging, security, WebSocket manager
│   ├── middleware/           # Auth, CORS, rate limiting, payments
│   ├── models/              # SQLAlchemy ORM models
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic + AgentManager
│   └── utils/               # Resilience patterns, helpers
├── .env                     # Environment config (gitignored)
└── requirements.txt

Larp-Frontend/research-lab/
├── src/
│   ├── components/
│   │   ├── ChatResearchView.tsx   # Main research chat + Markdown rendering
│   │   ├── SavedLibraryView.tsx   # Research history
│   │   ├── Sidebar.tsx            # Navigation
│   │   ├── TopAppBar.tsx          # Header bar
│   │   └── SourcesPanel.tsx       # Source citations panel
│   ├── App.tsx                    # Root + WebSocket orchestration
│   └── index.css                  # Tailwind v4 + Material 3 design tokens
├── package.json
└── vite.config.ts
```

---

## License

MIT
