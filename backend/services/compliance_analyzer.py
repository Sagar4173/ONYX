"""
Compliance Analysis Service
Handles compliance framework mapping and risk assessment
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from models.report import (
    VulnerabilityFinding, ComplianceMapping, ThreatAnalysis,
    CVSSScore, BusinessImpact, RiskLevel, ComplianceFramework,
    ThreatCategory, SeverityLevel
)

logger = logging.getLogger(__name__)


class ComplianceAnalysisService:
    """Service for compliance mapping and threat analysis"""
    
    def __init__(self):
        self.compliance_data = self._load_compliance_mapping()
        self.cwe_database = self._load_cwe_database()
        
    def _load_compliance_mapping(self) -> Dict[str, Any]:
        """Load compliance mapping configuration"""
        try:
            config_path = Path(__file__).parent.parent / "configs" / "compliance_mapping.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load compliance mapping: {e}")
            return {}
    
    def _load_cwe_database(self) -> Dict[str, Any]:
        """Load CWE database information"""
        # This would typically load from a comprehensive CWE database
        # For now, we'll use the mappings from our compliance file
        return self.compliance_data.get("cwe_mappings", {})
    
    def analyze_finding_compliance(
        self, 
        finding: VulnerabilityFinding,
        target_frameworks: Optional[List[ComplianceFramework]] = None
    ) -> List[ComplianceMapping]:
        """
        Analyze finding against compliance frameworks
        
        Args:
            finding: Vulnerability finding to analyze
            target_frameworks: Specific frameworks to check (if None, check all)
            
        Returns:
            List of compliance mappings
        """
        mappings = []
        
        if target_frameworks is None:
            target_frameworks = list(ComplianceFramework)
        
        for framework in target_frameworks:
            framework_mappings = self._map_to_framework(finding, framework)
            mappings.extend(framework_mappings)
        
        return mappings
    
    def _map_to_framework(
        self, 
        finding: VulnerabilityFinding, 
        framework: ComplianceFramework
    ) -> List[ComplianceMapping]:
        """Map finding to specific compliance framework"""
        mappings = []
        
        framework_key = framework.value.upper()
        framework_data = self.compliance_data.get("compliance_mappings", {}).get(framework_key, {})
        
        if not framework_data:
            return mappings
        
        # Check rule-based mappings
        rule_mappings = self._check_rule_mappings(finding, framework_data)
        mappings.extend(rule_mappings)
        
        # Check CWE-based mappings
        if finding.cwe_id:
            cwe_mappings = self._check_cwe_mappings(finding, framework)
            mappings.extend(cwe_mappings)
        
        return mappings
    
    def _check_rule_mappings(
        self, 
        finding: VulnerabilityFinding, 
        framework_data: Dict[str, Any]
    ) -> List[ComplianceMapping]:
        """Check rule-based compliance mappings"""
        mappings = []
        
        controls = framework_data.get("controls", {})
        
        for control_id, control_data in controls.items():
            scanner_mappings = control_data.get("scanner_mappings", [])
            
            for scanner_mapping in scanner_mappings:
                if (scanner_mapping.get("scanner") == finding.scanner.value and
                    self._rule_matches(finding.rule_id, scanner_mapping.get("rules", []))):
                    
                    mapping = ComplianceMapping(
                        framework=ComplianceFramework(framework_data.get("framework_info", {}).get("name", "").lower().replace(" ", "_")),
                        control_id=control_id,
                        control_title=control_data.get("title", ""),
                        control_description=control_data.get("description", ""),
                        severity=self._map_compliance_severity(finding.severity),
                        requirement_category=control_data.get("category", "")
                    )
                    mappings.append(mapping)
        
        return mappings
    
    def _check_cwe_mappings(
        self, 
        finding: VulnerabilityFinding, 
        framework: ComplianceFramework
    ) -> List[ComplianceMapping]:
        """Check CWE-based compliance mappings"""
        mappings = []
        
        cwe_data = self.cwe_database.get(finding.cwe_id, {})
        if not cwe_data:
            return mappings
        
        compliance_frameworks = cwe_data.get("compliance_frameworks", [])
        
        if framework.value.upper() in compliance_frameworks:
            # Create a generic mapping based on CWE category
            mapping = ComplianceMapping(
                framework=framework,
                control_id=f"CWE-{finding.cwe_id}",
                control_title=cwe_data.get("name", ""),
                control_description=f"CWE-based mapping for {cwe_data.get('name', '')}",
                severity=self._map_compliance_severity(finding.severity),
                requirement_category=cwe_data.get("category", "")
            )
            mappings.append(mapping)
        
        return mappings
    
    def _rule_matches(self, rule_id: str, rule_patterns: List[str]) -> bool:
        """Check if rule ID matches any patterns"""
        for pattern in rule_patterns:
            if pattern in rule_id or rule_id in pattern:
                return True
        return False
    
    def _map_compliance_severity(self, severity: SeverityLevel) -> SeverityLevel:
        """Map technical severity to compliance severity"""
        # For now, use the same severity levels
        return severity
    
    async def generate_compliance_report(
        self,
        findings: List[VulnerabilityFinding],
        framework: ComplianceFramework
    ) -> Dict[str, Any]:
        """Generate compliance report for specific framework"""
        
        # Map findings to compliance controls
        mapped_findings = []
        control_coverage = {}
        
        for finding in findings:
            compliance_mappings = self.analyze_finding_compliance(finding, [framework])
            mapped_findings.extend(compliance_mappings)
        
        # Calculate compliance metrics
        total_findings = len(findings)
        mapped_findings_count = len(mapped_findings)
        
        # Analyze control coverage
        framework_data = self.compliance_data.get("compliance_mappings", {}).get(framework.value.upper(), {})
        all_controls = framework_data.get("controls", {})
        
        for control_id, control_data in all_controls.items():
            control_findings = [m for m in mapped_findings if m.control_id == control_id]
            
            control_coverage[control_id] = {
                "control_name": control_data.get("title", control_id),
                "description": control_data.get("description", ""),
                "findings_count": len(control_findings),
                "compliant": len(control_findings) == 0,
                "risk_level": self._assess_control_risk(control_findings),
                "findings": [self._serialize_compliance_mapping(m) for m in control_findings]
            }
        
        # Calculate compliance score
        compliant_controls = sum(1 for c in control_coverage.values() if c["compliant"])
        total_controls = len(control_coverage)
        compliance_score = (compliant_controls / max(total_controls, 1)) * 100
        
        # Generate risk summary
        risk_summary = {
            "critical": len([f for f in findings if f.severity == SeverityLevel.CRITICAL]),
            "high": len([f for f in findings if f.severity == SeverityLevel.HIGH]),
            "medium": len([f for f in findings if f.severity == SeverityLevel.MEDIUM]),
            "low": len([f for f in findings if f.severity == SeverityLevel.LOW])
        }
        
        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(
            findings, mapped_findings, control_coverage, framework
        )
        
        return {
            "total_findings": total_findings,
            "mapped_findings": mapped_findings_count,
            "compliance_score": round(compliance_score, 2),
            "control_coverage": control_coverage,
            "risk_summary": risk_summary,
            "recommendations": recommendations
        }
    
    async def get_framework_control_status(
        self,
        findings: List[VulnerabilityFinding],
        framework: ComplianceFramework
    ) -> Dict[str, Any]:
        """Get detailed control status for framework"""
        
        control_status = {}
        
        # Map findings to controls
        mapped_findings = []
        for finding in findings:
            compliance_mappings = self.analyze_finding_compliance(finding, [framework])
            mapped_findings.extend(compliance_mappings)
        
        # Get framework controls
        framework_data = self.compliance_data.get("compliance_mappings", {}).get(framework.value.upper(), {})
        all_controls = framework_data.get("controls", {})
        
        for control_id, control_data in all_controls.items():
            control_findings = [m for m in mapped_findings if m.control_id == control_id]
            critical_findings = len([f for f in control_findings if f.severity == SeverityLevel.CRITICAL])
            
            status = "compliant"
            if control_findings:
                if critical_findings > 0:
                    status = "non_compliant"
                else:
                    status = "partial"
            
            control_status[control_id] = {
                "name": control_data.get("title", control_id),
                "description": control_data.get("description", ""),
                "status": status,
                "findings_count": len(control_findings),
                "critical_findings": critical_findings,
                "recommendations": self._generate_control_recommendations(control_data, control_findings)
            }
        
        return control_status
    
    async def generate_risk_summary(self, findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
        """Generate aggregated risk summary"""
        
        risk_summary = {
            "total_findings": len(findings),
            "by_severity": {
                "critical": len([f for f in findings if f.severity == SeverityLevel.CRITICAL]),
                "high": len([f for f in findings if f.severity == SeverityLevel.HIGH]),
                "medium": len([f for f in findings if f.severity == SeverityLevel.MEDIUM]),
                "low": len([f for f in findings if f.severity == SeverityLevel.LOW])
            },
            "by_category": {},
            "top_vulnerabilities": [],
            "compliance_impact": {}
        }
        
        # Category analysis
        categories = {}
        for finding in findings:
            category = finding.category or "uncategorized"
            categories[category] = categories.get(category, 0) + 1
        
        risk_summary["by_category"] = categories
        
        # Top vulnerabilities (by frequency)
        vulnerability_counts = {}
        for finding in findings:
            vuln_type = finding.rule_id or finding.title or "unknown"
            vulnerability_counts[vuln_type] = vulnerability_counts.get(vuln_type, 0) + 1
        
        top_vulns = sorted(vulnerability_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        risk_summary["top_vulnerabilities"] = [
            {"type": vuln_type, "count": count} for vuln_type, count in top_vulns
        ]
        
        # Compliance impact analysis
        frameworks = [ComplianceFramework.OWASP, ComplianceFramework.NIST, ComplianceFramework.ISO27001]
        
        for framework in frameworks:
            mapped_findings = []
            for finding in findings:
                mapped_findings.extend(self.analyze_finding_compliance(finding, [framework]))
            
            risk_summary["compliance_impact"][framework.value] = {
                "affected_controls": len(set(m.control_id for m in mapped_findings)),
                "total_violations": len(mapped_findings)
            }
        
        return risk_summary
    
    async def generate_compliance_trends(
        self,
        scan_reports: List,
        framework: Optional[ComplianceFramework] = None,
        days: int = 90
    ) -> Dict[str, Any]:
        """Generate compliance trends over time"""
        
        trends = {
            "period_days": days,
            "framework": framework.value if framework else "all",
            "compliance_score_trend": [],
            "findings_trend": [],
            "control_status_trend": {}
        }
        
        # Process each scan report
        for report in scan_reports:
            if not hasattr(report, 'scan_results') or not report.scan_results:
                continue
            
            # Extract findings
            all_findings = []
            for scan_result in report.scan_results:
                if hasattr(scan_result, 'findings'):
                    all_findings.extend(scan_result.findings)
            
            if not all_findings:
                continue
            
            # Calculate compliance score for the report date
            if framework:
                compliance_report = await self.generate_compliance_report(all_findings, framework)
                compliance_score = compliance_report["compliance_score"]
            else:
                # Average across all frameworks
                scores = []
                for fw in [ComplianceFramework.OWASP, ComplianceFramework.NIST, ComplianceFramework.ISO27001]:
                    try:
                        comp_report = await self.generate_compliance_report(all_findings, fw)
                        scores.append(comp_report["compliance_score"])
                    except:
                        pass
                compliance_score = sum(scores) / max(len(scores), 1)
            
            trends["compliance_score_trend"].append({
                "date": report.created_at.isoformat() if hasattr(report, 'created_at') else None,
                "score": round(compliance_score, 2),
                "total_findings": len(all_findings)
            })
            
            # Track findings by severity
            severity_counts = {
                "critical": len([f for f in all_findings if f.severity == SeverityLevel.CRITICAL]),
                "high": len([f for f in all_findings if f.severity == SeverityLevel.HIGH]),
                "medium": len([f for f in all_findings if f.severity == SeverityLevel.MEDIUM]),
                "low": len([f for f in all_findings if f.severity == SeverityLevel.LOW])
            }
            
            trends["findings_trend"].append({
                "date": report.created_at.isoformat() if hasattr(report, 'created_at') else None,
                "by_severity": severity_counts,
                "total": sum(severity_counts.values())
            })
        
        return trends
    
    def _assess_control_risk(self, control_findings: List) -> str:
        """Assess risk level for a control based on findings"""
        if not control_findings:
            return "low"
        
        critical_count = len([f for f in control_findings if f.severity == SeverityLevel.CRITICAL])
        high_count = len([f for f in control_findings if f.severity == SeverityLevel.HIGH])
        
        if critical_count > 0:
            return "critical"
        elif high_count > 2:
            return "high"
        elif high_count > 0:
            return "medium"
        else:
            return "low"
    
    def _generate_compliance_recommendations(
        self,
        findings: List[VulnerabilityFinding],
        mapped_findings: List,
        control_coverage: Dict,
        framework: ComplianceFramework
    ) -> List[str]:
        """Generate compliance-specific recommendations"""
        
        recommendations = []
        
        # Priority recommendations based on critical findings
        critical_findings = [f for f in findings if f.severity == SeverityLevel.CRITICAL]
        if critical_findings:
            recommendations.append(
                f"Immediately address {len(critical_findings)} critical security findings to meet compliance requirements."
            )
        
        # Control-specific recommendations
        non_compliant_controls = [
            control_id for control_id, control in control_coverage.items()
            if not control["compliant"]
        ]
        
        if non_compliant_controls:
            recommendations.append(
                f"Review and remediate findings in {len(non_compliant_controls)} non-compliant {framework.value} controls."
            )
        
        # Framework-specific recommendations
        if framework == ComplianceFramework.OWASP:
            recommendations.extend([
                "Implement secure coding practices aligned with OWASP guidelines.",
                "Establish regular security testing in the development lifecycle.",
                "Consider implementing OWASP Application Security Verification Standard (ASVS)."
            ])
        elif framework == ComplianceFramework.NIST:
            recommendations.extend([
                "Implement NIST Cybersecurity Framework controls.",
                "Establish continuous monitoring and assessment processes.",
                "Document security policies and procedures per NIST guidelines."
            ])
        elif framework == ComplianceFramework.ISO27001:
            recommendations.extend([
                "Implement Information Security Management System (ISMS).",
                "Conduct regular risk assessments per ISO 27001 requirements.",
                "Establish security awareness training programs."
            ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_control_recommendations(self, control_data: Dict, control_findings: List) -> List[str]:
        """Generate recommendations for specific control"""
        
        recommendations = []
        
        if not control_findings:
            recommendations.append("Control is compliant. Continue current security practices.")
            return recommendations
        
        # Generic recommendations based on findings
        critical_count = len([f for f in control_findings if f.severity == SeverityLevel.CRITICAL])
        high_count = len([f for f in control_findings if f.severity == SeverityLevel.HIGH])
        
        if critical_count > 0:
            recommendations.append(f"Immediately remediate {critical_count} critical findings.")
        
        if high_count > 0:
            recommendations.append(f"Prioritize fixing {high_count} high-severity findings.")
        
        # Control-specific guidance
        control_title = control_data.get("title", "").lower()
        
        if "authentication" in control_title:
            recommendations.append("Implement multi-factor authentication and strong password policies.")
        elif "encryption" in control_title:
            recommendations.append("Review and strengthen encryption implementation.")
        elif "access" in control_title:
            recommendations.append("Review access controls and implement principle of least privilege.")
        elif "logging" in control_title:
            recommendations.append("Enhance logging and monitoring capabilities.")
        
        return recommendations
    
    def _serialize_compliance_mapping(self, mapping) -> Dict[str, Any]:
        """Serialize compliance mapping for JSON response"""
        return {
            "framework": mapping.framework.value,
            "control_id": mapping.control_id,
            "control_title": mapping.control_title,
            "control_description": mapping.control_description,
            "severity": mapping.severity.value,
            "requirement_category": mapping.requirement_category
        }
    
    async def analyze_framework_compliance(
        self, 
        findings: List[VulnerabilityFinding], 
        framework: str
    ) -> Dict[str, Any]:
        """Analyze compliance for a specific framework"""
        try:
            framework_enum = ComplianceFramework(framework.lower())
            return await self.generate_compliance_report(findings, framework_enum)
        except ValueError:
            raise ValueError(f"Unsupported compliance framework: {framework}")
        """
        Perform comprehensive threat analysis
        
        Args:
            finding: Vulnerability finding to analyze
            repository_context: Additional context about the repository
            
        Returns:
            Comprehensive threat analysis
        """
        
        # Determine threat categories
        threat_categories = self._categorize_threat(finding)
        
        # Get attack patterns
        attack_patterns = self._get_attack_patterns(finding)
        
        # Assess exploitability
        exploitability = self._assess_exploitability(finding, repository_context)
        
        # Assess impact
        impact_assessment = self._assess_impact(finding, repository_context)
        
        # Calculate mitigation priority
        mitigation_priority = self._calculate_mitigation_priority(finding, exploitability, impact_assessment)
        
        # Estimate remediation effort
        remediation_effort = self._estimate_remediation_effort(finding)
        
        # Assess false positive likelihood
        false_positive_likelihood = self._assess_false_positive_likelihood(finding)
        
        return ThreatAnalysis(
            cwe_id=finding.cwe_id,
            cve_id=finding.cve_id,
            threat_categories=threat_categories,
            attack_patterns=attack_patterns,
            exploitability=exploitability,
            impact_assessment=impact_assessment,
            mitigation_priority=mitigation_priority,
            remediation_effort=remediation_effort,
            false_positive_likelihood=false_positive_likelihood
        )
    
    def _categorize_threat(self, finding: VulnerabilityFinding) -> List[ThreatCategory]:
        """Categorize threat based on finding characteristics"""
        categories = []
        
        # CWE-based categorization
        if finding.cwe_id:
            cwe_data = self.cwe_database.get(finding.cwe_id, {})
            cwe_categories = cwe_data.get("threat_categories", [])
            categories.extend([ThreatCategory(cat) for cat in cwe_categories if cat in ThreatCategory.__members__.values()])
        
        # Rule-based categorization
        rule_categories = self._categorize_by_rule(finding.rule_id, finding.scanner.value)
        categories.extend(rule_categories)
        
        # Keyword-based categorization
        keyword_categories = self._categorize_by_keywords(finding.title + " " + finding.description)
        categories.extend(keyword_categories)
        
        # Remove duplicates
        return list(set(categories))
    
    def _categorize_by_rule(self, rule_id: str, scanner: str) -> List[ThreatCategory]:
        """Categorize based on rule ID patterns"""
        categories = []
        
        rule_lower = rule_id.lower()
        
        # Injection patterns
        injection_patterns = ['injection', 'sqli', 'xss', 'command', 'ldap', 'xpath']
        if any(pattern in rule_lower for pattern in injection_patterns):
            categories.append(ThreatCategory.INJECTION)
        
        # Authentication patterns
        auth_patterns = ['auth', 'login', 'password', 'credential', 'session']
        if any(pattern in rule_lower for pattern in auth_patterns):
            categories.append(ThreatCategory.AUTHENTICATION)
        
        # Cryptography patterns
        crypto_patterns = ['crypto', 'encrypt', 'hash', 'ssl', 'tls', 'cipher']
        if any(pattern in rule_lower for pattern in crypto_patterns):
            categories.append(ThreatCategory.CRYPTOGRAPHY)
        
        # Secrets patterns
        secret_patterns = ['secret', 'key', 'token', 'api', 'hardcoded']
        if any(pattern in rule_lower for pattern in secret_patterns):
            categories.append(ThreatCategory.SECRETS)
        
        # Configuration patterns
        config_patterns = ['config', 'debug', 'default', 'misconfigur']
        if any(pattern in rule_lower for pattern in config_patterns):
            categories.append(ThreatCategory.CONFIGURATION)
        
        return categories
    
    def _categorize_by_keywords(self, text: str) -> List[ThreatCategory]:
        """Categorize based on text keywords"""
        categories = []
        text_lower = text.lower()
        
        keyword_mappings = {
            ThreatCategory.INJECTION: ['injection', 'sql', 'command', 'xss', 'script'],
            ThreatCategory.AUTHENTICATION: ['authentication', 'login', 'password', 'credential'],
            ThreatCategory.AUTHORIZATION: ['authorization', 'access', 'privilege', 'permission'],
            ThreatCategory.CRYPTOGRAPHY: ['encryption', 'cryptography', 'ssl', 'tls', 'hash'],
            ThreatCategory.DATA_EXPOSURE: ['exposure', 'leak', 'disclosure', 'sensitive'],
            ThreatCategory.CONFIGURATION: ['configuration', 'misconfiguration', 'debug', 'default'],
            ThreatCategory.DEPENDENCY: ['dependency', 'library', 'package', 'component'],
            ThreatCategory.SECRETS: ['secret', 'key', 'token', 'credential', 'api key']
        }
        
        for category, keywords in keyword_mappings.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def _get_attack_patterns(self, finding: VulnerabilityFinding) -> List[str]:
        """Get CAPEC attack patterns for the finding"""
        # This would typically integrate with CAPEC database
        # For now, provide basic mappings
        
        attack_patterns = []
        
        if finding.cwe_id:
            # Common CWE to CAPEC mappings
            cwe_capec_map = {
                "CWE-79": ["CAPEC-18", "CAPEC-32", "CAPEC-86"],  # XSS
                "CWE-89": ["CAPEC-66", "CAPEC-7", "CAPEC-109"],  # SQL Injection
                "CWE-78": ["CAPEC-88", "CAPEC-43"],             # Command Injection
                "CWE-798": ["CAPEC-70", "CAPEC-554"],           # Hard-coded Credentials
                "CWE-327": ["CAPEC-20", "CAPEC-97"],            # Broken Crypto
                "CWE-22": ["CAPEC-126", "CAPEC-64"]             # Path Traversal
            }
            
            attack_patterns.extend(cwe_capec_map.get(finding.cwe_id, []))
        
        return attack_patterns
    
    def _assess_exploitability(
        self, 
        finding: VulnerabilityFinding, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assess exploitability of the vulnerability"""
        
        # Base exploitability on severity and type
        base_exploitability = {
            SeverityLevel.CRITICAL: "very_high",
            SeverityLevel.HIGH: "high",
            SeverityLevel.MEDIUM: "medium",
            SeverityLevel.LOW: "low",
            SeverityLevel.INFO: "very_low"
        }.get(finding.severity, "medium")
        
        # Adjust based on threat categories
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            high_exploitability_categories = [
                ThreatCategory.INJECTION,
                ThreatCategory.SECRETS,
                ThreatCategory.AUTHENTICATION
            ]
            
            if any(cat in high_exploitability_categories for cat in finding.threat_analysis.threat_categories):
                if base_exploitability in ["low", "medium"]:
                    base_exploitability = "high"
        
        # Consider environment context
        if context:
            is_production = context.get("environment") == "production"
            is_public_facing = context.get("public_facing", False)
            
            if is_production and is_public_facing:
                if base_exploitability in ["low", "medium"]:
                    base_exploitability = "high"
        
        return base_exploitability
    
    def _assess_impact(
        self, 
        finding: VulnerabilityFinding, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assess impact of the vulnerability"""
        
        # Base impact on severity
        base_impact = {
            SeverityLevel.CRITICAL: "very_high",
            SeverityLevel.HIGH: "high",
            SeverityLevel.MEDIUM: "medium",
            SeverityLevel.LOW: "low",
            SeverityLevel.INFO: "very_low"
        }.get(finding.severity, "medium")
        
        # Adjust based on data sensitivity
        if context:
            data_classification = context.get("data_classification", "internal")
            
            if data_classification in ["confidential", "restricted"]:
                if base_impact in ["low", "medium"]:
                    base_impact = "high"
        
        return base_impact
    
    def _calculate_mitigation_priority(
        self, 
        finding: VulnerabilityFinding, 
        exploitability: str, 
        impact: str
    ) -> str:
        """Calculate mitigation priority based on exploitability and impact"""
        
        priority_matrix = {
            ("very_high", "very_high"): "critical",
            ("very_high", "high"): "critical",
            ("high", "very_high"): "critical",
            ("high", "high"): "high",
            ("very_high", "medium"): "high",
            ("medium", "very_high"): "high",
            ("high", "medium"): "high",
            ("medium", "high"): "high",
            ("high", "low"): "medium",
            ("low", "high"): "medium",
            ("medium", "medium"): "medium",
            ("medium", "low"): "low",
            ("low", "medium"): "low",
            ("low", "low"): "low",
            ("very_low", "very_low"): "very_low"
        }
        
        return priority_matrix.get((exploitability, impact), "medium")
    
    def _estimate_remediation_effort(self, finding: VulnerabilityFinding) -> str:
        """Estimate remediation effort"""
        
        # Base effort on finding type and complexity
        effort_map = {
            ThreatCategory.CONFIGURATION: "low",
            ThreatCategory.SECRETS: "low",
            ThreatCategory.DEPENDENCY: "medium",
            ThreatCategory.INJECTION: "medium",
            ThreatCategory.AUTHENTICATION: "high",
            ThreatCategory.CRYPTOGRAPHY: "high",
            ThreatCategory.AUTHORIZATION: "high"
        }
        
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            for category in finding.threat_analysis.threat_categories:
                if category in effort_map:
                    return effort_map[category]
        
        # Default based on severity
        return {
            SeverityLevel.CRITICAL: "high",
            SeverityLevel.HIGH: "medium",
            SeverityLevel.MEDIUM: "medium",
            SeverityLevel.LOW: "low",
            SeverityLevel.INFO: "low"
        }.get(finding.severity, "medium")
    
    def _assess_false_positive_likelihood(self, finding: VulnerabilityFinding) -> str:
        """Assess likelihood of false positive"""
        
        # Scanner-based assessment
        scanner_fp_rates = {
            "semgrep": "low",
            "bandit": "medium",
            "safety": "very_low",
            "trivy": "low",
            "gitleaks": "low",
            "lynis": "medium"
        }
        
        base_fp = scanner_fp_rates.get(finding.scanner.value, "medium")
        
        # Adjust based on confidence if available
        if finding.confidence:
            confidence_lower = finding.confidence.lower()
            if confidence_lower in ["high", "certain"]:
                return "low"
            elif confidence_lower in ["low", "uncertain"]:
                return "high"
        
        return base_fp
    
    def calculate_cvss_score(
        self, 
        finding: VulnerabilityFinding,
        environment_context: Optional[Dict[str, Any]] = None
    ) -> CVSSScore:
        """Calculate CVSS score for the finding"""
        
        # This is a simplified CVSS calculation
        # In production, you'd want a more comprehensive implementation
        
        # Base score calculation
        base_score = self._calculate_base_cvss(finding)
        
        # Environmental adjustments
        environmental_score = None
        if environment_context:
            environmental_score = self._adjust_environmental_cvss(base_score, environment_context)
        
        return CVSSScore(
            version="3.1",
            base_score=base_score,
            environmental_score=environmental_score,
            vector_string=self._generate_cvss_vector(finding),
            attack_vector=self._determine_attack_vector(finding),
            attack_complexity=self._determine_attack_complexity(finding),
            privileges_required=self._determine_privileges_required(finding),
            user_interaction=self._determine_user_interaction(finding),
            scope="unchanged",  # Simplified
            confidentiality_impact=self._determine_cia_impact(finding, "confidentiality"),
            integrity_impact=self._determine_cia_impact(finding, "integrity"),
            availability_impact=self._determine_cia_impact(finding, "availability")
        )
    
    def _calculate_base_cvss(self, finding: VulnerabilityFinding) -> float:
        """Calculate base CVSS score"""
        # Simplified base score calculation
        severity_scores = {
            SeverityLevel.CRITICAL: 9.5,
            SeverityLevel.HIGH: 7.5,
            SeverityLevel.MEDIUM: 5.0,
            SeverityLevel.LOW: 2.5,
            SeverityLevel.INFO: 0.0
        }
        
        return severity_scores.get(finding.severity, 5.0)
    
    def _adjust_environmental_cvss(
        self, 
        base_score: float, 
        context: Dict[str, Any]
    ) -> float:
        """Adjust CVSS score based on environment"""
        adjusted_score = base_score
        
        # Adjust based on environment type
        if context.get("environment") == "production":
            adjusted_score *= 1.2
        elif context.get("environment") == "development":
            adjusted_score *= 0.8
        
        # Adjust based on data sensitivity
        data_classification = context.get("data_classification", "internal")
        if data_classification == "confidential":
            adjusted_score *= 1.3
        elif data_classification == "public":
            adjusted_score *= 0.7
        
        return min(adjusted_score, 10.0)  # Cap at 10.0
    
    def _generate_cvss_vector(self, finding: VulnerabilityFinding) -> str:
        """Generate CVSS vector string"""
        # Simplified vector generation
        return f"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L"
    
    def _determine_attack_vector(self, finding: VulnerabilityFinding) -> str:
        """Determine CVSS attack vector"""
        # Simplified determination
        if finding.scanner.value in ["trivy", "lynis"]:
            return "Local"
        return "Network"
    
    def _determine_attack_complexity(self, finding: VulnerabilityFinding) -> str:
        """Determine CVSS attack complexity"""
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            complex_categories = [ThreatCategory.CRYPTOGRAPHY, ThreatCategory.AUTHORIZATION]
            if any(cat in complex_categories for cat in finding.threat_analysis.threat_categories):
                return "High"
        return "Low"
    
    def _determine_privileges_required(self, finding: VulnerabilityFinding) -> str:
        """Determine CVSS privileges required"""
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            if ThreatCategory.AUTHORIZATION in finding.threat_analysis.threat_categories:
                return "High"
            elif ThreatCategory.AUTHENTICATION in finding.threat_analysis.threat_categories:
                return "Low"
        return "None"
    
    def _determine_user_interaction(self, finding: VulnerabilityFinding) -> str:
        """Determine CVSS user interaction"""
        if finding.cwe_id == "CWE-79":  # XSS typically requires user interaction
            return "Required"
        return "None"
    
    def _determine_cia_impact(self, finding: VulnerabilityFinding, impact_type: str) -> str:
        """Determine CIA impact (Confidentiality, Integrity, Availability)"""
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            high_impact_categories = {
                "confidentiality": [ThreatCategory.DATA_EXPOSURE, ThreatCategory.SECRETS],
                "integrity": [ThreatCategory.INJECTION, ThreatCategory.CRYPTOGRAPHY],
                "availability": [ThreatCategory.INJECTION, ThreatCategory.CONFIGURATION]
            }
            
            if any(cat in high_impact_categories.get(impact_type, []) 
                   for cat in finding.threat_analysis.threat_categories):
                return "High"
        
        return "Low"
    
    def calculate_business_impact(
        self, 
        finding: VulnerabilityFinding,
        business_context: Dict[str, Any]
    ) -> BusinessImpact:
        """Calculate business impact assessment"""
        
        return BusinessImpact(
            confidentiality_impact=self._assess_confidentiality_impact(finding, business_context),
            integrity_impact=self._assess_integrity_impact(finding, business_context),
            availability_impact=self._assess_availability_impact(finding, business_context),
            business_criticality=business_context.get("criticality", "medium"),
            compliance_risk=self._assess_compliance_risk(finding),
            financial_impact=self._assess_financial_impact(finding, business_context)
        )
    
    def _assess_confidentiality_impact(
        self, 
        finding: VulnerabilityFinding, 
        context: Dict[str, Any]
    ) -> str:
        """Assess confidentiality impact"""
        
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            if ThreatCategory.DATA_EXPOSURE in finding.threat_analysis.threat_categories:
                data_classification = context.get("data_classification", "internal")
                return {"confidential": "high", "restricted": "high", "internal": "medium", "public": "low"}.get(
                    data_classification, "medium"
                )
        
        return "low"
    
    def _assess_integrity_impact(
        self, 
        finding: VulnerabilityFinding, 
        context: Dict[str, Any]
    ) -> str:
        """Assess integrity impact"""
        
        if finding.threat_analysis and finding.threat_analysis.threat_categories:
            high_integrity_categories = [ThreatCategory.INJECTION, ThreatCategory.AUTHORIZATION]
            if any(cat in high_integrity_categories for cat in finding.threat_analysis.threat_categories):
                return "high"
        
        return "low"
    
    def _assess_availability_impact(
        self, 
        finding: VulnerabilityFinding, 
        context: Dict[str, Any]
    ) -> str:
        """Assess availability impact"""
        
        service_criticality = context.get("service_criticality", "medium")
        
        if finding.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            return {"critical": "high", "high": "high", "medium": "medium", "low": "low"}.get(
                service_criticality, "medium"
            )
        
        return "low"
    
    def _assess_compliance_risk(self, finding: VulnerabilityFinding) -> str:
        """Assess compliance risk"""
        
        if finding.compliance_mappings:
            # High compliance risk if mapped to critical frameworks
            critical_frameworks = [ComplianceFramework.PCI_DSS, ComplianceFramework.GDPR]
            if any(mapping.framework in critical_frameworks for mapping in finding.compliance_mappings):
                return "high"
            return "medium"
        
        return "low"
    
    def _assess_financial_impact(
        self, 
        finding: VulnerabilityFinding, 
        context: Dict[str, Any]
    ) -> str:
        """Assess financial impact"""
        
        revenue_impact = context.get("revenue_impact", "low")
        compliance_penalties = context.get("compliance_penalties", False)
        
        if compliance_penalties and finding.compliance_mappings:
            return "high"
        
        return {"high": "high", "medium": "medium", "low": "low"}.get(revenue_impact, "low")
    
    def calculate_risk_level(
        self, 
        finding: VulnerabilityFinding,
        business_context: Optional[Dict[str, Any]] = None
    ) -> RiskLevel:
        """Calculate overall business risk level"""
        
        # Factors: Technical severity, exploitability, business impact, compliance risk
        
        # Technical severity weight (30%)
        severity_weight = 0.3
        severity_scores = {
            SeverityLevel.CRITICAL: 5,
            SeverityLevel.HIGH: 4,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFO: 1
        }
        
        technical_score = severity_scores.get(finding.severity, 3) * severity_weight
        
        # Exploitability weight (25%)
        exploitability_weight = 0.25
        exploitability_scores = {
            "very_high": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "very_low": 1
        }
        
        exploitability = "medium"
        if finding.threat_analysis:
            exploitability = finding.threat_analysis.exploitability
        
        exploitability_score = exploitability_scores.get(exploitability, 3) * exploitability_weight
        
        # Business impact weight (25%)
        business_weight = 0.25
        business_score = 3 * business_weight  # Default medium
        
        if business_context and finding.business_impact:
            # Use actual business impact assessment
            impact_scores = {"high": 5, "medium": 3, "low": 1}
            avg_impact = (
                impact_scores.get(finding.business_impact.confidentiality_impact, 3) +
                impact_scores.get(finding.business_impact.integrity_impact, 3) +
                impact_scores.get(finding.business_impact.availability_impact, 3)
            ) / 3
            business_score = avg_impact * business_weight
        
        # Compliance risk weight (20%)
        compliance_weight = 0.2
        compliance_score = 3 * compliance_weight  # Default medium
        
        if finding.compliance_mappings:
            # Higher score if mapped to critical compliance frameworks
            critical_frameworks = [ComplianceFramework.PCI_DSS, ComplianceFramework.GDPR]
            if any(mapping.framework in critical_frameworks for mapping in finding.compliance_mappings):
                compliance_score = 5 * compliance_weight
            else:
                compliance_score = 4 * compliance_weight
        
        # Calculate total risk score
        total_score = technical_score + exploitability_score + business_score + compliance_score
        
        # Map to risk levels
        if total_score >= 4.5:
            return RiskLevel.CRITICAL
        elif total_score >= 3.5:
            return RiskLevel.HIGH
        elif total_score >= 2.5:
            return RiskLevel.MEDIUM
        elif total_score >= 1.5:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFORMATIONAL
    
    async def generate_compliance_report(
        self, 
        findings: List[VulnerabilityFinding], 
        framework: ComplianceFramework
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report for specific framework
        """
        try:
            total_findings = len(findings)
            mapped_findings = 0
            framework_controls = self.compliance_mapping.get(framework.value, {}).get('controls', {})
            
            # Count findings mapped to framework controls
            control_findings = {}
            risk_summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            
            for finding in findings:
                if finding.compliance_mappings:
                    for mapping in finding.compliance_mappings:
                        if mapping.framework == framework:
                            mapped_findings += 1
                            for control_id in mapping.control_ids:
                                if control_id not in control_findings:
                                    control_findings[control_id] = []
                                control_findings[control_id].append(finding)
                
                # Count risk levels
                if finding.risk_level:
                    risk_summary[finding.risk_level.value] += 1
            
            # Calculate compliance score (percentage of controls without critical/high findings)
            total_controls = len(framework_controls)
            non_compliant_controls = 0
            
            for control_id, control_findings_list in control_findings.items():
                has_critical_high = any(
                    f.severity.value in ['critical', 'high'] 
                    for f in control_findings_list
                )
                if has_critical_high:
                    non_compliant_controls += 1
            
            compliance_score = (
                (total_controls - non_compliant_controls) / total_controls * 100
                if total_controls > 0 else 100
            )
            
            # Generate control coverage
            control_coverage = {}
            for control_id, control_info in framework_controls.items():
                findings_for_control = control_findings.get(control_id, [])
                control_coverage[control_id] = {
                    'name': control_info.get('name', control_id),
                    'findings_count': len(findings_for_control),
                    'critical_findings': len([
                        f for f in findings_for_control 
                        if f.severity.value == 'critical'
                    ]),
                    'status': self._determine_control_status(findings_for_control)
                }
            
            # Generate recommendations
            recommendations = self._generate_framework_recommendations(
                framework, control_findings, framework_controls
            )
            
            return {
                'total_findings': total_findings,
                'mapped_findings': mapped_findings,
                'compliance_score': round(compliance_score, 2),
                'control_coverage': control_coverage,
                'risk_summary': risk_summary,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    async def get_framework_control_status(
        self,
        findings: List[VulnerabilityFinding],
        framework: ComplianceFramework
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed status for each control in a framework
        """
        try:
            framework_controls = self.compliance_mapping.get(framework.value, {}).get('controls', {})
            control_status = {}
            
            # Map findings to controls
            control_findings = {}
            for finding in findings:
                if finding.compliance_mappings:
                    for mapping in finding.compliance_mappings:
                        if mapping.framework == framework:
                            for control_id in mapping.control_ids:
                                if control_id not in control_findings:
                                    control_findings[control_id] = []
                                control_findings[control_id].append(finding)
            
            # Generate status for each control
            for control_id, control_info in framework_controls.items():
                findings_for_control = control_findings.get(control_id, [])
                
                control_status[control_id] = {
                    'name': control_info.get('name', control_id),
                    'description': control_info.get('description', ''),
                    'status': self._determine_control_status(findings_for_control),
                    'findings_count': len(findings_for_control),
                    'critical_findings': len([
                        f for f in findings_for_control 
                        if f.severity.value == 'critical'
                    ]),
                    'recommendations': self._generate_control_recommendations(
                        control_id, findings_for_control
                    )
                }
            
            return control_status
            
        except Exception as e:
            logger.error(f"Error getting framework control status: {e}")
            raise
    
    async def generate_risk_summary(self, findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
        """
        Generate aggregated risk summary across all findings
        """
        try:
            risk_summary = {
                'total_findings': len(findings),
                'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0},
                'by_risk_level': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0},
                'by_threat_category': {},
                'business_impact_summary': {
                    'financial': 0,
                    'operational': 0,
                    'reputational': 0,
                    'regulatory': 0
                },
                'framework_coverage': {},
                'top_cwe_categories': {}
            }
            
            for finding in findings:
                # Count by severity
                risk_summary['by_severity'][finding.severity.value] += 1
                
                # Count by risk level
                if finding.risk_level:
                    risk_summary['by_risk_level'][finding.risk_level.value] += 1
                
                # Count by threat category
                if finding.threat_analysis and finding.threat_analysis.category:
                    category = finding.threat_analysis.category.value
                    risk_summary['by_threat_category'][category] = (
                        risk_summary['by_threat_category'].get(category, 0) + 1
                    )
                
                # Count business impacts
                if finding.business_impact:
                    if finding.business_impact.financial_impact > 0:
                        risk_summary['business_impact_summary']['financial'] += 1
                    if finding.business_impact.operational_impact > 0:
                        risk_summary['business_impact_summary']['operational'] += 1
                    if finding.business_impact.reputational_impact > 0:
                        risk_summary['business_impact_summary']['reputational'] += 1
                    if finding.business_impact.regulatory_impact > 0:
                        risk_summary['business_impact_summary']['regulatory'] += 1
                
                # Count framework coverage
                if finding.compliance_mappings:
                    for mapping in finding.compliance_mappings:
                        framework = mapping.framework.value
                        risk_summary['framework_coverage'][framework] = (
                            risk_summary['framework_coverage'].get(framework, 0) + 1
                        )
                
                # Count CWE categories
                if finding.cwe_id:
                    risk_summary['top_cwe_categories'][finding.cwe_id] = (
                        risk_summary['top_cwe_categories'].get(finding.cwe_id, 0) + 1
                    )
            
            # Sort and limit top CWE categories
            risk_summary['top_cwe_categories'] = dict(
                sorted(
                    risk_summary['top_cwe_categories'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
            
            return risk_summary
            
        except Exception as e:
            logger.error(f"Error generating risk summary: {e}")
            raise
    
    async def generate_compliance_trends(
        self,
        scan_reports: List,
        framework: Optional[ComplianceFramework] = None,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Generate compliance trends over time
        """
        try:
            trends = {
                'framework': framework.value if framework else 'all',
                'period_days': days,
                'data_points': [],
                'overall_trend': 'stable',
                'key_metrics': {
                    'average_compliance_score': 0,
                    'trend_direction': 'stable',
                    'improvement_rate': 0
                }
            }
            
            # Group reports by week for trend analysis
            weekly_data = {}
            for report in scan_reports:
                if hasattr(report, 'created_at') and hasattr(report, 'findings'):
                    week_key = report.created_at.strftime('%Y-W%U')
                    if week_key not in weekly_data:
                        weekly_data[week_key] = {
                            'date': report.created_at,
                            'findings': []
                        }
                    weekly_data[week_key]['findings'].extend(report.findings or [])
            
            # Calculate weekly compliance scores
            compliance_scores = []
            for week_key, week_data in sorted(weekly_data.items()):
                if framework:
                    # Generate compliance report for specific framework
                    week_report = await self.generate_compliance_report(
                        week_data['findings'], framework
                    )
                    compliance_score = week_report['compliance_score']
                else:
                    # Calculate overall compliance score across all frameworks
                    total_critical_high = len([
                        f for f in week_data['findings']
                        if f.severity.value in ['critical', 'high']
                    ])
                    total_findings = len(week_data['findings'])
                    compliance_score = (
                        (total_findings - total_critical_high) / total_findings * 100
                        if total_findings > 0 else 100
                    )
                
                trends['data_points'].append({
                    'date': week_data['date'].isoformat(),
                    'compliance_score': round(compliance_score, 2),
                    'total_findings': len(week_data['findings']),
                    'critical_high_findings': len([
                        f for f in week_data['findings']
                        if f.severity.value in ['critical', 'high']
                    ])
                })
                compliance_scores.append(compliance_score)
            
            # Calculate trend metrics
            if len(compliance_scores) >= 2:
                first_score = compliance_scores[0]
                last_score = compliance_scores[-1]
                improvement_rate = ((last_score - first_score) / first_score * 100
                                  if first_score > 0 else 0)
                
                trends['key_metrics']['average_compliance_score'] = round(
                    sum(compliance_scores) / len(compliance_scores), 2
                )
                trends['key_metrics']['improvement_rate'] = round(improvement_rate, 2)
                
                if improvement_rate > 5:
                    trends['key_metrics']['trend_direction'] = 'improving'
                    trends['overall_trend'] = 'improving'
                elif improvement_rate < -5:
                    trends['key_metrics']['trend_direction'] = 'declining'
                    trends['overall_trend'] = 'declining'
                else:
                    trends['key_metrics']['trend_direction'] = 'stable'
                    trends['overall_trend'] = 'stable'
            
            return trends
            
        except Exception as e:
            logger.error(f"Error generating compliance trends: {e}")
            raise
    
    def _determine_control_status(self, findings: List[VulnerabilityFinding]) -> str:
        """Determine control compliance status based on findings"""
        if not findings:
            return "not_tested"
        
        critical_count = len([f for f in findings if f.severity.value == 'critical'])
        high_count = len([f for f in findings if f.severity.value == 'high'])
        
        if critical_count > 0:
            return "non_compliant"
        elif high_count > 0:
            return "partial"
        else:
            return "compliant"
    
    def _generate_framework_recommendations(
        self,
        framework: ComplianceFramework,
        control_findings: Dict[str, List[VulnerabilityFinding]],
        framework_controls: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for framework compliance"""
        recommendations = []
        
        # Identify controls with critical/high findings
        problematic_controls = []
        for control_id, findings in control_findings.items():
            critical_high_count = len([
                f for f in findings 
                if f.severity.value in ['critical', 'high']
            ])
            if critical_high_count > 0:
                problematic_controls.append((control_id, critical_high_count))
        
        # Sort by severity
        problematic_controls.sort(key=lambda x: x[1], reverse=True)
        
        # Generate specific recommendations
        for control_id, count in problematic_controls[:5]:  # Top 5 issues
            control_name = framework_controls.get(control_id, {}).get('name', control_id)
            recommendations.append(
                f"Address {count} critical/high findings in {control_name} ({control_id})"
            )
        
        # Add general recommendations based on framework
        if framework == ComplianceFramework.SOC2:
            recommendations.append("Implement continuous monitoring for access controls")
            recommendations.append("Establish formal incident response procedures")
        elif framework == ComplianceFramework.PCI_DSS:
            recommendations.append("Encrypt sensitive cardholder data at rest and in transit")
            recommendations.append("Implement strong access control measures")
        elif framework == ComplianceFramework.GDPR:
            recommendations.append("Implement data protection by design and by default")
            recommendations.append("Establish procedures for data subject rights")
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _generate_control_recommendations(
        self,
        control_id: str,
        findings: List[VulnerabilityFinding]
    ) -> List[str]:
        """Generate specific recommendations for a control"""
        recommendations = []
        
        if not findings:
            return ["No specific issues identified for this control"]
        
        # Group findings by type
        finding_types = {}
        for finding in findings:
            finding_type = finding.title or finding.rule_id or "Unknown"
            if finding_type not in finding_types:
                finding_types[finding_type] = []
            finding_types[finding_type].append(finding)
        
        # Generate recommendations based on finding patterns
        for finding_type, type_findings in finding_types.items():
            severity_counts = {}
            for f in type_findings:
                severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1
            
            if severity_counts.get('critical', 0) > 0:
                recommendations.append(f"Immediately address {finding_type} (Critical)")
            elif severity_counts.get('high', 0) > 0:
                recommendations.append(f"Prioritize fixing {finding_type} (High)")
        
        return recommendations[:5]  # Limit to 5 recommendations per control


# Global compliance analysis service instance
compliance_service = ComplianceAnalysisService()
