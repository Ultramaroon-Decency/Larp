import pytest
import httpx
from fastapi.testclient import TestClient
from research_agent.app.main import app
from research_agent.app.planner import PlannerAgent
from research_agent.app.services.llm_base import MockLLMProvider
from research_agent.app.services.tools.scraper_tool import WebScraperTool
from research_agent.app.payment.payment_agent import PaymentAgent
from research_agent.app.payment.x402_transport import X402AsyncTransport

client = TestClient(app)


@pytest.mark.asyncio
async def test_web_scraper_tool_cleaning():
    scraper = WebScraperTool()
    html_content = "<html><head><title>Test Article</title></head><body><script>var x=1;</script><h1>Header</h1><p>Main body content.</p></body></html>"
    title, body = scraper._clean_html(html_content)
    
    assert title == "Test Article"
    assert "var x=1;" not in body
    assert "Header" in body
    assert "Main body content." in body


@pytest.mark.asyncio
async def test_web_scraper_tool_run_fallback():
    scraper = WebScraperTool()
    result = await scraper.execute(url="https://invalid-non-existent-domain-12345.org")
    
    assert result.success is True
    assert result.data is not None
    assert result.data.word_count > 0


@pytest.mark.asyncio
async def test_planner_llm_structured_decomposition():
    llm = MockLLMProvider()
    planner = PlannerAgent(llm_provider=llm)
    plan = await planner.create_plan("Compare renewable energy vs fossil fuels")
    
    assert plan.plan_id.startswith("plan-")
    assert len(plan.tasks) == 3
    assert len(plan.execution_order) >= 1


@pytest.mark.asyncio
async def test_x402_transport_interceptor():
    payment_agent = PaymentAgent(wallet_balance=50.0)
    
    # Custom mock transport that returns 402 on first attempt and 200 on retry with authorization header
    class Mock402Transport(httpx.AsyncBaseTransport):
        def __init__(self):
            self.attempts = 0

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            self.attempts += 1
            if self.attempts == 1:
                return httpx.Response(
                    status_code=402,
                    headers={"X-402-Price": "0.50", "X-402-Payee": "0x123", "X-402-Nonce": "nonce-test"},
                    json={"error": "Payment Required"}
                )
            else:
                auth_header = request.headers.get("Authorization", "")
                assert "X402-Token" in auth_header
                return httpx.Response(status_code=200, json={"data": "Access Granted"})

    x402_transport = X402AsyncTransport(payment_agent=payment_agent, inner_transport=Mock402Transport())
    
    async with httpx.AsyncClient(transport=x402_transport) as http_client:
        response = await http_client.get("https://paywalled-api.com/data")
        assert response.status_code == 200
        assert response.json()["data"] == "Access Granted"
        assert payment_agent.wallet_balance == 49.50


def test_sse_research_stream_endpoint():
    response = client.get("/api/v1/stream/research?query=Quantum+Computing+Breakthroughs")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data: " in response.text
    assert "plan_created" in response.text
    assert "report_ready" in response.text


@pytest.mark.asyncio
async def test_tavily_real_search_tool():
    from research_agent.app.services.tools.real_search_tool import RealWebSearchTool
    tool = RealWebSearchTool(tavily_key="mock_test", prefer="tavily")
    res = await tool.execute(query="test query")
    assert res.success is False
    assert res.data is None


@pytest.mark.asyncio
async def test_real_search_tool_serper_preference():
    from research_agent.app.services.tools.real_search_tool import RealWebSearchTool
    tool = RealWebSearchTool(serper_key="mock_test", tavily_key="mock_tavily", prefer="serper")
    res = await tool.execute(query="test query")
    assert res.success is False


@pytest.mark.asyncio
async def test_real_search_tool_no_keys():
    from research_agent.app.services.tools.real_search_tool import RealWebSearchTool
    tool = RealWebSearchTool()
    res = await tool.execute(query="fallback test")
    assert res.success is True
    assert res.data is not None
    assert res.data.total_results == 2


@pytest.mark.asyncio
async def test_sqlite_cache_basic_operations(tmp_path):
    from research_agent.app.memory import SqliteCache
    db_file = str(tmp_path / "test_cache.db")
    cache = SqliteCache(db_path=db_file, default_ttl_seconds=60)

    try:
        assert cache.get("k1") is None
        cache.set("k1", {"val": 42})
        assert cache.get("k1") == {"val": 42}
        assert cache.has("k1") is True
        assert cache.delete("k1") is True
        assert cache.has("k1") is False
    finally:
        cache.close()


@pytest.mark.asyncio
async def test_sqlite_cache_ttl_expiry(tmp_path):
    import time
    from research_agent.app.memory import SqliteCache
    db_file = str(tmp_path / "test_ttl.db")
    cache = SqliteCache(db_path=db_file, default_ttl_seconds=1)

    try:
        cache.set("short", "val")
        assert cache.get("short") == "val"
        time.sleep(1.1)
        assert cache.get("short") is None
    finally:
        cache.close()


@pytest.mark.asyncio
async def test_sqlite_cache_clear(tmp_path):
    from research_agent.app.memory import SqliteCache
    db_file = str(tmp_path / "test_clear.db")
    cache = SqliteCache(db_path=db_file)

    try:
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.has("a") is True
        cache.clear()
        assert cache.has("a") is False
        assert cache.has("b") is False
    finally:
        cache.close()
