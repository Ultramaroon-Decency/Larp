import uuid
import logging
from typing import Optional
from research_agent.app.models.aggregator import AggregatedResearchData
from research_agent.app.models.report import ResearchReport

logger = logging.getLogger(__name__)


class ReportGeneratorError(Exception):
    """Exception raised when report generation fails."""
    pass


class ReportGeneratorAgent:
    """
    Report Generator Agent responsible for rendering aggregated research data
    into publication-ready, structured Markdown reports.
    """

    def generate_report(
        self,
        data: AggregatedResearchData,
        format_type: str = "FULL"
    ) -> ResearchReport:
        """
        Generates a ResearchReport from AggregatedResearchData.

        Args:
            data: Aggregated research payload containing findings, claims, search items, and citations.
            format_type: 'FULL' for comprehensive report, 'EXECUTIVE' for briefing summary.

        Returns:
            ResearchReport containing formatted markdown content and metadata.
        """
        if not data:
            raise ReportGeneratorError("Aggregated research data cannot be empty.")

        logger.info(f"Generating '{format_type}' report for query '{data.query}' (Plan: {data.plan_id})")

        report_id = f"report-{uuid.uuid4().hex[:8]}"
        title = f"Research Report: {data.query.title()}"

        if format_type.upper() == "EXECUTIVE":
            markdown_content = self._build_executive_report(data, title)
        else:
            markdown_content = self._build_full_report(data, title)

        report = ResearchReport(
            report_id=report_id,
            plan_id=data.plan_id,
            query=data.query,
            title=title,
            markdown_content=markdown_content,
            confidence_score=data.average_confidence_score,
            total_sources=data.total_sources_count
        )

        logger.info(f"Successfully generated report {report_id} ({len(markdown_content)} chars).")
        return report

    def _build_full_report(self, data: AggregatedResearchData, title: str) -> str:
        """
        Constructs a full comprehensive Markdown research report with inline numerical citations.
        """
        lines = [
            f"# {title}",
            "",
            "> [!NOTE]",
            f"> **Plan ID:** `{data.plan_id}` | **Sources Count:** {data.total_sources_count} | **Confidence Score:** {data.average_confidence_score * 100:.1f}%",
            "",
            "## Executive Overview",
            f"This research report aggregates automated analysis and multi-source findings for the query: **\"{data.query}\"**.",
            ""
        ]

        # Build numerical source index map
        source_map = {}
        curr_idx = 1
        for item in data.all_search_results:
            source_map[item.url] = curr_idx
            curr_idx += 1
        for cite in data.all_citations:
            if cite.url and cite.url not in source_map:
                source_map[cite.url] = curr_idx
                curr_idx += 1

        # Key Takeaways with Inline Footnote Citations
        lines.append("## Key Findings & Synthesized Takeaways")
        if data.synthesized_takeaways:
            for idx, takeaway in enumerate(data.synthesized_takeaways, start=1):
                # Attach numerical citation tag matching search results if available
                cite_tag = f" [[{((idx - 1) % max(len(source_map), 1)) + 1}]]" if source_map else ""
                lines.append(f"- {takeaway}{cite_tag}")
        else:
            lines.append("- *No specific synthesized takeaways were extracted.*")
        lines.append("")

        # Verified Claims & Evidence Table
        lines.append("## Verified Evidence & Fact Analysis")
        if data.all_verified_claims:
            lines.append("| Claim / Statement | Status | Confidence | Source / Reference |")
            lines.append("| :--- | :---: | :---: | :--- |")
            for claim in data.all_verified_claims:
                status_icon = f"✅ {claim.status.title()}" if claim.status.lower() == "verified" else f"⚠️ {claim.status.title()}"
                conf_pct = f"{claim.confidence_score * 100:.0f}%"
                
                # Map source URLs to numerical citation markers
                ref_links = []
                for src in claim.evidence_sources:
                    num = source_map.get(src)
                    if num:
                        ref_links.append(f"[[{num}]]({src})")
                    else:
                        ref_links.append(src)
                sources_str = ", ".join(ref_links) if ref_links else "N/A"

                clean_claim = claim.claim.replace("|", "\\|")
                lines.append(f"| {clean_claim} | {status_icon} | {conf_pct} | {sources_str} |")
        else:
            lines.append("*No structured fact claims were logged for this research run.*")
        lines.append("")

        # Search References & Citations with matching numerical badges
        lines.append("## References & Domain Sources")
        if data.all_search_results:
            lines.append("### Web Search Findings")
            for item in data.all_search_results:
                s_num = source_map.get(item.url, "*")
                lines.append(f"[{s_num}] **[{item.title}]({item.url})**")
                lines.append(f"   > {item.snippet}")
                lines.append(f"   - *Relevance Score:* {item.score}")
            lines.append("")

        if data.all_citations:
            lines.append("### Academic & Verified Citations")
            for cite in data.all_citations:
                c_num = source_map.get(cite.url, "*")
                authors_str = f" by {', '.join(cite.authors)}" if cite.authors else ""
                year_str = f" ({cite.year})" if cite.year else ""
                lines.append(f"[{c_num}] **[{cite.title}]({cite.url})**{authors_str}{year_str}")
                lines.append(f"   > *Citation:* {cite.formatted_citation}")
            lines.append("")

        if not data.all_search_results and not data.all_citations:
            lines.append("*No external search links or citations recorded.*")
            lines.append("")

        # Multi-Modal Vision Artifacts (NEW)
        if data.extracted_tables or data.image_analyses:
            lines.append("## 📊 Multi-Modal Data Extracted (Charts & Tables)")
            if data.extracted_tables:
                lines.append("### Extracted Data Tables")
                for tbl in data.extracted_tables:
                    lines.append(tbl)
                    lines.append("")
            if data.image_analyses:
                lines.append("### Chart & Image Visual Analysis")
                for img_desc in data.image_analyses:
                    lines.append(f"- {img_desc}")
                lines.append("")

        lines.append("---")
        lines.append("*Report automatically generated by Larp AI Agent Orchestrator.*")
        return "\n".join(lines)

    def _build_executive_report(self, data: AggregatedResearchData, title: str) -> str:
        """
        Constructs a condensed executive summary report.
        """
        lines = [
            f"# Executive Summary: {title}",
            "",
            f"**Query:** {data.query}",
            f"**Confidence Rating:** {data.average_confidence_score * 100:.1f}%",
            "",
            "### Summary Highlights"
        ]

        if data.synthesized_takeaways:
            for takeaway in data.synthesized_takeaways:
                lines.append(f"* {takeaway}")
        else:
            lines.append("* Automated research completed with basic findings.")

        lines.append("")
        lines.append(f"**Total References Evaluated:** {data.total_sources_count}")
        return "\n".join(lines)
