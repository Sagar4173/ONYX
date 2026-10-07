"""Unified AI processing service.

Deterministic fields (risk/security scores, threat categories, fix time,
roadmap) are computed in code. The narrative fields come from a single
JSON-structured LLM call through the gateway - one call per scan instead
of the old 7-8 prompt fan-out.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.report import AIAnalysis, ScanResult
from services.ai.gateway import (
    GatewayError,
    LLMGateway,
    complete_structured,
    get_gateway,
)
from services.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    REMEDIATION_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_remediation_prompt,
)
from services.ai.schemas import AnalysisNarrative, RemediationAdvice

logger = logging.getLogger(__name__)


class AIProcessorError(Exception):
    """Custom exception for AI processing errors"""
    pass


class VulnerabilityAIProcessor:
    """AI processor for vulnerability analysis and recommendations"""

    def __init__(self, gateway: Optional[LLMGateway] = None):
        self._gateway = gateway

    @property
    def gateway(self) -> LLMGateway:
        return self._gateway if self._gateway is not None else get_gateway()

    async def analyze_scan_results(
        self,
        scan_results: List[ScanResult],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> AIAnalysis:
        """Analyze vulnerability scan results: deterministic math + 1 structured LLM call."""
        try:
            logger.info("Starting AI analysis of vulnerability findings")
            findings_data = self._prepare_findings_data(scan_results)
            if not findings_data["total_findings"]:
                return self._create_clean_analysis()

            # Deterministic fields - never re-asked to a model.
            risk_score, risk_level = self._calculate_risk_score(findings_data)
            security_score = self._calculate_security_score(findings_data)
            threat_categories = self._categorize_threats(findings_data)
            estimated_fix_time = self._estimate_fix_time(findings_data)
            roadmap = self._generate_remediation_roadmap(findings_data)

            model_used = "unavailable"
            raw_response = None
            narrative: Optional[AnalysisNarrative] = None
            try:
                narrative, result = await complete_structured(
                    self.gateway,
                    system=ANALYSIS_SYSTEM_PROMPT,
                    user=build_analysis_prompt(findings_data, project_context),
                    purpose="analysis",
                    schema=AnalysisNarrative,
                    temperature=0.3,
                )
                model_used = f"{result.provider}/{result.model}"
                raw_response = result.text
            except GatewayError as e:
                logger.warning("AI narrative unavailable, using deterministic fallback: %s", e)

            if narrative is None:
                narrative = self._fallback_narrative(findings_data)

            ai_analysis = AIAnalysis(
                model_used=model_used,
                generated_at=datetime.now(timezone.utc),
                executive_summary=narrative.executive_summary,
                risk_assessment=narrative.risk_assessment,
                risk_score=risk_score,
                risk_level=risk_level,
                priority_findings=narrative.priority_findings,
                recommendations=narrative.recommendations,
                secure_code_examples=narrative.secure_code_examples,
                compliance_impact=narrative.compliance_impact,
                estimated_fix_time=estimated_fix_time,
                attack_vectors=narrative.attack_vectors,
                threat_categories=threat_categories,
                remediation_roadmap=roadmap,
                security_score=security_score,
                raw_response=raw_response,
            )
            logger.info("AI analysis completed successfully (%s)", model_used)
            return ai_analysis
        except Exception as e:
            logger.error("AI analysis failed: %s", e)
            raise AIProcessorError(f"Failed to analyze vulnerabilities: {e}")

    async def enrich_findings_with_remediation(
        self,
        findings: List[Any],
        batch_size: int = 5,
    ) -> List[Any]:
        """Enrich findings with AI remediation guidance (sequential batches)."""
        try:
            logger.info("Enriching %s findings with AI remediation guidance", len(findings))
            applied = 0
            for i in range(0, len(findings), batch_size):
                applied += await self._enrich_batch_with_remediation(
                    findings[i : i + batch_size]
                )
            logger.info(
                "Remediation enrichment applied guidance to %s/%s findings",
                applied,
                len(findings),
            )
            return findings
        except Exception as e:
            logger.error("Error enriching findings with remediation: %s", e)
            return findings

    async def _enrich_batch_with_remediation(self, findings: List[Any]) -> int:
        applied = 0
        for finding in findings:
            try:
                data = self._finding_as_dict(finding)
                if not data.get("title") and not data.get("description"):
                    continue
                advice, _ = await complete_structured(
                    self.gateway,
                    system=REMEDIATION_SYSTEM_PROMPT,
                    user=build_remediation_prompt(data),
                    purpose="remediation",
                    schema=RemediationAdvice,
                    temperature=0.2,
                    use_cache=True,
                )
                if advice is None:
                    logger.warning(
                        "No parseable remediation for finding %r", data.get("title", "")[:80]
                    )
                    continue
                self._apply_advice(finding, advice)
                applied += 1
            except Exception as e:
                logger.warning("Failed to generate remediation for finding: %s", e)
                continue
        return applied

    # --- finding helpers --------------------------------------------------

    @staticmethod
    def _finding_as_dict(finding: Any) -> Dict[str, Any]:
        if isinstance(finding, dict):
            return finding
        severity = getattr(finding, "severity", "") or ""
        if hasattr(severity, "value"):
            severity = severity.value
        return {
            "title": getattr(finding, "title", "") or "",
            "description": getattr(finding, "description", "") or "",
            "severity": severity,
            "file_path": getattr(finding, "file_path", "") or "",
            "code_snippet": getattr(finding, "code_snippet", "") or "",
            "cwe_id": getattr(finding, "cwe_id", "") or "",
            "cve_id": getattr(finding, "cve_id", "") or "",
        }

    @staticmethod
    def _apply_advice(finding: Any, advice: RemediationAdvice) -> None:
        remediation = advice.remediation or None
        fix_effort = advice.fix_effort if advice.fix_effort in ("low", "medium", "high") else "medium"
        secure_code = advice.secure_code or None
        if isinstance(finding, dict):
            finding["remediation"] = remediation
            finding["fix_effort"] = fix_effort
            finding["remediation_code"] = secure_code
            return
        if hasattr(finding, "remediation"):
            finding.remediation = remediation
            finding.fix_effort = fix_effort
            finding.remediation_code = secure_code

    # --- deterministic analysis ------------------------------------------

    @staticmethod
    def _fallback_narrative(findings_data: Dict[str, Any]) -> AnalysisNarrative:
        """Degraded narrative when the LLM was unreachable or unparseable."""
        counts = findings_data["severity_counts"]
        total = findings_data["total_findings"]
        crit, high = counts.get("critical", 0), counts.get("high", 0)
        priority = [
            f.get("title", "")
            for f in findings_data.get("findings", [])
            if (f.get("severity") or "").lower() in ("critical", "high")
        ][:5]
        return AnalysisNarrative(
            executive_summary=(
                f"Automated scan identified {total} finding(s) "
                f"({crit} critical, {high} high). AI narrative generation was unavailable; "
                "the deterministic risk metrics below are computed directly from scanner results."
            ),
            risk_assessment=(
                f"{crit + high} critical/high finding(s) require prioritized remediation. "
                "Follow the remediation roadmap for a phased fix plan."
            ),
            priority_findings=priority,
            recommendations=[
                "Remediate critical and high-severity findings first",
                "Add automated security tests to the CI/CD pipeline",
                "Keep dependencies updated to patched versions",
            ],
            secure_code_examples={},
            compliance_impact={},
            attack_vectors=[],
        )

    def _prepare_findings_data(self, scan_results: List[ScanResult]) -> Dict[str, Any]:
        """Prepare findings data for AI analysis"""
        all_findings = []
        scanner_summary = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for scan_result in scan_results:
            scanner_summary[scan_result.scanner.value] = {
                "status": scan_result.status.value,
                "findings_count": len(scan_result.findings),
                "duration": scan_result.duration_seconds,
            }

            for finding in scan_result.findings:
                all_findings.append({
                    "scanner": finding.scanner.value,
                    "rule_id": finding.rule_id,
                    "title": finding.title,
                    "description": finding.description,
                    "severity": finding.severity.value,
                    "file_path": finding.file_path,
                    "cwe_id": finding.cwe_id,
                    "cve_id": finding.cve_id,
                    "owasp_category": finding.owasp_category,
                })
                severity_counts[finding.severity.value] += 1

        return {
            "total_findings": len(all_findings),
            # full set: deterministic categorization covers every finding;
            # build_analysis_prompt caps at 50 for the API call
            "findings": all_findings,
            "severity_counts": severity_counts,
            "scanner_summary": scanner_summary,
        }

    def _create_clean_analysis(self) -> AIAnalysis:
        """Create analysis for clean scan (no vulnerabilities)"""
        return AIAnalysis(
            model_used="none/clean-scan",
            generated_at=datetime.now(timezone.utc),
            executive_summary="🎉 Excellent security posture! No security vulnerabilities were detected in this comprehensive scan. The codebase demonstrates strong adherence to security best practices and secure coding standards.",
            risk_assessment="LOW - No immediate security risks identified. The application shows a mature security stance with no critical, high, or medium vulnerabilities detected. Continue following secure coding practices and regular security assessments.",
            risk_score=5,
            risk_level="LOW",
            security_score=98,
            priority_findings=[],
            recommendations=[
                "✅ Maintain current security practices and coding standards",
                "🔄 Continue regular automated security scans in CI/CD pipeline",
                "📦 Keep all dependencies updated to latest secure versions",
                "👥 Implement security-focused peer code reviews",
                "📚 Provide ongoing security training for development team",
            ],
            secure_code_examples={},
            compliance_impact={
                "overall_impact": "Positive",
                "analysis": "Clean scan results strongly support compliance requirements across all major frameworks",
                "frameworks_affected": "SOC 2, ISO 27001, NIST, PCI-DSS, GDPR, HIPAA",
                "required_actions": "No immediate actions required. Continue current security practices.",
            },
            estimated_fix_time="0 hours - No issues to fix",
            attack_vectors=[],
            threat_categories={},
            remediation_roadmap=[],
        )

    def _calculate_risk_score(self, findings_data: Dict[str, Any]) -> tuple:
        """Calculate numerical risk score and level based on findings"""
        severity_counts = findings_data["severity_counts"]

        # Weighted scoring: Critical=40, High=25, Medium=10, Low=3, Info=1
        score = (
            severity_counts["critical"] * 40
            + severity_counts["high"] * 25
            + severity_counts["medium"] * 10
            + severity_counts["low"] * 3
            + severity_counts["info"] * 1
        )
        risk_score = min(100, score)

        if severity_counts["critical"] > 0 or risk_score >= 70:
            risk_level = "CRITICAL"
        elif severity_counts["high"] > 0 or risk_score >= 40:
            risk_level = "HIGH"
        elif severity_counts["medium"] > 0 or risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return risk_score, risk_level

    def _calculate_security_score(self, findings_data: Dict[str, Any]) -> int:
        """Calculate overall security score (inverse of risk)"""
        severity_counts = findings_data["severity_counts"]

        score = 100
        score -= severity_counts["critical"] * 20
        score -= severity_counts["high"] * 12
        score -= severity_counts["medium"] * 5
        score -= severity_counts["low"] * 2
        score -= severity_counts["info"] * 0.5

        return max(0, int(score))

    def _categorize_threats(self, findings_data: Dict[str, Any]) -> Dict[str, int]:
        """Categorize findings into threat categories"""
        categories = {
            "Injection": 0,
            "Authentication": 0,
            "Sensitive Data": 0,
            "Access Control": 0,
            "Security Misconfiguration": 0,
            "Cryptographic Issues": 0,
            "Input Validation": 0,
            "Other": 0,
        }

        for finding in findings_data.get("findings", []):
            title = finding.get("title", "").lower()
            desc = finding.get("description", "").lower()
            if any(k in title + desc for k in ["sql", "injection", "sqli", "command injection", "ldap", "xpath"]):
                categories["Injection"] += 1
            elif any(k in title + desc for k in ["auth", "password", "credential", "session", "token", "login"]):
                categories["Authentication"] += 1
            elif any(k in title + desc for k in ["secret", "key", "api_key", "private", "sensitive", "exposure"]):
                categories["Sensitive Data"] += 1
            elif any(k in title + desc for k in ["access", "permission", "privilege", "authorization", "idor"]):
                categories["Access Control"] += 1
            elif any(k in title + desc for k in ["config", "setting", "debug", "verbose", "default"]):
                categories["Security Misconfiguration"] += 1
            elif any(k in title + desc for k in ["crypto", "encrypt", "hash", "ssl", "tls", "certificate"]):
                categories["Cryptographic Issues"] += 1
            elif any(k in title + desc for k in ["input", "validation", "sanitiz", "xss", "cross-site"]):
                categories["Input Validation"] += 1
            else:
                categories["Other"] += 1

        return {k: v for k, v in categories.items() if v > 0}

    def _estimate_fix_time(self, findings_data: Dict[str, Any]) -> str:
        """Estimate time required to fix identified issues"""
        severity_counts = findings_data["severity_counts"]

        critical_hours = severity_counts["critical"] * 8
        high_hours = severity_counts["high"] * 4
        medium_hours = severity_counts["medium"] * 2
        low_hours = severity_counts["low"] * 1

        total_hours = critical_hours + high_hours + medium_hours + low_hours

        if total_hours == 0:
            return "0 hours - No issues to fix"
        elif total_hours < 8:
            return f"{total_hours} hours"
        elif total_hours < 40:
            days = total_hours / 8
            return f"{days:.1f} days ({total_hours} hours)"
        else:
            weeks = total_hours / 40
            return f"{weeks:.1f} weeks ({total_hours} hours)"

    def _generate_remediation_roadmap(self, findings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Phased remediation roadmap (deterministic, ported from ollama processor)."""
        severity_counts = findings_data["severity_counts"]
        roadmap = []

        if severity_counts.get("critical", 0) > 0:
            roadmap.append({
                "phase": 1,
                "title": "Emergency Response",
                "timeline": "Within 24 hours",
                "priority": "CRITICAL",
                "tasks": [
                    f"Address {severity_counts['critical']} critical vulnerabilities immediately",
                    "Implement emergency patches or workarounds",
                    "Enable enhanced monitoring for exploitation attempts",
                    "Notify security team and stakeholders",
                ],
                "status": "pending",
            })

        if severity_counts.get("high", 0) > 0:
            roadmap.append({
                "phase": 2,
                "title": "High Priority Fixes",
                "timeline": "Within 1 week",
                "priority": "HIGH",
                "tasks": [
                    f"Remediate {severity_counts['high']} high-severity findings",
                    "Update vulnerable dependencies",
                    "Implement security controls and hardening",
                    "Conduct security code review",
                ],
                "status": "pending",
            })

        if severity_counts.get("medium", 0) > 0:
            roadmap.append({
                "phase": 3,
                "title": "Security Hardening",
                "timeline": "Within 2 weeks",
                "priority": "MEDIUM",
                "tasks": [
                    f"Address {severity_counts['medium']} medium-severity issues",
                    "Implement additional security best practices",
                    "Enhance input validation and sanitization",
                    "Review and update security configurations",
                ],
                "status": "pending",
            })

        if severity_counts.get("low", 0) > 0 or severity_counts.get("info", 0) > 0:
            roadmap.append({
                "phase": 4,
                "title": "Security Posture Improvement",
                "timeline": "Within 1 month",
                "priority": "LOW",
                "tasks": [
                    f"Address {severity_counts.get('low', 0)} low-severity findings",
                    "Implement security best practices",
                    "Update documentation and security policies",
                    "Conduct security awareness training",
                ],
                "status": "pending",
            })

        return roadmap


# Global AI processor instance - lazy initialization
_ai_processor = None


def get_ai_processor() -> VulnerabilityAIProcessor:
    """Get or create the global AI processor instance"""
    global _ai_processor
    if _ai_processor is None:
        try:
            from .factory import create_ai_processor

            _ai_processor = create_ai_processor()
            logger.info("AI processor initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize AI processor: {e}")
            raise AIProcessorError(f"AI processor initialization failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing AI processor: {e}")
            raise AIProcessorError(f"AI processor initialization failed: {e}")
    return _ai_processor


# Create function to get the processor when needed
def ai_processor():
    return get_ai_processor()
