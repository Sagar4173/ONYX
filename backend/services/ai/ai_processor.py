"""
AI processing service for analyzing vulnerability findings and generating recommendations
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import openai
from openai import AsyncOpenAI

from models.report import VulnerabilityFinding, AIAnalysis, ScanResult
from config import settings

logger = logging.getLogger(__name__)


class AIProcessorError(Exception):
    """Custom exception for AI processing errors"""
    pass


class VulnerabilityAIProcessor:
    """AI processor for vulnerability analysis and recommendations"""
    
    def __init__(self):
        try:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        except TypeError as e:
            # Handle version compatibility issues
            if "proxies" in str(e):
                # Fallback for older OpenAI client versions
                self.client = AsyncOpenAI(
                    api_key=settings.openai_api_key,
                    timeout=30.0
                )
            else:
                raise e
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
    
    async def analyze_scan_results(
        self,
        scan_results: List[ScanResult],
        project_context: Optional[Dict[str, Any]] = None
    ) -> AIAnalysis:
        """
        Analyze vulnerability scan results using AI
        
        Args:
            scan_results: List of scan results to analyze
            project_context: Additional project context
            
        Returns:
            AI analysis with recommendations
        """
        try:
            logger.info("Starting AI analysis of vulnerability findings")
            
            # Prepare findings data for AI analysis
            findings_data = self._prepare_findings_data(scan_results)
            
            if not findings_data['total_findings']:
                return self._create_clean_analysis()
            
            # Generate AI analysis
            analysis_tasks = [
                self._generate_executive_summary(findings_data, project_context),
                self._generate_risk_assessment(findings_data, project_context),
                self._generate_priority_findings(findings_data),
                self._generate_recommendations(findings_data, project_context),
                self._generate_secure_code_examples(findings_data),
                self._generate_compliance_impact(findings_data),
                self._generate_attack_vectors(findings_data),
                self._generate_remediation_roadmap(findings_data)
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
            remediation_roadmap = results[7] if not isinstance(results[7], Exception) else []
            
            # Calculate risk score and level
            risk_score, risk_level = self._calculate_risk_score(findings_data)
            security_score = self._calculate_security_score(findings_data)
            threat_categories = self._categorize_threats(findings_data)
            
            # Estimate fix time
            estimated_fix_time = self._estimate_fix_time(findings_data)
            
            ai_analysis = AIAnalysis(
                model_used=self.model,
                generated_at=datetime.now(timezone.utc),
                executive_summary=executive_summary,
                risk_assessment=risk_assessment,
                risk_score=risk_score,
                risk_level=risk_level,
                priority_findings=priority_findings,
                recommendations=recommendations,
                secure_code_examples=secure_code_examples,
                compliance_impact=compliance_impact,
                estimated_fix_time=estimated_fix_time,
                attack_vectors=attack_vectors,
                threat_categories=threat_categories,
                remediation_roadmap=remediation_roadmap,
                security_score=security_score
            )
            
            logger.info("AI analysis completed successfully")
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise AIProcessorError(f"Failed to analyze vulnerabilities: {e}")
    
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
            return findings
    
    async def _enrich_batch_with_remediation(self, findings: List[Any]) -> None:
        """Enrich a batch of findings with remediation guidance"""
        for finding in findings:
            try:
                title = getattr(finding, 'title', '') or finding.get('title', '')
                description = getattr(finding, 'description', '') or finding.get('description', '')
                severity = getattr(finding, 'severity', '') or finding.get('severity', '')
                file_path = getattr(finding, 'file_path', '') or finding.get('file_path', '')
                code_snippet = getattr(finding, 'code_snippet', '') or finding.get('code_snippet', '')
                cwe_id = getattr(finding, 'cwe_id', '') or finding.get('cwe_id', '')
                
                if not title and not description:
                    continue
                
                prompt = f"""
As a senior security engineer, provide specific remediation guidance for this vulnerability.

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
}}
"""
                
                response = await self._call_openai(prompt)
                
                try:
                    data = json.loads(response.strip())
                    remediation = data.get('remediation', '')
                    fix_effort = data.get('fix_effort', 'medium')
                    secure_code = data.get('secure_code')
                    
                    if hasattr(finding, 'remediation'):
                        finding.remediation = remediation if remediation else None
                        finding.fix_effort = fix_effort if fix_effort in ['low', 'medium', 'high'] else 'medium'
                        finding.remediation_code = secure_code if secure_code else None
                    elif isinstance(finding, dict):
                        finding['remediation'] = remediation if remediation else None
                        finding['fix_effort'] = fix_effort if fix_effort in ['low', 'medium', 'high'] else 'medium'
                        finding['remediation_code'] = secure_code if secure_code else None
                        
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI remediation response as JSON")
                    continue
                    
            except Exception as e:
                logger.warning(f"Failed to generate remediation for finding: {e}")
                continue
    
    def _prepare_findings_data(self, scan_results: List[ScanResult]) -> Dict[str, Any]:
        """Prepare findings data for AI analysis"""
        all_findings = []
        scanner_summary = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for scan_result in scan_results:
            scanner_summary[scan_result.scanner.value] = {
                "status": scan_result.status.value,
                "findings_count": len(scan_result.findings),
                "duration": scan_result.duration_seconds
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
                    "owasp_category": finding.owasp_category
                })
                severity_counts[finding.severity.value] += 1
        
        return {
            "total_findings": len(all_findings),
            "findings": all_findings[:50],  # Limit for API call
            "severity_counts": severity_counts,
            "scanner_summary": scanner_summary
        }
    
    def _create_clean_analysis(self) -> AIAnalysis:
        """Create analysis for clean scan (no vulnerabilities)"""
        return AIAnalysis(
            model_used=self.model,
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
                "📚 Provide ongoing security training for development team"
            ],
            secure_code_examples={},
            compliance_impact={
                "overall_impact": "Positive",
                "analysis": "Clean scan results strongly support compliance requirements across all major frameworks",
                "frameworks_affected": "SOC 2, ISO 27001, NIST, PCI-DSS, GDPR, HIPAA",
                "required_actions": "No immediate actions required. Continue current security practices."
            },
            estimated_fix_time="0 hours - No issues to fix",
            attack_vectors=[],
            threat_categories={},
            remediation_roadmap=[]
        )
    
    def _calculate_risk_score(self, findings_data: Dict[str, Any]) -> tuple:
        """Calculate numerical risk score and level based on findings"""
        severity_counts = findings_data['severity_counts']
        
        # Weighted scoring: Critical=40, High=25, Medium=10, Low=3, Info=1
        score = (
            severity_counts['critical'] * 40 +
            severity_counts['high'] * 25 +
            severity_counts['medium'] * 10 +
            severity_counts['low'] * 3 +
            severity_counts['info'] * 1
        )
        
        # Normalize to 0-100 scale (cap at 100)
        risk_score = min(100, score)
        
        # Determine risk level
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
        
        # Start with 100 and deduct based on findings
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
            title = finding.get('title', '').lower()
            desc = finding.get('description', '').lower()
            owasp = finding.get('owasp_category', '').lower()
            cwe = finding.get('cwe_id', '').lower()
            
            # Categorize based on keywords
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
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v > 0}
    
    async def _generate_attack_vectors(self, findings_data: Dict[str, Any]) -> List[str]:
        """Generate potential attack vectors based on findings"""
        if not findings_data['findings']:
            return []
        
        prompt = f"""
        As a penetration testing expert, analyze these security vulnerabilities and identify specific attack vectors:
        
        Findings: {json.dumps(findings_data['findings'][:15], indent=2)}
        
        List 5-7 specific attack scenarios that could exploit these vulnerabilities.
        Format each as a brief, actionable attack description.
        Focus on real-world exploitation paths.
        
        Return ONLY a JSON array of strings.
        Format: ["Attack vector 1", "Attack vector 2", ...]
        """
        
        try:
            response = await self._call_openai(prompt)
            return json.loads(response.strip())[:7]
        except:
            # Generate based on findings
            vectors = []
            severity_counts = findings_data['severity_counts']
            if severity_counts.get('critical', 0) > 0:
                vectors.append("Critical vulnerability exploitation leading to system compromise")
            if severity_counts.get('high', 0) > 0:
                vectors.append("High-severity vulnerability chaining for escalated access")
            return vectors
    
    async def _generate_remediation_roadmap(self, findings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate step-by-step remediation roadmap"""
        severity_counts = findings_data['severity_counts']
        
        roadmap = []
        
        # Phase 1: Critical (24 hours)
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
        
        # Phase 2: High (1 week)
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
        
        # Phase 3: Medium (2 weeks)
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
        
        # Phase 4: Low & Cleanup (1 month)
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
    
    async def _generate_executive_summary(
        self,
        findings_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate executive summary of security findings"""
        prompt = f"""
        As a senior cybersecurity analyst, provide an executive summary of the security scan results.
        
        Scan Results:
        - Total findings: {findings_data['total_findings']}
        - Critical: {findings_data['severity_counts']['critical']}
        - High: {findings_data['severity_counts']['high']}
        - Medium: {findings_data['severity_counts']['medium']}
        - Low: {findings_data['severity_counts']['low']}
        
        Key Findings:
        {json.dumps(findings_data['findings'][:10], indent=2)}
        
        Provide a concise executive summary (2-3 paragraphs) that:
        1. Summarizes the overall security posture
        2. Highlights the most critical concerns
        3. Provides a business-focused risk perspective
        
        Keep it professional and actionable for technical leadership.
        """
        
        response = await self._call_openai(prompt)
        return response.strip()
    
    async def _generate_risk_assessment(
        self,
        findings_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate detailed risk assessment"""
        prompt = f"""
        As a cybersecurity risk analyst, assess the security risk based on these vulnerability findings:
        
        Findings Summary:
        {json.dumps(findings_data['severity_counts'], indent=2)}
        
        Top Vulnerabilities:
        {json.dumps(findings_data['findings'][:15], indent=2)}
        
        Provide a comprehensive risk assessment including:
        1. Overall risk level (CRITICAL/HIGH/MEDIUM/LOW)
        2. Potential attack vectors
        3. Business impact if exploited
        4. Likelihood of exploitation
        5. Risk mitigation priority
        
        Be specific about the technical and business risks.
        """
        
        response = await self._call_openai(prompt)
        return response.strip()
    
    async def _generate_priority_findings(self, findings_data: Dict[str, Any]) -> List[str]:
        """Generate prioritized list of critical findings"""
        if not findings_data['findings']:
            return []
        
        prompt = f"""
        Analyze these security findings and identify the TOP 5 priority issues that require immediate attention:
        
        {json.dumps(findings_data['findings'], indent=2)}
        
        Return ONLY a JSON array of strings, where each string describes a priority finding.
        Focus on:
        1. Critical and high severity issues
        2. Exploitable vulnerabilities
        3. Issues that could lead to data breaches
        4. Authentication/authorization flaws
        5. Injection vulnerabilities
        
        Format: ["Priority finding 1", "Priority finding 2", ...]
        """
        
        response = await self._call_openai(prompt)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Fallback to manual parsing
            return [line.strip() for line in response.strip().split('\n') if line.strip()][:5]
    
    async def _generate_recommendations(
        self,
        findings_data: Dict[str, Any],
        project_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable security recommendations"""
        prompt = f"""
        Based on these security findings, provide specific, actionable remediation recommendations:
        
        {json.dumps(findings_data, indent=2)}
        
        Return ONLY a JSON array of strings with specific recommendations.
        Each recommendation should be:
        1. Actionable and specific
        2. Prioritized by impact
        3. Include timeline estimates
        4. Mention specific tools/techniques when relevant
        
        Format: ["Recommendation 1", "Recommendation 2", ...]
        Limit to 10 most important recommendations.
        """
        
        response = await self._call_openai(prompt)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Fallback to manual parsing
            return [line.strip() for line in response.strip().split('\n') if line.strip()][:10]
    
    async def _generate_secure_code_examples(self, findings_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate secure code examples for common vulnerabilities"""
        if not findings_data['findings']:
            return {}
        
        # Extract unique vulnerability types
        vulnerability_types = set()
        for finding in findings_data['findings'][:10]:
            if finding.get('cwe_id'):
                vulnerability_types.add(finding['cwe_id'])
            elif finding.get('rule_id'):
                vulnerability_types.add(finding['rule_id'])
        
        if not vulnerability_types:
            return {}
        
        prompt = f"""
        Provide secure code examples for these vulnerability types found in the scan:
        
        Vulnerability Types: {list(vulnerability_types)[:5]}
        
        Sample Findings:
        {json.dumps(findings_data['findings'][:5], indent=2)}
        
        Return ONLY a JSON object where keys are vulnerability types and values are secure code examples.
        Examples should be:
        1. Language-appropriate (detect from file paths)
        2. Show both vulnerable and secure versions
        3. Include brief explanations
        4. Be practical and implementable
        
        Format:
        {{
            "vulnerability_type": "// Vulnerable code\\ncode_example\\n\\n// Secure code\\nsecure_example\\n\\n// Explanation\\nexplanation"
        }}
        """
        
        response = await self._call_openai(prompt)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {}
    
    async def _generate_compliance_impact(self, findings_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate compliance framework impact analysis"""
        prompt = f"""
        Analyze how these security findings impact common compliance frameworks:
        
        {json.dumps(findings_data['severity_counts'], indent=2)}
        
        Sample Findings:
        {json.dumps(findings_data['findings'][:10], indent=2)}
        
        Return ONLY a JSON object analyzing impact on these frameworks:
        - SOC2
        - PCI-DSS
        - GDPR
        - HIPAA
        - SOX
        
        Format:
        {{
            "SOC2": "Impact description",
            "PCI-DSS": "Impact description",
            "GDPR": "Impact description",
            "HIPAA": "Impact description", 
            "SOX": "Impact description"
        }}
        
        Be specific about which findings affect which compliance requirements.
        """
        
        response = await self._call_openai(prompt)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"general": "Compliance impact analysis unavailable"}
    
    def _estimate_fix_time(self, findings_data: Dict[str, Any]) -> str:
        """Estimate time required to fix identified issues"""
        severity_counts = findings_data['severity_counts']
        
        # Basic time estimation algorithm
        critical_hours = severity_counts['critical'] * 8  # 8 hours per critical
        high_hours = severity_counts['high'] * 4         # 4 hours per high
        medium_hours = severity_counts['medium'] * 2     # 2 hours per medium
        low_hours = severity_counts['low'] * 1           # 1 hour per low
        
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
    
    async def _call_openai(self, prompt: str) -> str:
        """Make API call to OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior cybersecurity expert specializing in vulnerability analysis and secure coding practices. Provide detailed, actionable security advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for more consistent responses
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise AIProcessorError(f"AI analysis failed: {e}")


# Global AI processor instance - lazy initialization
_ai_processor = None

def get_ai_processor() -> VulnerabilityAIProcessor:
    """Get or create the global AI processor instance"""
    global _ai_processor
    if _ai_processor is None:
        try:
            # Use factory function from gemini_ai_processor for provider selection
            from .gemini_ai_processor import create_ai_processor
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
