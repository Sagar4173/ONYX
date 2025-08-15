"""
Security Orchestration, Automation and Response (SOAR) System
Orchestrates scanning, alerting, remediation, and threat containment
"""
import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AutomationStatus(Enum):
    """Automation execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ResponseAction(Enum):
    """Available response actions"""
    BLOCK_MERGE = "block_merge"
    CREATE_TICKET = "create_ticket"
    SEND_ALERT = "send_alert"
    QUARANTINE_CODE = "quarantine_code"
    AUTO_REMEDIATE = "auto_remediate"
    ESCALATE = "escalate"
    NOTIFY_TEAM = "notify_team"

@dataclass
class SecurityIncident:
    """Security incident data"""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    source: str  # e.g., "vulnerability_scan", "compliance_check", "anomaly_detection"
    repository: str
    branch: str = "main"
    commit_hash: Optional[str] = None
    file_paths: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "open"
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    external_ticket_id: Optional[str] = None

@dataclass
class PlaybookStep:
    """SOAR playbook step"""
    step_id: str
    name: str
    action: ResponseAction
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    depends_on: List[str] = field(default_factory=list)

@dataclass
class SOARPlaybook:
    """Security orchestration playbook"""
    playbook_id: str
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)  # Conditions that trigger this playbook
    steps: List[PlaybookStep] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_executed: Optional[datetime] = None
    execution_count: int = 0

@dataclass
class AutomationExecution:
    """SOAR automation execution record"""
    execution_id: str
    playbook_id: str
    incident_id: str
    status: AutomationStatus
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)

class SOAREngine:
    """Security Orchestration, Automation and Response Engine"""
    
    def __init__(self, data_dir: str = "soar_data"):
        """Initialize SOAR engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.soar_db_path = self.data_dir / "soar.db"
        
        # Configuration
        self.config = self._load_config()
        
        # Active executions
        self.active_executions: Dict[str, AutomationExecution] = {}
        
        # Integration clients
        self.integrations = self._init_integrations()
        
        # Default playbooks
        self.default_playbooks = self._create_default_playbooks()
        
        # Initialize database
        self._init_database()
        
        # Load playbooks
        asyncio.create_task(self._load_playbooks())
    
    def _load_config(self) -> Dict[str, Any]:
        """Load SOAR configuration"""
        return {
            "jira": {
                "url": "https://company.atlassian.net",
                "username": "soar-bot@company.com",
                "api_token": "your-jira-api-token",
                "project_key": "SEC"
            },
            "email": {
                "smtp_server": "smtp.company.com",
                "smtp_port": 587,
                "username": "alerts@company.com",
                "password": "email-password",
                "from_address": "alerts@company.com"
            },
            "slack": {
                "webhook_url": "https://hooks.slack.com/services/your/webhook/url",
                "security_channel": "#security-alerts"
            },
            "teams": {
                "webhook_url": "https://company.webhook.office.com/webhookb2/your-webhook-url",
                "security_channel": "Security Team"
            },
            "pagerduty": {
                "integration_key": "your-pagerduty-integration-key",
                "service_id": "your-service-id"
            },
            "severity_thresholds": {
                "critical": 9.0,
                "high": 7.0,
                "medium": 4.0,
                "low": 0.0
            },
            "auto_remediation": {
                "enabled": True,
                "max_attempts": 3,
                "quarantine_branch_prefix": "security-quarantine"
            }
        }
    
    def _init_integrations(self) -> Dict[str, Any]:
        """Initialize external integrations"""
        return {
            "jira_client": None,  # Would initialize Jira client
            "email_client": None,  # Would initialize email client
            "git_client": None    # Would initialize Git client
        }
    
    def _init_database(self):
        """Initialize SOAR database"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS security_incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    branch TEXT,
                    commit_hash TEXT,
                    file_paths TEXT,           -- JSON array
                    findings TEXT,             -- JSON array
                    created_at TEXT,
                    updated_at TEXT,
                    status TEXT,
                    assigned_to TEXT,
                    tags TEXT,                 -- JSON array
                    external_ticket_id TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS soar_playbooks (
                    playbook_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    triggers TEXT,             -- JSON array
                    steps TEXT,                -- JSON array of steps
                    enabled BOOLEAN,
                    created_at TEXT,
                    last_executed TEXT,
                    execution_count INTEGER
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS automation_executions (
                    execution_id TEXT PRIMARY KEY,
                    playbook_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    steps_completed TEXT,      -- JSON array
                    steps_failed TEXT,         -- JSON array
                    error_message TEXT,
                    results TEXT,              -- JSON object
                    FOREIGN KEY (playbook_id) REFERENCES soar_playbooks (playbook_id),
                    FOREIGN KEY (incident_id) REFERENCES security_incidents (incident_id)
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON security_incidents(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON automation_executions(status)")
                
        except Exception as e:
            logger.error(f"Failed to initialize SOAR database: {e}")
            raise
    
    def _create_default_playbooks(self) -> List[SOARPlaybook]:
        """Create default SOAR playbooks"""
        playbooks = []
        
        # Critical Vulnerability Response
        critical_vuln_playbook = SOARPlaybook(
            playbook_id="critical-vulnerability-response",
            name="Critical Vulnerability Response",
            description="Automated response for critical security vulnerabilities",
            triggers=["severity:critical", "source:vulnerability_scan"],
            steps=[
                PlaybookStep(
                    step_id="block-merge",
                    name="Block Merge Request",
                    action=ResponseAction.BLOCK_MERGE,
                    parameters={"reason": "Critical vulnerability detected"}
                ),
                PlaybookStep(
                    step_id="create-ticket",
                    name="Create Security Ticket",
                    action=ResponseAction.CREATE_TICKET,
                    parameters={
                        "priority": "Critical",
                        "assignee": "security-team",
                        "labels": ["security", "vulnerability", "critical"]
                    }
                ),
                PlaybookStep(
                    step_id="notify-team",
                    name="Notify Security Team",
                    action=ResponseAction.NOTIFY_TEAM,
                    parameters={
                        "channels": ["slack", "email"],
                        "urgency": "high"
                    }
                ),
                PlaybookStep(
                    step_id="quarantine",
                    name="Quarantine Code",
                    action=ResponseAction.QUARANTINE_CODE,
                    parameters={"create_branch": True}
                )
            ]
        )
        playbooks.append(critical_vuln_playbook)
        
        # Compliance Violation Response
        compliance_playbook = SOARPlaybook(
            playbook_id="compliance-violation-response",
            name="Compliance Violation Response",
            description="Automated response for compliance violations",
            triggers=["source:compliance_check", "severity:high"],
            steps=[
                PlaybookStep(
                    step_id="create-compliance-ticket",
                    name="Create Compliance Ticket",
                    action=ResponseAction.CREATE_TICKET,
                    parameters={
                        "priority": "High",
                        "assignee": "compliance-team",
                        "labels": ["compliance", "violation"]
                    }
                ),
                PlaybookStep(
                    step_id="send-alert",
                    name="Send Compliance Alert",
                    action=ResponseAction.SEND_ALERT,
                    parameters={
                        "recipients": ["compliance@company.com"],
                        "template": "compliance_violation"
                    }
                )
            ]
        )
        playbooks.append(compliance_playbook)
        
        # Secret Detection Response
        secret_detection_playbook = SOARPlaybook(
            playbook_id="secret-detection-response",
            name="Secret Detection Response",
            description="Automated response for exposed secrets",
            triggers=["finding_type:secret", "severity:high"],
            steps=[
                PlaybookStep(
                    step_id="immediate-block",
                    name="Immediately Block Merge",
                    action=ResponseAction.BLOCK_MERGE,
                    parameters={"reason": "Exposed secret detected - SECURITY RISK"}
                ),
                PlaybookStep(
                    step_id="create-urgent-ticket",
                    name="Create Urgent Security Ticket",
                    action=ResponseAction.CREATE_TICKET,
                    parameters={
                        "priority": "Urgent",
                        "assignee": "security-team",
                        "labels": ["security", "secret-exposure", "urgent"]
                    }
                ),
                PlaybookStep(
                    step_id="escalate-immediately",
                    name="Escalate to Security Lead",
                    action=ResponseAction.ESCALATE,
                    parameters={
                        "escalation_level": "security_lead",
                        "method": "immediate"
                    }
                ),
                PlaybookStep(
                    step_id="auto-remediate",
                    name="Attempt Auto-Remediation",
                    action=ResponseAction.AUTO_REMEDIATE,
                    parameters={
                        "remediation_type": "secret_removal",
                        "create_pr": True
                    }
                )
            ]
        )
        playbooks.append(secret_detection_playbook)
        
        return playbooks
    
    async def _load_playbooks(self):
        """Load playbooks into database"""
        try:
            for playbook in self.default_playbooks:
                await self._store_playbook(playbook)
                
        except Exception as e:
            logger.error(f"Failed to load default playbooks: {e}")
    
    async def create_incident(self, incident_data: Dict[str, Any]) -> str:
        """Create new security incident"""
        try:
            # Determine severity based on findings
            severity = self._calculate_incident_severity(incident_data)
            
            incident = SecurityIncident(
                incident_id=str(uuid.uuid4()),
                title=incident_data["title"],
                description=incident_data.get("description", ""),
                severity=severity,
                source=incident_data["source"],
                repository=incident_data["repository"],
                branch=incident_data.get("branch", "main"),
                commit_hash=incident_data.get("commit_hash"),
                file_paths=incident_data.get("file_paths", []),
                findings=incident_data.get("findings", [])
            )
            
            # Store incident
            await self._store_incident(incident)
            
            # Trigger automated response
            await self._trigger_automated_response(incident)
            
            logger.info(f"Created security incident: {incident.incident_id}")
            return incident.incident_id
            
        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            raise
    
    def _calculate_incident_severity(self, incident_data: Dict[str, Any]) -> IncidentSeverity:
        """Calculate incident severity based on findings"""
        findings = incident_data.get("findings", [])
        
        if not findings:
            return IncidentSeverity.LOW
        
        max_score = 0.0
        for finding in findings:
            score = finding.get("score", 0.0)
            max_score = max(max_score, score)
        
        thresholds = self.config["severity_thresholds"]
        
        if max_score >= thresholds["critical"]:
            return IncidentSeverity.CRITICAL
        elif max_score >= thresholds["high"]:
            return IncidentSeverity.HIGH
        elif max_score >= thresholds["medium"]:
            return IncidentSeverity.MEDIUM
        else:
            return IncidentSeverity.LOW
    
    async def _trigger_automated_response(self, incident: SecurityIncident):
        """Trigger automated response playbooks"""
        try:
            # Find matching playbooks
            matching_playbooks = await self._find_matching_playbooks(incident)
            
            for playbook in matching_playbooks:
                # Execute playbook
                execution_id = await self._execute_playbook(playbook.playbook_id, incident.incident_id)
                logger.info(f"Triggered playbook {playbook.name} for incident {incident.incident_id}")
                
        except Exception as e:
            logger.error(f"Failed to trigger automated response: {e}")
    
    async def _find_matching_playbooks(self, incident: SecurityIncident) -> List[SOARPlaybook]:
        """Find playbooks that match incident triggers"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM soar_playbooks WHERE enabled = 1"
                )
                rows = cursor.fetchall()
            
            matching_playbooks = []
            
            for row in rows:
                triggers = json.loads(row[3]) if row[3] else []
                
                # Check if incident matches triggers
                if self._incident_matches_triggers(incident, triggers):
                    playbook = SOARPlaybook(
                        playbook_id=row[0],
                        name=row[1],
                        description=row[2],
                        triggers=triggers,
                        steps=self._parse_playbook_steps(json.loads(row[4]) if row[4] else []),
                        enabled=bool(row[5]),
                        created_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(timezone.utc),
                        last_executed=datetime.fromisoformat(row[7]) if row[7] else None,
                        execution_count=row[8] or 0
                    )
                    matching_playbooks.append(playbook)
            
            return matching_playbooks
            
        except Exception as e:
            logger.error(f"Failed to find matching playbooks: {e}")
            return []
    
    def _incident_matches_triggers(self, incident: SecurityIncident, triggers: List[str]) -> bool:
        """Check if incident matches playbook triggers"""
        for trigger in triggers:
            if ":" in trigger:
                key, value = trigger.split(":", 1)
                
                if key == "severity" and incident.severity.value == value:
                    return True
                elif key == "source" and incident.source == value:
                    return True
                elif key == "finding_type":
                    # Check if any finding matches the type
                    for finding in incident.findings:
                        if finding.get("type") == value:
                            return True
            
        return False
    
    def _parse_playbook_steps(self, steps_data: List[Dict[str, Any]]) -> List[PlaybookStep]:
        """Parse playbook steps from JSON data"""
        steps = []
        for step_data in steps_data:
            step = PlaybookStep(
                step_id=step_data["step_id"],
                name=step_data["name"],
                action=ResponseAction(step_data["action"]),
                parameters=step_data.get("parameters", {}),
                conditions=step_data.get("conditions", []),
                timeout_seconds=step_data.get("timeout_seconds", 300),
                retry_count=step_data.get("retry_count", 0),
                depends_on=step_data.get("depends_on", [])
            )
            steps.append(step)
        return steps
    
    async def _execute_playbook(self, playbook_id: str, incident_id: str) -> str:
        """Execute SOAR playbook"""
        try:
            execution = AutomationExecution(
                execution_id=str(uuid.uuid4()),
                playbook_id=playbook_id,
                incident_id=incident_id,
                status=AutomationStatus.RUNNING
            )
            
            self.active_executions[execution.execution_id] = execution
            
            # Store execution record
            await self._store_execution(execution)
            
            # Execute steps
            await self._execute_playbook_steps(execution)
            
            return execution.execution_id
            
        except Exception as e:
            logger.error(f"Failed to execute playbook: {e}")
            raise
    
    async def _execute_playbook_steps(self, execution: AutomationExecution):
        """Execute playbook steps"""
        try:
            # Get playbook and incident
            playbook = await self._get_playbook(execution.playbook_id)
            incident = await self._get_incident(execution.incident_id)
            
            if not playbook or not incident:
                execution.status = AutomationStatus.FAILED
                execution.error_message = "Playbook or incident not found"
                await self._update_execution(execution)
                return
            
            # Execute steps in order
            for step in playbook.steps:
                try:
                    # Check dependencies
                    if step.depends_on:
                        if not all(dep in execution.steps_completed for dep in step.depends_on):
                            continue  # Skip step, dependencies not met
                    
                    # Execute step
                    result = await self._execute_step(step, incident, execution)
                    
                    if result.get("success", False):
                        execution.steps_completed.append(step.step_id)
                        execution.results[step.step_id] = result
                    else:
                        execution.steps_failed.append(step.step_id)
                        execution.results[step.step_id] = result
                        
                        # Handle step failure
                        if result.get("critical", False):
                            execution.status = AutomationStatus.FAILED
                            execution.error_message = result.get("error", "Critical step failed")
                            break
                    
                except Exception as step_error:
                    logger.error(f"Step {step.step_id} failed: {step_error}")
                    execution.steps_failed.append(step.step_id)
                    execution.results[step.step_id] = {
                        "success": False,
                        "error": str(step_error)
                    }
            
            # Complete execution
            if execution.status == AutomationStatus.RUNNING:
                execution.status = AutomationStatus.COMPLETED
            
            execution.completed_at = datetime.now(timezone.utc)
            await self._update_execution(execution)
            
            logger.info(f"Playbook execution completed: {execution.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute playbook steps: {e}")
            execution.status = AutomationStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            await self._update_execution(execution)
    
    async def _execute_step(self, step: PlaybookStep, incident: SecurityIncident,
                          execution: AutomationExecution) -> Dict[str, Any]:
        """Execute individual playbook step"""
        try:
            if step.action == ResponseAction.BLOCK_MERGE:
                return await self._block_merge_request(step, incident)
            elif step.action == ResponseAction.CREATE_TICKET:
                return await self._create_external_ticket(step, incident)
            elif step.action == ResponseAction.SEND_ALERT:
                return await self._send_security_alert(step, incident)
            elif step.action == ResponseAction.QUARANTINE_CODE:
                return await self._quarantine_code(step, incident)
            elif step.action == ResponseAction.AUTO_REMEDIATE:
                return await self._attempt_auto_remediation(step, incident)
            elif step.action == ResponseAction.ESCALATE:
                return await self._escalate_incident(step, incident)
            elif step.action == ResponseAction.NOTIFY_TEAM:
                return await self._notify_security_team(step, incident)
            else:
                return {"success": False, "error": f"Unknown action: {step.action}"}
                
        except Exception as e:
            logger.error(f"Failed to execute step {step.step_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _block_merge_request(self, step: PlaybookStep, 
                                 incident: SecurityIncident) -> Dict[str, Any]:
        """Block merge request"""
        try:
            reason = step.parameters.get("reason", "Security issue detected")
            
            # Mock implementation - would integrate with Git provider
            block_result = {
                "blocked": True,
                "repository": incident.repository,
                "branch": incident.branch,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Blocked merge for {incident.repository}:{incident.branch} - {reason}")
            
            return {
                "success": True,
                "action": "merge_blocked",
                "details": block_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_external_ticket(self, step: PlaybookStep,
                                    incident: SecurityIncident) -> Dict[str, Any]:
        """Create ticket in external system (Jira, etc.)"""
        try:
            ticket_data = {
                "title": f"Security Issue: {incident.title}",
                "description": incident.description,
                "priority": step.parameters.get("priority", "Medium"),
                "assignee": step.parameters.get("assignee", "security-team"),
                "labels": step.parameters.get("labels", []),
                "repository": incident.repository,
                "severity": incident.severity.value,
                "incident_id": incident.incident_id
            }
            
            # Mock ticket creation - would integrate with actual system
            ticket_id = f"SEC-{uuid.uuid4().hex[:8].upper()}"
            
            # Update incident with ticket ID
            incident.external_ticket_id = ticket_id
            await self._update_incident(incident)
            
            logger.info(f"Created external ticket {ticket_id} for incident {incident.incident_id}")
            
            return {
                "success": True,
                "action": "ticket_created",
                "ticket_id": ticket_id,
                "details": ticket_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_security_alert(self, step: PlaybookStep,
                                 incident: SecurityIncident) -> Dict[str, Any]:
        """Send security alert"""
        try:
            recipients = step.parameters.get("recipients", ["security@company.com"])
            template = step.parameters.get("template", "default")
            
            alert_data = {
                "incident_id": incident.incident_id,
                "title": incident.title,
                "severity": incident.severity.value,
                "repository": incident.repository,
                "description": incident.description,
                "timestamp": incident.created_at.isoformat()
            }
            
            # Mock alert sending - would integrate with actual systems
            logger.info(f"Sent security alert to {recipients} for incident {incident.incident_id}")
            
            return {
                "success": True,
                "action": "alert_sent",
                "recipients": recipients,
                "template": template,
                "details": alert_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _quarantine_code(self, step: PlaybookStep,
                             incident: SecurityIncident) -> Dict[str, Any]:
        """Quarantine suspicious code"""
        try:
            create_branch = step.parameters.get("create_branch", True)
            branch_prefix = self.config["auto_remediation"]["quarantine_branch_prefix"]
            
            if create_branch:
                quarantine_branch = f"{branch_prefix}-{incident.incident_id[:8]}"
                
                # Mock branch creation - would integrate with Git
                quarantine_result = {
                    "quarantine_branch": quarantine_branch,
                    "source_branch": incident.branch,
                    "repository": incident.repository,
                    "files_quarantined": incident.file_paths
                }
                
                logger.info(f"Quarantined code to branch {quarantine_branch}")
                
                return {
                    "success": True,
                    "action": "code_quarantined",
                    "details": quarantine_result
                }
            
            return {"success": True, "action": "quarantine_skipped"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _attempt_auto_remediation(self, step: PlaybookStep,
                                      incident: SecurityIncident) -> Dict[str, Any]:
        """Attempt automatic remediation"""
        try:
            if not self.config["auto_remediation"]["enabled"]:
                return {"success": False, "error": "Auto-remediation disabled"}
            
            remediation_type = step.parameters.get("remediation_type", "generic")
            create_pr = step.parameters.get("create_pr", False)
            
            # Mock remediation - would implement actual fixes
            remediation_result = {
                "type": remediation_type,
                "files_modified": incident.file_paths,
                "repository": incident.repository,
                "branch": incident.branch
            }
            
            if create_pr:
                pr_id = f"auto-fix-{incident.incident_id[:8]}"
                remediation_result["pull_request"] = pr_id
            
            logger.info(f"Applied auto-remediation for incident {incident.incident_id}")
            
            return {
                "success": True,
                "action": "auto_remediated",
                "details": remediation_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _escalate_incident(self, step: PlaybookStep,
                               incident: SecurityIncident) -> Dict[str, Any]:
        """Escalate incident to higher authority"""
        try:
            escalation_level = step.parameters.get("escalation_level", "manager")
            method = step.parameters.get("method", "email")
            
            escalation_data = {
                "incident_id": incident.incident_id,
                "escalation_level": escalation_level,
                "escalation_reason": f"Security incident severity: {incident.severity.value}",
                "original_assignee": incident.assigned_to,
                "escalated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Mock escalation - would integrate with notification systems
            logger.info(f"Escalated incident {incident.incident_id} to {escalation_level}")
            
            return {
                "success": True,
                "action": "incident_escalated",
                "details": escalation_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _notify_security_team(self, step: PlaybookStep,
                                  incident: SecurityIncident) -> Dict[str, Any]:
        """Notify security team"""
        try:
            channels = step.parameters.get("channels", ["email"])
            urgency = step.parameters.get("urgency", "medium")
            
            notification_data = {
                "incident_id": incident.incident_id,
                "title": incident.title,
                "severity": incident.severity.value,
                "urgency": urgency,
                "repository": incident.repository,
                "channels": channels
            }
            
            # Mock notification - would integrate with Slack, Teams, etc.
            logger.info(f"Notified security team via {channels} for incident {incident.incident_id}")
            
            return {
                "success": True,
                "action": "team_notified",
                "details": notification_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _store_incident(self, incident: SecurityIncident):
        """Store incident in database"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO security_incidents (
                    incident_id, title, description, severity, source,
                    repository, branch, commit_hash, file_paths, findings,
                    created_at, updated_at, status, assigned_to, tags,
                    external_ticket_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident.incident_id,
                    incident.title,
                    incident.description,
                    incident.severity.value,
                    incident.source,
                    incident.repository,
                    incident.branch,
                    incident.commit_hash,
                    json.dumps(incident.file_paths),
                    json.dumps(incident.findings),
                    incident.created_at.isoformat(),
                    incident.updated_at.isoformat(),
                    incident.status,
                    incident.assigned_to,
                    json.dumps(incident.tags),
                    incident.external_ticket_id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store incident: {e}")
            raise
    
    async def _update_incident(self, incident: SecurityIncident):
        """Update incident in database"""
        try:
            incident.updated_at = datetime.now(timezone.utc)
            with sqlite3.connect(self.soar_db_path) as conn:
                conn.execute("""
                UPDATE security_incidents SET
                    title = ?, description = ?, severity = ?, status = ?,
                    assigned_to = ?, tags = ?, external_ticket_id = ?, updated_at = ?
                WHERE incident_id = ?
                """, (
                    incident.title,
                    incident.description,
                    incident.severity.value,
                    incident.status,
                    incident.assigned_to,
                    json.dumps(incident.tags),
                    incident.external_ticket_id,
                    incident.updated_at.isoformat(),
                    incident.incident_id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update incident: {e}")
            raise
    
    async def _store_playbook(self, playbook: SOARPlaybook):
        """Store playbook in database"""
        try:
            # Convert steps to JSON
            steps_json = []
            for step in playbook.steps:
                step_dict = {
                    "step_id": step.step_id,
                    "name": step.name,
                    "action": step.action.value,
                    "parameters": step.parameters,
                    "conditions": step.conditions,
                    "timeout_seconds": step.timeout_seconds,
                    "retry_count": step.retry_count,
                    "depends_on": step.depends_on
                }
                steps_json.append(step_dict)
            
            with sqlite3.connect(self.soar_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO soar_playbooks (
                    playbook_id, name, description, triggers, steps,
                    enabled, created_at, last_executed, execution_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    playbook.playbook_id,
                    playbook.name,
                    playbook.description,
                    json.dumps(playbook.triggers),
                    json.dumps(steps_json),
                    playbook.enabled,
                    playbook.created_at.isoformat(),
                    playbook.last_executed.isoformat() if playbook.last_executed else None,
                    playbook.execution_count
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store playbook: {e}")
            raise
    
    async def _store_execution(self, execution: AutomationExecution):
        """Store execution in database"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO automation_executions (
                    execution_id, playbook_id, incident_id, status,
                    started_at, completed_at, steps_completed, steps_failed,
                    error_message, results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.playbook_id,
                    execution.incident_id,
                    execution.status.value,
                    execution.started_at.isoformat(),
                    execution.completed_at.isoformat() if execution.completed_at else None,
                    json.dumps(execution.steps_completed),
                    json.dumps(execution.steps_failed),
                    execution.error_message,
                    json.dumps(execution.results)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
            raise
    
    async def _update_execution(self, execution: AutomationExecution):
        """Update execution in database"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                conn.execute("""
                UPDATE automation_executions SET
                    status = ?, completed_at = ?, steps_completed = ?,
                    steps_failed = ?, error_message = ?, results = ?
                WHERE execution_id = ?
                """, (
                    execution.status.value,
                    execution.completed_at.isoformat() if execution.completed_at else None,
                    json.dumps(execution.steps_completed),
                    json.dumps(execution.steps_failed),
                    execution.error_message,
                    json.dumps(execution.results),
                    execution.execution_id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update execution: {e}")
            raise
    
    async def _get_playbook(self, playbook_id: str) -> Optional[SOARPlaybook]:
        """Get playbook by ID"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM soar_playbooks WHERE playbook_id = ?",
                    (playbook_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return SOARPlaybook(
                        playbook_id=row[0],
                        name=row[1],
                        description=row[2],
                        triggers=json.loads(row[3]) if row[3] else [],
                        steps=self._parse_playbook_steps(json.loads(row[4]) if row[4] else []),
                        enabled=bool(row[5]),
                        created_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(timezone.utc),
                        last_executed=datetime.fromisoformat(row[7]) if row[7] else None,
                        execution_count=row[8] or 0
                    )
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get playbook: {e}")
            return None
    
    async def _get_incident(self, incident_id: str) -> Optional[SecurityIncident]:
        """Get incident by ID"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM security_incidents WHERE incident_id = ?",
                    (incident_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return SecurityIncident(
                        incident_id=row[0],
                        title=row[1],
                        description=row[2],
                        severity=IncidentSeverity(row[3]),
                        source=row[4],
                        repository=row[5],
                        branch=row[6],
                        commit_hash=row[7],
                        file_paths=json.loads(row[8]) if row[8] else [],
                        findings=json.loads(row[9]) if row[9] else [],
                        created_at=datetime.fromisoformat(row[10]),
                        updated_at=datetime.fromisoformat(row[11]),
                        status=row[12],
                        assigned_to=row[13],
                        tags=json.loads(row[14]) if row[14] else [],
                        external_ticket_id=row[15]
                    )
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get incident: {e}")
            return None
    
    async def get_soar_dashboard(self) -> Dict[str, Any]:
        """Get SOAR dashboard data"""
        try:
            with sqlite3.connect(self.soar_db_path) as conn:
                # Get incident statistics
                cursor = conn.execute("""
                SELECT severity, status, COUNT(*) as count
                FROM security_incidents
                GROUP BY severity, status
                """)
                incident_stats = cursor.fetchall()
                
                # Get execution statistics
                cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM automation_executions
                GROUP BY status
                """)
                execution_stats = cursor.fetchall()
                
                # Get recent incidents
                cursor = conn.execute("""
                SELECT incident_id, title, severity, status, created_at
                FROM security_incidents
                ORDER BY created_at DESC
                LIMIT 10
                """)
                recent_incidents = cursor.fetchall()
            
            dashboard = {
                "incident_statistics": {
                    "by_severity": {},
                    "by_status": {},
                    "total": 0
                },
                "execution_statistics": {
                    "by_status": {},
                    "total": 0
                },
                "recent_incidents": [],
                "active_executions": len(self.active_executions),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Process incident statistics
            for severity, status, count in incident_stats:
                if severity not in dashboard["incident_statistics"]["by_severity"]:
                    dashboard["incident_statistics"]["by_severity"][severity] = 0
                if status not in dashboard["incident_statistics"]["by_status"]:
                    dashboard["incident_statistics"]["by_status"][status] = 0
                
                dashboard["incident_statistics"]["by_severity"][severity] += count
                dashboard["incident_statistics"]["by_status"][status] += count
                dashboard["incident_statistics"]["total"] += count
            
            # Process execution statistics
            for status, count in execution_stats:
                dashboard["execution_statistics"]["by_status"][status] = count
                dashboard["execution_statistics"]["total"] += count
            
            # Process recent incidents
            for incident in recent_incidents:
                dashboard["recent_incidents"].append({
                    "incident_id": incident[0],
                    "title": incident[1],
                    "severity": incident[2],
                    "status": incident[3],
                    "created_at": incident[4]
                })
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to get SOAR dashboard: {e}")
            return {"error": str(e)}

# Export main classes
__all__ = [
    'SOAREngine', 'SecurityIncident', 'SOARPlaybook', 'PlaybookStep',
    'AutomationExecution', 'IncidentSeverity', 'ResponseAction', 'AutomationStatus'
]
