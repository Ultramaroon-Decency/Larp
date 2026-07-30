"""Agent task and background execution endpoints backed by AgentService."""

from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.dependencies import get_agent_service, get_current_user
from app.schemas.agent import (
    AgentExecutionLogRead,
    AgentTaskCreate,
    AsyncTaskStatusResponse,
    TaskStatus,
)
from app.schemas.common import ResponseEnvelope
from app.services.agent_service import AgentService

router = APIRouter()


async def _dummy_agent_worker_process(agent_name: str, input_payload: dict) -> dict:
    """Mock agent worker simulating multi-step execution delay and producing output data."""
    import asyncio
    await asyncio.sleep(0.1)  # Simulate non-blocking async execution
    return {
        "processed_agent": agent_name,
        "input_processed": input_payload,
        "status": "success",
        "tokens_consumed": 342,
    }


@router.post(
    "/tasks",
    response_model=ResponseEnvelope[AgentExecutionLogRead],
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_agent_task(
    body: AgentTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> ResponseEnvelope[AgentExecutionLogRead]:
    """Enqueue a new asynchronous background task.

    Returns HTTP 202 Accepted immediately with status 'queued', while
    FastAPI BackgroundTasks executes the worker task across:
    QUEUED ──→ RUNNING ──→ COMPLETED / FAILED
    """
    queued_task = await agent_service.create_and_enqueue_task(body)

    # Schedule background execution lifecycle
    background_tasks.add_task(
        agent_service.execute_task_lifecycle,
        task_id=queued_task.id,
        worker_coroutine=_dummy_agent_worker_process,
        agent_name=body.agent_name,
        input_payload=body.input_data or {},
    )

    return ResponseEnvelope(
        success=True,
        message="Background task enqueued successfully",
        data=queued_task,
    )


@router.get("/tasks/{task_id}", response_model=ResponseEnvelope[AsyncTaskStatusResponse])
async def get_agent_task_status(
    task_id: UUID,
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> ResponseEnvelope[AsyncTaskStatusResponse]:
    """Track the execution state of an asynchronous background task."""
    task_status = await agent_service.get_task_status(task_id)

    return ResponseEnvelope(
        success=True,
        message="Background task status retrieved successfully",
        data=task_status,
    )


@router.get(
    "/sessions/{session_id}/tasks",
    response_model=ResponseEnvelope[Sequence[AgentExecutionLogRead]],
)
async def list_session_agent_tasks(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> ResponseEnvelope[Sequence[AgentExecutionLogRead]]:
    """List all agent task execution logs for a specific research session."""
    logs = await agent_service.list_job_tasks(session_id)

    return ResponseEnvelope(
        success=True,
        message="Agent task execution logs retrieved successfully",
        data=logs,
    )
