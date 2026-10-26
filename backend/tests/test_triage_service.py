from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.report import ScanReport
from models.triage import BusinessContext
from services.scanning.vulnerability.manager import EPSSData
from services.service_registry import ServiceRegistry
from services.triage.triage_service import (
    TriageService,
    _context_hash,
    _get_priority_label,
    _get_severity_score,
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
    triage_label=None,
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
    # Stored score wins over the deterministic heuristic (heuristics are
    # covered separately in test_fp_heuristics.py with real findings).
    mock.false_positive_score = false_positive if false_positive is not None else 0.0
    mock.cve_id = cve_id
    mock.compliance_mappings = compliance_mappings or []
    mock.business_impact = business_impact
    mock.triage_label = triage_label
    mock.metadata = {}
    return mock


def _make_report(findings, metadata=None):
    mock_report = MagicMock()
    mock_report.scan_id = "scan-001"
    mock_report.project_name = "test-project"
    mock_report.total_findings = len(findings)
    mock_report.metadata = metadata if metadata is not None else {}
    scan_result = MagicMock()
    scan_result.findings = findings
    mock_report.scan_results = [scan_result]
    return mock_report


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
    async def test_critical_cvss_exploitable_high_criticality(self, service):
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
        mock_vm.get_epss_score = AsyncMock(return_value=mock_epss)

        with patch(
            "services.service_registry.ServiceRegistry.get_vulnerability_manager",
            return_value=mock_vm,
        ):
            score, breakdown = await service._compute_composite_score(finding, context)
        assert score >= 70
        assert score < 80  # HIGH (not IMMEDIATE) without yet more factors
        assert breakdown.severity == 100
        assert breakdown.cvss == 90

    async def test_low_severity_low_criticality(self, service):
        finding = _make_finding(severity="low", cvss_base=2.0, exploitability=1.0)
        context = BusinessContext(asset_criticality="low")
        score, breakdown = await service._compute_composite_score(finding, context)
        assert score < 40

    async def test_false_positive_reduces_score(self, service):
        finding_low_fp = _make_finding(
            severity="high", cvss_base=7.0, exploitability=6.0, false_positive=0.1
        )
        finding_high_fp = _make_finding(
            severity="high", cvss_base=7.0, exploitability=6.0, false_positive=0.8
        )
        context = BusinessContext(asset_criticality="medium")
        score_low, _ = await service._compute_composite_score(finding_low_fp, context)
        score_high, _ = await service._compute_composite_score(finding_high_fp, context)
        assert score_high < score_low

    async def test_compliance_mapped_gets_boost(self, service):
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
        score_no, _ = await service._compute_composite_score(finding_no, context)
        score_yes, _ = await service._compute_composite_score(finding_yes, context)
        assert score_yes > score_no

    async def test_missing_scoring_fields_does_not_crash(self, service):
        finding = _make_finding(severity="info")
        context = BusinessContext()
        score, breakdown = await service._compute_composite_score(finding, context)
        assert score >= 0
        assert score < 20

    async def test_business_impact_adds_to_score(self, service):
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
        score_with, _ = await service._compute_composite_score(finding, context)
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
    async def test_with_cve_and_epss_data(self, service):
        mock_epss = MagicMock()
        mock_epss.epss_score = 0.75
        mock_vm = MagicMock()
        mock_vm.get_epss_score = AsyncMock(return_value=mock_epss)

        finding = _make_finding(cve_id="CVE-2024-1234")
        with patch(
            "services.service_registry.ServiceRegistry.get_vulnerability_manager",
            return_value=mock_vm,
        ):
            score = await service._compute_epss_score(finding)
        assert score == 75.0
        mock_vm.get_epss_score.assert_awaited_once_with("CVE-2024-1234")

    async def test_without_cve_returns_0(self, service):
        finding = _make_finding(cve_id=None)
        assert await service._compute_epss_score(finding) == 0.0

    async def test_epss_term_uses_manager_api(self, service, monkeypatch):
        epss_data = EPSSData(
            cve_id="CVE-2024-0001",
            epss_score=0.7,
            percentile=0.9,
            date=datetime(2026, 1, 1),
        )
        mock_vm = MagicMock()
        mock_vm.get_epss_score = AsyncMock(return_value=epss_data)
        monkeypatch.setattr(
            ServiceRegistry,
            "get_vulnerability_manager",
            classmethod(lambda cls: mock_vm),
        )

        finding = _make_finding(cve_id="CVE-2024-0001")
        score, breakdown = await service._compute_composite_score(
            finding, BusinessContext()
        )
        assert breakdown.epss == 70.0
        mock_vm.get_epss_score.assert_awaited_once_with("CVE-2024-0001")

    async def test_epss_failure_scores_zero(self, service, monkeypatch):
        mock_vm = MagicMock()
        mock_vm.get_epss_score = AsyncMock(side_effect=RuntimeError("EPSS API down"))
        monkeypatch.setattr(
            ServiceRegistry,
            "get_vulnerability_manager",
            classmethod(lambda cls: mock_vm),
        )

        finding = _make_finding(cve_id="CVE-2024-0001")
        score, breakdown = await service._compute_composite_score(
            finding, BusinessContext()
        )
        assert breakdown.epss == 0.0
        mock_vm.get_epss_score.assert_awaited_once_with("CVE-2024-0001")


class TestLabelIntegration:
    @pytest.mark.asyncio
    async def test_false_positive_label_excludes_from_ranking(self, service):
        findings = [
            _make_finding("f-1", "critical", "Real bug", "a.py", 9.0, 8.0),
            _make_finding(
                "f-2", "high", "Noise", "b.py", 7.0, 5.0, triage_label="false_positive"
            ),
            _make_finding(
                "f-3", "medium", "Ignored", "c.py", 5.0, 3.0, triage_label="dismissed"
            ),
        ]
        mock_report = _make_report(findings)

        with (
            patch.object(service, "_load_scan_report", AsyncMock(return_value=mock_report)),
            patch.object(service, "_call_ai", AsyncMock(return_value=None)),
            patch.object(service, "_cache_result", AsyncMock()),
        ):
            result = await service.triage_scan("scan-001")

        assert result is not None
        assert result.total_findings == 3
        assert len(result.ranked_findings) == 1
        assert result.ranked_findings[0].finding_id == "f-1"
        assert result.excluded_by_label == 2

    async def test_accepted_label_halves_fp_multiplier(self, service):
        plain = _make_finding(
            severity="high", cvss_base=7.0, exploitability=6.0, false_positive=0.8
        )
        accepted = _make_finding(
            severity="high",
            cvss_base=7.0,
            exploitability=6.0,
            false_positive=0.8,
            triage_label="accepted",
        )
        context = BusinessContext(asset_criticality="medium")

        score_plain, bd_plain = await service._compute_composite_score(plain, context)
        score_accepted, bd_accepted = await service._compute_composite_score(
            accepted, context
        )

        assert bd_plain.false_positive_adjustment == 0.8
        assert bd_accepted.false_positive_adjustment == 0.4
        assert score_accepted > score_plain

    @pytest.mark.asyncio
    async def test_from_cache_applies_same_exclusion(self, service):
        findings = [
            _make_finding("f-1", "critical", "Real bug", "a.py", 9.0, 8.0),
            _make_finding(
                "f-2", "high", "Noise", "b.py", 7.0, 5.0, triage_label="false_positive"
            ),
        ]
        context = BusinessContext()
        cached = {
            "context_hash": _context_hash(context),
            "summaries": {"f-1": "cached summary"},
            "executive_summary": "cached exec",
            "generated_at": "2026-01-01T00:00:00+00:00",
        }
        mock_report = _make_report(findings, metadata={"triage": cached})

        with patch.object(
            service, "_load_scan_report", AsyncMock(return_value=mock_report)
        ):
            result = await service.triage_scan("scan-001")

        assert result is not None
        assert result.total_findings == 2
        assert len(result.ranked_findings) == 1
        assert result.ranked_findings[0].finding_id == "f-1"
        assert result.ranked_findings[0].ai_triage_summary == "cached summary"
        assert result.excluded_by_label == 1
        assert result.executive_summary == "cached exec"

    @pytest.mark.asyncio
    async def test_ranked_finding_carries_label(self, service):
        findings = [
            _make_finding(
                "f-1", "critical", "Real bug", "a.py", 9.0, 8.0, triage_label="accepted"
            ),
            _make_finding("f-2", "low", "Debug log", "b.py", 2.0, 1.0),
        ]
        mock_report = _make_report(findings)

        with (
            patch.object(service, "_load_scan_report", AsyncMock(return_value=mock_report)),
            patch.object(service, "_call_ai", AsyncMock(return_value=None)),
            patch.object(service, "_cache_result", AsyncMock()),
        ):
            result = await service.triage_scan("scan-001")

        labels = {rf.finding_id: rf.triage_label for rf in result.ranked_findings}
        assert labels["f-1"] == "accepted"
        assert labels["f-2"] is None


class TestCacheResult:
    async def test_cache_uses_targeted_metadata_update(self, service):
        report = _make_report([])
        report.id = "scan-oid"
        result = MagicMock()
        result.ranked_findings = [
            MagicMock(finding_id="f-1", ai_triage_summary="summary one")
        ]
        result.executive_summary = "exec"
        result.generated_at = "2026-01-01T00:00:00+00:00"
        collection = MagicMock()
        collection.update_one = AsyncMock()

        with patch.object(ScanReport, "get_motor_collection", return_value=collection):
            await service._cache_result(report, result, "ctx-hash")

        filter_doc, update_doc = collection.update_one.await_args.args
        assert filter_doc == {"_id": "scan-oid"}
        assert update_doc == {
            "$set": {
                "metadata.triage": {
                    "context_hash": "ctx-hash",
                    "summaries": {"f-1": "summary one"},
                    "executive_summary": "exec",
                    "generated_at": "2026-01-01T00:00:00+00:00",
                }
            }
        }

    async def test_cache_failure_is_swallowed(self, service):
        report = _make_report([])
        result = MagicMock()
        result.ranked_findings = []
        collection = MagicMock()
        collection.update_one = AsyncMock(side_effect=RuntimeError("db down"))

        with patch.object(ScanReport, "get_motor_collection", return_value=collection):
            await service._cache_result(report, result, "ctx-hash")
