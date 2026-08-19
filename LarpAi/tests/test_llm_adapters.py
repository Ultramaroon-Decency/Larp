import pytest
from unittest.mock import AsyncMock, patch
from research_agent.app.services import (
    get_llm_provider,
    MockLLMProvider,
    OpenAIProvider,
    GeminiProvider,
    AnthropicProvider
)
from research_agent.app.services.tools import RealWebSearchTool
from research_agent.app.models.tools import ToolResult, SearchResponse


def test_get_llm_provider_fallback_to_mock():
    # Without environment keys, factory returns MockLLMProvider
    provider = get_llm_provider("openai")
    assert isinstance(provider, MockLLMProvider)


@pytest.mark.asyncio
async def test_openai_provider_missing_key_raises_error():
    provider = OpenAIProvider(api_key="")
    with pytest.raises(ValueError, match="OpenAI API key is missing"):
        await provider.generate_text("Test prompt")


@pytest.mark.asyncio
async def test_gemini_provider_missing_key_raises_error():
    provider = GeminiProvider(api_key="")
    with pytest.raises(ValueError, match="Gemini API key is missing"):
        await provider.generate_text("Test prompt")


@pytest.mark.asyncio
async def test_anthropic_provider_missing_key_raises_error():
    provider = AnthropicProvider(api_key="")
    with pytest.raises(ValueError, match="Anthropic API key is missing"):
        await provider.generate_text("Test prompt")


@pytest.mark.asyncio
async def test_real_web_search_tool_keyless_fallback():
    search_tool = RealWebSearchTool()
    result = await search_tool.execute(query="Quantum computing benchmarks")

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert isinstance(result.data, SearchResponse)
    assert len(result.data.results) > 0


from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_openai_provider_mocked_success(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "OpenAI generated research text."}}]
    }
    mock_post.return_value = mock_response

    provider = OpenAIProvider(api_key="sk-test-key-12345")
    res = await provider.generate_text("What is quantum supremacy?")

    assert res == "OpenAI generated research text."
    assert mock_post.called
