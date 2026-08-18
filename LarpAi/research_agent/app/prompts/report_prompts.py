REPORT_SYSTEM_PROMPT = (
    "You are an expert technical writer and research analyst. Generate a professional, "
    "publication-ready Markdown research report from the provided aggregated findings. "
    "Include inline citations, a confidence rating, and a structured format."
)

REPORT_FULL_TEMPLATE = (
    "# {title}\n\n"
    "**Query:** {query}\n"
    "**Confidence Score:** {confidence}\n"
    "**Sources Evaluated:** {source_count}\n\n"
    "## Executive Overview\n{overview}\n\n"
    "## Key Findings\n{findings}\n\n"
    "## Evidence & Analysis\n{evidence}\n\n"
    "## References\n{references}\n"
)

REPORT_EXECUTIVE_TEMPLATE = (
    "# Executive Summary: {title}\n\n"
    "**Query:** {query}\n"
    "**Confidence Rating:** {confidence}\n\n"
    "## Summary Highlights\n{findings}\n\n"
    "**Total References Evaluated:** {source_count}\n"
)
