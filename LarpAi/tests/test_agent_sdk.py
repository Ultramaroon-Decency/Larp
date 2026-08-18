import pytest
from research_agent import LarpAgent
from research_agent.app.services.llm_base import MockLLMProvider


@pytest.mark.asyncio
async def test_larp_agent_top_level_sdk_run():
    events_received = []

    def event_listener(event_type, payload):
        events_received.append((event_type, payload))

    agent = LarpAgent(
        llm_provider=MockLLMProvider(),
        wallet_balance=100.0,
        on_event=event_listener
    )

    report = await agent.run("Compare solar panels vs wind turbines", format_type="FULL", max_depth=1)

    assert report.report_id.startswith("report-")
    assert report.title == "Research Report: Compare Solar Panels Vs Wind Turbines"
    assert report.confidence_score > 0.0
    assert len(report.markdown_content) > 100

    # Verify inline numerical citation presence [[1]]
    assert "[[1]]" in report.markdown_content or "[1]" in report.markdown_content

    # Verify event listener callbacks were invoked
    event_names = [e[0] for e in events_received]
    assert "start" in event_names
    assert "planning_start" in event_names
    assert "plan_created" in event_names
    assert "execution_start" in event_names
    assert "execution_complete" in event_names
    assert "aggregation_start" in event_names
    assert "aggregation_complete" in event_names
    assert "report_ready" in event_names


@pytest.mark.asyncio
async def test_larp_agent_recursive_max_depth():
    agent = LarpAgent(llm_provider=MockLLMProvider())
    report = await agent.run("Deep dive into autonomous agent protocols", max_depth=2)
    
    assert report.total_sources > 0
    assert report.markdown_content is not None
