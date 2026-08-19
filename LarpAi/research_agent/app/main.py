from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from research_agent.app.api.health import router as health_router
from research_agent.app.api.plan import router as plan_router
from research_agent.app.api.execute import router as execute_router
from research_agent.app.api.aggregate import router as aggregate_router
from research_agent.app.api.report import router as report_router
from research_agent.app.api.stream import router as stream_router
from research_agent.app.core.logging import setup_logging
from research_agent.app.config.config import settings

# Initialize system-wide logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Multi-Step Research Agent with x402 Autonomous Payment Orchestration",
    version="0.1.0",
    debug=settings.DEBUG
)

# Include API routers
app.include_router(health_router, prefix="/health", tags=["Diagnostic"])
app.include_router(plan_router, prefix="/api/v1/plan", tags=["Planner"])
app.include_router(execute_router, prefix="/api/v1/execute", tags=["Executor"])
app.include_router(aggregate_router, prefix="/api/v1/aggregate", tags=["Aggregator"])
app.include_router(report_router, prefix="/api/v1/report", tags=["Report Generator"])
app.include_router(stream_router, prefix="/api/v1/stream", tags=["Real-Time Streaming"])


@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects root access to the API documentation.
    """
    return RedirectResponse(url="/docs")

