"""Golden eval: deterministic AI outputs for 24 hand-computed cases.

Run: .venv\\Scripts\\python.exe -m pytest evals/ -v -m eval
No network: every case drives the unified processor with FakeGateway.
"""
import json

import pytest

from evals.cases import CASES, NEUTRAL_DESCRIPTION, SEVERITIES, SEVERITY_TITLES
from models.base import ScannerType, ScanStatus, SeverityLevel
from models.report import ScanResult, VulnerabilityFinding
from services.ai.gateway import GatewayError, GatewayResult
from services.ai.prompts import (
    PROMPT_VERSION,
    build_analysis_prompt,
    build_remediation_prompt,
)
from services.ai.schemas import AnalysisNarrative

NARRATIVE = {
    "executive_summary": "Golden eval summary.",
    "risk_assessment": "Golden eval assessment.",
    "priority_findings": ["SQL Injection in login query"],
    "recommendations": ["Apply parameterized queries"],
    "secure_code_examples": {"python": "cursor.execute('SELECT 1 WHERE id = ?', (id,))"},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated scanners"],
}


class FakeGateway:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="golden",
            usage={}, latency_ms=1,
        )


def _finding(sev: str, i: int) -> VulnerabilityFinding:
    return VulnerabilityFinding(
        id=f"{sev}-{i}",
        scanner=ScannerType.BANDIT,
        rule_id=f"rule-{sev}",
        title=SEVERITY_TITLES[sev],
        description=NEUTRAL_DESCRIPTION,
        severity=SeverityLevel(sev),
        file_path=f"src/{sev}/file_{i}.py",
    )


def _scan_result(counts: dict) -> ScanResult:
    findings = [
        _finding(sev, i)
        for sev in SEVERITIES
        for i in range(counts.get(sev, 0))
    ]
    return ScanResult(
        scanner=ScannerType.BANDIT,
        status=ScanStatus.COMPLETED,
        findings=findings,
        duration_seconds=1.0,
    )


@pytest.mark.eval
@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
async def test_golden_case(case):
    from services.ai.ai_processor import VulnerabilityAIProcessor

    gw = FakeGateway(text=json.dumps(NARRATIVE))
    proc = VulnerabilityAIProcessor(gateway=gw)
    scan_results = [_scan_result(case["counts"])] if case["counts"] else []

    analysis = await proc.analyze_scan_results(scan_results)
    exp = case["expected"]

    assert analysis.risk_score == exp["risk_score"]
    assert analysis.risk_level == exp["risk_level"]
    assert analysis.security_score == exp["security_score"]
    assert analysis.estimated_fix_time == exp["estimated_fix_time"]
    assert [p["phase"] for p in analysis.remediation_roadmap] == exp["roadmap_phases"]
    assert analysis.threat_categories == exp["threat_categories"]

    if not case["counts"]:
        assert analysis.model_used == "none/clean-scan"
        assert "No security vulnerabilities were detected" in analysis.executive_summary
        assert gw.calls == []
    else:
        assert analysis.model_used == "fake/golden"
        assert analysis.executive_summary == "Golden eval summary."
        assert analysis.priority_findings == ["SQL Injection in login query"]
        assert analysis.recommendations == ["Apply parameterized queries"]
        assert analysis.raw_response == json.dumps(NARRATIVE)
        assert len(gw.calls) == 1
        assert gw.calls[0]["purpose"] == "analysis"
        assert gw.calls[0]["json_schema"] is AnalysisNarrative
        assert gw.calls[0]["use_cache"] is False


@pytest.mark.eval
async def test_gateway_error_degrades_to_deterministic_analysis():
    from services.ai.ai_processor import VulnerabilityAIProcessor

    gw = FakeGateway(error=GatewayError("All AI providers failed: gemini: 401"))
    proc = VulnerabilityAIProcessor(gateway=gw)
    analysis = await proc.analyze_scan_results([_scan_result({"critical": 1})])

    assert analysis.model_used == "unavailable"
    assert analysis.risk_score == 40
    assert analysis.risk_level == "CRITICAL"
    assert analysis.security_score == 80
    assert analysis.executive_summary
    assert "Automated scan identified" in analysis.executive_summary
    assert analysis.raw_response is None


@pytest.mark.eval
def test_analysis_prompt_shape():
    prompt = build_analysis_prompt(
        {
            "total_findings": 1,
            "findings": [{"title": "SQL Injection in login query", "description": "SQLi", "severity": "critical"}],
            "severity_counts": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
            "scanner_summary": {"bandit": {"status": "completed", "findings_count": 1, "duration": 1.0}},
        },
        {"project_name": "demo"},
    )
    assert f"Prompt version: {PROMPT_VERSION}" in prompt
    assert "<scan_data>" in prompt and "</scan_data>" in prompt
    assert '"SQL Injection in login query"' in prompt
    assert '"executive_summary"' in prompt  # schema embedded
    assert "demo" in prompt


@pytest.mark.eval
def test_analysis_prompt_truncates_descriptions_and_caps_findings():
    long_desc = "D" * 600
    findings = [
        {"title": f"f{i}", "description": long_desc, "severity": "high"}
        for i in range(55)
    ]
    prompt = build_analysis_prompt(
        {
            "total_findings": 55,
            "findings": findings,
            "severity_counts": {"critical": 0, "high": 55, "medium": 0, "low": 0, "info": 0},
            "scanner_summary": {},
        }
    )
    assert '"f49"' in prompt          # last of the capped 50
    assert '"f50"' not in prompt      # findings[:50] cap
    assert "D" * 500 in prompt        # description[:500]
    assert "D" * 501 not in prompt


@pytest.mark.eval
def test_remediation_prompt_includes_identifiers_and_schema():
    prompt = build_remediation_prompt(
        {
            "title": "SQL Injection",
            "severity": "critical",
            "description": "SQLi in query",
            "file_path": "app/login.py",
            "code_snippet": "cursor.execute(f\"SELECT {q}\")",
            "cwe_id": "CWE-89",
            "cve_id": "CVE-2024-1234",
        }
    )
    assert f"Prompt version: {PROMPT_VERSION}" in prompt
    assert "CWE-89" in prompt
    assert "CVE-2024-1234" in prompt
    assert "app/login.py" in prompt
    assert "cursor.execute" in prompt
    assert '"remediation"' in prompt and '"fix_effort"' in prompt
