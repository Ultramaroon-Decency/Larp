from fastapi import APIRouter, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from research_agent.app.models.executor import PlanExecutionResult
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent, AggregatorError

router = APIRouter()


class AggregateRequest(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Research query. If provided without execution_result, plan and execution will run automatically.",
        json_schema_extra={"example": "Investigate renewable energy storage solutions"}
    )
    execution_result: Optional[PlanExecutionResult] = Field(
        default=None,
        description="Pre-executed PlanExecutionResult object to aggregate."
    )


@router.post("", response_model=AggregatedResearchData, status_code=status.HTTP_200_OK)
async def aggregate_results(request: AggregateRequest):
    """
    Deduplicates and synthesizes multi-stage execution results into unified research data.
    Accepts either an explicit PlanExecutionResult or a research query.
    """
    if not request.query and not request.execution_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'query' or 'execution_result' must be provided."
        )

    aggregator = ResultAggregatorAgent()

    try:
        if request.execution_result:
            exec_res = request.execution_result
        else:
            planner = PlannerAgent()
            executor = ResearchExecutorAgent()
            plan = await planner.create_plan(request.query)
            exec_res = await executor.execute_plan(plan)

        aggregated_data = aggregator.aggregate_results(exec_res)
        return aggregated_data
    except AggregatorError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Aggregation failed: {str(e)}"
        )
