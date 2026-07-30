"""Agent and background task execution schemas with execution metrics, status, cost, and error tracking."""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, enum.Enum):
    """Asynchronous background task states."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTaskCreate(BaseModel):
    """Payload for creating a background agent execution task."""

    job_id: uuid.UUID = Field(description="Parent research job UUID")
    agent_name: str = Field(description="Agent identifier: 'PlannerAgent', 'SearchAgent', 'FactCheckerAgent', 'CitationAgent', 'ReportAgent'")
    step_number: int = Field(default=1, ge=1, description="Execution step sequence index")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input payload passed to the agent")
    priority: int = Field(default=0, ge=0, description="Task execution priority")


class AgentExecutionLogRead(BaseModel):
    """Schema representing an agent task execution log storing execution time, cost, errors, and status."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    agent_name: str
    step_number: int
    status: str = Field(description="Execution status: 'queued', 'running', 'completed', 'failed'")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution duration in milliseconds")
    cost_usd: float = Field(default=0.0, description="Estimated API execution cost in USD")
    error_message: Optional[str] = Field(default=None, description="Error details if execution failed")
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class AsyncTaskStatusResponse(BaseModel):
    """Response payload for tracking background task progress."""

    job_id: uuid.UUID
    task_id: uuid.UUID
    agent_name: str
    step_number: int
    status: str
    execution_time_ms: Optional[int] = None
    cost_usd: float = 0.0
    error_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    updated_at: datetime


# Backwards compatibility aliases
AgentTaskRead = AgentExecutionLogRead
AgentResultRead = AgentExecutionLogRead
