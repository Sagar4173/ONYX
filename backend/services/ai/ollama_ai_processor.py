import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from openai import AsyncOpenAI

from config import settings
from models.report import AIAnalysis, ScanResult

logger = logging.getLogger(__name__)


class OllamaAIProcessorError(Exception):
    """Custom exception for Ollama AI processing errors"""
    pass


class OllamaVulnerabilityAIProcessor:
    """Local AI processor using Ollama for vulnerability analysis"""

    def __init__(self):
        self.base_url = settings.ai_local_base_url.rstrip("/")
        self.model = settings.ai_local_model
        self.timeout = settings.ai_local_timeout
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key="ollama",
            timeout=self.timeout,
            max_retries=0,
        )

    async def _check_health(self) -> bool:
        """Check if Ollama is reachable and has models loaded"""
        try:
            ollama_base = self.base_url.replace("/v1", "").replace("/v1/", "")
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{ollama_base}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    if models:
                        logger.info(f"Ollama available with models: {', '.join(models)}")
                        return True
                    logger.warning("Ollama running but no models pulled")
                    return False
                return False
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def _call_ollama(self, prompt: str, response_format: Optional[dict] = None) -> str:
        try:
            kwargs = dict(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior cybersecurity expert specializing in vulnerability analysis and secure coding practices. Provide detailed, actionable security advice."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=0.3,
            )
            if response_format:
                kwargs["response_format"] = response_format

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise OllamaAIProcessorError(f"Ollama analysis failed: {e}")

    async def analyze_scan_results(
        self,
        scan_results: List[ScanResult],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> AIAnalysis:
        try:
            logger.info("Starting local Ollama AI analysis of vulnerability findings")

            findings_data = self._prepare_findings_data(scan_results)

            if not findings_data["total_findings"]:
                return self._create_clean_analysis()

            analysis_tasks = [
                self._generate_executive_summary(findings_data, project_context),
                self._generate_risk_assessment(findings_data, project_context),
                self._generate_priority_findings(findings_data),
                self._generate_recommendations(findings_data, project_context),
                self._generate_secure_code_examples(findings_data),
                self._generate_compliance_impact(findings_data),
                self._generate_attack_vectors(findings_data),
            ]

            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            executive_summary = results[0] if not isinstance(results[0], Exception) else "Analysis failed"
            risk_assessment = results[1] if not isinstance(results[1], Exception) else "Risk assessment unavailable"
            priority_findings = results[2] if not isinstance(results[2], Exception) else []
            recommendations = results[3] if not isinstance(results[3], Exception) else []
            secure_code_examples = results[4] if not isinstance(results[4], Exception) else {}
            compliance_impact = results[5] if not isinstance(results[5], Exception) else {}
            attack_vectors = results[6] if not isinstance(results[6], Exception) else []

            risk_score, risk_level = self._calculate_risk_score(findings_data)
            security_score = self._calculate_security_score(findings_data)
            threat_categories = self._categorize_threats(findings_data)
            remediation_roadmap = self._generate_remediation_roadmap(findings_data)
            estimated_fix_time = self._estimate_fix_time(findings_data)

            ai_analysis = AIAnalysis(
                model_used=f"ollama/{self.model}",
                generated_at=datetime.now(timezone.utc),
                executive_summary=executive_summary,
                risk_assessment=risk_assessment,
                risk_score=risk_score,
                risk_level=risk_level,
                security_score=security_score,
                priority_findings=priority_findings,
                recommendations=recommendations,
                secure_code_examples=secure_code_examples,
                compliance_impact=compliance_impact,
                estimated_fix_time=estimated_fix_time,
                attack_vectors=attack_vectors,
                threat_categories=threat_categories,
                remediation_roadmap=remediation_roadmap,
            )

            logger.info("Local Ollama AI analysis completed successfully")
            return ai_analysis

        except Exception as e:
            logger.error(f"Error in Ollama AI analysis: {e}")
            raise OllamaAIProcessorError(f"Analysis failed: {e}")

    async def enrich_findings_with_remediation(
        self,
        findings: List[Any],
        batch_size: int = 5,
    ) -> List[Any]:
        try:
            logger.info(f"Enriching {len(findings)} findings with Ollama AI remediation guidance")

            for i in range(0, len(findings), batch_size):
                batch = findings[i : i + batch_size]
                await self._enrich_batch_with_remediation(batch)

            logger.info("Successfully enriched findings with Ollama remediation")
            return findings

        except Exception as e:
            logger.error(f"Error enriching findings with remediation: {e}")
            return findings

    async def _enrich_batch_with_remediation(self, findings: List[Any]) -> None:
        for finding in findings:
            try:
                title = getattr(finding, "title", "") or finding.get("title", "")
                description = getattr(finding, "description", "") or finding.get("description", "")
                severity = getattr(finding, "severity", "") or finding.get("severity", "")
                file_path = getattr(finding, "file_path", "") or finding.get("file_path", "")
                code_snippet = getattr(finding, "code_snippet", "") or finding.get("code_snippet", "")
                cwe_id = getattr(finding, "cwe_id", "") or finding.get("cwe_id", "")

                if not title and not description:
                    continue

                prompt = f"""As a senior security engineer, provide specific remediation guidance for this vulnerability.

Vulnerability: {title}
Severity: {severity}
Description: {description[:500] if description else 'N/A'}
File: {file_path}
CWE ID: {cwe_id if cwe_id else 'N/A'}
Code Context: {code_snippet[:300] if code_snippet else 'N/A'}

Return ONLY a JSON object in this exact format:
{{
    "remediation": "2-4 sentence step-by-step fix instructions",
    "fix_effort": "low|medium|high",
    "secure_code": "Brief secure code example or null if not applicable"
}}"""

                response = await self._call_ollama(prompt, response_format={"type": "json_object"})

                try:
                    data = json.loads(response.strip())
                    remediation = data.get("remediation", "")
                    fix_effort = data.get("fix_effort", "medium")
                    secure_code = data.get("secure_code")

                    if hasattr(finding, "remediation"):
                        finding.remediation = remediation if remediation else None
                        finding.fix_effort = fix_effort if fix_effort in ["low", "medium", "high"] else "medium"
                        finding.remediation_code = secure_code if secure_code else None
                    elif isinstance(finding, dict):
                        finding["remediation"] = remediation if remediation else None
                        finding["fix_effort"] = fix_effort if fix_effort in ["low", "medium", "high"] else "medium"
                        finding["remediation_code"] = secure_code if secure_code else None

                except json.JSONDecodeError:
                    logger.warning("Failed to parse Ollama remediation response as JSON")
                    continue

            except Exception as e:
                logger.warning(f"Failed to generate remediation for finding: {e}")
                continue

    def _prepare_findings_data(self, scan_results: List[ScanResult]) -> Dict[str, Any]:
        all_findings = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        scanner_summary = {}

        for scan_result in scan_results:
            scanner_name = scan_result.scanner.value if hasattr(scan_result.scanner, "value") else str(scan_result.scanner)

            if scan_result.findings:
                all_findings.extend(scan_result.findings)
                scanner_summary[scanner_name] = len(scan_result.findings)

                for finding in scan_result.findings:
                    severity = finding.severity.lower() if finding.severity else "info"
                    if severity in severity_counts:
                        severity_counts[severity] += 1

        return {
            "findings": all_findings,
            "total_findings": len(all_findings),
            "severity_counts": severity_counts,
            "scanner_summary": scanner_summary,
            "high_severity_count": severity_counts["critical"] + severity_counts["high"],
        }

    def _create_clean_analysis(self) -> AIAnalysis:
        return AIAnalysis(
            model_used=f"ollama/{self.model}",
            generated_at=datetime.now(timezone.utc),
            executive_summary="Excellent security posture! No security vulnerabilities were detected in this comprehensive scan. The codebase demonstrates strong adherence to security best practices.",
            risk_assessment="LOW - No immediate security risks identified. Continue following secure coding practices and regular security assessments.",
            risk_score=5,
            risk_level="LOW",
            security_score=98,
            priority_findings=[],
            recommendations=[
                "Maintain current security practices and coding standards",
                "Continue regular automated security scans in CI/CD pipeline",
                "Keep all dependencies updated to latest secure versions",
                "Implement security-focused peer code reviews",
                "Provide ongoing security training for development team",
            ],
            secure_code_examples={},
            compliance_impact={
                "overall_impact": "Positive",
                "analysis": "Clean security scan strongly supports compliance requirements across all major frameworks",
                "frameworks_affected": "SOC 2, ISO 27001, NIST, PCI-DSS, GDPR, HIPAA",
                "required_actions": "No immediate actions required. Continue current security practices.",
            },
            estimated_fix_time="0 hours - No issues to fix",
            attack_vectors=[],
            threat_categories={},
            remediation_roadmap=[],
        )

    def _calculate_risk_score(self, findings_data: Dict[str, Any]) -> tuple:
        severity_counts = findings_data["severity_counts"]
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
        severity_counts = findings_data["severity_counts"]
        score = 100
        score -= severity_counts["critical"] * 20
        score -= severity_counts["high"] * 12
        score -= severity_counts["medium"] * 5
        score -= severity_counts["low"] * 2
        score -= severity_counts["info"] * 0.5
        return max(0, int(score))

    def _categorize_threats(self, findings_data: Dict[str, Any]) -> Dict[str, int]:
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
            title = (finding.get("title") or "").lower()
            desc = (finding.get("description") or "").lower()

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

    async def _generate_executive_summary(
        self,
        findings_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            total = findings_data["total_findings"]
            counts = findings_data["severity_counts"]
            prompt = f"""As a cybersecurity expert, provide an executive summary for a security scan that found {total} total vulnerabilities.

Severity breakdown:
- Critical: {counts['critical']}
- High: {counts['high']}
- Medium: {counts['medium']}
- Low: {counts['low']}
- Info: {counts['info']}

Scanner results: {findings_data['scanner_summary']}

Provide a concise 2-3 sentence executive summary that includes:
1. Overall security posture assessment
2. Key risk level determination
3. Immediate action requirements

Focus on business impact and urgency. Be professional and actionable."""

            response = await self._call_ollama(prompt)
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return f"Security scan completed with {findings_data['total_findings']} findings requiring attention."

    async def _generate_risk_assessment(
        self,
        findings_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            findings = findings_data["findings"][:10]
            findings_context = ""
            for i, finding in enumerate(findings, 1):
                findings_context += f"{i}. {finding.title} (Severity: {finding.severity}, Scanner: {finding.scanner})\n"

            prompt = f"""As a senior security analyst, provide a detailed risk assessment for these vulnerability findings:

{findings_context}

Total findings: {findings_data['total_findings']}
Critical/High severity: {findings_data['high_severity_count']}

Provide a risk assessment that covers:
1. Exploitability analysis
2. Potential business impact
3. Attack surface implications
4. Compliance considerations
5. Recommended mitigation timeline

Be specific and actionable. Focus on real-world security implications."""

            response = await self._call_ollama(prompt)
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return "Detailed risk assessment unavailable due to processing error."

    async def _generate_priority_findings(self, findings_data: Dict[str, Any]) -> List[str]:
        try:
            findings = findings_data["findings"]
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            sorted_findings = sorted(findings, key=lambda x: severity_order.get(x.severity.lower() if x.severity else "info", 4))
            top_findings = sorted_findings[:8]

            findings_list = ""
            for i, finding in enumerate(top_findings, 1):
                findings_list += f"{i}. {finding.title} - {finding.severity} ({finding.scanner})\n"
                findings_list += f"   File: {finding.file_path}\n"
                if finding.description:
                    findings_list += f"   Issue: {finding.description[:100]}...\n"
                findings_list += "\n"

            prompt = f"""As a security expert, analyze these vulnerability findings and create prioritized action items:

{findings_list}

Create a prioritized list of 5-7 specific action items that focus on:
1. Most critical security risks first
2. Easiest wins for maximum security improvement
3. Issues that could lead to compliance violations
4. Findings that suggest systemic problems

Return ONLY a JSON array of strings. Example: ["Action item 1", "Action item 2", ...]"""

            response = await self._call_ollama(prompt, response_format={"type": "json_object"})
            try:
                items = json.loads(response.strip())
                return items[:7] if isinstance(items, list) else items.get("items", items.get("actions", []))[:7]
            except json.JSONDecodeError:
                items = []
                for line in response.strip().split("\n"):
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("•") or line.startswith("*") or (line and line[0].isdigit())):
                        clean = line.lstrip("-•*0123456789. ").strip()
                        if clean:
                            items.append(clean)
                return items[:7]

        except Exception as e:
            logger.error(f"Error generating priority findings: {e}")
            return ["Review critical and high severity findings", "Address authentication vulnerabilities", "Fix input validation issues"]

    async def _generate_recommendations(
        self,
        findings_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        try:
            prompt = f"""As a DevSecOps consultant, provide specific recommendations for a project with these security findings:

Severity breakdown: {findings_data['severity_counts']}
Scanner results: {findings_data['scanner_summary']}

Provide 6-8 specific, actionable recommendations that include:
1. Immediate fixes for critical/high issues
2. Process improvements to prevent future issues
3. Tool configuration optimizations
4. Developer training suggestions
5. CI/CD pipeline security enhancements

Return ONLY a JSON array of strings. Format: ["Recommendation 1", "Recommendation 2", ...]"""

            response = await self._call_ollama(prompt, response_format={"type": "json_object"})
            try:
                items = json.loads(response.strip())
                return items[:8] if isinstance(items, list) else items.get("recommendations", [])[:8]
            except json.JSONDecodeError:
                items = []
                for line in response.strip().split("\n"):
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("•") or line.startswith("*") or (line and line[0].isdigit())):
                        clean = line.lstrip("-•*0123456789. ").strip()
                        if clean:
                            items.append(clean)
                return items[:8]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Implement security code review process", "Add automated security testing to CI/CD", "Provide security training for developers"]

    async def _generate_secure_code_examples(self, findings_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            findings = findings_data["findings"][:5]
            examples = {}
            for finding in findings:
                if finding.title and finding.description:
                    prompt = f"""For this security vulnerability: "{finding.title}"
Description: {finding.description}

Provide a brief secure code example or fix in the appropriate language.
Keep it concise (2-5 lines) and practical. Include a one-line explanation."""

                    try:
                        response = await self._call_ollama(prompt)
                        examples[finding.title] = response.strip()
                    except Exception as e:
                        logger.warning(f"Error generating example for {finding.title}: {e}")
                        continue
            return examples

        except Exception as e:
            logger.error(f"Error generating secure code examples: {e}")
            return {}

    async def _generate_compliance_impact(self, findings_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            high_risk_count = findings_data["high_severity_count"]
            prompt = f"""As a compliance expert, assess the regulatory impact of these security findings:

Total findings: {findings_data['total_findings']}
High-risk findings: {high_risk_count}
Severity distribution: {findings_data['severity_counts']}

Provide compliance impact assessment for:
1. SOC 2 Type II
2. ISO 27001
3. NIST Cybersecurity Framework
4. GDPR/Privacy regulations

Format as a structured assessment with specific compliance considerations and required actions."""

            response = await self._call_ollama(prompt)

            return {
                "overall_impact": "Medium to High" if high_risk_count > 0 else "Low to Medium",
                "analysis": response.strip(),
                "frameworks_affected": ", ".join(["SOC 2", "ISO 27001", "NIST", "GDPR"]),
                "required_actions": f"Address {high_risk_count} high-risk findings for compliance maintenance",
            }

        except Exception as e:
            logger.error(f"Error generating compliance impact: {e}")
            return {
                "overall_impact": "Assessment unavailable",
                "analysis": "Compliance impact analysis could not be completed",
                "frameworks_affected": "",
                "required_actions": "Manual compliance review recommended",
            }

    def _estimate_fix_time(self, findings_data: Dict[str, Any]) -> str:
        severity_counts = findings_data["severity_counts"]
        time_per_severity = {"critical": 8, "high": 4, "medium": 2, "low": 1, "info": 0.5}
        total_hours = sum(severity_counts[s] * time_per_severity[s] for s in severity_counts)
        business_days = max(1, int(total_hours / 8))
        priority_hours = int(
            severity_counts["critical"] * time_per_severity["critical"]
            + severity_counts["high"] * time_per_severity["high"]
        )
        return f"{total_hours:.1f} hours ({business_days} business days, {priority_hours} priority hours)"

    async def _generate_attack_vectors(self, findings_data: Dict[str, Any]) -> List[str]:
        if not findings_data["findings"]:
            return []

        severity_counts = findings_data["severity_counts"]
        vectors = []

        try:
            import json as _json

            findings_slice = []
            for f in findings_data["findings"][:10]:
                findings_slice.append({"title": f.title, "severity": f.severity, "file": f.file_path, "description": f.description[:150] if f.description else ""})

            prompt = f"""As a penetration testing expert, identify 5-7 specific attack vectors based on these vulnerabilities:

{_json.dumps(findings_slice, indent=2)}

Focus on real-world exploitation paths. Provide a JSON array of strings.
Format: ["Attack vector 1", "Attack vector 2", ...]"""

            response = await self._call_ollama(prompt, response_format={"type": "json_object"})
            try:
                parsed = _json.loads(response.strip())
                if isinstance(parsed, list):
                    return parsed[:7]
                if isinstance(parsed, dict):
                    for key in ("attack_vectors", "vectors", "attacks", "items"):
                        if key in parsed and isinstance(parsed[key], list):
                            return parsed[key][:7]
            except _json.JSONDecodeError:
                for line in response.strip().split("\n"):
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("•") or line.startswith("*") or (line and line[0].isdigit())):
                        clean = line.lstrip("-•*0123456789. ").strip()
                        if clean:
                            vectors.append(clean)
                return vectors[:7]

        except Exception as e:
            logger.warning(f"Error generating attack vectors: {e}")

        if severity_counts.get("critical", 0) > 0:
            vectors.append("Critical vulnerability exploitation leading to system compromise")
        if severity_counts.get("high", 0) > 0:
            vectors.append("High-severity vulnerability chaining for escalated access")
        return vectors

    def _generate_remediation_roadmap(self, findings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
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
