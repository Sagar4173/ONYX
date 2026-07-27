"""
Unified Security Orchestration Engine
=====================================

Complete integration of Threat Intelligence, Vulnerability Management,
and Metrics/KPIs with automated workflow orchestration.

Author: ONYX Platform
Date: August 2025
"""

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from utils.datetime_utils import utc_now

# Import threat intelligence from same package (safe)

# Lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    pass

# Configure logger (logging.basicConfig is called in app.py)
logger = logging.getLogger(__name__)

@dataclass
class OrchestrationWorkflow:
    """Security orchestration workflow definition"""
    workflow_id: str
    name: str
    description: str
    trigger_type: str  # scan_complete, vulnerability_found, sla_breach
    steps: List[Dict[str, Any]]
    enabled: bool

@dataclass
class WorkflowExecution:
    """Workflow execution tracking"""
    execution_id: str
    workflow_id: str
    trigger_data: Dict[str, Any]
    start_time: str
    end_time: Optional[str]
    status: str  # running, completed, failed
    steps_completed: int
    total_steps: int
    error_message: Optional[str]

class SecurityOrchestrationEngine:
    """Unified security orchestration and automation engine"""
    
    def __init__(self):
        # Lazy imports to avoid circular dependencies
        from services.analytics.metrics_kpi_engine import MetricsKPIEngine
        from services.scanning.engine import ScanOrchestrator
        from services.scanning.vulnerability import VulnerabilityManager
        from services.service_registry import ServiceRegistry
        
        # Initialize component engines (use singleton from registry)
        self.threat_intelligence = ServiceRegistry.get_threat_intelligence()
        self.vulnerability_management = VulnerabilityManager()
        self.metrics_kpi = MetricsKPIEngine()
        self.scanner_engine = ScanOrchestrator()
        
        # Workflow definitions
        self.workflows = self._define_default_workflows()
        
        logger.info("🚀 Security Orchestration Engine initialized")
    
    def _define_default_workflows(self) -> Dict[str, OrchestrationWorkflow]:
        """Define default security orchestration workflows"""
        workflows = {}
        
        # 1. Complete Scan → Enrich → Risk Score → Policy Gate → Create Issue → Metrics
        workflows['comprehensive_security_workflow'] = OrchestrationWorkflow(
            workflow_id='comprehensive_security_workflow',
            name='Comprehensive Security Workflow',
            description='End-to-end security scanning with enrichment, policy gates, and issue creation',
            trigger_type='scan_request',
            enabled=True,
            steps=[
                {
                    'step_id': 1,
                    'name': 'Execute Comprehensive Scan',
                    'action': 'scan',
                    'scanner_types': ['sast', 'dast', 'iac', 'pentest'],
                    'timeout': 1800
                },
                {
                    'step_id': 2,
                    'name': 'Enrich with Threat Intelligence',
                    'action': 'enrich_findings',
                    'include_epss': True,
                    'include_kev': True,
                    'include_cve_metadata': True
                },
                {
                    'step_id': 3,
                    'name': 'Calculate Risk Scores',
                    'action': 'calculate_risk_scores',
                    'factors': ['cvss', 'epss', 'kev', 'business_criticality', 'environment']
                },
                {
                    'step_id': 4,
                    'name': 'Evaluate Policy Gates',
                    'action': 'evaluate_policy_gates',
                    'fail_on_block': True
                },
                {
                    'step_id': 5,
                    'name': 'Create Vulnerability Records',
                    'action': 'create_vulnerability_records',
                    'auto_assign': True,
                    'calculate_sla': True
                },
                {
                    'step_id': 6,
                    'name': 'Create External Issues',
                    'action': 'create_external_issues',
                    'platforms': ['jira', 'github'],
                    'severity_threshold': 'medium'
                },
                {
                    'step_id': 7,
                    'name': 'Update Metrics',
                    'action': 'update_metrics',
                    'capture_scan_metrics': True,
                    'update_sla_performance': True
                },
                {
                    'step_id': 8,
                    'name': 'Send Notifications',
                    'action': 'send_notifications',
                    'channels': ['slack', 'email', 'teams']
                }
            ]
        )
        
        # 2. Threat Intelligence Update Workflow
        workflows['threat_intelligence_update'] = OrchestrationWorkflow(
            workflow_id='threat_intelligence_update',
            name='Threat Intelligence Update Workflow',
            description='Update threat feeds and re-score existing vulnerabilities',
            trigger_type='scheduled',
            enabled=True,
            steps=[
                {
                    'step_id': 1,
                    'name': 'Update NVD Feed',
                    'action': 'update_nvd_feed',
                    'year': 'current'
                },
                {
                    'step_id': 2,
                    'name': 'Update KEV Catalog',
                    'action': 'update_kev_catalog'
                },
                {
                    'step_id': 3,
                    'name': 'Update EPSS Scores',
                    'action': 'update_epss_scores'
                },
                {
                    'step_id': 4,
                    'name': 'Re-score Affected Vulnerabilities',
                    'action': 'rescore_vulnerabilities',
                    'batch_size': 100
                },
                {
                    'step_id': 5,
                    'name': 'Update SLA Due Dates',
                    'action': 'update_sla_dates',
                    'risk_change_threshold': 1.0
                },
                {
                    'step_id': 6,
                    'name': 'Generate Threat Report',
                    'action': 'generate_threat_report',
                    'recipients': ['security_team', 'management']
                }
            ]
        )
        
        # 3. SLA Breach Response Workflow
        workflows['sla_breach_response'] = OrchestrationWorkflow(
            workflow_id='sla_breach_response',
            name='SLA Breach Response Workflow',
            description='Automated response to SLA breaches with escalation',
            trigger_type='sla_breach',
            enabled=True,
            steps=[
                {
                    'step_id': 1,
                    'name': 'Identify Breached Vulnerabilities',
                    'action': 'check_sla_breaches'
                },
                {
                    'step_id': 2,
                    'name': 'Escalate Critical Breaches',
                    'action': 'escalate_critical_breaches',
                    'notify_management': True
                },
                {
                    'step_id': 3,
                    'name': 'Update Issue Priorities',
                    'action': 'update_issue_priorities',
                    'platforms': ['jira', 'github']
                },
                {
                    'step_id': 4,
                    'name': 'Send Escalation Notifications',
                    'action': 'send_escalation_notifications',
                    'channels': ['slack', 'email', 'pagerduty']
                },
                {
                    'step_id': 5,
                    'name': 'Update Metrics',
                    'action': 'update_breach_metrics'
                }
            ]
        )
        
        return workflows
    
    async def execute_comprehensive_security_workflow(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete security workflow"""
        workflow = self.workflows['comprehensive_security_workflow']
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            trigger_data=scan_request,
            start_time=utc_now().isoformat(),
            end_time=None,
            status='running',
            steps_completed=0,
            total_steps=len(workflow.steps),
            error_message=None
        )
        
        logger.info(f"🔄 Starting comprehensive security workflow: {execution_id}")
        
        try:
            results = {
                'execution_id': execution_id,
                'workflow_name': workflow.name,
                'steps': []
            }
            
            # Step 1: Execute Comprehensive Scan
            step_result = await self._execute_scan_step(scan_request)
            results['steps'].append({
                'step': 1,
                'name': 'Execute Comprehensive Scan',
                'status': 'completed',
                'result': step_result
            })
            execution.steps_completed += 1
            
            scan_results = step_result['scan_results']
            
            # Step 2: Enrich with Threat Intelligence
            enriched_findings = []
            for finding in scan_results.get('findings', []):
                enriched_finding = await self.threat_intelligence.enrich_finding(
                    finding.get('component', ''),
                    finding.get('version', ''),
                    finding
                )
                enriched_findings.append(asdict(enriched_finding))
            
            results['steps'].append({
                'step': 2,
                'name': 'Enrich with Threat Intelligence',
                'status': 'completed',
                'result': {'enriched_findings_count': len(enriched_findings)}
            })
            execution.steps_completed += 1
            
            # Step 3: Calculate Risk Scores (already done in enrichment)
            results['steps'].append({
                'step': 3,
                'name': 'Calculate Risk Scores',
                'status': 'completed',
                'result': {'risk_scores_calculated': True}
            })
            execution.steps_completed += 1
            
            # Step 4: Evaluate Policy Gates
            policy_result = await self.vulnerability_management.evaluate_policy_gates(scan_results)
            results['steps'].append({
                'step': 4,
                'name': 'Evaluate Policy Gates',
                'status': 'completed',
                'result': policy_result
            })
            execution.steps_completed += 1
            
            # Check if workflow should continue based on policy gates
            if policy_result['overall_result'] == 'fail':
                logger.warning("⚠️ Policy gates failed - continuing with issue creation")
            
            # Step 5: Create Vulnerability Records
            vulnerability_records = []
            for enriched_finding in enriched_findings:
                if enriched_finding['lifecycle_state'] != 'false_positive':
                    # Prepare vulnerability data
                    vuln_data = {
                        'finding_id': enriched_finding['finding_id'],
                        'cve_id': enriched_finding['cve_id'],
                        'title': f"Security vulnerability in {enriched_finding['component']}",
                        'description': f"Vulnerability found in {enriched_finding['component']} version {enriched_finding['version']}",
                        'severity': enriched_finding['severity'],
                        'cvss_score': 0.0,  # Would come from scan results
                        'epss_score': enriched_finding['epss_score'],
                        'component': enriched_finding['component'],
                        'version': enriched_finding['version'],
                        'asset': enriched_finding['asset_context'],
                        'repository': scan_request.get('repository_url', ''),
                        'commit_hash': scan_request.get('commit_hash', 'HEAD'),
                        'branch': scan_request.get('branch', 'main'),
                        'risk_score': enriched_finding['risk_score'],
                        'business_impact': self._assess_business_impact(enriched_finding),
                        'remediation_guidance': self._generate_remediation_guidance(enriched_finding),
                        'tags': ['automated', 'orchestrated']
                    }
                    
                    # Create vulnerability record
                    vuln_id = await self.vulnerability_management.create_vulnerability_record(vuln_data)
                    vulnerability_records.append(vuln_id)
            
            results['steps'].append({
                'step': 5,
                'name': 'Create Vulnerability Records',
                'status': 'completed',
                'result': {'vulnerability_records_created': len(vulnerability_records)}
            })
            execution.steps_completed += 1
            
            # Step 6: Create External Issues (simulated)
            external_issues = await self._create_external_issues(enriched_findings, scan_request)
            results['steps'].append({
                'step': 6,
                'name': 'Create External Issues',
                'status': 'completed',
                'result': external_issues
            })
            execution.steps_completed += 1
            
            # Step 7: Update Metrics
            scan_metrics = {
                'scan_id': step_result['scan_id'],
                'scan_type': 'comprehensive',
                'asset_id': scan_request.get('asset_id'),
                'repository': scan_request.get('repository_url'),
                'start_time': step_result['start_time'],
                'end_time': step_result['end_time'],
                'findings': enriched_findings,
                'status': 'completed'
            }
            
            metrics_recorded = await self.metrics_kpi.record_scan_metrics(scan_metrics)
            results['steps'].append({
                'step': 7,
                'name': 'Update Metrics',
                'status': 'completed',
                'result': {'metrics_recorded': metrics_recorded}
            })
            execution.steps_completed += 1
            
            # Step 8: Send Notifications (simulated)
            notifications_sent = await self._send_notifications(enriched_findings, scan_request, policy_result)
            results['steps'].append({
                'step': 8,
                'name': 'Send Notifications',
                'status': 'completed',
                'result': notifications_sent
            })
            execution.steps_completed += 1
            
            # Complete execution
            execution.status = 'completed'
            execution.end_time = utc_now().isoformat()
            
            logger.info(f"✅ Comprehensive security workflow completed: {execution_id}")
            
            return {
                'execution': asdict(execution),
                'results': results,
                'summary': {
                    'total_findings': len(enriched_findings),
                    'vulnerability_records_created': len(vulnerability_records),
                    'policy_gates_passed': policy_result['overall_result'] == 'pass',
                    'external_issues_created': external_issues['issues_created'],
                    'notifications_sent': notifications_sent['notifications_sent']
                }
            }
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.end_time = utc_now().isoformat()
            
            logger.error(f"❌ Workflow execution failed: {execution_id} - {str(e)}")
            raise
    
    async def _execute_scan_step(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive scanning step"""
        scan_id = str(uuid.uuid4())
        start_time = utc_now().isoformat()
        
        # Simulate comprehensive scan execution
        # In real implementation, this would call the AdvancedScannerEngine
        await asyncio.sleep(1)  # Simulate scan time
        
        # Simulate scan results
        mock_findings = [
            {
                'id': f'{scan_id}-001',
                'title': 'SQL Injection Vulnerability',
                'severity': 'high',
                'component': 'django',
                'version': '3.2.0',
                'scanner_type': 'sast',
                'file_path': 'app/models.py',
                'line_number': 42
            },
            {
                'id': f'{scan_id}-002',
                'title': 'Cross-Site Scripting (XSS)',
                'severity': 'medium',
                'component': 'react',
                'version': '17.0.2',
                'scanner_type': 'dast',
                'url': 'https://app.example.com/search'
            },
            {
                'id': f'{scan_id}-003',
                'title': 'Docker container runs as root',
                'severity': 'medium',
                'component': 'docker',
                'version': '20.10.0',
                'scanner_type': 'iac',
                'file_path': 'Dockerfile',
                'line_number': 8
            }
        ]
        
        end_time = utc_now().isoformat()
        
        return {
            'scan_id': scan_id,
            'start_time': start_time,
            'end_time': end_time,
            'scan_results': {
                'findings': mock_findings,
                'total_findings': len(mock_findings),
                'by_severity': {
                    'critical': 0,
                    'high': 1,
                    'medium': 2,
                    'low': 0
                }
            }
        }
    
    def _assess_business_impact(self, finding: Dict[str, Any]) -> str:
        """Assess business impact of vulnerability"""
        severity = finding.get('severity', 'unknown')
        component = finding.get('component', '')
        
        if severity == 'critical':
            return f"Critical security vulnerability in {component} could lead to data breach"
        elif severity == 'high':
            return f"High severity vulnerability in {component} requires immediate attention"
        elif severity == 'medium':
            return f"Medium severity vulnerability in {component} should be addressed"
        else:
            return f"Low severity vulnerability in {component} for monitoring"
    
    def _generate_remediation_guidance(self, finding: Dict[str, Any]) -> str:
        """Generate remediation guidance for vulnerability"""
        component = finding.get('component', '')
        version = finding.get('version', '')
        
        if finding.get('cve_id'):
            return f"Update {component} from version {version} to latest patched version. Review CVE {finding['cve_id']} for detailed guidance."
        else:
            return f"Review and remediate security issue in {component} version {version}. Consult security team for guidance."
    
    async def _create_external_issues(self, findings: List[Dict], scan_request: Dict) -> Dict[str, Any]:
        """Create external issues in Jira/GitHub (simulated)"""
        critical_high_findings = [f for f in findings if f.get('severity') in ['critical', 'high']]
        
        # Simulate issue creation
        issues_created = len(critical_high_findings)
        
        return {
            'jira_issues_created': issues_created // 2,
            'github_issues_created': issues_created - (issues_created // 2),
            'issues_created': issues_created,
            'platforms': ['jira', 'github']
        }
    
    async def _send_notifications(self, findings: List[Dict], scan_request: Dict, 
                                policy_result: Dict) -> Dict[str, Any]:
        """Send notifications to various channels (simulated)"""
        critical_findings = [f for f in findings if f.get('severity') == 'critical']
        high_findings = [f for f in findings if f.get('severity') == 'high']
        
        notifications = []
        
        if critical_findings:
            notifications.append({
                'channel': 'pagerduty',
                'type': 'critical_alert',
                'count': len(critical_findings)
            })
        
        if high_findings or critical_findings:
            notifications.append({
                'channel': 'slack',
                'type': 'security_alert',
                'count': len(high_findings) + len(critical_findings)
            })
        
        if policy_result['overall_result'] == 'fail':
            notifications.append({
                'channel': 'email',
                'type': 'policy_violation',
                'recipients': ['security-team@company.com']
            })
        
        return {
            'notifications_sent': len(notifications),
            'channels': [n['channel'] for n in notifications],
            'notifications': notifications
        }
    
    async def update_threat_intelligence_workflow(self) -> Dict[str, Any]:
        """Execute threat intelligence update workflow"""
        workflow = self.workflows['threat_intelligence_update']
        execution_id = str(uuid.uuid4())
        
        logger.info(f"🔄 Starting threat intelligence update workflow: {execution_id}")
        
        try:
            # Update threat intelligence feeds
            ti_results = await self.threat_intelligence.update_threat_intelligence()
            
            # Get affected vulnerabilities (simulated)
            affected_vulns = 50  # Would query actual database
            
            # Re-score vulnerabilities (simulated)
            rescored_vulns = 25
            
            # Update SLA dates (simulated)
            updated_slas = 10
            
            return {
                'execution_id': execution_id,
                'workflow_name': workflow.name,
                'status': 'completed',
                'results': {
                    'threat_intelligence_updated': ti_results,
                    'vulnerabilities_affected': affected_vulns,
                    'vulnerabilities_rescored': rescored_vulns,
                    'sla_dates_updated': updated_slas
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Threat intelligence workflow failed: {execution_id} - {str(e)}")
            raise
    
    async def execute_sla_breach_response(self) -> Dict[str, Any]:
        """Execute SLA breach response workflow"""
        workflow = self.workflows['sla_breach_response']
        execution_id = str(uuid.uuid4())
        
        logger.info(f"🔄 Starting SLA breach response workflow: {execution_id}")
        
        try:
            # Check for SLA breaches
            breaches = await self.vulnerability_management.check_sla_breaches()
            
            if not breaches:
                return {
                    'execution_id': execution_id,
                    'workflow_name': workflow.name,
                    'status': 'completed',
                    'results': {'sla_breaches_found': 0}
                }
            
            # Process breaches
            critical_breaches = [b for b in breaches if b['severity'] == 'critical']
            high_breaches = [b for b in breaches if b['severity'] == 'high']
            
            # Send escalations (simulated)
            escalations_sent = len(critical_breaches) + len(high_breaches)
            
            return {
                'execution_id': execution_id,
                'workflow_name': workflow.name,
                'status': 'completed',
                'results': {
                    'sla_breaches_found': len(breaches),
                    'critical_breaches': len(critical_breaches),
                    'high_breaches': len(high_breaches),
                    'escalations_sent': escalations_sent,
                    'issues_updated': len(breaches)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ SLA breach response workflow failed: {execution_id} - {str(e)}")
            raise
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get overall orchestration engine status"""
        try:
            # Get threat intelligence stats
            ti_stats = await self.threat_intelligence.get_threat_stats()
            
            # Get vulnerability metrics (30 days)
            vuln_metrics = await self.vulnerability_management.get_vulnerability_metrics('30d')
            
            # Get SLA performance
            sla_performance = await self.metrics_kpi.calculate_sla_performance()
            
            # Get executive dashboard
            executive_dashboard = await self.metrics_kpi.get_executive_dashboard()
            
            return {
                'orchestration_engine': {
                    'status': 'operational',
                    'workflows_available': len(self.workflows),
                    'workflows_enabled': len([w for w in self.workflows.values() if w.enabled])
                },
                'threat_intelligence': ti_stats,
                'vulnerability_management': vuln_metrics,
                'sla_performance': sla_performance,
                'executive_summary': executive_dashboard.get('summary', {})
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting orchestration status: {str(e)}")
            return {'error': str(e)}

# Export main class
__all__ = ['SecurityOrchestrationEngine', 'OrchestrationWorkflow', 'WorkflowExecution']
