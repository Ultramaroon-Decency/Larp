import pytest
from fastapi.testclient import TestClient
from research_agent.app.main import app
from research_agent.app.planner import PlannerAgent, PlannerError
from research_agent.app.models.plan import ResearchTask


client = TestClient(app)


@pytest.mark.asyncio
async def test_create_plan_standard_query():
    planner = PlannerAgent()
    query = "Investigate renewable energy storage solutions"
    plan = await planner.create_plan(query)

    assert plan.plan_id.startswith("plan-")
    assert plan.query == query
    assert len(plan.tasks) >= 2
    assert len(plan.execution_order) >= 2


@pytest.mark.asyncio
async def test_create_plan_comparative_query():
    planner = PlannerAgent()
    query = "Compare solar vs wind energy costs and efficiency"
    plan = await planner.create_plan(query)

    assert len(plan.tasks) == 3
    assert len(plan.execution_order) == 3
    # Check dependencies ordering
    task_map = {t.task_id: t for t in plan.tasks}
    assert "task-1" in task_map["task-2"].dependencies
    assert "task-1" in task_map["task-3"].dependencies
    assert "task-2" in task_map["task-3"].dependencies


@pytest.mark.asyncio
async def test_planner_empty_query():
    planner = PlannerAgent()
    with pytest.raises(PlannerError, match="Query cannot be empty"):
        await planner.create_plan("   ")


def test_compute_execution_order_parallel():
    # Tasks 1 & 2 have no dependencies, Task 3 depends on both
    t1 = ResearchTask(task_id="t1", description="Task 1", expected_output="Out 1", dependencies=[])
    t2 = ResearchTask(task_id="t2", description="Task 2", expected_output="Out 2", dependencies=[])
    t3 = ResearchTask(task_id="t3", description="Task 3", expected_output="Out 3", dependencies=["t1", "t2"])

    stages = PlannerAgent.compute_execution_order([t1, t2, t3])
    assert stages == [["t1", "t2"], ["t3"]]


def test_compute_execution_order_cyclic():
    t1 = ResearchTask(task_id="t1", description="Task 1", expected_output="Out 1", dependencies=["t2"])
    t2 = ResearchTask(task_id="t2", description="Task 2", expected_output="Out 2", dependencies=["t1"])

    with pytest.raises(PlannerError, match="Cyclic or unresolved dependency"):
        PlannerAgent.compute_execution_order([t1, t2])


def test_plan_api_endpoint_success():
    response = client.post("/api/v1/plan", json={"query": "Explain quantum cryptography principles"})
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert data["query"] == "Explain quantum cryptography principles"
    assert len(data["tasks"]) >= 2
    assert "execution_order" in data


def test_plan_api_endpoint_validation_error():
    response = client.post("/api/v1/plan", json={"query": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Query cannot be empty."
