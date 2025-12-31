"""
Advanced Compliance Reporting Service
SOX, HIPAA, ISO 27001, and custom compliance framework support
"""
import structlog
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from pymongo import ASCENDING, DESCENDING
import json

# Import from canonical source
from models.base import ComplianceFramework, ComplianceStatus, utc_now

logger = structlog.get_logger()


class AdvancedComplianceService:
    """Service for advanced compliance reporting and assessment"""

    def __init__(self, db):
        self.db = db
        self.logger = logger.bind(service="compliance")

        # Compliance framework requirements
        self.framework_requirements = self._load_framework_requirements()

    def _load_framework_requirements(self) -> Dict[str, Any]:
        """Load compliance framework requirements"""
        return {
            ComplianceFramework.SOX: {
                "name": "Sarbanes-Oxley Act (SOX)",
                "description": "Financial reporting and IT controls compliance",
                "controls": [
                    {
                        "id": "SOX-302",
                        "name": "Corporate Responsibility for Financial Reports",
                        "requirements": [
                            "Access controls for financial systems",
                            "Audit trail for financial data changes",
                            "Segregation of duties",
                            "Change management procedures",
                        ],
                    },
                    {
                        "id": "SOX-404",
                        "name": "Management Assessment of Internal Controls",
                        "requirements": [
                            "Documented security policies",
                            "Regular security assessments",
                            "Vulnerability management process",
                            "Incident response procedures",
                        ],
                    },
                    {
                        "id": "SOX-409",
                        "name": "Real-Time Issuer Disclosures",
                        "requirements": [
                            "Real-time security monitoring",
                            "Immediate incident reporting",
                            "Automated alerting systems",
                        ],
                    },
                ],
            },
            ComplianceFramework.HIPAA: {
                "name": "Health Insurance Portability and Accountability Act (HIPAA)",
                "description": "Healthcare data privacy and security standards",
                "controls": [
                    {
                        "id": "HIPAA-164.308",
                        "name": "Administrative Safeguards",
                        "requirements": [
                            "Security management process",
                            "Workforce security controls",
                            "Access authorization procedures",
                            "Security awareness training",
                        ],
                    },
                    {
                        "id": "HIPAA-164.310",
                        "name": "Physical Safeguards",
                        "requirements": [
                            "Facility access controls",
                            "Workstation security",
                            "Device and media controls",
                        ],
                    },
                    {
                        "id": "HIPAA-164.312",
                        "name": "Technical Safeguards",
                        "requirements": [
                            "Access control mechanisms",
                            "Audit controls and logging",
                            "Data integrity controls",
                            "Encryption and decryption",
                            "Authentication procedures",
                        ],
                    },
                    {
                        "id": "HIPAA-164.316",
                        "name": "Policies and Procedures",
                        "requirements": [
                            "Documented security policies",
                            "Regular policy reviews",
                            "Policy enforcement mechanisms",
                        ],
                    },
                ],
            },
            ComplianceFramework.ISO_27001: {
                "name": "ISO/IEC 27001:2013",
                "description": "Information Security Management System (ISMS)",
                "controls": [
                    {
                        "id": "ISO-A.12.6",
                        "name": "Technical Vulnerability Management",
                        "requirements": [
                            "Regular vulnerability scanning",
                            "Vulnerability assessment process",
                            "Patch management procedures",
                            "Vulnerability tracking system",
                        ],
                    },
                    {
                        "id": "ISO-A.12.4",
                        "name": "Logging and Monitoring",
                        "requirements": [
                            "Event logging enabled",
                            "Log protection mechanisms",
                            "Administrator and operator logs",
                            "Clock synchronization",
                        ],
                    },
                    {
                        "id": "ISO-A.9.2",
                        "name": "User Access Management",
                        "requirements": [
                            "User registration process",
                            "Access provisioning procedures",
                            "Access rights review process",
                            "Removal of access rights",
                        ],
                    },
                    {
                        "id": "ISO-A.18.1",
                        "name": "Compliance with Legal Requirements",
                        "requirements": [
                            "Identification of applicable legislation",
                            "Intellectual property rights protection",
                            "Protection of records",
                            "Privacy and personal information protection",
                        ],
                    },
                ],
            },
            ComplianceFramework.PCI_DSS: {
                "name": "Payment Card Industry Data Security Standard",
                "description": "Security standards for payment card data",
                "controls": [
                    {
                        "id": "PCI-6.5",
                        "name": "Secure Coding Practices",
                        "requirements": [
                            "Protection against injection flaws",
                            "Buffer overflow prevention",
                            "Insecure cryptographic storage prevention",
                            "Improper error handling prevention",
                            "Cross-site scripting (XSS) prevention",
                        ],
                    },
                    {
                        "id": "PCI-11.2",
                        "name": "Vulnerability Scanning",
                        "requirements": [
                            "Quarterly vulnerability scans",
                            "Scan after significant changes",
                            "Qualified scan vendor usage",
                            "Rescan until passing results",
                        ],
                    },
                ],
            },
            ComplianceFramework.GDPR: {
                "name": "General Data Protection Regulation",
                "description": "EU data protection and privacy regulation",
                "controls": [
                    {
                        "id": "GDPR-32",
                        "name": "Security of Processing",
                        "requirements": [
                            "Pseudonymization and encryption",
                            "Confidentiality and integrity assurance",
                            "Availability and resilience",
                            "Regular security testing",
                        ],
                    },
                    {
                        "id": "GDPR-33",
                        "name": "Breach Notification",
                        "requirements": [
                            "72-hour breach notification",
                            "Breach impact assessment",
                            "Documentation of breaches",
                        ],
                    },
                ],
            },
        }

    async def assess_compliance(
        self,
        project_id: str,
        framework: ComplianceFramework,
        scan_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess compliance against a specific framework"""
        try:
            assessment_id = f"compliance_{framework.value}_{utc_now().timestamp()}"

            framework_req = self.framework_requirements.get(framework, {})
            if not framework_req:
                return {"success": False, "error": "Framework requirements not found"}

            assessment = {
                "assessment_id": assessment_id,
                "project_id": project_id,
                "framework": framework.value,
                "framework_name": framework_req["name"],
                "assessed_at": utc_now(),
                "overall_status": ComplianceStatus.UNDER_REVIEW.value,
                "compliance_score": 0.0,
                "controls_assessed": 0,
                "controls_compliant": 0,
                "controls_non_compliant": 0,
                "controls_partial": 0,
                "controls": [],
                "findings": [],
                "recommendations": [],
            }

            # Assess each control
            for control in framework_req.get("controls", []):
                control_assessment = await self._assess_control(
                    control, scan_results, framework
                )
                assessment["controls"].append(control_assessment)
                assessment["controls_assessed"] += 1

                if control_assessment["status"] == ComplianceStatus.COMPLIANT.value:
                    assessment["controls_compliant"] += 1
                elif control_assessment["status"] == ComplianceStatus.NON_COMPLIANT.value:
                    assessment["controls_non_compliant"] += 1
                elif control_assessment["status"] == ComplianceStatus.PARTIALLY_COMPLIANT.value:
                    assessment["controls_partial"] += 1

                # Collect findings and recommendations
                assessment["findings"].extend(control_assessment.get("findings", []))
                assessment["recommendations"].extend(
                    control_assessment.get("recommendations", [])
                )

            # Calculate compliance score
            if assessment["controls_assessed"] > 0:
                assessment["compliance_score"] = (
                    (assessment["controls_compliant"] + 0.5 * assessment["controls_partial"])
                    / assessment["controls_assessed"]
                ) * 100

            # Determine overall status
            if assessment["compliance_score"] >= 95:
                assessment["overall_status"] = ComplianceStatus.COMPLIANT.value
            elif assessment["compliance_score"] >= 70:
                assessment["overall_status"] = ComplianceStatus.PARTIALLY_COMPLIANT.value
            else:
                assessment["overall_status"] = ComplianceStatus.NON_COMPLIANT.value

            # Store assessment
            await self.db.compliance_assessments.insert_one(assessment)

            self.logger.info(
                "compliance_assessed",
                assessment_id=assessment_id,
                framework=framework.value,
                score=assessment["compliance_score"],
            )

            return {"success": True, "assessment": assessment}

        except Exception as e:
            self.logger.error("assess_compliance_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def _assess_control(
        self,
        control: Dict[str, Any],
        scan_results: Dict[str, Any],
        framework: ComplianceFramework,
    ) -> Dict[str, Any]:
        """Assess a specific compliance control"""
        control_assessment = {
            "control_id": control["id"],
            "control_name": control["name"],
            "status": ComplianceStatus.COMPLIANT.value,
            "findings": [],
            "recommendations": [],
            "evidence": [],
        }

        findings = scan_results.get("findings", [])
        
        # Framework-specific control assessment logic
        if framework == ComplianceFramework.SOX:
            control_assessment = self._assess_sox_control(control, findings, control_assessment)
        elif framework == ComplianceFramework.HIPAA:
            control_assessment = self._assess_hipaa_control(control, findings, control_assessment)
        elif framework == ComplianceFramework.ISO_27001:
            control_assessment = self._assess_iso_control(control, findings, control_assessment)
        elif framework == ComplianceFramework.PCI_DSS:
            control_assessment = self._assess_pci_control(control, findings, control_assessment)
        elif framework == ComplianceFramework.GDPR:
            control_assessment = self._assess_gdpr_control(control, findings, control_assessment)

        return control_assessment

    def _assess_sox_control(
        self, control: Dict[str, Any], findings: List[Dict], assessment: Dict
    ) -> Dict:
        """Assess SOX-specific controls"""
        if control["id"] == "SOX-302":
            # Check for access control issues
            access_issues = [
                f for f in findings
                if any(term in f.get("title", "").lower() for term in ["access", "authentication", "authorization"])
            ]
            if access_issues:
                assessment["status"] = ComplianceStatus.NON_COMPLIANT.value
                assessment["findings"] = access_issues[:5]
                assessment["recommendations"].append(
                    "Implement robust access controls for financial systems"
                )

        elif control["id"] == "SOX-404":
            # Check for security policy violations
            critical_findings = [f for f in findings if f.get("severity") == "critical"]
            if critical_findings:
                assessment["status"] = ComplianceStatus.NON_COMPLIANT.value
                assessment["findings"] = critical_findings[:5]
                assessment["recommendations"].append(
                    "Address critical security vulnerabilities immediately"
                )

        return assessment

    def _assess_hipaa_control(
        self, control: Dict[str, Any], findings: List[Dict], assessment: Dict
    ) -> Dict:
        """Assess HIPAA-specific controls"""
        if control["id"] == "HIPAA-164.312":
            # Check for encryption and authentication issues
            crypto_issues = [
                f for f in findings
                if any(term in f.get("title", "").lower() for term in ["encrypt", "crypto", "password", "auth"])
            ]
            if crypto_issues:
                assessment["status"] = ComplianceStatus.NON_COMPLIANT.value
                assessment["findings"] = crypto_issues[:5]
                assessment["recommendations"].append(
                    "Implement strong encryption and authentication mechanisms"
                )

        return assessment

    def _assess_iso_control(
        self, control: Dict[str, Any], findings: List[Dict], assessment: Dict
    ) -> Dict:
        """Assess ISO 27001-specific controls"""
        if control["id"] == "ISO-A.12.6":
            # Check vulnerability management
            vuln_count = len(findings)
            if vuln_count > 50:
                assessment["status"] = ComplianceStatus.NON_COMPLIANT.value
                assessment["recommendations"].append(
                    f"Reduce vulnerability count from {vuln_count} to acceptable levels"
                )
            elif vuln_count > 20:
                assessment["status"] = ComplianceStatus.PARTIALLY_COMPLIANT.value
                assessment["recommendations"].append(
                    "Continue vulnerability remediation efforts"
                )

        return assessment

    def _assess_pci_control(
        self, control: Dict[str, Any], findings: List[Dict], assessment: Dict
    ) -> Dict:
        """Assess PCI DSS-specific controls"""
        if control["id"] == "PCI-6.5":
            # Check for secure coding violations
            coding_issues = [
                f for f in findings
                if any(term in f.get("title", "").lower() for term in ["injection", "xss", "csrf", "buffer"])
            ]
            if coding_issues:
                assessment["status"] = ComplianceStatus.NON_COMPLIANT.value
                assessment["findings"] = coding_issues[:5]
                assessment["recommendations"].append(
                    "Address secure coding practice violations"
                )

        return assessment

    def _assess_gdpr_control(
        self, control: Dict[str, Any], findings: List[Dict], assessment: Dict
    ) -> Dict:
        """Assess GDPR-specific controls"""
        if control["id"] == "GDPR-32":
            # Check data protection controls
            data_issues = [
                f for f in findings
                if any(term in f.get("title", "").lower() for term in ["data", "privacy", "encrypt", "exposure"])
            ]
            if data_issues:
                assessment["status"] = ComplianceStatus.NON_COMPLIANT.value
                assessment["findings"] = data_issues[:5]
                assessment["recommendations"].append(
                    "Implement data protection and encryption controls"
                )

        return assessment

    async def generate_compliance_report(
        self,
        project_id: str,
        frameworks: List[ComplianceFramework],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        try:
            if not end_date:
                end_date = utc_now()
            if not start_date:
                start_date = end_date - timedelta(days=90)

            report_id = f"compliance_report_{utc_now().timestamp()}"

            # Get latest scan results for project
            latest_scan = await self.db.scan_reports.find_one(
                {"project_id": project_id}, sort=[("created_at", DESCENDING)]
            )

            if not latest_scan:
                return {"success": False, "error": "No scan results found for project"}

            report = {
                "report_id": report_id,
                "project_id": project_id,
                "generated_at": utc_now(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "frameworks_assessed": [],
                "overall_compliance_score": 0.0,
                "executive_summary": {},
                "detailed_assessments": [],
                "recommendations": [],
                "action_items": [],
            }

            # Assess each framework
            total_score = 0
            for framework in frameworks:
                assessment = await self.assess_compliance(
                    project_id, framework, latest_scan
                )
                if assessment.get("success"):
                    report["frameworks_assessed"].append(framework.value)
                    report["detailed_assessments"].append(assessment["assessment"])
                    total_score += assessment["assessment"]["compliance_score"]

                    # Collect recommendations
                    report["recommendations"].extend(
                        assessment["assessment"]["recommendations"]
                    )

            # Calculate overall compliance score
            if report["frameworks_assessed"]:
                report["overall_compliance_score"] = total_score / len(
                    report["frameworks_assessed"]
                )

            # Generate executive summary
            report["executive_summary"] = self._generate_executive_summary(report)

            # Generate action items
            report["action_items"] = self._generate_action_items(report)

            # Store report
            await self.db.compliance_reports.insert_one(report)

            self.logger.info(
                "compliance_report_generated",
                report_id=report_id,
                project_id=project_id,
                frameworks=len(frameworks),
            )

            return {"success": True, "report": report}

        except Exception as e:
            self.logger.error("generate_compliance_report_failed", error=str(e))
            return {"success": False, "error": str(e)}

    def _generate_executive_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary for compliance report"""
        summary = {
            "overall_status": "Compliant",
            "key_findings": [],
            "risk_level": "Low",
            "frameworks_count": len(report["frameworks_assessed"]),
            "compliance_score": report["overall_compliance_score"],
        }

        # Determine overall status and risk level
        if report["overall_compliance_score"] < 70:
            summary["overall_status"] = "Non-Compliant"
            summary["risk_level"] = "High"
        elif report["overall_compliance_score"] < 95:
            summary["overall_status"] = "Partially Compliant"
            summary["risk_level"] = "Medium"

        # Extract key findings
        for assessment in report["detailed_assessments"]:
            if assessment["controls_non_compliant"] > 0:
                summary["key_findings"].append(
                    f"{assessment['framework_name']}: {assessment['controls_non_compliant']} non-compliant controls"
                )

        return summary

    def _generate_action_items(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized action items"""
        action_items = []
        priority_map = {"High": 1, "Medium": 2, "Low": 3}

        # Collect all recommendations with priority
        for assessment in report["detailed_assessments"]:
            for control in assessment["controls"]:
                if control["status"] == ComplianceStatus.NON_COMPLIANT.value:
                    action_items.append({
                        "priority": "High",
                        "framework": assessment["framework_name"],
                        "control": control["control_name"],
                        "action": f"Address non-compliant control: {control['control_id']}",
                        "recommendations": control.get("recommendations", []),
                    })
                elif control["status"] == ComplianceStatus.PARTIALLY_COMPLIANT.value:
                    action_items.append({
                        "priority": "Medium",
                        "framework": assessment["framework_name"],
                        "control": control["control_name"],
                        "action": f"Improve partially compliant control: {control['control_id']}",
                        "recommendations": control.get("recommendations", []),
                    })

        # Sort by priority
        action_items.sort(key=lambda x: priority_map.get(x["priority"], 999))

        return action_items[:20]  # Return top 20 action items

    async def get_compliance_trend(
        self, project_id: str, framework: ComplianceFramework, days: int = 90
    ) -> Dict[str, Any]:
        """Get compliance trend over time"""
        try:
            start_date = utc_now() - timedelta(days=days)

            assessments = await self.db.compliance_assessments.find(
                {
                    "project_id": project_id,
                    "framework": framework.value,
                    "assessed_at": {"$gte": start_date},
                }
            ).sort("assessed_at", ASCENDING).to_list(length=None)

            trend_data = {
                "project_id": project_id,
                "framework": framework.value,
                "period_days": days,
                "data_points": [],
                "trend": "stable",
                "improvement_rate": 0.0,
            }

            for assessment in assessments:
                trend_data["data_points"].append({
                    "date": assessment["assessed_at"].isoformat(),
                    "score": assessment["compliance_score"],
                    "status": assessment["overall_status"],
                })

            # Calculate trend
            if len(trend_data["data_points"]) >= 2:
                first_score = trend_data["data_points"][0]["score"]
                last_score = trend_data["data_points"][-1]["score"]
                
                trend_data["improvement_rate"] = (
                    (last_score - first_score) / first_score * 100
                    if first_score > 0
                    else 0
                )

                if trend_data["improvement_rate"] > 5:
                    trend_data["trend"] = "improving"
                elif trend_data["improvement_rate"] < -5:
                    trend_data["trend"] = "declining"

            return {"success": True, "trend": trend_data}

        except Exception as e:
            self.logger.error("get_compliance_trend_failed", error=str(e))
            return {"success": False, "error": str(e)}


# Singleton instance
_compliance_service_instance = None


def get_compliance_service(db) -> AdvancedComplianceService:
    """Get or create compliance service instance"""
    global _compliance_service_instance
    if _compliance_service_instance is None:
        _compliance_service_instance = AdvancedComplianceService(db)
    return _compliance_service_instance

