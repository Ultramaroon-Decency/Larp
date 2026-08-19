import re
import logging
from typing import List, Dict, Set
from research_agent.app.models.executor import PlanExecutionResult, TaskExecutionResult
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.models.tools import (
    SearchResultItem,
    FactCheckItem,
    CitationItem
)

logger = logging.getLogger(__name__)


class AggregatorError(Exception):
    """Exception raised when aggregation fails."""
    pass


# Weight multipliers for confidence scoring based on claim verification status.
_CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "verified": 1.0,
    "disputed": 0.5,
    "unverified": 0.25,
}


class ResultAggregatorAgent:
    """
    Result Aggregator Agent responsible for merging, deduplicating,
    and normalizing structured findings from multi-stage task executions.

    Claim deduplication is performed on normalised text (lowercased,
    collapsed whitespace) to catch near-duplicate claims. Confidence
    scoring uses status-weighted averaging: verified claims contribute
    at full weight, disputed at 0.5×, and unverified at 0.25×.
    """

    @staticmethod
    def _normalize_claim(text: str) -> str:
        """Lowercase and collapse whitespace for deduplication comparison."""
        return re.sub(r"\s+", " ", text.strip().lower())

    def aggregate_results(self, exec_result: PlanExecutionResult) -> AggregatedResearchData:
        """
        Merges task results from PlanExecutionResult into a unified AggregatedResearchData payload.
        """
        if not exec_result.stage_results:
            raise AggregatorError("Cannot aggregate empty execution results.")

        logger.info(f"Aggregating results for plan '{exec_result.plan_id}' ('{exec_result.query}')")

        seen_urls: Set[str] = set()
        seen_claims: Set[str] = set()
        seen_takeaways: Set[str] = set()
        seen_citations: Set[str] = set()

        search_results: List[SearchResultItem] = []
        verified_claims: List[FactCheckItem] = []
        takeaways: List[str] = []
        citations: List[CitationItem] = []

        # Traversal over stages and tasks
        for stage in exec_result.stage_results:
            for task_res in stage:
                if task_res.status != "completed" and not task_res.service_results:
                    continue

                for service_name, payload in task_res.service_results.items():
                    if not isinstance(payload, dict):
                        continue

                    # 1. Process Search Results
                    if service_name == "search" and "results" in payload:
                        for item in payload.get("results", []):
                            url = item.get("url", "")
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                search_results.append(SearchResultItem(**item))

                    # 2. Process Fact Check Claims
                    elif service_name == "fact_check" and "claims" in payload:
                        for claim_obj in payload.get("claims", []):
                            c_text = claim_obj.get("claim", "")
                            normalized = self._normalize_claim(c_text) if c_text else ""
                            if normalized and normalized not in seen_claims:
                                seen_claims.add(normalized)
                                verified_claims.append(FactCheckItem(**claim_obj))

                    # 3. Process Summaries & Takeaways
                    elif service_name == "summary":
                        summary_txt = payload.get("summary", "")
                        if summary_txt and summary_txt not in seen_takeaways:
                            seen_takeaways.add(summary_txt)
                            takeaways.append(summary_txt)

                        for kw in payload.get("key_takeaways", []):
                            if kw and kw not in seen_takeaways:
                                seen_takeaways.add(kw)
                                takeaways.append(kw)

                    # 4. Process Citations
                    elif service_name == "citation" and "citations" in payload:
                        for cite_obj in payload.get("citations", []):
                            c_url = cite_obj.get("url", "") or cite_obj.get("title", "")
                            if c_url and c_url not in seen_citations:
                                seen_citations.add(c_url)
                                citations.append(CitationItem(**cite_obj))

                    # 5. Process Scraper (Multi-Modal Vision Tables / Image Analyses)
                    elif service_name == "scraper":
                        # Also check if scraper returns clean body text to append as a takeaway
                        body_txt = payload.get("content", "")
                        if body_txt and len(body_txt) < 300 and body_txt not in seen_takeaways:
                            seen_takeaways.add(body_txt)
                            takeaways.append(body_txt)

        # Gather vision artifacts from scraper payloads across all completed tasks
        extracted_tables: List[str] = []
        image_analyses: List[str] = []
        for stage in exec_result.stage_results:
            for task_res in stage:
                for s_name, s_payload in task_res.service_results.items():
                    if s_name == "scraper" and isinstance(s_payload, dict):
                        extracted_tables.extend(s_payload.get("extracted_tables", []))
                        image_analyses.extend(s_payload.get("image_analyses", []))

        # Compute weighted confidence: status weight × raw score, normalised by total weight.
        # This gives higher influence to 'verified' claims and penalises 'disputed' evidence.
        if verified_claims:
            total_weight = 0.0
            weighted_sum = 0.0
            for claim in verified_claims:
                w = _CONFIDENCE_WEIGHTS.get(claim.status, 0.25)
                weighted_sum += w * claim.confidence_score
                total_weight += w
            avg_confidence = weighted_sum / total_weight if total_weight > 0 else 1.0
        else:
            avg_confidence = 1.0

        aggregated = AggregatedResearchData(
            plan_id=exec_result.plan_id,
            query=exec_result.query,
            synthesized_takeaways=takeaways,
            all_search_results=search_results,
            all_verified_claims=verified_claims,
            all_citations=citations,
            total_sources_count=len(search_results) + len(citations),
            average_confidence_score=round(avg_confidence, 3),
            extracted_tables=extracted_tables,
            image_analyses=image_analyses
        )

        logger.info(f"Aggregation complete: {len(search_results)} search items, {len(verified_claims)} claims, {len(citations)} citations, {len(extracted_tables)} vision tables.")
        return aggregated

