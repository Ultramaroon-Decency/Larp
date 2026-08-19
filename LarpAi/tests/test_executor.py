import pytest
from fastapi.testclient import TestClient
from research_agent.app.main import app
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent, ExecutorError
from research_agent.app.models.executor import PlanExecutionResult, TaskExecutionResult


client = TestClient(app)


@pytest.mark.asyncio
async def test_execute_plan_success():
    planner = PlannerAgent()
    executor = ResearchExecutorAgent()

    plan = await planner.create_plan("Compare renewable energy vs fossil fuels")
    res = await executor.execute_plan(plan)

    assert isinstance(res, PlanExecutionResult)
    assert res.plan_id == plan.plan_id
    assert res.status in ["completed", "partial_success"]
    assert res.total_tasks == len(plan.tasks)
    assert res.completed_tasks == len(plan.tasks)
    assert len(res.stage_results) == len(plan.execution_order)
    assert res.total_execution_time_seconds >= 0.0


@pytest.mark.asyncio
async def test_execute_plan_empty_tasks():
    planner = PlannerAgent()
    executor = ResearchExecutorAgent()

    plan = await planner.create_plan("Test query")
    plan.tasks = []

    with pytest.raises(ExecutorError, match="Execution plan contains no tasks"):
        await executor.execute_plan(plan)


def test_execute_api_endpoint_with_query():
    response = client.post("/api/v1/execute", json={"query": "Investigate AI robotics progress"})
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert data["status"] == "completed"
    assert data["total_tasks"] >= 2
    assert "stage_results" in data


def test_execute_api_endpoint_empty_request():
    response = client.post("/api/v1/execute", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Either 'query' or 'plan' must be provided."
