from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from research_agent.app.models.plan import ExecutionPlan
from research_agent.app.planner import PlannerAgent, PlannerError

router = APIRouter()


class PlanRequest(BaseModel):
    query: str = Field(..., description="Research query or topic to construct an execution plan for.", json_schema_extra={"example": "Compare quantum computing and classical supercomputing algorithms."})


@router.post("", response_model=ExecutionPlan, status_code=status.HTTP_200_OK)
async def create_plan(request: PlanRequest):
    """
    Decomposes a research query into structured subtasks with estimated service requirements and parallel execution stages.
    """
    planner = PlannerAgent()
    try:
        plan = await planner.create_plan(request.query)
        return plan
    except PlannerError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate execution plan: {str(e)}")
