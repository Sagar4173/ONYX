"""
Google Gemini AI processing service for analyzing vulnerability findings and generating recommendations
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from config import settings
from models.report import AIAnalysis, ScanResult

logger = logging.getLogger(__name__)


class GeminiAIProcessorError(Exception):
    """Custom exception for Gemini AI processing errors"""
    pass


class GeminiVulnerabilityAIProcessor:
    """Gemini AI processor for vulnerability analysis and recommendations"""
    
    def __init__(self):
        try:
            # Initialize Gemini API client
            self.client = genai.Client(api_key=settings.gemini_api_key)
            
            # Safety settings for security analysis (allow all content)
            self.safety_settings = [
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",
                ),
            ]
            
            self.max_tokens = settings.gemini_max_tokens
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI processor: {e}")
            raise GeminiAIProcessorError(f"Gemini initialization failed: {e}")

    async def _generate(self, prompt: str) -> str:
        response = await self.client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=self.safety_settings,
                max_output_tokens=self.max_tokens,
            ),
        )
        return response.text
    
    async def analyze_scan_results(
        self,
        scan_results: List[ScanResult],
        project_context: Optional[Dict[str, Any]] = None
    ) -> AIAnalysis:
        """
        Analyze vulnerability scan results using Gemini AI
        
        Args:
            scan_results: List of scan results to analyze
            project_context: Additional project context
            
        Returns:
            AI analysis with recommendations
        """
        try:
            logger.info("Starting Gemini AI analysis of vulnerability findings")
            
            # Prepare findings data for AI analysis
            findings_data = self._prepare_findings_data(scan_results)
            
            if not findings_data['total_findings']:
                return self._create_clean_analysis()
            
            # Generate AI analysis using concurrent tasks
            analysis_tasks = [
                self._generate_executive_summary(findings_data, project_context),
                self._generate_risk_assessment(findings_data, project_context),
                self._generate_priority_findings(findings_data),
                self._generate_recommendations(findings_data, project_context),
                self._generate_secure_code_examples(findings_data),
                self._generate_compliance_impact(findings_data),
                self._generate_attack_vectors(findings_data)
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            executive_summary = results[0] if not isinstance(results[0], Exception) else "Analysis failed"
            risk_assessment = results[1] if not isinstance(results[1], Exception) else "Risk assessment unavailable"
            priority_findings = results[2] if not isinstance(results[2], Exception) else []
            recommendations = results[3] if not isinstance(results[3], Exception) else []
            secure_code_examples = results[4] if not isinstance(results[4], Exception) else {}
            compliance_impact = results[5] if not isinstance(results[5], Exception) else {}
            attack_vectors = results[6] if not isinstance(results[6], Exception) else []
            
            # Calculate scores and generate roadmap
            risk_score, risk_level = self._calculate_risk_score(findings_data)
            security_score = self._calculate_security_score(findings_data)
            threat_categories = self._categorize_threats(findings_data)
            remediation_roadmap = self._generate_remediation_roadmap(findings_data)
            estimated_fix_time = self._estimate_fix_time(findings_data)
            
            ai_analysis = AIAnalysis(
                model_used=settings.gemini_model,
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
                remediation_roadmap=remediation_roadmap
            )
            
            logger.info("Gemini AI analysis completed successfully")
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Error in Gemini AI analysis: {e}")
            raise GeminiAIProcessorError(f"Analysis failed: {e}")
    
    async def enrich_findings_with_remediation(
        self,
        findings: List[Any],
        batch_size: int = 5
    ) -> List[Any]:
        """
        Enrich vulnerability findings with AI-generated remediation guidance
        
        Args:
            findings: List of vulnerability findings to enrich
            batch_size: Number of findings to process in each batch
            
        Returns:
            List of enriched findings with remediation
        """
        try:
            logger.info(f"Enriching {len(findings)} findings with AI remediation guidance")
            
            # Process in batches to avoid API rate limits
            for i in range(0, len(findings), batch_size):
                batch = findings[i:i + batch_size]
                await self._enrich_batch_with_remediation(batch)
            
            logger.info("Successfully enriched findings with AI remediation")
            return findings
            
        except Exception as e:
            logger.error(f"Error enriching findings with remediation: {e}")
            return findings  # Return original findings if enrichment fails
    
    async def _enrich_batch_with_remediation(self, findings: List[Any]) -> None:
        """Enrich a batch of findings with remediation guidance"""
        for finding in findings:
            try:
                # Build context for the finding
                title = getattr(finding, 'title', '') or finding.get('title', '')
                description = getattr(finding, 'description', '') or finding.get('description', '')
                severity = getattr(finding, 'severity', '') or finding.get('severity', '')
                file_path = getattr(finding, 'file_path', '') or finding.get('file_path', '')
                code_snippet = getattr(finding, 'code_snippet', '') or finding.get('code_snippet', '')
                cwe_id = getattr(finding, 'cwe_id', '') or finding.get('cwe_id', '')
                
                # Skip if no meaningful context
                if not title and not description:
                    continue
                
                prompt = f"""
You are a senior security engineer. Provide specific remediation guidance for this vulnerability:

**Vulnerability:** {title}
**Severity:** {severity}
**Description:** {description[:500] if description else 'N/A'}
**File:** {file_path}
**CWE ID:** {cwe_id if cwe_id else 'N/A'}
**Code Context:** {code_snippet[:300] if code_snippet else 'N/A'}

Provide a response in exactly this format:

REMEDIATION:
[2-4 sentences explaining exactly how to fix this issue step by step]

FIX_EFFORT: [low/medium/high]

SECURE_CODE:
[If applicable, provide a brief secure code example. If not applicable, write "N/A"]
"""
                
                response = await self._generate(prompt)
                response_text = response.text.strip()
                
                # Parse the response
                remediation = ""
                fix_effort = "medium"
                secure_code = ""
                
                # Extract REMEDIATION section
                if "REMEDIATION:" in response_text:
                    parts = response_text.split("REMEDIATION:")
                    if len(parts) > 1:
                        remediation_part = parts[1]
                        if "FIX_EFFORT:" in remediation_part:
                            remediation = remediation_part.split("FIX_EFFORT:")[0].strip()
                        else:
                            remediation = remediation_part.strip()
                
                # Extract FIX_EFFORT
                if "FIX_EFFORT:" in response_text:
                    effort_part = response_text.split("FIX_EFFORT:")[1]
                    if "SECURE_CODE:" in effort_part:
                        effort_text = effort_part.split("SECURE_CODE:")[0].strip().lower()
                    else:
                        effort_text = effort_part.strip().lower()
                    
                    if "low" in effort_text:
                        fix_effort = "low"
                    elif "high" in effort_text:
                        fix_effort = "high"
                    else:
                        fix_effort = "medium"
                
                # Extract SECURE_CODE section
                if "SECURE_CODE:" in response_text:
                    code_part = response_text.split("SECURE_CODE:")[1].strip()
                    if code_part and code_part.lower() != "n/a":
                        secure_code = code_part
                
                # Set the attributes on the finding
                if hasattr(finding, 'remediation'):
                    finding.remediation = remediation if remediation else None
                    finding.fix_effort = fix_effort
                    finding.remediation_code = secure_code if secure_code else None
                elif isinstance(finding, dict):
                    finding['remediation'] = remediation if remediation else None
                    finding['fix_effort'] = fix_effort
                    finding['remediation_code'] = secure_code if secure_code else None
                    
            except Exception as e:
                logger.warning(f"Failed to generate remediation for finding: {e}")
                continue
    
    def _prepare_findings_data(self, scan_results: List[ScanResult]) -> Dict[str, Any]:
        """Prepare findings data for AI analysis"""
        all_findings = []
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        scanner_summary = {}
        
        for scan_result in scan_results:
            scanner_name = scan_result.scanner.value if hasattr(scan_result.scanner, 'value') else str(scan_result.scanner)
            
            if scan_result.findings:
                all_findings.extend(scan_result.findings)
                scanner_summary[scanner_name] = len(scan_result.findings)
                
                # Count by severity
                for finding in scan_result.findings:
                    severity = finding.severity.lower() if finding.severity else 'info'
                    if severity in severity_counts:
                        severity_counts[severity] += 1
        
        return {
            'findings': all_findings,
            'total_findings': len(all_findings),
            'severity_counts': severity_counts,
            'scanner_summary': scanner_summary,
            'high_severity_count': severity_counts['critical'] + severity_counts['high']
        }
    
    async def _generate_executive_summary(
        self, 
        findings_data: Dict[str, Any], 
        project_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate executive summary using Gemini"""
        try:
            total_findings = findings_data['total_findings']
            severity_counts = findings_data['severity_counts']
            scanner_summary = findings_data['scanner_summary']
            
            prompt = f"""
            As a cybersecurity expert, provide an executive summary for a security scan that found {total_findings} total vulnerabilities.
            
            Severity breakdown:
            - Critical: {severity_counts['critical']}
            - High: {severity_counts['high']}
            - Medium: {severity_counts['medium']}
            - Low: {severity_counts['low']}
            - Info: {severity_counts['info']}
            
            Scanner results: {scanner_summary}
            
            Provide a concise 2-3 sentence executive summary that includes:
            1. Overall security posture assessment
            2. Key risk level determination
            3. Immediate action requirements
            
            Focus on business impact and urgency. Be professional and actionable.
            """
            
            response = await self._generate(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return f"Security scan completed with {findings_data['total_findings']} findings requiring attention."
    
    async def _generate_risk_assessment(
        self, 
        findings_data: Dict[str, Any], 
        project_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate detailed risk assessment using Gemini"""
        try:
            findings = findings_data['findings'][:10]  # Top 10 findings for context
            
            findings_context = ""
            for i, finding in enumerate(findings, 1):
                findings_context += f"{i}. {finding.title} (Severity: {finding.severity}, Scanner: {finding.scanner})\n"
            
            prompt = f"""
            As a senior security analyst, provide a detailed risk assessment for these vulnerability findings:
            
            {findings_context}
            
            Total findings: {findings_data['total_findings']}
            Critical/High severity: {findings_data['high_severity_count']}
            
            Provide a risk assessment that covers:
            1. Exploitability analysis
            2. Potential business impact
            3. Attack surface implications
            4. Compliance considerations
            5. Recommended mitigation timeline
            
            Be specific and actionable. Focus on real-world security implications.
            """
            
            response = await self._generate(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return "Detailed risk assessment unavailable due to processing error."
    
    async def _generate_priority_findings(self, findings_data: Dict[str, Any]) -> List[str]:
        """Generate priority findings list using Gemini"""
        try:
            findings = findings_data['findings']
            
            # Sort by severity and get top findings
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
            sorted_findings = sorted(
                findings, 
                key=lambda x: severity_order.get(x.severity.lower() if x.severity else 'info', 4)
            )
            
            top_findings = sorted_findings[:8]  # Top 8 findings
            
            findings_list = ""
            for i, finding in enumerate(top_findings, 1):
                findings_list += f"{i}. {finding.title} - {finding.severity} ({finding.scanner})\n"
                findings_list += f"   File: {finding.file_path}\n"
                if finding.description:
                    findings_list += f"   Issue: {finding.description[:100]}...\n"
                findings_list += "\n"
            
            prompt = f"""
            As a security expert, analyze these vulnerability findings and create prioritized action items:
            
            {findings_list}
            
            Create a prioritized list of 5-7 specific action items that focus on:
            1. Most critical security risks first
            2. Easiest wins for maximum security improvement
            3. Issues that could lead to compliance violations
            4. Findings that suggest systemic problems
            
            Format as clear, actionable bullet points. Be specific and practical.
            """
            
            response = await self._generate(prompt)
            
            # Parse response into list
            priority_items = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                    # Clean up the line
                    clean_line = line.lstrip('-•*0123456789. ').strip()
                    if clean_line:
                        priority_items.append(clean_line)
            
            return priority_items[:7]  # Limit to 7 items
            
        except Exception as e:
            logger.error(f"Error generating priority findings: {e}")
            return ["Review critical and high severity findings", "Address authentication vulnerabilities", "Fix input validation issues"]
    
    async def _generate_recommendations(
        self, 
        findings_data: Dict[str, Any], 
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate actionable recommendations using Gemini"""
        try:
            severity_counts = findings_data['severity_counts']
            scanner_summary = findings_data['scanner_summary']
            
            prompt = f"""
            As a DevSecOps consultant, provide specific recommendations for a project with these security findings:
            
            Severity breakdown: {severity_counts}
            Scanner results: {scanner_summary}
            
            Provide 6-8 specific, actionable recommendations that include:
            1. Immediate fixes for critical/high issues
            2. Process improvements to prevent future issues
            3. Tool configuration optimizations
            4. Developer training suggestions
            5. CI/CD pipeline security enhancements
            
            Make recommendations specific, measurable, and implementable. Focus on both quick wins and long-term security posture improvement.
            """
            
            response = await self._generate(prompt)
            
            # Parse response into list
            recommendations = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                    # Clean up the line
                    clean_line = line.lstrip('-•*0123456789. ').strip()
                    if clean_line:
                        recommendations.append(clean_line)
            
            return recommendations[:8]  # Limit to 8 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Implement security code review process", "Add automated security testing to CI/CD", "Provide security training for developers"]
    
    async def _generate_secure_code_examples(self, findings_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate secure code examples using Gemini"""
        try:
            findings = findings_data['findings'][:5]  # Top 5 for examples
            
            examples = {}
            for finding in findings:
                if finding.title and finding.description:
                    prompt = f"""
                    For this security vulnerability: "{finding.title}"
                    Description: {finding.description}
                    
                    Provide a brief secure code example or fix in the appropriate language.
                    Keep it concise (2-5 lines) and practical. Include a one-line explanation.
                    """
                    
                    try:
                        response = await self._generate(prompt)
                        examples[finding.title] = response.text.strip()
                    except Exception as e:
                        logger.warning(f"Error generating example for {finding.title}: {e}")
                        continue
            
            return examples
            
        except Exception as e:
            logger.error(f"Error generating secure code examples: {e}")
            return {}
    
    async def _generate_compliance_impact(self, findings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance impact assessment using Gemini"""
        try:
            severity_counts = findings_data['severity_counts']
            high_risk_count = severity_counts['critical'] + severity_counts['high']
            
            prompt = f"""
            As a compliance expert, assess the regulatory impact of these security findings:
            
            Total findings: {findings_data['total_findings']}
            High-risk findings: {high_risk_count}
            Severity distribution: {severity_counts}
            
            Provide compliance impact assessment for:
            1. SOC 2 Type II
            2. ISO 27001
            3. NIST Cybersecurity Framework
            4. GDPR/Privacy regulations
            5. Industry-specific requirements (if applicable)
            
            Format as a structured assessment with specific compliance considerations and required actions.
            """
            
            response = await self._generate(prompt)
            
            return {
                "overall_impact": "Medium to High" if high_risk_count > 0 else "Low to Medium",
                "analysis": response.text.strip(),
                "frameworks_affected": ", ".join(["SOC 2", "ISO 27001", "NIST", "GDPR"]),
                "required_actions": f"Address {high_risk_count} high-risk findings for compliance maintenance"
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance impact: {e}")
            return {
                "overall_impact": "Assessment unavailable",
                "analysis": "Compliance impact analysis could not be completed",
                "frameworks_affected": "",
                "required_actions": "Manual compliance review recommended"
            }
    
    def _estimate_fix_time(self, findings_data: Dict[str, Any]) -> str:
        """Estimate time to fix vulnerabilities"""
        severity_counts = findings_data['severity_counts']
        
        # Time estimates in hours
        time_per_severity = {
            'critical': 8,   # 1 day per critical
            'high': 4,       # Half day per high
            'medium': 2,     # 2 hours per medium
            'low': 1,        # 1 hour per low
            'info': 0.5      # 30 minutes per info
        }
        
        total_hours = sum(
            severity_counts[severity] * time_per_severity[severity]
            for severity in severity_counts
        )
        
        business_days = max(1, int(total_hours / 8))
        priority_hours = int(
            severity_counts['critical'] * time_per_severity['critical'] +
            severity_counts['high'] * time_per_severity['high']
        )
        
        return f"{total_hours:.1f} hours ({business_days} business days, {priority_hours} priority hours)"
    
    def _calculate_risk_score(self, findings_data: Dict[str, Any]) -> tuple:
        """Calculate numerical risk score and level based on findings"""
        severity_counts = findings_data['severity_counts']
        
        score = (
            severity_counts['critical'] * 40 +
            severity_counts['high'] * 25 +
            severity_counts['medium'] * 10 +
            severity_counts['low'] * 3 +
            severity_counts['info'] * 1
        )
        
        risk_score = min(100, score)
        
        if severity_counts['critical'] > 0 or risk_score >= 70:
            risk_level = "CRITICAL"
        elif severity_counts['high'] > 0 or risk_score >= 40:
            risk_level = "HIGH"
        elif severity_counts['medium'] > 0 or risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return risk_score, risk_level
    
    def _calculate_security_score(self, findings_data: Dict[str, Any]) -> int:
        """Calculate overall security score (inverse of risk)"""
        severity_counts = findings_data['severity_counts']
        
        score = 100
        score -= severity_counts['critical'] * 20
        score -= severity_counts['high'] * 12
        score -= severity_counts['medium'] * 5
        score -= severity_counts['low'] * 2
        score -= severity_counts['info'] * 0.5
        
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
            "Other": 0
        }
        
        for finding in findings_data.get('findings', []):
            title = (finding.get('title') or '').lower()
            desc = (finding.get('description') or '').lower()
            
            if any(k in title + desc for k in ['sql', 'injection', 'sqli', 'command injection', 'ldap', 'xpath']):
                categories["Injection"] += 1
            elif any(k in title + desc for k in ['auth', 'password', 'credential', 'session', 'token', 'login']):
                categories["Authentication"] += 1
            elif any(k in title + desc for k in ['secret', 'key', 'api_key', 'private', 'sensitive', 'exposure']):
                categories["Sensitive Data"] += 1
            elif any(k in title + desc for k in ['access', 'permission', 'privilege', 'authorization', 'idor']):
                categories["Access Control"] += 1
            elif any(k in title + desc for k in ['config', 'setting', 'debug', 'verbose', 'default']):
                categories["Security Misconfiguration"] += 1
            elif any(k in title + desc for k in ['crypto', 'encrypt', 'hash', 'ssl', 'tls', 'certificate']):
                categories["Cryptographic Issues"] += 1
            elif any(k in title + desc for k in ['input', 'validation', 'sanitiz', 'xss', 'cross-site']):
                categories["Input Validation"] += 1
            else:
                categories["Other"] += 1
        
        return {k: v for k, v in categories.items() if v > 0}
    
    async def _generate_attack_vectors(self, findings_data: Dict[str, Any]) -> List[str]:
        """Generate potential attack vectors based on findings"""
        if not findings_data['findings']:
            return []
        
        severity_counts = findings_data['severity_counts']
        vectors = []
        
        try:
            prompt = f"""
            As a penetration testing expert, identify 5-7 specific attack vectors based on these vulnerabilities:
            
            Findings: {json.dumps(findings_data['findings'][:10], indent=2)}
            
            Focus on real-world exploitation paths. Format as a brief list.
            """
            
            response = await self._generate(prompt)
            
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                    clean_line = line.lstrip('-•*0123456789. ').strip()
                    if clean_line:
                        vectors.append(clean_line)
            
            return vectors[:7]
        except Exception as e:
            logger.warning(f"Error generating attack vectors: {e}")
            if severity_counts.get('critical', 0) > 0:
                vectors.append("Critical vulnerability exploitation leading to system compromise")
            if severity_counts.get('high', 0) > 0:
                vectors.append("High-severity vulnerability chaining for escalated access")
            return vectors
    
    def _generate_remediation_roadmap(self, findings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate step-by-step remediation roadmap"""
        severity_counts = findings_data['severity_counts']
        roadmap = []
        
        if severity_counts.get('critical', 0) > 0:
            roadmap.append({
                "phase": 1,
                "title": "Emergency Response",
                "timeline": "Within 24 hours",
                "priority": "CRITICAL",
                "tasks": [
                    f"Address {severity_counts['critical']} critical vulnerabilities immediately",
                    "Implement emergency patches or workarounds",
                    "Enable enhanced monitoring for exploitation attempts",
                    "Notify security team and stakeholders"
                ],
                "status": "pending"
            })
        
        if severity_counts.get('high', 0) > 0:
            roadmap.append({
                "phase": 2,
                "title": "High Priority Fixes",
                "timeline": "Within 1 week",
                "priority": "HIGH",
                "tasks": [
                    f"Remediate {severity_counts['high']} high-severity findings",
                    "Update vulnerable dependencies",
                    "Implement security controls and hardening",
                    "Conduct security code review"
                ],
                "status": "pending"
            })
        
        if severity_counts.get('medium', 0) > 0:
            roadmap.append({
                "phase": 3,
                "title": "Security Hardening",
                "timeline": "Within 2 weeks",
                "priority": "MEDIUM",
                "tasks": [
                    f"Address {severity_counts['medium']} medium-severity issues",
                    "Implement additional security best practices",
                    "Enhance input validation and sanitization",
                    "Review and update security configurations"
                ],
                "status": "pending"
            })
        
        if severity_counts.get('low', 0) > 0 or severity_counts.get('info', 0) > 0:
            roadmap.append({
                "phase": 4,
                "title": "Security Posture Improvement",
                "timeline": "Within 1 month",
                "priority": "LOW",
                "tasks": [
                    f"Address {severity_counts.get('low', 0)} low-severity findings",
                    "Implement security best practices",
                    "Update documentation and security policies",
                    "Conduct security awareness training"
                ],
                "status": "pending"
            })
        
        return roadmap
    
    def _create_clean_analysis(self) -> AIAnalysis:
        """Create analysis for clean scans with no findings"""
        return AIAnalysis(
            model_used=settings.gemini_model,
            generated_at=datetime.now(timezone.utc),
            executive_summary="🎉 Excellent security posture! No security vulnerabilities were detected in this comprehensive scan. The codebase demonstrates strong adherence to security best practices.",
            risk_assessment="LOW - No immediate security risks identified. Continue following secure coding practices and regular security assessments.",
            risk_score=5,
            risk_level="LOW",
            security_score=98,
            priority_findings=[],
            recommendations=[
                "✅ Maintain current security practices and coding standards",
                "🔄 Continue regular automated security scans in CI/CD pipeline",
                "📦 Keep all dependencies updated to latest secure versions",
                "👥 Implement security-focused peer code reviews",
                "📚 Provide ongoing security training for development team"
            ],
            secure_code_examples={},
            compliance_impact={
                "overall_impact": "Positive",
                "analysis": "Clean security scan strongly supports compliance requirements across all major frameworks",
                "frameworks_affected": "SOC 2, ISO 27001, NIST, PCI-DSS, GDPR, HIPAA",
                "required_actions": "No immediate actions required. Continue current security practices."
            },
            estimated_fix_time="0 hours - No issues to fix",
            attack_vectors=[],
            threat_categories={},
            remediation_roadmap=[]
        )


# Factory function to create the appropriate AI processor
def create_ai_processor():
    """Create AI processor based on configuration.
    
    Provider priority:
      auto    → ollama → gemini → openai
      ollama  → ollama (no fallback)
      gemini  → gemini → openai
      openai  → openai → gemini
    """
    provider = settings.ai_provider.lower() if settings.ai_provider else "auto"
    
    logger.info(f"Creating AI processor with provider: {provider}")
    
    if provider == "ollama":
        return _create_ollama_or_raise()
    
    if provider == "auto":
        processor = _try_ollama()
        if processor:
            return processor
    
    if provider in ("auto", "gemini"):
        if settings.gemini_api_key:
            logger.info("Using Gemini AI processor")
            return GeminiVulnerabilityAIProcessor()
        if provider == "gemini":
            logger.warning("Gemini API key not configured, falling back to OpenAI")
    
    if provider in ("auto", "gemini", "openai"):
        if settings.openai_api_key:
            from .ai_processor import VulnerabilityAIProcessor
            logger.info("Using OpenAI AI processor")
            return VulnerabilityAIProcessor()
        if provider == "openai":
            logger.warning("OpenAI API key not configured, falling back to Gemini")
            if settings.gemini_api_key:
                logger.info("Using Gemini as fallback AI processor")
                return GeminiVulnerabilityAIProcessor()
    
    raise ValueError(
        "No AI provider available. Configure at least one of:\n"
        "  - AI_PROVIDER=ollama (with AI_LOCAL_BASE_URL pointing to running Ollama)\n"
        "  - OPENAI_API_KEY\n"
        "  - GEMINI_API_KEY"
    )


def _create_ollama_or_raise():
    """Create Ollama processor or raise"""
    from .ollama_ai_processor import OllamaVulnerabilityAIProcessor
    logger.info("Using Ollama local AI processor")
    return OllamaVulnerabilityAIProcessor()


def _try_ollama() -> object | None:
    """Try to create an Ollama processor. Returns None if unavailable."""
    try:
        processor = _create_ollama_or_raise()
        logger.info("Ollama local AI configured - will use for analysis")
        return processor
    except Exception as e:
        logger.warning(f"Ollama not available ({e}), trying next provider")
        return None
