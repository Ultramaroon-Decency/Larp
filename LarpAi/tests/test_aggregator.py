import pytest
from fastapi.testclient import TestClient
from research_agent.app.main import app
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent
from research_agent.app.agents import ResultAggregatorAgent, AggregatorError
from research_agent.app.models.aggregator import AggregatedResearchData


client = TestClient(app)


@pytest.mark.asyncio
async def test_aggregate_results_success():
    planner = PlannerAgent()
    executor = ResearchExecutorAgent()
    aggregator = ResultAggregatorAgent()

    plan = await planner.create_plan("Compare electric vs hydrogen fuel vehicles")
    exec_res = await executor.execute_plan(plan)
    aggregated = aggregator.aggregate_results(exec_res)

    assert isinstance(aggregated, AggregatedResearchData)
    assert aggregated.plan_id == plan.plan_id
    assert aggregated.query == plan.query
    assert len(aggregated.all_search_results) > 0
    assert len(aggregated.synthesized_takeaways) > 0
    assert aggregated.total_sources_count > 0
    assert 0.0 <= aggregated.average_confidence_score <= 1.0


@pytest.mark.asyncio
async def test_aggregate_results_empty_stage():
    aggregator = ResultAggregatorAgent()
    planner = PlannerAgent()

    plan = await planner.create_plan("Test empty stage")
    executor = ResearchExecutorAgent()
    exec_res = await executor.execute_plan(plan)
    exec_res.stage_results = []

    with pytest.raises(AggregatorError, match="Cannot aggregate empty execution results"):
        aggregator.aggregate_results(exec_res)


def test_aggregate_api_endpoint_with_query():
    response = client.post("/api/v1/aggregate", json={"query": "Quantum computing in financial cryptography"})
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert "synthesized_takeaways" in data
    assert "all_search_results" in data
    assert "total_sources_count" in data
    assert data["total_sources_count"] > 0


def test_aggregate_api_endpoint_empty_request():
    response = client.post("/api/v1/aggregate", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Either 'query' or 'execution_result' must be provided."
