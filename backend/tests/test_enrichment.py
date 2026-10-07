"""Severity-stratified top-N remediation enrichment."""
from unittest.mock import AsyncMock, MagicMock, patch

import services.ai.enrichment as enrichment_mod
from services.ai.enrichment import enrich_detailed_findings, select_findings_for_enrichment


def _finding(sev, i):
    return {"id": f"f-{i}", "title": f"t{i}", "description": "d", "severity": sev}


def test_select_orders_by_severity_and_caps_at_top_n():
    findings = (
        [_finding("info", i) for i in range(4)]
        + [_finding("low", 10 + i) for i in range(1)]
        + [_finding("medium", 20 + i) for i in range(3)]
        + [_finding("high", 30 + i) for i in range(2)]
        + [_finding("critical", 40 + i) for i in range(2)]
    )  # 12 total
    selected = select_findings_for_enrichment(findings, top_n=10)
    assert len(selected) == 10
    severities = [f["severity"] for f in selected]
    # all critical + high first, then medium, low, info last
    assert severities[:4] == ["critical", "critical", "high", "high"]
    assert severities[4:7] == ["medium", "medium", "medium"]
    assert severities[7:] == ["low", "info", "info"]


def test_select_zero_top_n_returns_empty():
    assert select_findings_for_enrichment([_finding("critical", 1)], top_n=0) == []


def test_select_empty_findings_returns_empty():
    assert select_findings_for_enrichment([], top_n=10) == []


async def test_enrich_runs_processor_on_selected_subset_only():
    findings = [_finding("critical", 1)] + [_finding("low", i) for i in range(2, 15)]
    fake_processor = MagicMock()
    fake_processor.enrich_findings_with_remediation = AsyncMock(return_value=None)

    with patch.object(enrichment_mod, "get_ai_processor", return_value=fake_processor):
        ran = await enrich_detailed_findings(findings, top_n=3, batch_size=2)

    assert ran is True
    passed = fake_processor.enrich_findings_with_remediation.call_args.args[0]
    assert len(passed) == 3
    assert passed[0]["severity"] == "critical"
    kwargs = fake_processor.enrich_findings_with_remediation.call_args.kwargs
    assert kwargs["batch_size"] == 2


async def test_enrich_processor_unavailable_returns_false_and_leaves_findings():
    from services.ai.ai_processor import AIProcessorError

    findings = [_finding("critical", 1)]
    with patch.object(
        enrichment_mod, "get_ai_processor", side_effect=AIProcessorError("no provider")
    ):
        assert await enrich_detailed_findings(findings) is False
    assert findings == [_finding("critical", 1)]


async def test_enrich_processor_crash_returns_false():
    findings = [_finding("critical", 1)]
    fake_processor = MagicMock()
    fake_processor.enrich_findings_with_remediation = AsyncMock(side_effect=RuntimeError("boom"))
    with patch.object(enrichment_mod, "get_ai_processor", return_value=fake_processor):
        assert await enrich_detailed_findings(findings) is False


async def test_enrich_no_findings_skips_processor():
    with patch.object(enrichment_mod, "get_ai_processor") as m:
        assert await enrich_detailed_findings([]) is False
    m.assert_not_called()


async def test_enrich_never_raises_on_bad_findings():
    with patch.object(enrichment_mod, "get_ai_processor") as m:
        assert await enrich_detailed_findings([object()]) is False
    m.assert_not_called()
