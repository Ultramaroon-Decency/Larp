import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from research_agent.app.models.aggregator import AggregatedResearchData


class ReportRequest(BaseModel):
    """
    Input schema for requesting report generation.
    Supports supplying either a query to run end-to-end or pre-aggregated research data.
    """
    query: Optional[str] = Field(default=None, description="Research query for end-to-end report generation.")
    execution_data: Optional[AggregatedResearchData] = Field(default=None, description="Pre-aggregated research data.")
    format_type: str = Field(default="FULL", description="Report format type: 'FULL' or 'EXECUTIVE'.")


class ResearchReport(BaseModel):
    """
    Schema representing a completed, formatted research report.
    """
    report_id: str = Field(..., description="Unique identifier for the generated report.")
    plan_id: str = Field(..., description="Associated execution plan ID.")
    query: str = Field(..., description="Original research topic or query.")
    title: str = Field(..., description="Title of the research report.")
    markdown_content: str = Field(..., description="Full formatted Markdown content of the report.")
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO timestamp of report creation."
    )
    confidence_score: float = Field(..., description="Average confidence score across facts (0.0 - 1.0).")
    total_sources: int = Field(..., description="Total number of cited references and search sources.")
