import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent
from research_agent.app.report import ReportGeneratorAgent

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamResearchRequest(BaseModel):
    query: str = Field(..., description="Research query topic")
    format_type: str = Field(default="FULL", description="Report format ('FULL' or 'EXECUTIVE')")


async def research_event_generator(query: str, format_type: str = "FULL") -> AsyncGenerator[str, None]:
    """
    Generator function yielding Server-Sent Events (SSE) for research execution progress.
    """
    try:
        # Event 1: Initialized
        yield f"data: {json.dumps({'event': 'init', 'message': f'Starting research for query: {query}'})}\n\n"
        await asyncio.sleep(0.1)

        # Event 2: Planning Stage
        yield f"data: {json.dumps({'event': 'planning_start', 'message': 'Decomposing query into DAG tasks...'})}\n\n"
        planner = PlannerAgent()
        plan = await planner.create_plan(query)

        yield f"data: {json.dumps({'event': 'plan_created', 'plan_id': plan.plan_id, 'tasks_count': len(plan.tasks), 'stages_count': len(plan.execution_order)})}\n\n"
        await asyncio.sleep(0.1)

        # Event 3: Executor Stage
        executor = ResearchExecutorAgent()
        for idx, stage in enumerate(plan.execution_order, start=1):
            yield f"data: {json.dumps({'event': 'stage_start', 'stage_number': idx, 'task_ids': stage})}\n\n"
            await asyncio.sleep(0.1)

        exec_result = await executor.execute_plan(plan)
        yield f"data: {json.dumps({'event': 'execution_complete', 'execution_time_seconds': exec_result.total_execution_time_seconds})}\n\n"
        await asyncio.sleep(0.1)

        # Event 4: Aggregation Stage
        yield f"data: {json.dumps({'event': 'aggregation_start', 'message': 'Synthesizing multi-source findings...'})}\n\n"
        aggregator = ResultAggregatorAgent()
        aggregated = aggregator.aggregate_results(exec_result)

        yield f"data: {json.dumps({'event': 'aggregation_complete', 'total_sources': aggregated.total_sources_count, 'confidence_score': round(aggregated.average_confidence_score * 100, 1)})}\n\n"
        await asyncio.sleep(0.1)

        # Event 5: Report Generation Stage
        yield f"data: {json.dumps({'event': 'report_generating', 'message': 'Rendering publication-ready Markdown report...'})}\n\n"
        generator = ReportGeneratorAgent()
        report = generator.generate_report(aggregated, format_type=format_type)

        yield f"data: {json.dumps({'event': 'report_ready', 'report_id': report.report_id, 'title': report.title, 'markdown_content': report.markdown_content})}\n\n"

    except Exception as e:
        logger.error(f"Error during SSE research stream: {e}")
        yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"


@router.get("/research")
async def stream_research_get(
    query: str = Query(..., description="Research query topic"),
    format_type: str = Query(default="FULL", description="Report format")
):
    """
    Server-Sent Events (SSE) endpoint to stream research progress in real-time.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")
    
    return StreamingResponse(
        research_event_generator(query.strip(), format_type),
        media_type="text/event-stream"
    )


@router.post("/research")
async def stream_research_post(req: StreamResearchRequest):
    """
    Server-Sent Events (SSE) POST endpoint for structured requests.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query body cannot be empty.")

    return StreamingResponse(
        research_event_generator(req.query.strip(), req.format_type),
        media_type="text/event-stream"
    )
