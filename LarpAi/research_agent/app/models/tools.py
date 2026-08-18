from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """
    Standardized result wrapper for all tool execution calls.
    """
    success: bool = Field(..., description="True if execution succeeded without errors.")
    data: Optional[Any] = Field(default=None, description="Payload returned by the tool execution.")
    error: Optional[str] = Field(default=None, description="Error message if execution failed.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as execution time, provider, etc.")


class SearchResultItem(BaseModel):
    """
    Individual search result item.
    """
    title: str = Field(..., description="Title of the search result page.")
    snippet: str = Field(..., description="Text summary snippet from the page.")
    url: str = Field(..., description="URL of the source page.")
    score: float = Field(default=1.0, description="Relevance score of the search result.")


class SearchResponse(BaseModel):
    """
    Response returned by search tools.
    """
    query: str = Field(..., description="Original search query.")
    results: List[SearchResultItem] = Field(default_factory=list, description="List of search result items.")
    total_results: int = Field(default=0, description="Total count of results found.")


class FactCheckItem(BaseModel):
    """
    Verification status for a single statement or claim.
    """
    claim: str = Field(..., description="The claim or statement being verified.")
    status: str = Field(..., description="Verification status: 'verified', 'disputed', or 'unverified'.")
    confidence_score: float = Field(..., description="Confidence score from 0.0 to 1.0.")
    evidence_sources: List[str] = Field(default_factory=list, description="List of source URLs or citations supporting status.")


class FactCheckResponse(BaseModel):
    """
    Response returned by fact-checking tools.
    """
    claims: List[FactCheckItem] = Field(default_factory=list, description="Verified claims.")


class SummaryResponse(BaseModel):
    """
    Response returned by summarization tools.
    """
    summary: str = Field(..., description="Concise summarized text.")
    key_takeaways: List[str] = Field(default_factory=list, description="List of key points extracted.")
    word_count: int = Field(..., description="Word count of the summary.")


class CitationItem(BaseModel):
    """
    Normalized citation object.
    """
    source_id: str = Field(..., description="Identifier for the source (e.g., 'src-1').")
    title: str = Field(..., description="Title of the cited work.")
    authors: List[str] = Field(default_factory=list, description="List of author names.")
    url: Optional[str] = Field(default=None, description="URL link to work.")
    year: Optional[int] = Field(default=None, description="Publication year.")
    formatted_citation: str = Field(..., description="Formatted citation text (APA/IEEE style).")


class CitationResponse(BaseModel):
    """
    Response returned by citation tools.
    """
    citations: List[CitationItem] = Field(default_factory=list, description="Normalized citation list.")


class ScrapeResult(BaseModel):
    """
    Result of a web page content scrape operation.
    """
    url: str = Field(..., description="Target URL that was scraped.")
    title: str = Field(..., description="Extracted title of the page.")
    content: str = Field(..., description="Cleaned body text extracted from the page.")
    word_count: int = Field(default=0, description="Word count of the extracted body text.")
    status_code: int = Field(default=200, description="HTTP status code returned by the target host.")
    extracted_tables: List[str] = Field(default_factory=list, description="Markdown formatting of tables extracted from page / PDFs.")
    image_analyses: List[str] = Field(default_factory=list, description="Text analysis/transcriptions of scraped charts or diagrams.")


