from fastapi import APIRouter, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from research_agent.app.models.plan import ExecutionPlan
from research_agent.app.models.executor import PlanExecutionResult
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent, ExecutorError

router = APIRouter()


class ExecuteRequest(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Research query. If provided without plan, a plan will be generated automatically.",
        json_schema_extra={"example": "Investigate renewable energy storage solutions"}
    )
    plan: Optional[ExecutionPlan] = Field(
        default=None,
        description="Pre-constructed execution plan to execute."
    )


@router.post("", response_model=PlanExecutionResult, status_code=status.HTTP_200_OK)
async def execute_plan(request: ExecuteRequest):
    """
    Executes a research plan stage-by-stage concurrently.
    Accepts either an explicit ExecutionPlan or a research query (which automatically generates a plan).
    """
    if not request.query and not request.plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'query' or 'plan' must be provided."
        )

    executor = ResearchExecutorAgent()

    try:
        if request.plan:
            plan = request.plan
        else:
            planner = PlannerAgent()
            plan = await planner.create_plan(request.query)

        result = await executor.execute_plan(plan)
        return result
    except ExecutorError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )
