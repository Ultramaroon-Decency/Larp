"""Tool pricing registry defining costs and free fallback mappings for paid tools."""

from typing import Dict, Optional


class ToolPricingRegistry:
    """Registry maintaining tool pricing schedules and free fallback tool mappings."""

    # Default Tool Pricing Schedule (USD)
    TOOL_PRICING: Dict[str, float] = {
        # Free Tools ($0.00)
        "SearchTool": 0.00,
        "WebSearchTool": 0.00,
        "MockSearchAgent": 0.00,
        "FactCheckerTool": 0.00,
        "MockFactCheckerAgent": 0.00,
        "PlannerTool": 0.00,
        "ReportTool": 0.00,
        "CitationTool": 0.00,
        
        # Paid Premium Tools (USD)
        "PremiumSearchTool": 0.15,
        "AcademicPremiumTool": 0.10,
        "DeepFactCheckTool": 0.05,
        "ExpensiveAnalysisTool": 0.30,
        "HighTierDataTool": 0.40,
    }

    # Fallback Tool Mapping: Paid Tool -> Free Alternative Tool
    FALLBACK_MAPPING: Dict[str, str] = {
        "PremiumSearchTool": "SearchTool",
        "AcademicPremiumTool": "WebSearchTool",
        "DeepFactCheckTool": "FactCheckerTool",
        "ExpensiveAnalysisTool": "SearchTool",
        "HighTierDataTool": "WebSearchTool",
    }

    @classmethod
    def get_tool_cost(cls, tool_name: str) -> float:
        """Get the cost in USD for a specified tool."""
        return cls.TOOL_PRICING.get(tool_name, 0.00)

    @classmethod
    def is_paid_tool(cls, tool_name: str) -> bool:
        """Check if a tool requires micropayment (cost > 0.0)."""
        return cls.get_tool_cost(tool_name) > 0.0

    @classmethod
    def get_free_fallback(cls, tool_name: str) -> Optional[str]:
        """Get equivalent free fallback tool name if available."""
        return cls.FALLBACK_MAPPING.get(tool_name, "SearchTool" if cls.is_paid_tool(tool_name) else None)
