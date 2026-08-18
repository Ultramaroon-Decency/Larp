from typing import List, Optional
from pydantic import BaseModel, Field
from research_agent.app.models.tools import (
    SearchResultItem,
    FactCheckItem,
    CitationItem
)


class AggregatedResearchData(BaseModel):
    """
    Synthesized data payload combining search results, fact-checks, takeaways, and citations.
    """
    plan_id: str = Field(..., description="ID of the execution plan.")
    query: str = Field(..., description="Original research query.")
    synthesized_takeaways: List[str] = Field(default_factory=list, description="Deduplicated list of key takeaways.")
    all_search_results: List[SearchResultItem] = Field(default_factory=list, description="Deduplicated list of search items.")
    all_verified_claims: List[FactCheckItem] = Field(default_factory=list, description="Consolidated list of claim verifications.")
    all_citations: List[CitationItem] = Field(default_factory=list, description="Normalized citation entries.")
    total_sources_count: int = Field(default=0, description="Total count of unique sources processed.")
    average_confidence_score: float = Field(default=0.0, description="Average confidence score across claims.")
