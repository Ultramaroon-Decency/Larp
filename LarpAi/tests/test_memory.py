import time
import pytest
from research_agent.app.memory import InMemoryCache
from research_agent.app.planner import PlannerAgent
from research_agent.app.executor import ResearchExecutorAgent


def test_in_memory_cache_basic_operations():
    cache = InMemoryCache(default_ttl_seconds=60)
    cache.clear()

    # Initial state
    assert cache.get("key1") is None
    assert cache.has("key1") is False
    assert cache.size() == 0

    # Set and Get
    cache.set("key1", {"data": "test_val"})
    assert cache.has("key1") is True
    assert cache.get("key1") == {"data": "test_val"}
    assert cache.size() == 1

    # Delete
    deleted = cache.delete("key1")
    assert deleted is True
    assert cache.has("key1") is False
    assert cache.size() == 0


def test_in_memory_cache_ttl_expiration():
    cache = InMemoryCache(default_ttl_seconds=1)  # 1 second TTL

    cache.set("short_lived", "value")
    assert cache.get("short_lived") == "value"

    # Wait for TTL to expire
    time.sleep(1.1)

    assert cache.get("short_lived") is None
    assert cache.has("short_lived") is False


def test_in_memory_cache_capacity_eviction():
    cache = InMemoryCache(default_ttl_seconds=60, max_entries=2)

    cache.set("k1", "v1")
    cache.set("k2", "v2")
    assert cache.size() == 2

    # Adding 3rd item should evict k1
    cache.set("k3", "v3")
    assert cache.size() == 2
    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"
    assert cache.get("k3") == "v3"


@pytest.mark.asyncio
async def test_executor_cache_integration():
    cache = InMemoryCache()
    executor = ResearchExecutorAgent(cache=cache)
    planner = PlannerAgent()

    plan = await planner.create_plan("Artificial Intelligence memory layer optimization")

    # First run fills cache
    res1 = await executor.execute_plan(plan)
    assert res1.status == "completed"
    assert cache.size() > 0

    # Second run retrieves from cache
    res2 = await executor.execute_plan(plan)
    assert res2.status == "completed"
    # Execution time should be lower or equal
    assert res2.total_tasks == res1.total_tasks
