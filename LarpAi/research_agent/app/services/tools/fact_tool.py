from abc import ABC
from typing import List
from research_agent.app.services.tools.base import BaseTool
from research_agent.app.models.tools import FactCheckResponse, FactCheckItem


class BaseFactCheckTool(BaseTool, ABC):
    """
    Abstract interface for Fact Checking Tools.
    """
    def __init__(self, name: str = "FactCheckTool", description: str = "Verifies claims and statements against trusted sources."):
        super().__init__(name=name, description=description)


class MockFactCheckTool(BaseFactCheckTool):
    """
    Mock implementation of FactCheckTool for Phase 3 testing and offline development.
    """

    def __init__(self):
        super().__init__(
            name="MockFactCheckTool",
            description="Returns mock claim verification statuses and confidence metrics."
        )

    async def _run(self, claims: List[str]) -> FactCheckResponse:
        """
        Generates mock fact-checking outputs for a list of claims.
        """
        if not claims:
            raise ValueError("Claims list cannot be empty.")

        verified_items: List[FactCheckItem] = []
        for idx, claim in enumerate(claims):
            clean_claim = claim.strip()
            if not clean_claim:
                continue

            # Deterministic mocking rule based on length/index
            is_verified = len(clean_claim) % 2 == 0
            status = "verified" if is_verified else "disputed"
            confidence = 0.92 if is_verified else 0.65

            verified_items.append(
                FactCheckItem(
                    claim=clean_claim,
                    status=status,
                    confidence_score=confidence,
                    evidence_sources=[
                        f"https://factcheck.org/ref/{idx + 101}",
                        f"https://academic-verify.org/id/{idx + 500}"
                    ]
                )
            )

        return FactCheckResponse(claims=verified_items)
