"""Pydantic schemas for structured LLM outputs."""
import json
import re
from typing import Any, Dict, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field, ValidationError

T = TypeVar("T", bound=BaseModel)


class AnalysisNarrative(BaseModel):
    """LLM-authored narrative portion of an AI analysis.

    Deterministic fields (risk_score, security_score, threat_categories,
    estimated_fix_time, remediation_roadmap) are computed in code and
    deliberately absent here - they are never re-asked to a model.
    """

    executive_summary: str = Field(..., min_length=1)
    risk_assessment: str = Field(..., min_length=1)
    priority_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    secure_code_examples: Dict[str, str] = Field(default_factory=dict)
    compliance_impact: Dict[str, Any] = Field(default_factory=dict)
    attack_vectors: List[str] = Field(default_factory=list)


class RemediationAdvice(BaseModel):
    """LLM-authored remediation for a single finding."""

    remediation: str = Field(..., min_length=1)
    fix_effort: Literal["low", "medium", "high"] = "medium"
    secure_code: Optional[str] = None


def parse_json_model(text: Optional[str], schema: type[T]) -> Optional[T]:
    """Parse `text` into `schema`, tolerating fences and surrounding prose.

    Returns None when no candidate parses and validates.
    """
    if not text:
        return None
    stripped = text.strip()
    candidates = [stripped]
    if stripped.startswith("```"):
        inner = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        inner = re.sub(r"\s*```$", "", inner)
        candidates.append(inner)
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            return schema.model_validate_json(candidate)
        except (ValidationError, ValueError, AttributeError):
            continue
    return None
