import json
import logging
from datetime import datetime, timezone
from hashlib import md5
from typing import Any, Optional

import httpx

from config import settings
from models.report import ScanReport, VulnerabilityFinding
from models.triage import (
    BusinessContext,
    RankedFinding,
    ScoreBreakdown,
    TriageResult,
)

logger = logging.getLogger(__name__)

PRIORITY_MAP = [
    (80, "IMMEDIATE", "24h"),
    (60, "HIGH", "7d"),
    (40, "MEDIUM", "30d"),
    (20, "LOW", "90d"),
]
PRIORITY_DEFAULT = ("INFORMATIONAL", None)

SEVERITY_SCORES = {
    "critical": 100,
    "high": 75,
    "medium": 50,
    "low": 25,
    "info": 5,
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

CRITICALITY_MAP = {"critical": 80, "high": 60, "medium": 40, "low": 20}

CACHE_KEY = "triage"


def _context_hash(context: BusinessContext) -> str:
    raw = f"{context.asset_criticality}|{context.data_classification}|{context.exposure_level}|{sorted(context.compliance_frameworks)}"
    return md5(raw.encode()).hexdigest()[:12]


def _get_severity_score(finding: VulnerabilityFinding) -> float:
    raw = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
    return SEVERITY_SCORES.get(raw.lower(), 5)


def _get_priority_label(score: float):
    for threshold, label, sla in PRIORITY_MAP:
        if score >= threshold:
            return label, sla
    return PRIORITY_DEFAULT


class TriageService:
    def __init__(self):
        self._ai_client_initialized = False
        self._ai_http_client: Optional[httpx.AsyncClient] = None

    async def _ensure_ai_client(self):
        if not self._ai_client_initialized:
            if settings.openai_api_key and len(settings.openai_api_key) > 10:
                self._ai_http_client = httpx.AsyncClient(
                    base_url="https://api.openai.com/v1",
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
            self._ai_client_initialized = True

    async def _load_scan_report(self, scan_id: str) -> Optional[ScanReport]:
        try:
            return await ScanReport.find_one(ScanReport.scan_id == scan_id)
        except Exception as e:
            logger.error(f"Failed to load scan report {scan_id}: {e}")
            return None

    async def triage_scan(
        self,
        scan_id: str,
        business_context: Optional[BusinessContext] = None,
    ) -> Optional[TriageResult]:
        report = await self._load_scan_report(scan_id)
        if not report:
            return None

        context = business_context or BusinessContext()
        ch = _context_hash(context)

        cached = report.metadata.get(CACHE_KEY, {}) if report.metadata else {}
        if cached.get("context_hash") == ch:
            logger.info(f"Returning cached triage for scan {scan_id}")
            return self._from_cache(report, context, cached)

        findings: list[VulnerabilityFinding] = []
        for scan_result in report.scan_results:
            findings.extend(scan_result.findings)

        if not findings:
            result = TriageResult(
                scan_id=scan_id,
                project_name=report.project_name or "Unknown",
                total_findings=0,
                ranked_findings=[],
                priority_counts={"immediate": 0, "high": 0, "medium": 0, "low": 0, "informational": 0},
                business_context=context,
                generated_at=datetime.now(timezone.utc).isoformat(),
                executive_summary="No findings to triage.",
            )
            return result

        ranked = []
        for finding in findings:
            score, breakdown = self._compute_composite_score(finding, context)
            priority_label, sla = _get_priority_label(score)
            ranked.append(
                RankedFinding(
                    finding_id=finding.id or "",
                    title=finding.title or "Untitled finding",
                    severity=finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
                    file_path=finding.file_path or "",
                    composite_score=round(score, 1),
                    priority=priority_label,
                    score_breakdown=breakdown,
                    sla_deadline=sla,
                )
            )

        ranked.sort(key=lambda rf: (-rf.composite_score, SEVERITY_ORDER.get(rf.severity.lower(), 99)))

        await self._generate_ai_triage_summaries(ranked, report)

        priority_counts = {"immediate": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for rf in ranked:
            key = rf.priority.lower()
            if key in priority_counts:
                priority_counts[key] += 1

        executive = None
        if ranked:
            exec_prompt = self._build_executive_prompt(ranked, report)
            executive = await self._call_ai(exec_prompt)

        result = TriageResult(
            scan_id=scan_id,
            project_name=report.project_name or "Unknown",
            total_findings=len(findings),
            ranked_findings=ranked,
            priority_counts=priority_counts,
            executive_summary=executive,
            business_context=context,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        await self._cache_result(report, result, ch)
        return result

    def _compute_composite_score(
        self,
        finding: VulnerabilityFinding,
        context: BusinessContext,
    ) -> tuple[float, ScoreBreakdown]:
        sev = _get_severity_score(finding)
        cvss = 0.0
        if finding.cvss_score and finding.cvss_score.base_score:
            cvss = finding.cvss_score.base_score * 10
        exploitable = finding.exploitability_score or 0.0

        business_raw = self._compute_business_impact_score(finding, context)
        compliance_raw = 100.0 if self._compute_compliance_risk_score(finding) > 0 else 0.0
        epss_raw = self._compute_epss_score(finding)
        fp_raw = finding.false_positive_score or 0.0

        raw = (
            sev * 0.20
            + cvss * 0.15
            + exploitable * 0.15
            + business_raw * 0.20
            + compliance_raw * 0.10
            + epss_raw * 0.10
        ) * (1.0 - fp_raw * 0.10)

        total = max(0.0, min(100.0, raw))

        breakdown = ScoreBreakdown(
            total=round(total, 1),
            severity=round(sev, 1),
            cvss=round(cvss, 1),
            exploitability=round(exploitable, 1),
            business_impact=round(business_raw, 1),
            compliance_risk=round(compliance_raw, 1),
            epss=round(epss_raw, 1),
            false_positive_adjustment=round(fp_raw, 2),
        )
        return total, breakdown

    def _compute_business_impact_score(
        self,
        finding: VulnerabilityFinding,
        context: BusinessContext,
    ) -> float:
        score = 0.0
        bi = finding.business_impact
        if bi:
            if bi.confidentiality_impact:
                score += 25.0
            if bi.integrity_impact:
                score += 25.0
            if bi.availability_impact:
                score += 25.0
            if bi.business_criticality and str(bi.business_criticality).lower() in ("critical", "high"):
                score += 25.0
        ctx_score = CRITICALITY_MAP.get(context.asset_criticality.lower(), 40)
        return (score + ctx_score) / 2.0

    def _compute_compliance_risk_score(self, finding: VulnerabilityFinding) -> float:
        if finding.compliance_mappings and len(finding.compliance_mappings) > 0:
            return 100.0
        return 0.0

    def _compute_epss_score(self, finding: VulnerabilityFinding) -> float:
        if not finding.cve_id:
            return 0.0
        try:
            from services.service_registry import ServiceRegistry
            vm = ServiceRegistry.get_vulnerability_manager()
            if vm:
                epss = vm.epss_service.get_epss_score(finding.cve_id)
                if epss:
                    return epss.epss_score * 100.0
        except Exception:
            pass
        return 0.0

    async def _generate_ai_triage_summaries(
        self,
        ranked: list[RankedFinding],
        report: ScanReport,
    ):
        top = ranked[:10]
        if not top:
            return
        lines = []
        for i, rf in enumerate(top, 1):
            lines.append(f"{i}. [{rf.severity}] {rf.title} — score {rf.composite_score}")
        prompt = (
            "You are a senior security engineer performing incident triage. "
            "For each finding below, write exactly 2-3 sentences explaining:\n"
            "1) Why this finding matters from a business perspective\n"
            "2) What real-world impact it could have\n"
            "3) The first action to take\n\n"
            f"Project: {report.project_name}\n"
            f"Findings (ranked by priority):\n"
            + "\n".join(lines)
            + "\n\nRespond with one paragraph per finding, numbered to match."
        )
        response = await self._call_ai(prompt)
        if response and top:
            paragraphs = [p.strip() for p in response.split("\n") if p.strip()]
            for i, rf in enumerate(top):
                if i < len(paragraphs):
                    rf.ai_triage_summary = paragraphs[i]
                else:
                    rf.ai_triage_summary = response[:500]

    def _build_executive_prompt(
        self,
        ranked: list[RankedFinding],
        report: ScanReport,
    ) -> str:
        counts = {"immediate": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for rf in ranked:
            k = rf.priority.lower()
            if k in counts:
                counts[k] += 1
        summary = ", ".join(f"{v} {k}" for k, v in counts.items() if v > 0)
        return (
            "You are a security lead writing an executive triage summary. "
            "Write 3-4 sentences covering:\n"
            "1) Overall security posture based on triage\n"
            "2) The most critical risk to address\n"
            "3) Recommended next steps\n\n"
            f"Project: {report.project_name}\n"
            f"Findings: {report.total_findings} total ({summary})"
        )

    async def _call_ai(self, prompt: str) -> Optional[str]:
        await self._ensure_ai_client()
        if not self._ai_http_client:
            return None
        try:
            resp = await self._ai_http_client.post(
                "/chat/completions",
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a senior cybersecurity expert specializing in vulnerability triage and business risk analysis.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": settings.openai_max_tokens,
                    "temperature": 0.3,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            logger.warning(f"AI API returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"AI call failed: {e}")
        return None

    async def _cache_result(
        self,
        report: ScanReport,
        result: TriageResult,
        context_hash: str,
    ):
        try:
            summaries = {}
            for rf in result.ranked_findings:
                if rf.ai_triage_summary:
                    summaries[rf.finding_id] = rf.ai_triage_summary
            cache = {
                "context_hash": context_hash,
                "summaries": summaries,
                "executive_summary": result.executive_summary,
                "generated_at": result.generated_at,
            }
            meta = dict(report.metadata or {})
            meta[CACHE_KEY] = cache
            await ScanReport.find_one(ScanReport.scan_id == report.scan_id).update(
                {"$set": {"metadata": meta}}
            )
        except Exception as e:
            logger.warning(f"Failed to cache triage result: {e}")

    def _from_cache(
        self,
        report: ScanReport,
        context: BusinessContext,
        cached: dict,
    ) -> TriageResult:
        findings: list[VulnerabilityFinding] = []
        for scan_result in report.scan_results:
            findings.extend(scan_result.findings)
        ranked = []
        for finding in findings:
            score, breakdown = self._compute_composite_score(finding, context)
            priority_label, sla = _get_priority_label(score)
            rf = RankedFinding(
                finding_id=finding.id or "",
                title=finding.title or "Untitled finding",
                severity=finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
                file_path=finding.file_path or "",
                composite_score=round(score, 1),
                priority=priority_label,
                score_breakdown=breakdown,
                sla_deadline=sla,
                ai_triage_summary=cached.get("summaries", {}).get(finding.id),
            )
            ranked.append(rf)
        ranked.sort(key=lambda rf: (-rf.composite_score, SEVERITY_ORDER.get(rf.severity.lower(), 99)))
        priority_counts = {"immediate": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for rf in ranked:
            k = rf.priority.lower()
            if k in priority_counts:
                priority_counts[k] += 1
        return TriageResult(
            scan_id=report.scan_id,
            project_name=report.project_name or "Unknown",
            total_findings=len(findings),
            ranked_findings=ranked,
            priority_counts=priority_counts,
            executive_summary=cached.get("executive_summary"),
            business_context=context,
            generated_at=cached.get("generated_at", datetime.now(timezone.utc).isoformat()),
        )


triage_service = TriageService()
