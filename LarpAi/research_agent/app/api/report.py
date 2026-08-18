from fastapi import APIRouter, HTTPException, status
from research_agent.app.models.report import ReportRequest, ResearchReport
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent
from research_agent.app.report import ReportGeneratorAgent, ReportGeneratorError

router = APIRouter()


@router.post("/", response_model=ResearchReport, status_code=status.HTTP_200_OK)
async def generate_research_report(req: ReportRequest):
    """
    Generates a publication-ready Markdown research report.
    Can be invoked with pre-aggregated research data or with a query to perform full end-to-end research.
    """
    generator = ReportGeneratorAgent()

    if req.execution_data:
        aggregated_data = req.execution_data
    elif req.query:
        try:
            planner = PlannerAgent()
            executor = ResearchExecutorAgent()
            aggregator = ResultAggregatorAgent()

            plan = await planner.create_plan(req.query)
            exec_res = await executor.execute_plan(plan)
            aggregated_data = aggregator.aggregate_results(exec_res)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"End-to-end research workflow failed during report generation: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'query' or 'execution_data' must be provided in the request payload."
        )

    try:
        report = generator.generate_report(data=aggregated_data, format_type=req.format_type)
        return report
    except ReportGeneratorError as rge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(rge)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report formatting failed: {str(e)}"
        )
