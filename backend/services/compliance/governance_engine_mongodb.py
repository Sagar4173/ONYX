"""
Governance & Compliance Engine (MongoDB Version)
=================================================

Enterprise governance framework mapping findings to compliance standards
(PCI-DSS, SOC 2, ISO 27001, NIST, CIS) with MongoDB storage and Git-based audit trails.

IMPORTANT: This is the MongoDB-based implementation replacing the SQLite version.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import from canonical source
from models.base import utc_now

# Configure logger (logging.basicConfig is called in app.py)
logger = logging.getLogger(__name__)


class ComplianceFrameworkDoc:
    """Compliance framework document for MongoDB"""
    
    def __init__(
        self,
        framework_id: str,
        name: str,
        version: str,
        description: str,
        authority: str,
        controls: Dict[str, Dict[str, Any]],
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.framework_id = framework_id
        self.name = name
        self.version = version
        self.description = description
        self.authority = authority
        self.controls = controls
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework_id": self.framework_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "authority": self.authority,
            "controls": self.controls,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ComplianceMappingDoc:
    """Mapping between security finding and compliance requirements"""
    
    def __init__(
        self,
        mapping_id: str,
        finding_type: str,
        finding_identifier: str,
        framework_id: str,
        control_id: str,
        control_title: str,
        severity_impact: str,
        remediation_required: bool,
        evidence_required: List[str],
        audit_frequency: str,
        created_at: datetime = None,
        last_reviewed: datetime = None,
        reviewer: str = None
    ):
        self.mapping_id = mapping_id
        self.finding_type = finding_type
        self.finding_identifier = finding_identifier
        self.framework_id = framework_id
        self.control_id = control_id
        self.control_title = control_title
        self.severity_impact = severity_impact
        self.remediation_required = remediation_required
        self.evidence_required = evidence_required
        self.audit_frequency = audit_frequency
        self.created_at = created_at or utc_now()
        self.last_reviewed = last_reviewed or utc_now()
        self.reviewer = reviewer
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "finding_type": self.finding_type,
            "finding_identifier": self.finding_identifier,
            "framework_id": self.framework_id,
            "control_id": self.control_id,
            "control_title": self.control_title,
            "severity_impact": self.severity_impact,
            "remediation_required": self.remediation_required,
            "evidence_required": self.evidence_required,
            "audit_frequency": self.audit_frequency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "reviewer": self.reviewer
        }


class ComplianceAssessmentDoc:
    """Compliance assessment results"""
    
    def __init__(
        self,
        assessment_id: str,
        framework_id: str,
        scope: str,
        assessment_date: datetime = None,
        total_controls: int = 0,
        compliant_controls: int = 0,
        non_compliant_controls: int = 0,
        gaps_identified: List[Dict[str, Any]] = None,
        remediation_plan: List[Dict[str, Any]] = None,
        next_review_date: datetime = None,
        assessor: str = None
    ):
        self.assessment_id = assessment_id
        self.framework_id = framework_id
        self.scope = scope
        self.assessment_date = assessment_date or utc_now()
        self.total_controls = total_controls
        self.compliant_controls = compliant_controls
        self.non_compliant_controls = non_compliant_controls
        self.gaps_identified = gaps_identified or []
        self.remediation_plan = remediation_plan or []
        self.next_review_date = next_review_date
        self.assessor = assessor
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "framework_id": self.framework_id,
            "scope": self.scope,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "total_controls": self.total_controls,
            "compliant_controls": self.compliant_controls,
            "non_compliant_controls": self.non_compliant_controls,
            "gaps_identified": self.gaps_identified,
            "remediation_plan": self.remediation_plan,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "assessor": self.assessor
        }


class GovernanceComplianceEngine:
    """Enterprise governance and compliance management engine using MongoDB"""
    
    # Collection names
    FRAMEWORKS_COLLECTION = "compliance_frameworks"
    MAPPINGS_COLLECTION = "compliance_mappings"
    ASSESSMENTS_COLLECTION = "compliance_assessments"
    AUDIT_TRAILS_COLLECTION = "compliance_audit_trails"
    
    # Standard compliance frameworks
    STANDARD_FRAMEWORKS = {
        "pci_dss": {
            "name": "PCI Data Security Standard",
            "version": "4.0",
            "description": "Payment Card Industry Data Security Standard",
            "authority": "PCI Security Standards Council",
            "controls": {
                "1": {"title": "Install and maintain network security controls", "category": "network"},
                "2": {"title": "Apply secure configurations", "category": "configuration"},
                "3": {"title": "Protect stored cardholder data", "category": "data_protection"},
                "4": {"title": "Protect cardholder data with strong cryptography", "category": "encryption"},
                "5": {"title": "Protect all systems and networks from malicious software", "category": "malware"},
                "6": {"title": "Develop and maintain secure systems and software", "category": "secure_development"},
                "7": {"title": "Restrict access by business need-to-know", "category": "access_control"},
                "8": {"title": "Identify users and authenticate access", "category": "authentication"},
                "9": {"title": "Restrict physical access", "category": "physical_security"},
                "10": {"title": "Log and monitor all access", "category": "logging"},
                "11": {"title": "Test security of systems and networks regularly", "category": "testing"},
                "12": {"title": "Support information security with organizational policies", "category": "governance"}
            }
        },
        "soc2": {
            "name": "SOC 2 Type II",
            "version": "2017",
            "description": "System and Organization Controls 2",
            "authority": "AICPA",
            "controls": {
                "CC1": {"title": "Control Environment", "category": "common_criteria"},
                "CC2": {"title": "Communication and Information", "category": "common_criteria"},
                "CC3": {"title": "Risk Assessment", "category": "common_criteria"},
                "CC4": {"title": "Monitoring Activities", "category": "common_criteria"},
                "CC5": {"title": "Control Activities", "category": "common_criteria"},
                "CC6": {"title": "Logical and Physical Access Controls", "category": "common_criteria"},
                "CC7": {"title": "System Operations", "category": "common_criteria"},
                "CC8": {"title": "Change Management", "category": "common_criteria"},
                "CC9": {"title": "Risk Mitigation", "category": "common_criteria"},
                "A1": {"title": "Availability Processing", "category": "availability"},
                "C1": {"title": "Confidentiality Processing", "category": "confidentiality"},
                "P1": {"title": "Privacy Processing", "category": "privacy"}
            }
        },
        "iso27001": {
            "name": "ISO/IEC 27001:2022",
            "version": "2022",
            "description": "Information Security Management Systems",
            "authority": "International Organization for Standardization",
            "controls": {
                "A.5": {"title": "Information security policies", "category": "organizational"},
                "A.6": {"title": "Organization of information security", "category": "organizational"},
                "A.7": {"title": "Human resource security", "category": "people"},
                "A.8": {"title": "Asset management", "category": "physical_environmental"},
                "A.9": {"title": "Access control", "category": "access_control"},
                "A.10": {"title": "Cryptography", "category": "cryptography"},
                "A.11": {"title": "Physical and environmental security", "category": "physical_environmental"},
                "A.12": {"title": "Operations security", "category": "operations"},
                "A.13": {"title": "Communications security", "category": "communications"},
                "A.14": {"title": "System acquisition, development and maintenance", "category": "development"},
                "A.15": {"title": "Supplier relationships", "category": "supplier"},
                "A.16": {"title": "Information security incident management", "category": "incident"},
                "A.17": {"title": "Business continuity", "category": "continuity"},
                "A.18": {"title": "Compliance", "category": "compliance"}
            }
        },
        "nist_csf": {
            "name": "NIST Cybersecurity Framework",
            "version": "2.0",
            "description": "Framework for Improving Critical Infrastructure Cybersecurity",
            "authority": "National Institute of Standards and Technology",
            "controls": {
                "ID": {"title": "Identify", "category": "identify"},
                "PR": {"title": "Protect", "category": "protect"},
                "DE": {"title": "Detect", "category": "detect"},
                "RS": {"title": "Respond", "category": "respond"},
                "RC": {"title": "Recover", "category": "recover"},
                "GV": {"title": "Govern", "category": "govern"}
            }
        }
    }
    
    def __init__(self, db_manager=None):
        """Initialize the governance compliance engine with MongoDB."""
        self.db_manager = db_manager
        self._db = None
        logger.info("🏛️ Governance & Compliance Engine initialized (MongoDB)")
    
    async def _get_db(self):
        """Get the MongoDB database instance."""
        if self._db is None:
            if self.db_manager is None:
                from database import db_manager
                self.db_manager = db_manager
            self._db = self.db_manager.db
        return self._db
    
    async def initialize(self):
        """Initialize database collections and load standard frameworks."""
        db = await self._get_db()
        if db is None:
            logger.warning("Database not connected, running in memory-only mode")
            return
        
        # Create indexes
        await db[self.FRAMEWORKS_COLLECTION].create_index("framework_id", unique=True)
        await db[self.MAPPINGS_COLLECTION].create_index("mapping_id", unique=True)
        await db[self.MAPPINGS_COLLECTION].create_index("framework_id")
        await db[self.ASSESSMENTS_COLLECTION].create_index("assessment_id", unique=True)
        await db[self.AUDIT_TRAILS_COLLECTION].create_index("timestamp")
        
        # Load standard frameworks
        await self._load_standard_frameworks()
        logger.info("📋 Governance database initialized")
    
    async def _load_standard_frameworks(self):
        """Load standard compliance frameworks into MongoDB."""
        db = await self._get_db()
        if db is None:
            return
        
        for framework_id, framework_data in self.STANDARD_FRAMEWORKS.items():
            existing = await db[self.FRAMEWORKS_COLLECTION].find_one({"framework_id": framework_id})
            if not existing:
                doc = ComplianceFrameworkDoc(
                    framework_id=framework_id,
                    **framework_data
                )
                await db[self.FRAMEWORKS_COLLECTION].insert_one(doc.to_dict())
        
        logger.info("📋 Loaded standard compliance frameworks")
    
    async def get_frameworks(self) -> List[Dict[str, Any]]:
        """Get all compliance frameworks."""
        db = await self._get_db()
        if db is None:
            return list(self.STANDARD_FRAMEWORKS.values())
        
        cursor = db[self.FRAMEWORKS_COLLECTION].find({})
        frameworks = await cursor.to_list(length=100)
        return frameworks
    
    async def get_framework(self, framework_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific compliance framework by ID."""
        db = await self._get_db()
        if db is None:
            return self.STANDARD_FRAMEWORKS.get(framework_id)
        
        return await db[self.FRAMEWORKS_COLLECTION].find_one({"framework_id": framework_id})
    
    async def map_finding_to_compliance(
        self,
        finding_type: str,
        finding_identifier: str,
        framework_mappings: List[Dict[str, Any]],
        reviewer: str
    ) -> List[str]:
        """Map a security finding to compliance framework controls."""
        mapping_ids = []
        db = await self._get_db()
        
        for mapping in framework_mappings:
            mapping_id = f"{finding_type}_{finding_identifier}_{mapping['framework_id']}_{mapping['control_id']}"
            
            doc = ComplianceMappingDoc(
                mapping_id=mapping_id,
                finding_type=finding_type,
                finding_identifier=finding_identifier,
                framework_id=mapping["framework_id"],
                control_id=mapping["control_id"],
                control_title=mapping.get("control_title", ""),
                severity_impact=mapping.get("severity_impact", "medium"),
                remediation_required=mapping.get("remediation_required", True),
                evidence_required=mapping.get("evidence_required", []),
                audit_frequency=mapping.get("audit_frequency", "quarterly"),
                reviewer=reviewer
            )
            
            if db:
                await db[self.MAPPINGS_COLLECTION].update_one(
                    {"mapping_id": mapping_id},
                    {"$set": doc.to_dict()},
                    upsert=True
                )
            
            mapping_ids.append(mapping_id)
            
            # Log audit trail
            await self._log_audit(
                event_type="mapping_created",
                resource_type="compliance_mapping",
                resource_id=mapping_id,
                action="create",
                actor=reviewer,
                details={"framework_id": mapping["framework_id"], "control_id": mapping["control_id"]}
            )
        
        return mapping_ids
    
    async def get_mappings_for_finding(
        self,
        finding_type: str,
        finding_identifier: str
    ) -> List[Dict[str, Any]]:
        """Get all compliance mappings for a specific finding."""
        db = await self._get_db()
        if db is None:
            return []
        
        cursor = db[self.MAPPINGS_COLLECTION].find({
            "finding_type": finding_type,
            "finding_identifier": finding_identifier
        })
        return await cursor.to_list(length=100)
    
    async def create_assessment(
        self,
        framework_id: str,
        scope: str,
        assessor: str,
        controls_evaluated: Dict[str, bool]
    ) -> ComplianceAssessmentDoc:
        """Create a compliance assessment for a framework."""
        assessment_id = f"assessment_{framework_id}_{uuid.uuid4().hex[:8]}"
        
        framework = await self.get_framework(framework_id)
        if not framework:
            raise ValueError(f"Framework {framework_id} not found")
        
        total_controls = len(controls_evaluated)
        compliant_controls = sum(1 for v in controls_evaluated.values() if v)
        non_compliant_controls = total_controls - compliant_controls
        
        # Identify gaps
        gaps = [
            {"control_id": k, "status": "non_compliant"}
            for k, v in controls_evaluated.items() if not v
        ]
        
        assessment = ComplianceAssessmentDoc(
            assessment_id=assessment_id,
            framework_id=framework_id,
            scope=scope,
            total_controls=total_controls,
            compliant_controls=compliant_controls,
            non_compliant_controls=non_compliant_controls,
            gaps_identified=gaps,
            assessor=assessor
        )
        
        db = await self._get_db()
        if db:
            await db[self.ASSESSMENTS_COLLECTION].insert_one(assessment.to_dict())
        
        # Log audit
        await self._log_audit(
            event_type="assessment_created",
            resource_type="compliance_assessment",
            resource_id=assessment_id,
            action="create",
            actor=assessor,
            details={"framework_id": framework_id, "compliance_rate": compliant_controls / total_controls if total_controls > 0 else 0}
        )
        
        return assessment
    
    async def get_assessments(
        self,
        framework_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get compliance assessments, optionally filtered by framework."""
        db = await self._get_db()
        if db is None:
            return []
        
        query = {"framework_id": framework_id} if framework_id else {}
        cursor = db[self.ASSESSMENTS_COLLECTION].find(query).sort("assessment_date", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get aggregated compliance dashboard data."""
        db = await self._get_db()
        
        frameworks = await self.get_frameworks()
        
        # Get latest assessment for each framework
        framework_status = {}
        for framework in frameworks:
            fid = framework.get("framework_id")
            if db:
                latest = await db[self.ASSESSMENTS_COLLECTION].find_one(
                    {"framework_id": fid},
                    sort=[("assessment_date", -1)]
                )
                if latest:
                    compliance_rate = (latest["compliant_controls"] / latest["total_controls"] * 100) if latest["total_controls"] > 0 else 0
                    framework_status[fid] = {
                        "name": framework.get("name"),
                        "compliance_rate": round(compliance_rate, 1),
                        "last_assessed": latest.get("assessment_date"),
                        "gaps_count": len(latest.get("gaps_identified", []))
                    }
                else:
                    framework_status[fid] = {
                        "name": framework.get("name"),
                        "compliance_rate": None,
                        "last_assessed": None,
                        "gaps_count": 0
                    }
            else:
                framework_status[fid] = {
                    "name": framework.get("name"),
                    "compliance_rate": None,
                    "last_assessed": None,
                    "gaps_count": 0
                }
        
        return {
            "frameworks": framework_status,
            "total_frameworks": len(frameworks),
            "timestamp": utc_now().isoformat()
        }
    
    async def _log_audit(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: str,
        actor: str,
        details: Dict[str, Any] = None
    ):
        """Log an audit trail entry."""
        db = await self._get_db()
        if db is None:
            return
        
        audit_entry = {
            "audit_id": f"audit_{uuid.uuid4().hex}",
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "actor": actor,
            "timestamp": utc_now().isoformat(),
            "details": details or {}
        }
        
        await db[self.AUDIT_TRAILS_COLLECTION].insert_one(audit_entry)


# Create singleton instance
governance_engine = GovernanceComplianceEngine()

__all__ = [
    "GovernanceComplianceEngine",
    "ComplianceFrameworkDoc",
    "ComplianceMappingDoc",
    "ComplianceAssessmentDoc",
    "governance_engine"
]
