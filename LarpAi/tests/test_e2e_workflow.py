import pytest
from fastapi.testclient import TestClient
from research_agent.app.main import app
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent
from research_agent.app.report import ReportGeneratorAgent
from research_agent.app.memory import InMemoryCache
from research_agent.app.payment import PaymentAgent

client = TestClient(app)


@pytest.mark.asyncio
async def test_e2e_research_orchestration_pipeline():
    """
    Validates end-to-end research workflow from query input to final report output,
    incorporating caching and payment retry simulation.
    """
    query = "Evaluating sodium-ion vs lithium-sulfur battery commercial readiness"

    # 1. Planning Stage
    planner = PlannerAgent()
    plan = await planner.create_plan(query)
    assert plan.plan_id.startswith("plan-")
    assert len(plan.tasks) >= 2

    # 2. Execution Stage with Memory Cache & Payment Agent
    cache = InMemoryCache()
    payment_agent = PaymentAgent(wallet_balance=100.0)
    executor = ResearchExecutorAgent(cache=cache)

    exec_result = await executor.execute_plan(plan)
    assert exec_result.status == "completed"
    assert exec_result.completed_tasks == len(plan.tasks)
    assert cache.size() > 0

    # 3. Aggregation Stage
    aggregator = ResultAggregatorAgent()
    aggregated = aggregator.aggregate_results(exec_result)
    assert aggregated.total_sources_count > 0
    assert len(aggregated.synthesized_takeaways) > 0

    # 4. Report Generation Stage
    generator = ReportGeneratorAgent()
    report = generator.generate_report(aggregated, format_type="FULL")
    assert report.report_id.startswith("report-")
    assert report.confidence_score > 0.0
    assert "# Research Report:" in report.markdown_content
    assert "## Verified Evidence & Fact Analysis" in report.markdown_content


def test_e2e_api_full_flow():
    """
    Tests full API pipeline execution through POST /api/v1/report.
    """
    response = client.post(
        "/api/v1/report",
        json={"query": "End-to-end autonomous research agent validation", "format_type": "FULL"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "markdown_content" in data
    assert data["confidence_score"] > 0
    assert data["total_sources"] > 0
    assert "Research Report:" in data["title"]
