from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskExecutionResult(BaseModel):
    """
    Result of executing a single subtask within an ExecutionPlan.
    """
    task_id: str = Field(..., description="ID of the executed subtask.")
    status: str = Field(..., description="Execution status: 'completed' or 'failed'.")
    service_results: Dict[str, Any] = Field(default_factory=dict, description="Results keyed by tool/service name.")
    error: Optional[str] = Field(default=None, description="Error details if execution failed.")
    execution_time_seconds: float = Field(..., description="Duration of task execution in seconds.")


class PlanExecutionResult(BaseModel):
    """
    Result of executing a full multi-stage ExecutionPlan.
    """
    plan_id: str = Field(..., description="ID of the executed plan.")
    query: str = Field(..., description="Original research query.")
    status: str = Field(..., description="Overall plan execution status: 'completed', 'partial_success', or 'failed'.")
    stage_results: List[List[TaskExecutionResult]] = Field(
        default_factory=list,
        description="Results grouped by parallel execution stages."
    )
    total_tasks: int = Field(..., description="Total count of subtasks executed.")
    completed_tasks: int = Field(..., description="Count of successfully completed subtasks.")
    total_execution_time_seconds: float = Field(..., description="Total execution duration in seconds.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when execution finished."
    )
