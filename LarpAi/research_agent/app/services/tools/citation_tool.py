from abc import ABC
from typing import List, Dict, Any
from research_agent.app.services.tools.base import BaseTool
from research_agent.app.models.tools import CitationResponse, CitationItem


class BaseCitationTool(BaseTool, ABC):
    """
    Abstract interface for Citation Formatting Tools.
    """
    def __init__(self, name: str = "CitationTool", description: str = "Formats and normalizes reference sources into standard citations."):
        super().__init__(name=name, description=description)


class MockCitationTool(BaseCitationTool):
    """
    Mock implementation of CitationTool for Phase 3 testing and offline development.
    """

    def __init__(self):
        super().__init__(
            name="MockCitationTool",
            description="Normalizes raw source data into APA/IEEE formatted citations."
        )

    async def _run(self, raw_sources: List[Dict[str, Any]], style: str = "APA") -> CitationResponse:
        """
        Normalizes raw source references into formatted citation items.
        """
        if not raw_sources:
            raise ValueError("Raw sources list cannot be empty.")

        citations: List[CitationItem] = []
        for idx, src in enumerate(raw_sources):
            title = src.get("title", f"Untitled Source {idx + 1}")
            authors = src.get("authors", ["Research Team"])
            url = src.get("url", f"https://example.org/source-{idx + 1}")
            year = src.get("year", 2026)
            author_str = ", ".join(authors)

            if style.upper() == "IEEE":
                formatted = f"[{idx + 1}] {author_str}, \"{title},\" {year}. Available: {url}"
            else:  # Default to APA style
                formatted = f"{author_str} ({year}). {title}. Retrieved from {url}"

            citations.append(
                CitationItem(
                    source_id=f"src-{idx + 1}",
                    title=title,
                    authors=authors,
                    url=url,
                    year=year,
                    formatted_citation=formatted
                )
            )

        return CitationResponse(citations=citations)
