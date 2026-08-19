from abc import ABC
from typing import List, Optional
from research_agent.app.services.tools.base import BaseTool
from research_agent.app.models.tools import SummaryResponse


class BaseSummaryTool(BaseTool, ABC):
    """
    Abstract interface for Summarization Tools.
    """
    def __init__(self, name: str = "SummaryTool", description: str = "Summarizes long-form research text and extracts key points."):
        super().__init__(name=name, description=description)


class MockSummaryTool(BaseSummaryTool):
    """
    Mock implementation of SummaryTool for Phase 3 testing and offline development.
    """

    def __init__(self):
        super().__init__(
            name="MockSummaryTool",
            description="Returns deterministic mock summaries and key takeaways."
        )

    async def _run(self, text: str, max_takeaways: int = 3) -> SummaryResponse:
        """
        Generates mock summary and takeaway points from input text.
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Input text for summary cannot be empty.")

        summary_text = (
            f"Summary of provided text ({len(clean_text.split())} words): "
            f"The analyzed document highlights core findings, methodologies, and conclusions regarding '{clean_text[:50]}...'."
        )

        takeaways = [
            f"Key Insight 1: Primary focus revolves around {clean_text[:30]}.",
            "Key Insight 2: Empirical evidence suggests consistent performance trends across test parameters.",
            "Key Insight 3: Strategic recommendations emphasize scalable adoption and robust error handling."
        ][:max_takeaways]

        return SummaryResponse(
            summary=summary_text,
            key_takeaways=takeaways,
            word_count=len(summary_text.split())
        )
