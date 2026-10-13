"""Path-based false-positive heuristics (Phase 4 Task 4).

Tests, vendored and generated code produce systematically noisier findings;
`deterministic_fp_score` (used by triage when a finding carries no stored
false_positive_score) must raise FP odds for those paths and cap at 0.95.
"""

from models.report import ScannerType, SeverityLevel, ThreatAnalysis, VulnerabilityFinding
from services.triage.triage_service import deterministic_fp_score


def _finding(
    scanner=ScannerType.BANDIT,
    file_path="src/app.py",
    confidence="high",
    false_positive_likelihood=None,
):
    threat = None
    if false_positive_likelihood is not None:
        threat = ThreatAnalysis(
            exploitability="high",
            impact_assessment="high",
            mitigation_priority="high",
            remediation_effort="medium",
            false_positive_likelihood=false_positive_likelihood,
        )
    return VulnerabilityFinding(
        id="f-1",
        scanner=scanner,
        rule_id="RULE-1",
        title="Test finding",
        description="description",
        severity=SeverityLevel.MEDIUM,
        confidence=confidence,
        file_path=file_path,
        threat_analysis=threat,
    )


def test_test_path_increases_fp_score():
    # bandit baseline 0.25 * confidence high x0.5 = 0.125
    baseline = deterministic_fp_score(_finding(file_path="src/app.py"))
    # tests/ path multiplies by 1.5 -> 0.1875 -> rounds to 0.19
    test_path = deterministic_fp_score(_finding(file_path="tests/test_scanner.py"))
    assert baseline == 0.12
    assert test_path == 0.19
    assert test_path > baseline
    assert test_path < 0.95


def test_vendor_path_increases_fp_score():
    baseline = deterministic_fp_score(_finding(file_path="src/app.py"))
    # vendor/ path multiplies by 1.4 -> 0.175 -> rounds to 0.17
    vendor_path = deterministic_fp_score(_finding(file_path="vendor/lib/helper.py"))
    assert vendor_path == 0.17
    assert vendor_path > baseline
    assert vendor_path < 0.95


def test_min_js_path_increases_fp_score():
    baseline = deterministic_fp_score(_finding(file_path="src/app.js"))
    # .min.js path multiplies by 1.3 -> 0.1625 -> rounds to 0.16
    minified = deterministic_fp_score(_finding(file_path="static/app.min.js"))
    assert minified == 0.16
    assert minified > baseline
    assert minified < 0.95


def test_production_path_unchanged():
    finding = _finding(file_path="src/api/handler.py")
    # Pre-Phase-4 formula: scanner 0.25 * confidence high x0.5
    expected = round(min(0.25 * 0.5, 1.0), 2)
    assert expected == 0.12
    assert deterministic_fp_score(finding) == expected


def test_cap_at_095():
    # lynis 0.3 * low confidence x1.5 * very_high threat x1.5 * test path x1.5
    # = 1.0125 -> capped at 0.95
    capped = deterministic_fp_score(
        _finding(
            scanner=ScannerType.LYNIS,
            file_path="tests/test_audit.py",
            confidence="low",
            false_positive_likelihood="very_high",
        )
    )
    assert capped == 0.95
