from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.triage import BusinessContext
from services.triage.triage_service import (
    TriageService,
    _get_severity_score,
    _get_priority_label,
    PRIORITY_MAP,
)


@pytest.fixture
def service():
    return TriageService()


def _make_finding(
    finding_id="f-1",
    severity="critical",
    title="Test finding",
    file_path="src/app.py",
    cvss_base=None,
    exploitability=None,
    false_positive=None,
    cve_id=None,
    compliance_mappings=None,
    business_impact=None,
):
    mock = MagicMock()
    mock.id = finding_id
    mock.severity = MagicMock()
    mock.severity.value = severity
    mock.title = title
    mock.file_path = file_path
    mock.cvss_score = None
    if cvss_base is not None:
        mock.cvss_score = MagicMock()
        mock.cvss_score.base_score = cvss_base
    mock.exploitability_score = exploitability
    mock.false_positive_score = false_positive
    mock.cve_id = cve_id
    mock.compliance_mappings = compliance_mappings or []
    mock.business_impact = business_impact
    mock.metadata = {}
    return mock


class TestGetSeverityScore:
    def test_critical_returns_100(self):
        finding = _make_finding(severity="critical")
        assert _get_severity_score(finding) == 100

    def test_high_returns_75(self):
        finding = _make_finding(severity="high")
        assert _get_severity_score(finding) == 75

    def test_info_returns_5(self):
        finding = _make_finding(severity="info")
        assert _get_severity_score(finding) == 5


class TestGetPriorityLabel:
    def test_100_is_immediate(self):
        label, sla = _get_priority_label(100)
        assert label == "IMMEDIATE"
        assert sla == "24h"

    def test_80_is_immediate(self):
        label, sla = _get_priority_label(80)
        assert label == "IMMEDIATE"

    def test_60_is_high(self):
        label, sla = _get_priority_label(60)
        assert label == "HIGH"
        assert sla == "7d"

    def test_40_is_medium(self):
        label, sla = _get_priority_label(40)
        assert label == "MEDIUM"
        assert sla == "30d"

    def test_20_is_low(self):
        label, sla = _get_priority_label(20)
        assert label == "LOW"
        assert sla == "90d"

    def test_0_is_informational(self):
        label, sla = _get_priority_label(0)
        assert label == "INFORMATIONAL"
        assert sla is None


class TestComputeCompositeScore:
    def test_critical_cvss_exploitable_high_criticality(self, service):
        bi = MagicMock()
        bi.confidentiality_impact = "high"
        bi.integrity_impact = "high"
        bi.availability_impact = "high"
        bi.business_criticality = "critical"
        finding = _make_finding(
            severity="critical",
            cvss_base=9.0,
            exploitability=8.5,
            business_impact=bi,
            cve_id="CVE-2024-1234",
            compliance_mappings=[MagicMock()],
        )
        context = BusinessContext(asset_criticality="critical")

        mock_vm = MagicMock()
        mock_epss = MagicMock()
        mock_epss.epss_score = 0.75
        mock_vm.epss_service.get_epss_score.return_value = mock_epss

        with patch(
            "services.service_registry.ServiceRegistry.get_vulnerability_manager",
            return_value=mock_vm,
        ):
            score, breakdown = service._compute_composite_score(finding, context)
        assert score >= 70
        assert score < 80  # HIGH (not IMMEDIATE) without yet more factors
        assert breakdown.severity == 100
        assert breakdown.cvss == 90

    def test_low_severity_low_criticality(self, service):
        finding = _make_finding(severity="low", cvss_base=2.0, exploitability=1.0)
        context = BusinessContext(asset_criticality="low")
        score, breakdown = service._compute_composite_score(finding, context)
        assert score < 40

    def test_false_positive_reduces_score(self, service):
        finding_low_fp = _make_finding(
            severity="high", cvss_base=7.0, exploitability=6.0, false_positive=0.1
        )
        finding_high_fp = _make_finding(
            severity="high", cvss_base=7.0, exploitability=6.0, false_positive=0.8
        )
        context = BusinessContext(asset_criticality="medium")
        score_low, _ = service._compute_composite_score(finding_low_fp, context)
        score_high, _ = service._compute_composite_score(finding_high_fp, context)
        assert score_high < score_low

    def test_compliance_mapped_gets_boost(self, service):
        finding_no = _make_finding(
            severity="medium", cvss_base=5.0, exploitability=4.0,
        )
        finding_yes = _make_finding(
            severity="medium",
            cvss_base=5.0,
            exploitability=4.0,
            compliance_mappings=[MagicMock()],
        )
        context = BusinessContext(asset_criticality="medium")
        score_no, _ = service._compute_composite_score(finding_no, context)
        score_yes, _ = service._compute_composite_score(finding_yes, context)
        assert score_yes > score_no

    def test_missing_scoring_fields_does_not_crash(self, service):
        finding = _make_finding(severity="info")
        context = BusinessContext()
        score, breakdown = service._compute_composite_score(finding, context)
        assert score >= 0
        assert score < 20

    def test_business_impact_adds_to_score(self, service):
        bi = MagicMock()
        bi.confidentiality_impact = True
        bi.integrity_impact = True
        bi.availability_impact = False
        bi.business_criticality = "critical"

        bi.availability_impact = "high"
        finding = _make_finding(
            severity="medium", cvss_base=5.0, exploitability=4.0, business_impact=bi
        )
        context = BusinessContext()
        score_with, _ = service._compute_composite_score(finding, context)
        assert score_with > 0
        assert score_with >= 30


class TestTriageScan:
    @pytest.mark.asyncio
    async def test_scan_not_found_returns_none(self, service):
        with patch.object(
            service, "_load_scan_report", AsyncMock(return_value=None)
        ):
            result = await service.triage_scan("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_scan_with_findings_returns_sorted(self, service):
        finding1 = _make_finding("f-1", "critical", "SQL Injection", "app.py", 9.0, 8.0)
        finding2 = _make_finding("f-2", "low", "Debug log", "utils.py", 1.0, 0.5)

        mock_report = MagicMock()
        mock_report.scan_id = "scan-001"
        mock_report.project_name = "test-project"
        mock_report.total_findings = 2
        mock_report.metadata = {}
        scan_result = MagicMock()
        scan_result.findings = [finding1, finding2]
        mock_report.scan_results = [scan_result]

        with (
            patch.object(service, "_load_scan_report", AsyncMock(return_value=mock_report)),
            patch.object(service, "_call_ai", AsyncMock(return_value=None)),
            patch.object(service, "_cache_result", AsyncMock()),
        ):
            result = await service.triage_scan("scan-001")

        assert result is not None
        assert result.total_findings == 2
        assert len(result.ranked_findings) == 2
        assert result.ranked_findings[0].finding_id == "f-1"
        assert result.ranked_findings[1].finding_id == "f-2"

    @pytest.mark.asyncio
    async def test_scan_no_findings(self, service):
        mock_report = MagicMock()
        mock_report.scan_id = "scan-001"
        mock_report.project_name = "test-project"
        mock_report.total_findings = 0
        mock_report.metadata = {}
        scan_result = MagicMock()
        scan_result.findings = []
        mock_report.scan_results = [scan_result]

        with patch.object(service, "_load_scan_report", AsyncMock(return_value=mock_report)):
            result = await service.triage_scan("scan-001")

        assert result is not None
        assert result.total_findings == 0
        assert len(result.ranked_findings) == 0
        assert "No findings" in (result.executive_summary or "")

    @pytest.mark.asyncio
    async def test_db_error_returns_none(self, service):
        # _load_scan_report already catches exceptions internally
        with patch.object(service, "_load_scan_report", AsyncMock(return_value=None)):
            result = await service.triage_scan("scan-001")
        assert result is None


class TestBusinessImpactScore:
    def test_full_impact_with_critical_asset(self, service):
        bi = MagicMock()
        bi.confidentiality_impact = "high"
        bi.integrity_impact = "high"
        bi.availability_impact = "high"
        bi.business_criticality = "critical"
        finding = _make_finding(business_impact=bi)
        context = BusinessContext(asset_criticality="critical")
        score = service._compute_business_impact_score(finding, context)
        assert score == 90.0

    def test_no_impact_no_context(self, service):
        finding = _make_finding(business_impact=None)
        context = BusinessContext()
        score = service._compute_business_impact_score(finding, context)
        assert score == 20.0


class TestComplianceRiskScore:
    def test_with_mappings_returns_100(self, service):
        finding = _make_finding(compliance_mappings=[MagicMock()])
        assert service._compute_compliance_risk_score(finding) == 100.0

    def test_without_mappings_returns_0(self, service):
        finding = _make_finding(compliance_mappings=[])
        assert service._compute_compliance_risk_score(finding) == 0.0


class TestComputeEpssScore:
    def test_with_cve_and_epss_data(self, service):
        mock_epss = MagicMock()
        mock_epss.epss_score = 0.75
        mock_vm = MagicMock()
        mock_vm.epss_service.get_epss_score.return_value = mock_epss

        finding = _make_finding(cve_id="CVE-2024-1234")
        with patch(
            "services.service_registry.ServiceRegistry.get_vulnerability_manager",
            return_value=mock_vm,
        ):
            score = service._compute_epss_score(finding)
        assert score == 75.0

    def test_without_cve_returns_0(self, service):
        finding = _make_finding(cve_id=None)
        assert service._compute_epss_score(finding) == 0.0
