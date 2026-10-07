"""Tests for the unified vulnerability AI processor."""
import json

import pytest

from models.base import ScannerType, ScanStatus, SeverityLevel
from models.report import AIAnalysis, ScanResult, VulnerabilityFinding
from services.ai.gateway import GatewayError, GatewayResult
from services.ai.schemas import AnalysisNarrative


class FakeGateway:
    """Deterministic gateway double: returns fixed text or raises."""

    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="fake-1",
            usage={"prompt_tokens": 1, "completion_tokens": 1}, latency_ms=1,
        )


def _finding(title="SQL Injection", severity="critical", **kwargs):
    return VulnerabilityFinding(
        id=kwargs.pop("id", "f-1"),
        scanner=ScannerType.BANDIT,
        rule_id="rule-1",
        title=title,
        description=kwargs.pop("description", "SQL injection in login"),
        severity=SeverityLevel(severity),
        file_path=kwargs.pop("file_path", "app/login.py"),
        **kwargs,
    )


def _scan_result(findings, scanner=ScannerType.BANDIT):
    return ScanResult(
        scanner=scanner, status=ScanStatus.COMPLETED,
        findings=findings, duration_seconds=1.0,
    )


VALID_NARRATIVE = {
    "executive_summary": "Two issues need attention.",
    "risk_assessment": "High risk overall.",
    "priority_findings": ["SQL Injection"],
    "recommendations": ["Parameterize queries"],
    "secure_code_examples": {"sql": "cursor.execute('...', (id,))"},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated scanners"],
}


class TestAnalyzeScanResults:
    async def test_clean_scan_short_circuits_without_gateway_call(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(error=AssertionError("gateway must not be called"))
        proc = VulnerabilityAIProcessor(gateway=gw)
        result = await proc.analyze_scan_results([])
        assert isinstance(result, AIAnalysis)
        assert result.risk_score == 5
        assert result.risk_level == "LOW"
        assert result.security_score == 98
        assert result.model_used == "none/clean-scan"
        assert gw.calls == []

    async def test_assembles_narrative_and_deterministic_fields(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(text=json.dumps(VALID_NARRATIVE))
        proc = VulnerabilityAIProcessor(gateway=gw)
        findings = [
            _finding(title="SQL Injection", severity="critical"),
            _finding(
                title="Weak password hash",
                severity="high",
                description="md5 used for password storage",
            ),
        ]
        result = await proc.analyze_scan_results(
            [_scan_result(findings)], {"project_name": "demo"}
        )
        assert result.model_used == "fake/fake-1"
        assert result.executive_summary == "Two issues need attention."
        assert result.priority_findings == ["SQL Injection"]
        assert result.recommendations == ["Parameterize queries"]
        # Deterministic fields computed in code:
        assert result.risk_score == 65          # 40*1 + 25*1
        assert result.risk_level == "CRITICAL"
        assert result.security_score == 68      # 100 - 20 - 12
        assert result.threat_categories == {"Injection": 1, "Authentication": 1}
        assert [p["phase"] for p in result.remediation_roadmap] == [1, 2]
        assert "days" in result.estimated_fix_time  # 12h
        # Single gateway call, structured:
        assert len(gw.calls) == 1
        assert gw.calls[0]["purpose"] == "analysis"
        assert gw.calls[0]["json_schema"] is AnalysisNarrative
        assert gw.calls[0]["use_cache"] is False

    async def test_gateway_error_yields_degraded_analysis(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(error=GatewayError("All AI providers failed: gemini: boom"))
        proc = VulnerabilityAIProcessor(gateway=gw)
        result = await proc.analyze_scan_results([_scan_result([_finding(severity="critical")])])
        assert result.model_used == "unavailable"
        assert result.risk_score == 40
        assert result.risk_level == "CRITICAL"
        assert result.security_score == 80
        assert result.executive_summary  # deterministic fallback text
        assert result.raw_response is None

    async def test_unparseable_narrative_falls_back_but_keeps_raw(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(text="definitely not json")
        proc = VulnerabilityAIProcessor(gateway=gw)
        result = await proc.analyze_scan_results([_scan_result([_finding(severity="high")])])
        assert result.model_used == "fake/fake-1"
        assert result.raw_response == "definitely not json"
        assert result.risk_score == 25
        assert result.executive_summary  # fallback narrative, not empty
        # one retry with schema reminder = 2 calls
        assert len(gw.calls) == 2


class TestEnrichment:
    async def test_sets_fields_on_model_finding(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        advice = {
            "remediation": "Use parameterized queries",
            "fix_effort": "high",
            "secure_code": "cursor.execute('SELECT * FROM t WHERE id = ?', (id,))",
        }
        gw = FakeGateway(text=json.dumps(advice))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = _finding()
        result = await proc.enrich_findings_with_remediation([finding])
        assert result == [finding]
        assert finding.remediation == "Use parameterized queries"
        assert finding.fix_effort == "high"
        assert finding.remediation_code is not None
        assert gw.calls[0]["purpose"] == "remediation"
        assert gw.calls[0]["use_cache"] is True
        assert gw.calls[0]["json_schema"].__name__ == "RemediationAdvice"

    async def test_sets_fields_on_dict_finding(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        advice = {"remediation": "Escape output", "fix_effort": "low", "secure_code": None}
        gw = FakeGateway(text=json.dumps(advice))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = {"title": "XSS", "description": "reflected", "remediation": None}
        await proc.enrich_findings_with_remediation([finding])
        assert finding["remediation"] == "Escape output"
        assert finding["fix_effort"] == "low"
        assert finding["remediation_code"] is None

    async def test_skips_findings_without_title_or_description(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(text=json.dumps({"remediation": "x"}))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = _finding(title="", description="")
        await proc.enrich_findings_with_remediation([finding])
        assert gw.calls == []

    async def test_gateway_error_returns_findings_unchanged(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(error=GatewayError("All AI providers failed"))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = _finding()
        result = await proc.enrich_findings_with_remediation([finding])
        assert result == [finding]
        assert finding.remediation is None
        assert finding.remediation_code is None


class TestHelpers:
    @pytest.fixture
    def proc(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        return VulnerabilityAIProcessor(gateway=FakeGateway())

    def test_prepare_findings_data(self, proc):
        data = proc._prepare_findings_data(
            [_scan_result([_finding(severity="high")])]
        )
        assert data["total_findings"] == 1
        assert data["severity_counts"]["high"] == 1
        assert data["scanner_summary"]["bandit"]["findings_count"] == 1

    def test_prepare_findings_data_empty(self, proc):
        data = proc._prepare_findings_data([])
        assert data["total_findings"] == 0
        assert data["severity_counts"]["critical"] == 0

    def test_calculate_risk_score(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 0, "low": 0, "info": 0},
        }
        score, level = proc._calculate_risk_score(data)
        assert score == 90
        assert level == "CRITICAL"

    def test_calculate_security_score(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1},
        }
        assert proc._calculate_security_score(data) == 60

    def test_categorize_threats(self, proc):
        data = {"findings": [
            {"title": "SQL Injection vulnerability", "description": "SQL injection in login"}
        ]}
        assert proc._categorize_threats(data).get("Injection") == 1

    def test_estimate_fix_time(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1},
        }
        assert "hours" in proc._estimate_fix_time(data)

    def test_remediation_roadmap(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 3, "low": 0, "info": 0},
        }
        roadmap = proc._generate_remediation_roadmap(data)
        assert [r["priority"] for r in roadmap] == ["CRITICAL", "HIGH", "MEDIUM"]

    def test_create_clean_analysis(self, proc):
        analysis = proc._create_clean_analysis()
        assert isinstance(analysis, AIAnalysis)
        assert analysis.risk_score == 5
        assert analysis.security_score == 98
