# Larp AI

> **AI-Powered Multi-Step Research Agent with x402 Autonomous Payment Orchestration**

Larp AI is a production-quality, lightweight AI Research Orchestrator designed to decompose complex queries into structured research tasks, execute parallel API calls, handle autonomous micro-payments via x402, aggregate multi-source findings, and generate publication-ready cited Markdown reports.

---

## ⚡ Hardware Constraints & Optimization

This application is strictly engineered and optimized for low-spec developer hardware:
- **Target CPU:** Intel Core i3 (10th Gen)
- **Target RAM:** 8GB
- **Target OS:** Windows
- **Memory Footprint:** Keeps memory consumption **< 500MB** during normal execution.
- **Zero Local LLM Requirement:** All AI inference is delegated to cloud LLM providers (OpenAI, Gemini, Anthropic) via lightweight async HTTP clients (`httpx`), avoiding heavy GPU/RAM overhead.
- **Lightweight Dependencies:** Uses standard library templates and in-memory TTL caching instead of heavy databases (Elasticsearch, Redis, Docker, or Kubernetes).

---

## 📁 Architecture & Directory Structure

```text
Multi step research agent/
├── research_agent/
│   └── app/
│       ├── api/          # FastAPI routers (health, plan, execute, aggregate, report)
│       ├── agents/       # Result Aggregator & synthesis agents
│       ├── planner/      # Planner Agent & DAG stage dependency builder
│       ├── executor/     # Research Executor Agent & async stage execution
│       ├── report/       # Report Generator Agent & Markdown template renderer
│       ├── memory/       # In-Memory cache provider & BaseCache interface
│       ├── payment/      # x402 Autonomous Payment Agent & retry protocol
│       ├── services/     # Cloud LLM Adapters (OpenAI, Gemini, Anthropic) & Tool services
│       │   └── tools/    # Web search, fact extraction, summarization, citation tools
│       ├── models/       # Pydantic data schemas (plan, executor, aggregator, report, payment)
│       ├── config/       # Environment settings & configuration management
│       ├── core/         # Logging and diagnostic utilities
│       └── main.py       # FastAPI application entrypoint
├── tests/                # Automated test suite (39+ unit and E2E integration tests)
├── .env.example          # Environment variable template
├── requirements.txt      # Lightweight Python dependencies
└── README.md             # Complete documentation
```

---

## 🚀 Workflow & Execution Lifecycle

```text
User Query
    │
    ▼
Planner Agent ────────► [Decomposes query into DAG Tasks & Execution Stages]
    │
    ▼
Research Executor ───► [Parallel Stage Execution via asyncio.gather]
    ├── Memory Layer   [Checks TTL cache to prevent duplicate API calls]
    ├── Service Tools  [Web Search, Fact Extraction, Summarization, Citations]
    └── Payment Agent  [Intercepts HTTP 402, handles x402 tokens, auto-retries]
    │
    ▼
Result Aggregator ───► [Deduplicates claims, calculates confidence score]
    │
    ▼
Report Generator ────► [Renders publication-ready Markdown report with citations]
```

---

## 🛠️ API Reference Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Diagnostic health check and system status. |
| `POST` | `/api/v1/plan` | Decomposes a research query into an execution plan. |
| `POST` | `/api/v1/execute` | Executes an execution plan across service tools. |
| `POST` | `/api/v1/aggregate` | Aggregates execution findings into structured data. |
| `POST` | `/api/v1/report` | End-to-end endpoint: plans, executes, aggregates, and renders Markdown report. |
| `GET / POST` | `/api/v1/stream/research` | Real-time Server-Sent Events (SSE) streaming endpoint for live execution progress. |


---

## 💻 Getting Started

### 1. Installation & Environment Setup
Ensure Python 3.11+ is installed.

```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file from template
copy .env.example .env
```

### 2. Configuration (`.env`)
Add your preferred API keys (Optional; system defaults to keyless offline mock adapters if omitted):

```env
APP_NAME="Larp AI"
DEBUG=True

# Optional Cloud LLM API Keys
OPENAI_API_KEY=""
GEMINI_API_KEY=""
ANTHROPIC_API_KEY=""

# Optional Search API Keys
SERPER_API_KEY=""
TAVILY_API_KEY=""
```

### 3. Running the Server

```bash
uvicorn research_agent.app.main:app --reload --port 8000
```
Access interactive API documentation at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing & Verification

Run the full automated test suite using `pytest`:

```bash
pytest
```

---

## 🗺️ Roadmap & Future Extensibility

- **Payment Providers:** Extend x402 payment handler to support real Web3 lightning/crypto wallets.
- **External Caching:** Plug in Redis adapter (`RedisCache`) implementing `BaseCache` for persistent distributed cache.
- **Persistence Layer:** Optional SQLite / PostgreSQL database integration for historical research report storage.
