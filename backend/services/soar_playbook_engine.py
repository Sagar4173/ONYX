"""
SOAR Playbook Engine
===================

Security Orchestration, Automation, and Response (SOAR) playbooks for
automated incident response, remediation workflows, and real-time alerting.

Author: SecureDevOpsAI Platform  
Date: August 2025
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import subprocess
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlaybookAction:
    """Individual SOAR playbook action"""
    action_id: str
    action_type: str  # notification, remediation, investigation, escalation
    name: str
    description: str
    parameters: Dict[str, Any]
    timeout_seconds: int
    retry_count: int
    conditions: List[str]  # Conditions for execution

@dataclass
class PlaybookWorkflow:
    """Complete SOAR playbook workflow"""
    playbook_id: str
    name: str
    description: str
    trigger_conditions: List[str]
    severity_threshold: str
    actions: List[PlaybookAction]
    parallel_execution: bool
    enabled: bool
    created_by: str
    created_date: str

@dataclass
class PlaybookExecution:
    """SOAR playbook execution instance"""
    execution_id: str
    playbook_id: str
    trigger_event: Dict[str, Any]
    start_time: str
    end_time: Optional[str]
    status: str  # running, completed, failed, cancelled
    executed_actions: List[Dict[str, Any]]
    execution_log: List[str]
    success_rate: float

@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    channel_id: str
    channel_type: str  # email, slack, teams, webhook, sms
    name: str
    configuration: Dict[str, Any]
    enabled: bool

class SOARPlaybookEngine:
    """Security Orchestration, Automation, and Response (SOAR) playbook engine"""
    
    def __init__(self, db_path: str = "soar_playbooks.db",
                 playbooks_path: str = "soar_playbooks"):
        self.db_path = db_path
        self.playbooks_path = Path(playbooks_path)
        self.playbooks_path.mkdir(exist_ok=True)
        
        self.active_executions = {}
        self.notification_channels = {}
        self.action_handlers = {}
        
        self._init_database()
        self._init_action_handlers()
        self._load_notification_channels()
        
        logger.info("🤖 SOAR Playbook Engine initialized")
    
    def _init_database(self):
        """Initialize SOAR playbooks database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Playbooks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playbooks (
                playbook_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                trigger_conditions_json TEXT,
                severity_threshold TEXT,
                actions_json TEXT,
                parallel_execution BOOLEAN,
                enabled BOOLEAN DEFAULT TRUE,
                created_by TEXT,
                created_date TEXT,
                last_modified TEXT
            )
        ''')
        
        # Playbook executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playbook_executions (
                execution_id TEXT PRIMARY KEY,
                playbook_id TEXT,
                trigger_event_json TEXT,
                start_time TEXT,
                end_time TEXT,
                status TEXT,
                executed_actions_json TEXT,
                execution_log_json TEXT,
                success_rate REAL,
                FOREIGN KEY (playbook_id) REFERENCES playbooks (playbook_id)
            )
        ''')
        
        # Notification channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_channels (
                channel_id TEXT PRIMARY KEY,
                channel_type TEXT NOT NULL,
                name TEXT,
                configuration_json TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                created_date TEXT
            )
        ''')
        
        # Remediation actions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remediation_actions (
                action_id TEXT PRIMARY KEY,
                execution_id TEXT,
                action_type TEXT,
                target_asset TEXT,
                action_details_json TEXT,
                status TEXT,
                timestamp TEXT,
                result_json TEXT,
                FOREIGN KEY (execution_id) REFERENCES playbook_executions (execution_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("🗄️ SOAR playbooks database initialized")
    
    def _init_action_handlers(self):
        """Initialize action handlers for different types of SOAR actions"""
        self.action_handlers = {
            'notification': self._handle_notification_action,
            'email_notification': self._handle_email_notification,
            'slack_notification': self._handle_slack_notification,
            'teams_notification': self._handle_teams_notification,
            'webhook_notification': self._handle_webhook_notification,
            'block_ip': self._handle_block_ip_action,
            'quarantine_file': self._handle_quarantine_file_action,
            'disable_user': self._handle_disable_user_action,
            'create_ticket': self._handle_create_ticket_action,
            'scan_asset': self._handle_scan_asset_action,
            'deploy_patch': self._handle_deploy_patch_action,
            'isolate_system': self._handle_isolate_system_action,
            'escalate_incident': self._handle_escalate_incident_action,
            'custom_script': self._handle_custom_script_action
        }
    
    def _load_notification_channels(self):
        """Load notification channels from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM notification_channels WHERE enabled = TRUE')
        channels = cursor.fetchall()
        
        for channel_row in channels:
            channel = NotificationChannel(
                channel_id=channel_row[0],
                channel_type=channel_row[1],
                name=channel_row[2],
                configuration=json.loads(channel_row[3]) if channel_row[3] else {},
                enabled=bool(channel_row[4])
            )
            self.notification_channels[channel.channel_id] = channel
        
        conn.close()
        logger.info(f"📡 Loaded {len(self.notification_channels)} notification channels")
    
    async def create_playbook(self, workflow: PlaybookWorkflow) -> str:
        """Create a new SOAR playbook"""
        logger.info(f"📝 Creating SOAR playbook: {workflow.name}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO playbooks
            (playbook_id, name, description, trigger_conditions_json,
             severity_threshold, actions_json, parallel_execution, enabled,
             created_by, created_date, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow.playbook_id, workflow.name, workflow.description,
            json.dumps(workflow.trigger_conditions), workflow.severity_threshold,
            json.dumps([asdict(action) for action in workflow.actions]),
            workflow.parallel_execution, workflow.enabled, workflow.created_by,
            workflow.created_date, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Save playbook YAML file
        playbook_file = self.playbooks_path / f"{workflow.playbook_id}.yaml"
        with open(playbook_file, 'w') as f:
            yaml.dump(asdict(workflow), f, default_flow_style=False, indent=2)
        
        logger.info(f"✅ SOAR playbook created: {workflow.playbook_id}")
        return workflow.playbook_id
    
    async def trigger_playbook(self, event: Dict[str, Any]) -> List[str]:
        """Trigger SOAR playbooks based on event"""
        logger.info(f"🚨 Triggering SOAR playbooks for event: {event.get('type', 'unknown')}")
        
        triggered_executions = []
        
        # Find matching playbooks
        matching_playbooks = await self._find_matching_playbooks(event)
        
        for playbook in matching_playbooks:
            execution_id = await self._execute_playbook(playbook, event)
            if execution_id:
                triggered_executions.append(execution_id)
        
        logger.info(f"🎯 Triggered {len(triggered_executions)} playbook executions")
        return triggered_executions
    
    async def _find_matching_playbooks(self, event: Dict[str, Any]) -> List[PlaybookWorkflow]:
        """Find playbooks that match the event conditions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM playbooks WHERE enabled = TRUE')
        playbook_rows = cursor.fetchall()
        conn.close()
        
        matching_playbooks = []
        
        for row in playbook_rows:
            playbook = PlaybookWorkflow(
                playbook_id=row[0],
                name=row[1],
                description=row[2],
                trigger_conditions=json.loads(row[3]) if row[3] else [],
                severity_threshold=row[4],
                actions=[PlaybookAction(**action_data) for action_data in json.loads(row[5])],
                parallel_execution=bool(row[6]),
                enabled=bool(row[7]),
                created_by=row[8],
                created_date=row[9]
            )
            
            if await self._evaluate_trigger_conditions(playbook, event):
                matching_playbooks.append(playbook)
        
        return matching_playbooks
    
    async def _evaluate_trigger_conditions(self, playbook: PlaybookWorkflow, 
                                          event: Dict[str, Any]) -> bool:
        """Evaluate if playbook trigger conditions are met"""
        # Check severity threshold
        event_severity = event.get('severity', 'LOW').upper()
        threshold = playbook.severity_threshold.upper()
        
        severity_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if severity_order.index(event_severity) < severity_order.index(threshold):
            return False
        
        # Check trigger conditions
        for condition in playbook.trigger_conditions:
            if not self._evaluate_condition(condition, event):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: str, event: Dict[str, Any]) -> bool:
        """Evaluate a single trigger condition"""
        try:
            # Simple condition evaluation (can be enhanced with more complex logic)
            if condition.startswith('event_type='):
                expected_type = condition.split('=')[1]
                return event.get('type') == expected_type
            
            elif condition.startswith('finding_count>'):
                threshold = int(condition.split('>')[1])
                return event.get('finding_count', 0) > threshold
            
            elif condition.startswith('anomaly_detected'):
                return event.get('anomaly_detected', False)
            
            elif condition.startswith('critical_vulnerability'):
                return event.get('severity') == 'CRITICAL'
            
            elif condition.startswith('new_cve'):
                return 'cve_id' in event and event.get('is_new_cve', False)
            
            # Default: condition is met
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Condition evaluation failed: {condition} - {e}")
            return False
    
    async def _execute_playbook(self, playbook: PlaybookWorkflow, 
                               event: Dict[str, Any]) -> Optional[str]:
        """Execute a SOAR playbook"""
        execution_id = f"exec_{playbook.playbook_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution = PlaybookExecution(
            execution_id=execution_id,
            playbook_id=playbook.playbook_id,
            trigger_event=event,
            start_time=datetime.now().isoformat(),
            end_time=None,
            status="running",
            executed_actions=[],
            execution_log=[f"Playbook execution started: {playbook.name}"],
            success_rate=0.0
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            logger.info(f"🚀 Executing playbook: {playbook.name} ({execution_id})")
            
            if playbook.parallel_execution:
                # Execute actions in parallel
                tasks = [self._execute_action(action, event, execution) for action in playbook.actions]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Execute actions sequentially
                results = []
                for action in playbook.actions:
                    result = await self._execute_action(action, event, execution)
                    results.append(result)
            
            # Calculate success rate
            successful_actions = sum(1 for result in results if isinstance(result, dict) and result.get('success'))
            execution.success_rate = successful_actions / len(results) if results else 0.0
            execution.status = "completed"
            execution.end_time = datetime.now().isoformat()
            
            # Store execution results
            await self._store_execution_results(execution)
            
            logger.info(f"✅ Playbook execution completed: {execution_id} (Success rate: {execution.success_rate:.1%})")
            
        except Exception as e:
            execution.status = "failed"
            execution.end_time = datetime.now().isoformat()
            execution.execution_log.append(f"Execution failed: {str(e)}")
            logger.error(f"❌ Playbook execution failed: {execution_id} - {e}")
            
            await self._store_execution_results(execution)
        
        finally:
            # Remove from active executions
            self.active_executions.pop(execution_id, None)
        
        return execution_id
    
    async def _execute_action(self, action: PlaybookAction, event: Dict[str, Any],
                             execution: PlaybookExecution) -> Dict[str, Any]:
        """Execute a single SOAR action"""
        logger.info(f"⚡ Executing action: {action.name} ({action.action_type})")
        
        # Check action conditions
        for condition in action.conditions:
            if not self._evaluate_condition(condition, event):
                return {"success": False, "reason": f"Condition not met: {condition}"}
        
        # Execute action with retry logic
        for attempt in range(action.retry_count + 1):
            try:
                # Get action handler
                handler = self.action_handlers.get(action.action_type)
                if not handler:
                    return {"success": False, "reason": f"Unknown action type: {action.action_type}"}
                
                # Execute action with timeout
                result = await asyncio.wait_for(
                    handler(action, event, execution),
                    timeout=action.timeout_seconds
                )
                
                # Log successful execution
                execution.executed_actions.append({
                    "action_id": action.action_id,
                    "action_type": action.action_type,
                    "timestamp": datetime.now().isoformat(),
                    "result": result
                })
                execution.execution_log.append(f"Action completed: {action.name}")
                
                return result
                
            except asyncio.TimeoutError:
                execution.execution_log.append(f"Action timeout: {action.name} (attempt {attempt + 1})")
                if attempt == action.retry_count:
                    return {"success": False, "reason": "Timeout"}
                
            except Exception as e:
                execution.execution_log.append(f"Action failed: {action.name} - {str(e)} (attempt {attempt + 1})")
                if attempt == action.retry_count:
                    return {"success": False, "reason": str(e)}
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {"success": False, "reason": "All retry attempts failed"}
    
    # Action Handlers
    async def _handle_notification_action(self, action: PlaybookAction, 
                                         event: Dict[str, Any], 
                                         execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle generic notification action"""
        message = action.parameters.get('message', 'SOAR notification triggered')
        channels = action.parameters.get('channels', [])
        
        results = []
        for channel_id in channels:
            if channel_id in self.notification_channels:
                channel = self.notification_channels[channel_id]
                result = await self._send_notification(channel, message, event)
                results.append(result)
        
        return {"success": all(r.get('success', False) for r in results), "results": results}
    
    async def _handle_email_notification(self, action: PlaybookAction,
                                        event: Dict[str, Any],
                                        execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle email notification action"""
        try:
            recipients = action.parameters.get('recipients', [])
            subject = action.parameters.get('subject', 'Security Alert')
            template = action.parameters.get('template', 'basic_alert')
            
            # Generate email content
            content = self._generate_email_content(template, event, execution)
            
            # Simulate email sending (replace with actual SMTP in production)
            logger.info(f"📧 Sending email to {len(recipients)} recipients: {subject}")
            
            return {
                "success": True,
                "action": "email_sent",
                "recipients": recipients,
                "subject": subject
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_slack_notification(self, action: PlaybookAction,
                                        event: Dict[str, Any],
                                        execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle Slack notification action"""
        try:
            webhook_url = action.parameters.get('webhook_url')
            channel = action.parameters.get('channel', '#security-alerts')
            message = action.parameters.get('message', 'Security incident detected')
            
            # Simulate Slack notification (replace with actual Slack API in production)
            logger.info(f"💬 Sending Slack notification to {channel}: {message}")
            
            return {
                "success": True,
                "action": "slack_notification_sent",
                "channel": channel
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_teams_notification(self, action: PlaybookAction,
                                        event: Dict[str, Any],
                                        execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle Microsoft Teams notification action"""
        try:
            webhook_url = action.parameters.get('webhook_url')
            message = action.parameters.get('message', 'Security incident detected')
            
            # Simulate Teams notification
            logger.info(f"🎯 Sending Teams notification: {message}")
            
            return {
                "success": True,
                "action": "teams_notification_sent"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_webhook_notification(self, action: PlaybookAction,
                                          event: Dict[str, Any],
                                          execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle webhook notification action"""
        try:
            webhook_url = action.parameters.get('webhook_url')
            payload = {
                "event": event,
                "execution_id": execution.execution_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Simulate webhook call
            logger.info(f"🔗 Sending webhook notification to {webhook_url}")
            
            return {
                "success": True,
                "action": "webhook_sent",
                "url": webhook_url
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_block_ip_action(self, action: PlaybookAction,
                                     event: Dict[str, Any],
                                     execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle IP blocking action"""
        try:
            ip_address = action.parameters.get('ip_address', event.get('source_ip'))
            firewall_rule = action.parameters.get('firewall_rule', 'block_all')
            
            # Simulate IP blocking
            logger.info(f"🚫 Blocking IP address: {ip_address}")
            
            return {
                "success": True,
                "action": "ip_blocked",
                "ip_address": ip_address,
                "rule": firewall_rule
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_quarantine_file_action(self, action: PlaybookAction,
                                            event: Dict[str, Any],
                                            execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle file quarantine action"""
        try:
            file_path = action.parameters.get('file_path', event.get('file_path'))
            quarantine_location = action.parameters.get('quarantine_location', '/quarantine/')
            
            # Simulate file quarantine
            logger.info(f"🔒 Quarantining file: {file_path}")
            
            return {
                "success": True,
                "action": "file_quarantined",
                "file_path": file_path,
                "quarantine_location": quarantine_location
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_disable_user_action(self, action: PlaybookAction,
                                         event: Dict[str, Any],
                                         execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle user account disable action"""
        try:
            username = action.parameters.get('username', event.get('username'))
            disable_reason = action.parameters.get('reason', 'Security incident')
            
            # Simulate user disable
            logger.info(f"👤 Disabling user account: {username}")
            
            return {
                "success": True,
                "action": "user_disabled",
                "username": username,
                "reason": disable_reason
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_create_ticket_action(self, action: PlaybookAction,
                                          event: Dict[str, Any],
                                          execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle ticket creation action"""
        try:
            ticket_system = action.parameters.get('ticket_system', 'jira')
            priority = action.parameters.get('priority', 'high')
            assignee = action.parameters.get('assignee', 'security-team')
            
            # Generate ticket details
            ticket_id = f"SEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"🎫 Creating security ticket: {ticket_id}")
            
            return {
                "success": True,
                "action": "ticket_created",
                "ticket_id": ticket_id,
                "system": ticket_system,
                "priority": priority
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_scan_asset_action(self, action: PlaybookAction,
                                       event: Dict[str, Any],
                                       execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle asset scanning action"""
        try:
            asset_id = action.parameters.get('asset_id', event.get('asset_id'))
            scan_type = action.parameters.get('scan_type', 'vulnerability')
            
            # Simulate asset scan
            logger.info(f"🔍 Initiating {scan_type} scan for asset: {asset_id}")
            
            return {
                "success": True,
                "action": "scan_initiated",
                "asset_id": asset_id,
                "scan_type": scan_type
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_deploy_patch_action(self, action: PlaybookAction,
                                         event: Dict[str, Any],
                                         execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle patch deployment action"""
        try:
            asset_id = action.parameters.get('asset_id', event.get('asset_id'))
            patch_id = action.parameters.get('patch_id', event.get('cve_id'))
            
            # Simulate patch deployment
            logger.info(f"🔧 Deploying patch {patch_id} to asset: {asset_id}")
            
            return {
                "success": True,
                "action": "patch_deployed",
                "asset_id": asset_id,
                "patch_id": patch_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_isolate_system_action(self, action: PlaybookAction,
                                           event: Dict[str, Any],
                                           execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle system isolation action"""
        try:
            system_id = action.parameters.get('system_id', event.get('asset_id'))
            isolation_type = action.parameters.get('isolation_type', 'network')
            
            # Simulate system isolation
            logger.info(f"🚨 Isolating system: {system_id} ({isolation_type})")
            
            return {
                "success": True,
                "action": "system_isolated",
                "system_id": system_id,
                "isolation_type": isolation_type
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_escalate_incident_action(self, action: PlaybookAction,
                                              event: Dict[str, Any],
                                              execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle incident escalation action"""
        try:
            escalation_level = action.parameters.get('escalation_level', 'level_2')
            notify_users = action.parameters.get('notify_users', ['security-manager'])
            
            # Simulate incident escalation
            logger.info(f"📈 Escalating incident to {escalation_level}")
            
            return {
                "success": True,
                "action": "incident_escalated",
                "escalation_level": escalation_level,
                "notified_users": notify_users
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_custom_script_action(self, action: PlaybookAction,
                                          event: Dict[str, Any],
                                          execution: PlaybookExecution) -> Dict[str, Any]:
        """Handle custom script execution action"""
        try:
            script_path = action.parameters.get('script_path')
            script_args = action.parameters.get('args', [])
            
            # Simulate custom script execution
            logger.info(f"🖥️ Executing custom script: {script_path}")
            
            return {
                "success": True,
                "action": "custom_script_executed",
                "script_path": script_path,
                "args": script_args
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_notification(self, channel: NotificationChannel, 
                                message: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification through specified channel"""
        try:
            if channel.channel_type == 'email':
                # Simulate email notification
                logger.info(f"📧 Email notification sent via {channel.name}")
                return {"success": True, "channel": channel.name}
            
            elif channel.channel_type == 'slack':
                # Simulate Slack notification
                logger.info(f"💬 Slack notification sent via {channel.name}")
                return {"success": True, "channel": channel.name}
            
            elif channel.channel_type == 'teams':
                # Simulate Teams notification
                logger.info(f"🎯 Teams notification sent via {channel.name}")
                return {"success": True, "channel": channel.name}
            
            else:
                return {"success": False, "error": f"Unsupported channel type: {channel.channel_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_email_content(self, template: str, event: Dict[str, Any],
                               execution: PlaybookExecution) -> str:
        """Generate email content from template"""
        if template == 'basic_alert':
            return f"""
Security Alert - SOAR Automation

Event Type: {event.get('type', 'Unknown')}
Severity: {event.get('severity', 'Unknown')}
Timestamp: {event.get('timestamp', 'Unknown')}
Description: {event.get('description', 'No description available')}

Playbook Execution: {execution.execution_id}
Status: {execution.status}

This is an automated message from the SOAR system.
"""
        
        return "Security alert notification"
    
    async def _store_execution_results(self, execution: PlaybookExecution):
        """Store playbook execution results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO playbook_executions
            (execution_id, playbook_id, trigger_event_json, start_time,
             end_time, status, executed_actions_json, execution_log_json, success_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            execution.execution_id, execution.playbook_id,
            json.dumps(execution.trigger_event), execution.start_time,
            execution.end_time, execution.status,
            json.dumps(execution.executed_actions),
            json.dumps(execution.execution_log), execution.success_rate
        ))
        
        conn.commit()
        conn.close()
    
    async def get_soar_dashboard(self) -> Dict[str, Any]:
        """Generate SOAR dashboard with execution statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent executions
        cursor.execute('''
            SELECT * FROM playbook_executions
            WHERE start_time > datetime('now', '-7 days')
            ORDER BY start_time DESC
        ''')
        recent_executions = cursor.fetchall()
        
        # Get execution statistics
        cursor.execute('''
            SELECT status, COUNT(*) FROM playbook_executions
            WHERE start_time > datetime('now', '-30 days')
            GROUP BY status
        ''')
        execution_stats = dict(cursor.fetchall())
        
        # Get active playbooks
        cursor.execute('SELECT COUNT(*) FROM playbooks WHERE enabled = TRUE')
        active_playbooks = cursor.fetchone()[0]
        
        conn.close()
        
        dashboard = {
            "recent_executions": [
                {
                    "execution_id": row[0],
                    "playbook_id": row[1],
                    "status": row[4],
                    "success_rate": row[8],
                    "start_time": row[3]
                }
                for row in recent_executions[:10]
            ],
            "execution_statistics": execution_stats,
            "active_playbooks": active_playbooks,
            "active_executions": len(self.active_executions),
            "notification_channels": len(self.notification_channels),
            "total_recent_executions": len(recent_executions)
        }
        
        return dashboard
