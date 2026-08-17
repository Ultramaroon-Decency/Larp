"""Pydantic schemas for Confidence Scoring system."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfidenceLevel(str, Enum):
    """Human-readable confidence level classification."""

    HIGH = "HIGH"        # 90–100
    MEDIUM = "MEDIUM"    # 75–89
    LOW = "LOW"          # 0–74


class ClaimConfidence(BaseModel):
    """Confidence representation for an individual claim or factual finding."""

    model_config = ConfigDict(from_attributes=True)

    claim: str = Field(description="Factual claim or statement text")
    score: float = Field(ge=0.0, le=100.0, description="Claim confidence score (0.0 to 100.0)")
    confidence_level: ConfidenceLevel = Field(description="Human-readable level: HIGH, MEDIUM, LOW")
    supporting_sources: List[str] = Field(default_factory=list, description="List of supporting source URLs or titles")
    conflicting_sources: List[str] = Field(default_factory=list, description="List of contradictory source URLs or titles")
    explanation: str = Field(description="Empirical explanation derived from evidence inputs")


class ConfidenceScore(BaseModel):
    """Overall confidence evaluation model for a research job result."""

    model_config = ConfigDict(from_attributes=True)

    overall_score: float = Field(ge=0.0, le=100.0, description="Deterministic overall confidence score (0.0 to 100.0)")
    source_quality_score: float = Field(ge=0.0, le=100.0, description="Normalized source authority score (0.0 to 100.0)")
    evidence_coverage_score: float = Field(ge=0.0, le=100.0, description="Ratio of claims supported by evidence (0.0 to 100.0)")
    source_agreement_score: float = Field(ge=0.0, le=100.0, description="Source consensus score (0.0 to 100.0)")
    citation_coverage_score: float = Field(ge=0.0, le=100.0, description="Ratio of claims properly cited (0.0 to 100.0)")
    conflict_penalty: float = Field(ge=0.0, le=100.0, description="Deduction penalty from detected source conflicts")
    confidence_level: ConfidenceLevel = Field(description="Overall confidence level: HIGH, MEDIUM, LOW")
    explanation: str = Field(description="Human-readable overall confidence summary explanation")
    claim_confidences: List[ClaimConfidence] = Field(default_factory=list, description="Claim-level confidence evaluations")


# Alias for response schema
ConfidenceScoreRead = ConfidenceScore
