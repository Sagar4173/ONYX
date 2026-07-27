from typing import Optional

from pydantic import BaseModel


class BusinessContext(BaseModel):
    asset_criticality: str = "medium"
    data_classification: str = "internal"
    exposure_level: str = "internal_network"
    compliance_frameworks: list[str] = []


class ScoreBreakdown(BaseModel):
    total: float
    severity: float
    cvss: float
    exploitability: float
    business_impact: float
    compliance_risk: float
    epss: float
    false_positive_adjustment: float


class RankedFinding(BaseModel):
    finding_id: str
    title: str
    severity: str
    file_path: str
    composite_score: float
    priority: str
    score_breakdown: ScoreBreakdown
    ai_triage_summary: Optional[str] = None
    sla_deadline: Optional[str] = None


class TriageResult(BaseModel):
    scan_id: str
    project_name: str
    total_findings: int
    ranked_findings: list[RankedFinding]
    priority_counts: dict[str, int]
    executive_summary: Optional[str] = None
    business_context: BusinessContext
    generated_at: str
