"""
Google Gemini AI processing service for analyzing vulnerability findings and generating recommendations
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from models.report import VulnerabilityFinding, AIAnalysis, ScanResult
from config import settings

logger = logging.getLogger(__name__)


class GeminiAIProcessorError(Exception):
    """Custom exception for Gemini AI processing errors"""
    pass


class GeminiVulnerabilityAIProcessor:
    """Gemini AI processor for vulnerability analysis and recommendations"""
    
    def __init__(self):
        try:
            # Configure Gemini API
            genai.configure(api_key=settings.gemini_api_key)
            
            # Initialize the model with safety settings for security analysis
            self.model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            self.max_tokens = settings.gemini_max_tokens
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI processor: {e}")
            raise GeminiAIProcessorError(f"Gemini initialization failed: {e}")
    
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
                self._generate_compliance_impact(findings_data)
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            executive_summary = results[0] if not isinstance(results[0], Exception) else "Analysis failed"
            risk_assessment = results[1] if not isinstance(results[1], Exception) else "Risk assessment unavailable"
            priority_findings = results[2] if not isinstance(results[2], Exception) else []
            recommendations = results[3] if not isinstance(results[3], Exception) else []
            secure_code_examples = results[4] if not isinstance(results[4], Exception) else {}
            compliance_impact = results[5] if not isinstance(results[5], Exception) else {}
            
            # Estimate fix time
            estimated_fix_time = self._estimate_fix_time(findings_data)
            
            ai_analysis = AIAnalysis(
                model_used=settings.gemini_model,
                generated_at=datetime.now(timezone.utc),
                executive_summary=executive_summary,
                risk_assessment=risk_assessment,
                priority_findings=priority_findings,
                recommendations=recommendations,
                secure_code_examples=secure_code_examples,
                compliance_impact=compliance_impact,
                estimated_fix_time=estimated_fix_time
            )
            
            logger.info("Gemini AI analysis completed successfully")
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Error in Gemini AI analysis: {e}")
            raise GeminiAIProcessorError(f"Analysis failed: {e}")
    
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
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
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
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
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
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
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
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
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
                        response = await asyncio.to_thread(self.model.generate_content, prompt)
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
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
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
    
    def _create_clean_analysis(self) -> AIAnalysis:
        """Create analysis for clean scans with no findings"""
        return AIAnalysis(
            model_used=settings.gemini_model,
            generated_at=datetime.now(timezone.utc),
            executive_summary="Security scan completed successfully with no vulnerabilities detected. The codebase demonstrates good security practices.",
            risk_assessment="Low risk profile. No immediate security concerns identified. Continue monitoring and maintain current security practices.",
            priority_findings=[],
            recommendations=[
                "Maintain current security practices",
                "Continue regular security scanning",
                "Keep dependencies updated",
                "Monitor for new security threats"
            ],
            secure_code_examples={},
            compliance_impact={
                "overall_impact": "Positive",
                "analysis": "Clean security scan supports compliance requirements",
                "frameworks_affected": "SOC 2, ISO 27001, NIST",
                "required_actions": "Continue current security practices"
            },
            estimated_fix_time="0 hours (0 business days, 0 priority hours)"
        )


# Factory function to create the appropriate AI processor
def create_ai_processor():
    """Create AI processor based on configuration"""
    if settings.ai_provider.lower() == "gemini":
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured, falling back to OpenAI")
            if settings.openai_api_key:
                from .ai_processor import VulnerabilityAIProcessor
                return VulnerabilityAIProcessor()
            else:
                raise ValueError("No AI provider API key configured")
        return GeminiVulnerabilityAIProcessor()
    else:
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured, trying Gemini")
            if settings.gemini_api_key:
                return GeminiVulnerabilityAIProcessor()
            else:
                raise ValueError("No AI provider API key configured")
        from .ai_processor import VulnerabilityAIProcessor
        return VulnerabilityAIProcessor()
