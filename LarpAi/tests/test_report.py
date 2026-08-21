import pytest
from fastapi.testclient import TestClient
from research_agent.app.main import app
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent
from research_agent.app.report import ReportGeneratorAgent, ReportGeneratorError
from research_agent.app.models.report import ResearchReport

client = TestClient(app)


@pytest.mark.asyncio
async def test_generate_full_report_success():
    planner = PlannerAgent()
    executor = ResearchExecutorAgent()
    aggregator = ResultAggregatorAgent()
    generator = ReportGeneratorAgent()

    plan = await planner.create_plan("Impact of solid state batteries on electric aviation")
    exec_res = await executor.execute_plan(plan)
    aggregated = aggregator.aggregate_results(exec_res)

    report = generator.generate_report(aggregated, format_type="FULL")

    assert isinstance(report, ResearchReport)
    assert report.report_id.startswith("report-")
    assert report.plan_id == plan.plan_id
    assert report.query == plan.query
    assert "# Research Report:" in report.markdown_content
    assert "## Executive Overview" in report.markdown_content
    assert "## Key Findings & Synthesized Takeaways" in report.markdown_content
    assert "## Verified Evidence & Fact Analysis" in report.markdown_content
    assert report.total_sources > 0
    assert 0.0 <= report.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_generate_executive_report_success():
    planner = PlannerAgent()
    executor = ResearchExecutorAgent()
    aggregator = ResultAggregatorAgent()
    generator = ReportGeneratorAgent()

    plan = await planner.create_plan("Autonomous AI agents in healthcare")
    exec_res = await executor.execute_plan(plan)
    aggregated = aggregator.aggregate_results(exec_res)

    report = generator.generate_report(aggregated, format_type="EXECUTIVE")

    assert isinstance(report, ResearchReport)
    assert "# Executive Summary:" in report.markdown_content
    assert "### Summary Highlights" in report.markdown_content


def test_report_generator_empty_data_raises_error():
    generator = ReportGeneratorAgent()
    with pytest.raises(ReportGeneratorError, match="Aggregated research data cannot be empty."):
        generator.generate_report(data=None)


def test_report_api_endpoint_with_query():
    response = client.post(
        "/api/v1/report",
        json={"query": "Comparison of quantum key distribution vs post-quantum cryptography", "format_type": "FULL"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "markdown_content" in data
    assert data["query"] == "Comparison of quantum key distribution vs post-quantum cryptography"
    assert "# Research Report:" in data["markdown_content"]


def test_report_api_endpoint_empty_request():
    response = client.post("/api/v1/report", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Either 'query' or 'execution_data' must be provided in the request payload."
