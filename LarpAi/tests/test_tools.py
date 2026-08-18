import pytest
from research_agent.app.services.tools import (
    MockSearchTool,
    MockFactCheckTool,
    MockSummaryTool,
    MockCitationTool
)
from research_agent.app.models.tools import (
    SearchResponse,
    FactCheckResponse,
    SummaryResponse,
    CitationResponse
)


@pytest.mark.asyncio
async def test_mock_search_tool_success():
    tool = MockSearchTool()
    query = "Quantum Computing Optimization"
    res = await tool.execute(query=query, max_results=2)

    assert res.success is True
    assert res.error is None
    assert isinstance(res.data, SearchResponse)
    assert res.data.query == query
    assert len(res.data.results) == 2
    assert "execution_time_seconds" in res.metadata


@pytest.mark.asyncio
async def test_mock_search_tool_empty_query():
    tool = MockSearchTool()
    res = await tool.execute(query="   ")

    assert res.success is False
    assert res.error == "Search query cannot be empty."
    assert res.data is None


@pytest.mark.asyncio
async def test_mock_fact_check_tool_success():
    tool = MockFactCheckTool()
    claims = ["Solar energy cost dropped by 80%", "Nuclear energy produces carbon dioxide"]
    res = await tool.execute(claims=claims)

    assert res.success is True
    assert isinstance(res.data, FactCheckResponse)
    assert len(res.data.claims) == 2
    assert res.data.claims[0].claim == claims[0]
    assert res.data.claims[0].status in ["verified", "disputed"]
    assert 0.0 <= res.data.claims[0].confidence_score <= 1.0


@pytest.mark.asyncio
async def test_mock_fact_check_tool_empty_claims():
    tool = MockFactCheckTool()
    res = await tool.execute(claims=[])

    assert res.success is False
    assert res.error == "Claims list cannot be empty."


@pytest.mark.asyncio
async def test_mock_summary_tool_success():
    tool = MockSummaryTool()
    text = "Artificial intelligence research has advanced rapidly across deep learning and reinforcement learning paradigms."
    res = await tool.execute(text=text, max_takeaways=2)

    assert res.success is True
    assert isinstance(res.data, SummaryResponse)
    assert res.data.word_count > 0
    assert len(res.data.key_takeaways) == 2


@pytest.mark.asyncio
async def test_mock_summary_tool_empty_text():
    tool = MockSummaryTool()
    res = await tool.execute(text="")

    assert res.success is False
    assert res.error == "Input text for summary cannot be empty."


@pytest.mark.asyncio
async def test_mock_citation_tool_apa_and_ieee():
    tool = MockCitationTool()
    raw_sources = [
        {
            "title": "Autonomous AI Agents in Healthcare",
            "authors": ["Dr. Alice Smith", "Bob Johnson"],
            "url": "https://healthai.org/paper1",
            "year": 2025
        }
    ]

    # Test APA format
    apa_res = await tool.execute(raw_sources=raw_sources, style="APA")
    assert apa_res.success is True
    assert isinstance(apa_res.data, CitationResponse)
    assert "Dr. Alice Smith, Bob Johnson (2025)" in apa_res.data.citations[0].formatted_citation

    # Test IEEE format
    ieee_res = await tool.execute(raw_sources=raw_sources, style="IEEE")
    assert ieee_res.success is True
    assert ieee_res.data.citations[0].formatted_citation.startswith("[1]")
