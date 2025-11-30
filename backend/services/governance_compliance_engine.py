"""
Governance & Compliance Engine
==============================

Enterprise governance framework mapping findings to compliance standards
(PCI-DSS, SOC 2, ISO 27001, NIST, CIS) with Git-based audit trails.

Author: ONYX Platform
Date: August 2025
"""

import asyncio
import json
import logging
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import git
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComplianceFramework:
    """Compliance framework definition"""
    framework_id: str
    name: str
    version: str
    description: str
    authority: str
    controls: Dict[str, Dict[str, Any]]  # control_id -> control_details

@dataclass
class ComplianceMapping:
    """Mapping between security finding and compliance requirements"""
    mapping_id: str
    finding_type: str  # CWE, CVE, custom rule
    finding_identifier: str
    framework_id: str
    control_id: str
    control_title: str
    severity_impact: str  # critical, high, medium, low
    remediation_required: bool
    evidence_required: List[str]
    audit_frequency: str  # continuous, quarterly, annually
    created_date: str
    last_reviewed: str
    reviewer: str

@dataclass
class ComplianceAssessment:
    """Compliance assessment results"""
    assessment_id: str
    framework_id: str
    scope: str  # organization, project, asset
    assessment_date: str
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    gaps_identified: List[Dict[str, Any]]
    remediation_plan: List[Dict[str, Any]]
    next_review_date: str
    assessor: str

class GovernanceComplianceEngine:
    """Enterprise governance and compliance management engine"""
    
    def __init__(self, db_path: str = "governance_compliance.db", 
                 git_repo_path: str = "compliance_mappings"):
        self.db_path = db_path
        self.git_repo_path = git_repo_path
        self._init_database()
        self._init_git_repository()
        self._load_compliance_frameworks()
        
        logger.info("🏛️ Governance & Compliance Engine initialized")
    
    def _init_database(self):
        """Initialize compliance database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compliance frameworks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_frameworks (
                framework_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                authority TEXT,
                controls_json TEXT,
                created_date TEXT,
                last_updated TEXT
            )
        ''')
        
        # Compliance mappings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_mappings (
                mapping_id TEXT PRIMARY KEY,
                finding_type TEXT NOT NULL,
                finding_identifier TEXT NOT NULL,
                framework_id TEXT NOT NULL,
                control_id TEXT NOT NULL,
                control_title TEXT,
                severity_impact TEXT,
                remediation_required BOOLEAN,
                evidence_required_json TEXT,
                audit_frequency TEXT,
                created_date TEXT,
                last_reviewed TEXT,
                reviewer TEXT,
                FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(framework_id)
            )
        ''')
        
        # Compliance assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_assessments (
                assessment_id TEXT PRIMARY KEY,
                framework_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                assessment_date TEXT,
                total_controls INTEGER,
                compliant_controls INTEGER,
                non_compliant_controls INTEGER,
                gaps_json TEXT,
                remediation_plan_json TEXT,
                next_review_date TEXT,
                assessor TEXT,
                FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(framework_id)
            )
        ''')
        
        # Audit trails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trails (
                audit_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT,
                details_json TEXT,
                git_commit_hash TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("📊 Governance database initialized")
    
    def _init_git_repository(self):
        """Initialize Git repository for compliance mappings"""
        Path(self.git_repo_path).mkdir(exist_ok=True)
        
        try:
            self.repo = git.Repo(self.git_repo_path)
            logger.info(f"📋 Using existing Git repository: {self.git_repo_path}")
        except git.exc.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.git_repo_path)
            
            # Create initial structure
            frameworks_dir = Path(self.git_repo_path) / "frameworks"
            mappings_dir = Path(self.git_repo_path) / "mappings" 
            assessments_dir = Path(self.git_repo_path) / "assessments"
            
            for dir_path in [frameworks_dir, mappings_dir, assessments_dir]:
                dir_path.mkdir(exist_ok=True)
                (dir_path / ".gitkeep").touch()
            
            # Initial commit
            self.repo.index.add([str(frameworks_dir / ".gitkeep"), 
                               str(mappings_dir / ".gitkeep"),
                               str(assessments_dir / ".gitkeep")])
            self.repo.index.commit("Initial compliance repository structure")
            
            logger.info(f"📋 Initialized new Git repository: {self.git_repo_path}")
    
    def _load_compliance_frameworks(self):
        """Load standard compliance frameworks"""
        frameworks = {
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
            }
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for framework_id, framework_data in frameworks.items():
            cursor.execute('''
                INSERT OR REPLACE INTO compliance_frameworks 
                (framework_id, name, version, description, authority, controls_json, created_date, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                framework_id,
                framework_data["name"],
                framework_data["version"],
                framework_data["description"],
                framework_data["authority"],
                json.dumps(framework_data["controls"]),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        logger.info("📋 Loaded standard compliance frameworks")
    
    async def map_finding_to_compliance(self, finding_type: str, finding_identifier: str,
                                       framework_mappings: List[Dict[str, Any]], 
                                       reviewer: str) -> List[str]:
        """Map a security finding to compliance framework controls"""
        mapping_ids = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for mapping in framework_mappings:
                mapping_id = f"{finding_type}_{finding_identifier}_{mapping['framework_id']}_{mapping['control_id']}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO compliance_mappings
                    (mapping_id, finding_type, finding_identifier, framework_id, control_id,
                     control_title, severity_impact, remediation_required, evidence_required_json,
                     audit_frequency, created_date, last_reviewed, reviewer)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mapping_id,
                    finding_type,
                    finding_identifier,
                    mapping['framework_id'],
                    mapping['control_id'],
                    mapping.get('control_title', ''),
                    mapping.get('severity_impact', 'medium'),
                    mapping.get('remediation_required', True),
                    json.dumps(mapping.get('evidence_required', [])),
                    mapping.get('audit_frequency', 'quarterly'),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    reviewer
                ))
                
                mapping_ids.append(mapping_id)
                
                # Store mapping in Git for audit trail
                await self._store_mapping_in_git(mapping_id, {
                    'finding_type': finding_type,
                    'finding_identifier': finding_identifier,
                    'framework_mapping': mapping,
                    'reviewer': reviewer,
                    'timestamp': datetime.now().isoformat()
                })
            
            conn.commit()
            logger.info(f"✅ Created {len(mapping_ids)} compliance mappings for {finding_identifier}")
            return mapping_ids
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to create compliance mappings: {e}")
            raise
        finally:
            conn.close()
    
    async def _store_mapping_in_git(self, mapping_id: str, mapping_data: Dict[str, Any]):
        """Store compliance mapping in Git for audit trail"""
        mapping_file = Path(self.git_repo_path) / "mappings" / f"{mapping_id}.yaml"
        
        with open(mapping_file, 'w') as f:
            yaml.dump(mapping_data, f, default_flow_style=False)
        
        # Git commit
        self.repo.index.add([str(mapping_file)])
        commit_message = f"Add compliance mapping: {mapping_id}"
        commit = self.repo.index.commit(commit_message)
        
        # Record audit trail
        await self._record_audit_event(
            event_type="compliance_mapping",
            resource_type="mapping",
            resource_id=mapping_id,
            action="create",
            actor=mapping_data.get('reviewer', 'system'),
            details=mapping_data,
            git_commit_hash=commit.hexsha
        )
    
    async def assess_compliance_posture(self, framework_id: str, scope: str, 
                                       assessor: str) -> ComplianceAssessment:
        """Assess current compliance posture against framework"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get framework controls
        cursor.execute('SELECT controls_json FROM compliance_frameworks WHERE framework_id = ?', 
                      (framework_id,))
        framework_result = cursor.fetchone()
        if not framework_result:
            raise ValueError(f"Framework {framework_id} not found")
        
        controls = json.loads(framework_result[0])
        total_controls = len(controls)
        
        # Get current mappings for this framework
        cursor.execute('''
            SELECT control_id, severity_impact, remediation_required 
            FROM compliance_mappings 
            WHERE framework_id = ?
        ''', (framework_id,))
        
        mappings = cursor.fetchall()
        mapped_controls = set(mapping[0] for mapping in mappings)
        
        # Identify gaps
        gaps_identified = []
        for control_id, control_info in controls.items():
            if control_id not in mapped_controls:
                gaps_identified.append({
                    'control_id': control_id,
                    'control_title': control_info['title'],
                    'category': control_info['category'],
                    'gap_type': 'no_mapping',
                    'severity': 'medium'
                })
        
        # Calculate compliance metrics
        compliant_controls = total_controls - len(gaps_identified)
        non_compliant_controls = len(gaps_identified)
        
        # Generate remediation plan
        remediation_plan = []
        for gap in gaps_identified:
            remediation_plan.append({
                'control_id': gap['control_id'],
                'action': 'create_security_finding_mapping',
                'priority': gap['severity'],
                'estimated_effort': 'medium',
                'target_date': (datetime.now()).isoformat()
            })
        
        # Create assessment record
        assessment_id = f"assessment_{framework_id}_{scope}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        assessment = ComplianceAssessment(
            assessment_id=assessment_id,
            framework_id=framework_id,
            scope=scope,
            assessment_date=datetime.now().isoformat(),
            total_controls=total_controls,
            compliant_controls=compliant_controls,
            non_compliant_controls=non_compliant_controls,
            gaps_identified=gaps_identified,
            remediation_plan=remediation_plan,
            next_review_date=(datetime.now()).isoformat(),
            assessor=assessor
        )
        
        # Store assessment
        cursor.execute('''
            INSERT INTO compliance_assessments
            (assessment_id, framework_id, scope, assessment_date, total_controls,
             compliant_controls, non_compliant_controls, gaps_json, remediation_plan_json,
             next_review_date, assessor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment_id, framework_id, scope, assessment.assessment_date,
            total_controls, compliant_controls, non_compliant_controls,
            json.dumps(gaps_identified), json.dumps(remediation_plan),
            assessment.next_review_date, assessor
        ))
        
        conn.commit()
        conn.close()
        
        # Store assessment in Git
        await self._store_assessment_in_git(assessment)
        
        logger.info(f"📊 Compliance assessment completed: {compliant_controls}/{total_controls} controls compliant")
        return assessment
    
    async def _store_assessment_in_git(self, assessment: ComplianceAssessment):
        """Store compliance assessment in Git"""
        assessment_file = Path(self.git_repo_path) / "assessments" / f"{assessment.assessment_id}.yaml"
        
        with open(assessment_file, 'w') as f:
            yaml.dump(asdict(assessment), f, default_flow_style=False)
        
        # Git commit
        self.repo.index.add([str(assessment_file)])
        commit_message = f"Add compliance assessment: {assessment.assessment_id}"
        commit = self.repo.index.commit(commit_message)
        
        # Record audit trail
        await self._record_audit_event(
            event_type="compliance_assessment",
            resource_type="assessment",
            resource_id=assessment.assessment_id,
            action="create",
            actor=assessment.assessor,
            details=asdict(assessment),
            git_commit_hash=commit.hexsha
        )
    
    async def get_compliance_dashboard(self, framework_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate compliance dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if framework_id:
            frameworks = [framework_id]
        else:
            cursor.execute('SELECT framework_id FROM compliance_frameworks')
            frameworks = [row[0] for row in cursor.fetchall()]
        
        dashboard = {
            'frameworks': {},
            'overall_status': {},
            'recent_assessments': [],
            'top_gaps': [],
            'compliance_trends': {}
        }
        
        for fw_id in frameworks:
            # Get latest assessment
            cursor.execute('''
                SELECT * FROM compliance_assessments 
                WHERE framework_id = ? 
                ORDER BY assessment_date DESC LIMIT 1
            ''', (fw_id,))
            
            assessment_row = cursor.fetchone()
            if assessment_row:
                compliance_rate = (assessment_row[5] / assessment_row[4]) * 100  # compliant/total
                dashboard['frameworks'][fw_id] = {
                    'compliance_rate': compliance_rate,
                    'total_controls': assessment_row[4],
                    'compliant_controls': assessment_row[5],
                    'gaps': assessment_row[6],
                    'last_assessment': assessment_row[3]
                }
        
        conn.close()
        return dashboard
    
    async def _record_audit_event(self, event_type: str, resource_type: str, 
                                 resource_id: str, action: str, actor: str,
                                 details: Dict[str, Any], git_commit_hash: str = None):
        """Record audit event for governance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        audit_id = f"audit_{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        cursor.execute('''
            INSERT INTO audit_trails
            (audit_id, event_type, resource_type, resource_id, action, actor, 
             timestamp, details_json, git_commit_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            audit_id, event_type, resource_type, resource_id, action, actor,
            datetime.now().isoformat(), json.dumps(details), git_commit_hash
        ))
        
        conn.commit()
        conn.close()
    
    async def generate_compliance_report(self, framework_id: str, 
                                        output_format: str = "yaml") -> str:
        """Generate comprehensive compliance report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest assessment
        cursor.execute('''
            SELECT * FROM compliance_assessments 
            WHERE framework_id = ? 
            ORDER BY assessment_date DESC LIMIT 1
        ''', (framework_id,))
        
        assessment = cursor.fetchone()
        if not assessment:
            raise ValueError(f"No assessments found for framework {framework_id}")
        
        # Get all mappings for this framework
        cursor.execute('''
            SELECT * FROM compliance_mappings 
            WHERE framework_id = ?
            ORDER BY control_id
        ''', (framework_id,))
        
        mappings = cursor.fetchall()
        
        # Generate report
        report = {
            'framework_id': framework_id,
            'assessment_date': assessment[3],
            'compliance_summary': {
                'total_controls': assessment[4],
                'compliant_controls': assessment[5],
                'compliance_rate': f"{(assessment[5]/assessment[4])*100:.1f}%"
            },
            'gaps_identified': json.loads(assessment[7]),
            'remediation_plan': json.loads(assessment[8]),
            'control_mappings': [
                {
                    'finding_type': mapping[1],
                    'finding_identifier': mapping[2],
                    'control_id': mapping[4],
                    'severity_impact': mapping[6],
                    'remediation_required': bool(mapping[7])
                }
                for mapping in mappings
            ],
            'recommendations': [
                "Implement automated compliance monitoring",
                "Regular security scanning aligned with controls",
                "Continuous control testing and validation",
                "Enhanced documentation and evidence collection"
            ]
        }
        
        conn.close()
        
        # Store report in Git
        report_file = Path(self.git_repo_path) / "reports" / f"compliance_report_{framework_id}_{datetime.now().strftime('%Y%m%d')}.yaml"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            yaml.dump(report, f, default_flow_style=False)
        
        # Commit to Git
        self.repo.index.add([str(report_file)])
        self.repo.index.commit(f"Add compliance report: {framework_id}")
        
        logger.info(f"📋 Generated compliance report: {report_file}")
        return str(report_file)
