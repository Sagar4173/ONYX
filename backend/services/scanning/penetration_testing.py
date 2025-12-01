"""
Penetration Testing Integration System
Automated pentests, red team simulation, security assessment automation
"""
import asyncio
import logging
import json
import sqlite3
import subprocess
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import yaml
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class PentestType(Enum):
    """Types of penetration tests"""
    AUTOMATED = "automated"
    MANUAL = "manual"
    RED_TEAM = "red_team"
    BLUE_TEAM = "blue_team"
    PURPLE_TEAM = "purple_team"
    BUG_BOUNTY = "bug_bounty"

class AttackVector(Enum):
    """Attack vectors for testing"""
    NETWORK = "network"
    WEB_APPLICATION = "web_application"
    SOCIAL_ENGINEERING = "social_engineering"
    PHYSICAL = "physical"
    WIRELESS = "wireless"
    CLOUD = "cloud"

class TestStatus(Enum):
    """Penetration test status"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PentestTarget:
    """Penetration test target"""
    target_id: str
    name: str
    description: str
    target_type: str  # host, application, network, etc.
    endpoints: List[str] = field(default_factory=list)
    credentials: Dict[str, str] = field(default_factory=dict)  # For authorized testing
    scope: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    environment: str = "staging"  # staging, development, production
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AttackPath:
    """Red team attack path"""
    path_id: str
    name: str
    description: str
    tactics: List[str] = field(default_factory=list)  # MITRE ATT&CK tactics
    techniques: List[str] = field(default_factory=list)  # MITRE ATT&CK techniques
    prerequisites: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    detection_opportunities: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard, expert
    estimated_duration: int = 60  # minutes

@dataclass
class PentestExecution:
    """Penetration test execution record"""
    execution_id: str
    test_type: PentestType
    target_id: str
    attack_vectors: List[AttackVector]
    status: TestStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    tools_used: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    attack_paths: List[str] = field(default_factory=list)  # Attack path IDs
    evidence: List[str] = field(default_factory=list)  # File paths to evidence
    report_path: Optional[str] = None
    operator: str = "automated"
    success_rate: float = 0.0
    risk_score: float = 0.0

class PenetrationTestingEngine:
    """Advanced penetration testing integration system"""
    
    def __init__(self, data_dir: str = "data/pentest"):
        """Initialize penetration testing engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.pentest_db_path = self.data_dir / "pentest.db"
        
        # Tools configuration
        self.tools_config = self._load_tools_config()
        
        # Attack paths
        self.attack_paths = self._load_attack_paths()
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize penetration testing database"""
        try:
            with sqlite3.connect(self.pentest_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS pentest_targets (
                    target_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    target_type TEXT,
                    endpoints TEXT,      -- JSON array
                    credentials TEXT,    -- JSON object (encrypted)
                    scope TEXT,         -- JSON array
                    exclusions TEXT,    -- JSON array
                    environment TEXT,
                    metadata TEXT,      -- JSON object
                    created_at TEXT,
                    updated_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS pentest_executions (
                    execution_id TEXT PRIMARY KEY,
                    test_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    attack_vectors TEXT,    -- JSON array
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration_minutes INTEGER,
                    tools_used TEXT,        -- JSON array
                    findings TEXT,          -- JSON array
                    attack_paths TEXT,      -- JSON array
                    evidence TEXT,          -- JSON array
                    report_path TEXT,
                    operator TEXT,
                    success_rate REAL,
                    risk_score REAL,
                    FOREIGN KEY (target_id) REFERENCES pentest_targets (target_id)
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS attack_paths (
                    path_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    tactics TEXT,           -- JSON array
                    techniques TEXT,        -- JSON array
                    prerequisites TEXT,     -- JSON array
                    steps TEXT,            -- JSON array
                    success_criteria TEXT, -- JSON array
                    detection_opportunities TEXT, -- JSON array
                    difficulty TEXT,
                    estimated_duration INTEGER
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON pentest_executions(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_type ON pentest_executions(test_type)")
                
        except Exception as e:
            logger.error(f"Failed to initialize pentest database: {e}")
            raise
    
    def _load_tools_config(self) -> Dict[str, Dict[str, Any]]:
        """Load penetration testing tools configuration"""
        return {
            "nmap": {
                "name": "Nmap Network Scanner",
                "category": "network_discovery",
                "command": "nmap",
                "default_args": ["-sV", "-sC", "-O"],
                "output_format": "xml",
                "timeout": 300
            },
            "zap": {
                "name": "OWASP ZAP",
                "category": "web_application",
                "command": "zap-baseline.py",
                "default_args": ["-t", "{target}", "-J", "{output}"],
                "output_format": "json",
                "timeout": 1800
            },
            "nuclei": {
                "name": "Nuclei Vulnerability Scanner",
                "category": "vulnerability_scanning",
                "command": "nuclei",
                "default_args": ["-u", "{target}", "-json", "-o", "{output}"],
                "output_format": "json",
                "timeout": 600
            },
            "metasploit": {
                "name": "Metasploit Framework",
                "category": "exploitation",
                "command": "msfconsole",
                "default_args": ["-r", "{script}"],
                "output_format": "text",
                "timeout": 1800
            },
            "gobuster": {
                "name": "Gobuster Directory Brute Forcer",
                "category": "web_discovery",
                "command": "gobuster",
                "default_args": ["dir", "-u", "{target}", "-w", "{wordlist}", "-o", "{output}"],
                "output_format": "text",
                "timeout": 900
            },
            "sqlmap": {
                "name": "SQLMap SQL Injection Tool",
                "category": "web_exploitation",
                "command": "sqlmap",
                "default_args": ["-u", "{target}", "--batch", "--output-dir", "{output}"],
                "output_format": "text",
                "timeout": 1200
            }
        }
    
    def _load_attack_paths(self) -> Dict[str, AttackPath]:
        """Load predefined attack paths"""
        return {
            "web_app_basic": AttackPath(
                path_id="web_app_basic",
                name="Basic Web Application Attack",
                description="Standard web application penetration test",
                tactics=["Initial Access", "Discovery", "Credential Access"],
                techniques=["T1190", "T1040", "T1552"],
                prerequisites=["Web application target", "Network connectivity"],
                steps=[
                    {"step": 1, "action": "Port scan", "tool": "nmap", "expected": "Open HTTP/HTTPS ports"},
                    {"step": 2, "action": "Web discovery", "tool": "gobuster", "expected": "Hidden directories"},
                    {"step": 3, "action": "Vulnerability scan", "tool": "nuclei", "expected": "Known vulnerabilities"},
                    {"step": 4, "action": "SQL injection test", "tool": "sqlmap", "expected": "Database access"},
                    {"step": 5, "action": "XSS testing", "tool": "zap", "expected": "Script execution"}
                ],
                success_criteria=["Valid vulnerability found", "Proof of concept created"],
                detection_opportunities=["Network scanning", "Failed login attempts", "Error messages"],
                difficulty="medium",
                estimated_duration=120
            ),
            "network_lateral": AttackPath(
                path_id="network_lateral",
                name="Network Lateral Movement",
                description="Internal network lateral movement simulation",
                tactics=["Lateral Movement", "Persistence", "Collection"],
                techniques=["T1021", "T1053", "T1005"],
                prerequisites=["Initial network access", "Valid credentials"],
                steps=[
                    {"step": 1, "action": "Network discovery", "tool": "nmap", "expected": "Live hosts identified"},
                    {"step": 2, "action": "Service enumeration", "tool": "nmap", "expected": "Running services"},
                    {"step": 3, "action": "Credential testing", "tool": "custom", "expected": "Valid access"},
                    {"step": 4, "action": "Privilege escalation", "tool": "metasploit", "expected": "Higher privileges"},
                    {"step": 5, "action": "Data collection", "tool": "custom", "expected": "Sensitive data found"}
                ],
                success_criteria=["Lateral movement achieved", "Persistence established"],
                detection_opportunities=["Unusual network traffic", "New process execution", "Account activity"],
                difficulty="hard",
                estimated_duration=180
            ),
            "supply_chain": AttackPath(
                path_id="supply_chain",
                name="Supply Chain Attack Simulation",
                description="Software supply chain compromise simulation",
                tactics=["Initial Access", "Defense Evasion", "Impact"],
                techniques=["T1195", "T1036", "T1496"],
                prerequisites=["Development environment access", "CI/CD pipeline"],
                steps=[
                    {"step": 1, "action": "Repository analysis", "tool": "custom", "expected": "Dependencies identified"},
                    {"step": 2, "action": "Vulnerable dependency", "tool": "nuclei", "expected": "Exploitable component"},
                    {"step": 3, "action": "Malicious package", "tool": "custom", "expected": "Package injection"},
                    {"step": 4, "action": "Build compromise", "tool": "custom", "expected": "Malicious build"},
                    {"step": 5, "action": "Distribution", "tool": "custom", "expected": "Compromised artifact"}
                ],
                success_criteria=["Malicious code in build", "Supply chain compromised"],
                detection_opportunities=["Package integrity checks", "Build anomalies", "Network beacons"],
                difficulty="expert",
                estimated_duration=240
            )
        }
    
    async def register_target(self, target: PentestTarget) -> bool:
        """Register penetration test target"""
        try:
            with sqlite3.connect(self.pentest_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO pentest_targets (
                    target_id, name, description, target_type, endpoints,
                    credentials, scope, exclusions, environment, metadata,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    target.target_id,
                    target.name,
                    target.description,
                    target.target_type,
                    json.dumps(target.endpoints),
                    json.dumps(target.credentials),  # Should be encrypted in production
                    json.dumps(target.scope),
                    json.dumps(target.exclusions),
                    target.environment,
                    json.dumps(target.metadata),
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
            
            logger.info(f"Registered pentest target: {target.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register pentest target: {e}")
            return False
    
    async def execute_automated_pentest(self, target_id: str, 
                                      test_type: PentestType = PentestType.AUTOMATED) -> str:
        """Execute automated penetration test"""
        try:
            execution_id = str(uuid.uuid4())
            
            # Get target information
            target = await self.get_target(target_id)
            if not target:
                raise ValueError(f"Target {target_id} not found")
            
            execution = PentestExecution(
                execution_id=execution_id,
                test_type=test_type,
                target_id=target_id,
                attack_vectors=[AttackVector.WEB_APPLICATION, AttackVector.NETWORK],
                status=TestStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                operator="automated_system"
            )
            
            # Store execution record
            await self._store_execution(execution)
            
            # Run tests based on target type
            if target["target_type"] == "web_application":
                await self._run_web_app_tests(execution, target)
            elif target["target_type"] == "network":
                await self._run_network_tests(execution, target)
            else:
                await self._run_generic_tests(execution, target)
            
            # Update execution status
            execution.status = TestStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_minutes = int((execution.completed_at - execution.started_at).total_seconds() / 60)
            execution.success_rate = self._calculate_success_rate(execution.findings)
            execution.risk_score = self._calculate_risk_score(execution.findings)
            
            await self._update_execution(execution)
            
            logger.info(f"Completed automated pentest: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to execute automated pentest: {e}")
            # Update execution status to failed
            if 'execution' in locals():
                execution.status = TestStatus.FAILED
                await self._update_execution(execution)
            raise
    
    async def execute_red_team_simulation(self, target_id: str, 
                                        attack_path_id: str) -> str:
        """Execute red team attack simulation"""
        try:
            execution_id = str(uuid.uuid4())
            
            # Get target and attack path
            target = await self.get_target(target_id)
            attack_path = self.attack_paths.get(attack_path_id)
            
            if not target or not attack_path:
                raise ValueError("Target or attack path not found")
            
            execution = PentestExecution(
                execution_id=execution_id,
                test_type=PentestType.RED_TEAM,
                target_id=target_id,
                attack_vectors=[AttackVector.NETWORK, AttackVector.WEB_APPLICATION],
                status=TestStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                attack_paths=[attack_path_id],
                operator="red_team"
            )
            
            await self._store_execution(execution)
            
            # Execute attack path steps
            for step in attack_path.steps:
                try:
                    result = await self._execute_attack_step(step, target, execution)
                    execution.findings.append({
                        "step": step["step"],
                        "action": step["action"],
                        "tool": step["tool"],
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Check success criteria
                    if any(criteria in result.get("output", "") for criteria in attack_path.success_criteria):
                        execution.findings[-1]["success"] = True
                    
                except Exception as e:
                    logger.warning(f"Attack step failed: {step['action']} - {e}")
                    execution.findings.append({
                        "step": step["step"],
                        "action": step["action"],
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            
            # Complete execution
            execution.status = TestStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_minutes = int((execution.completed_at - execution.started_at).total_seconds() / 60)
            execution.success_rate = self._calculate_attack_path_success(execution.findings)
            execution.risk_score = self._calculate_risk_score(execution.findings)
            
            await self._update_execution(execution)
            
            logger.info(f"Completed red team simulation: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to execute red team simulation: {e}")
            raise
    
    async def _run_web_app_tests(self, execution: PentestExecution, target: Dict[str, Any]):
        """Run web application specific tests"""
        try:
            endpoints = json.loads(target["endpoints"])
            
            for endpoint in endpoints:
                # ZAP baseline scan
                zap_result = await self._run_tool("zap", {"target": endpoint}, execution)
                if zap_result:
                    execution.findings.extend(zap_result.get("findings", []))
                    execution.tools_used.append("zap")
                
                # Nuclei vulnerability scan
                nuclei_result = await self._run_tool("nuclei", {"target": endpoint}, execution)
                if nuclei_result:
                    execution.findings.extend(nuclei_result.get("findings", []))
                    execution.tools_used.append("nuclei")
                
                # Directory discovery
                gobuster_result = await self._run_tool("gobuster", {
                    "target": endpoint,
                    "wordlist": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"
                }, execution)
                if gobuster_result:
                    execution.findings.extend(gobuster_result.get("findings", []))
                    execution.tools_used.append("gobuster")
                
        except Exception as e:
            logger.error(f"Failed to run web app tests: {e}")
    
    async def _run_network_tests(self, execution: PentestExecution, target: Dict[str, Any]):
        """Run network specific tests"""
        try:
            endpoints = json.loads(target["endpoints"])
            
            for endpoint in endpoints:
                # Network discovery
                nmap_result = await self._run_tool("nmap", {"target": endpoint}, execution)
                if nmap_result:
                    execution.findings.extend(nmap_result.get("findings", []))
                    execution.tools_used.append("nmap")
                
        except Exception as e:
            logger.error(f"Failed to run network tests: {e}")
    
    async def _run_generic_tests(self, execution: PentestExecution, target: Dict[str, Any]):
        """Run generic security tests"""
        try:
            endpoints = json.loads(target["endpoints"])
            
            # Run basic vulnerability scan
            for endpoint in endpoints:
                nuclei_result = await self._run_tool("nuclei", {"target": endpoint}, execution)
                if nuclei_result:
                    execution.findings.extend(nuclei_result.get("findings", []))
                    execution.tools_used.append("nuclei")
                
        except Exception as e:
            logger.error(f"Failed to run generic tests: {e}")
    
    async def _run_tool(self, tool_name: str, params: Dict[str, Any], 
                       execution: PentestExecution) -> Optional[Dict[str, Any]]:
        """Run penetration testing tool"""
        try:
            tool_config = self.tools_config.get(tool_name)
            if not tool_config:
                logger.warning(f"Tool {tool_name} not configured")
                return None
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{tool_config["output_format"]}', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Build command
            command = [tool_config["command"]]
            for arg in tool_config["default_args"]:
                if "{target}" in arg:
                    command.append(arg.replace("{target}", params["target"]))
                elif "{output}" in arg:
                    command.append(arg.replace("{output}", output_path))
                elif "{wordlist}" in arg and "wordlist" in params:
                    command.append(arg.replace("{wordlist}", params["wordlist"]))
                else:
                    command.append(arg)
            
            # Execute tool (mock implementation for safety)
            logger.info(f"Would execute: {' '.join(command)}")
            
            # Mock results for demonstration
            mock_result = {
                "tool": tool_name,
                "target": params["target"],
                "findings": [
                    {
                        "type": "vulnerability",
                        "severity": "medium",
                        "title": f"Mock finding from {tool_name}",
                        "description": f"Simulated vulnerability detected by {tool_name}",
                        "location": params["target"],
                        "evidence": f"Mock evidence from tool execution"
                    }
                ],
                "execution_time": 30,
                "output_file": output_path
            }
            
            return mock_result
            
        except Exception as e:
            logger.error(f"Failed to run tool {tool_name}: {e}")
            return None
    
    async def _execute_attack_step(self, step: Dict[str, Any], target: Dict[str, Any], 
                                 execution: PentestExecution) -> Dict[str, Any]:
        """Execute individual attack step"""
        try:
            tool_name = step["tool"]
            
            if tool_name == "custom":
                # Custom attack logic
                return {
                    "success": True,
                    "output": f"Custom attack step '{step['action']}' executed",
                    "evidence": "Mock evidence for custom step"
                }
            else:
                # Use configured tool
                endpoints = json.loads(target["endpoints"])
                target_endpoint = endpoints[0] if endpoints else "localhost"
                
                result = await self._run_tool(tool_name, {"target": target_endpoint}, execution)
                return {
                    "success": result is not None,
                    "output": f"Tool {tool_name} executed for {step['action']}",
                    "findings": result.get("findings", []) if result else []
                }
                
        except Exception as e:
            logger.error(f"Failed to execute attack step: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_success_rate(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate penetration test success rate"""
        if not findings:
            return 0.0
        
        successful_findings = len([f for f in findings if f.get("success", True)])
        return (successful_findings / len(findings)) * 100
    
    def _calculate_attack_path_success(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate attack path success rate"""
        if not findings:
            return 0.0
        
        successful_steps = len([f for f in findings if f.get("success", False)])
        return (successful_steps / len(findings)) * 100
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate risk score based on findings"""
        if not findings:
            return 0.0
        
        severity_weights = {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 2.0,
            "info": 1.0
        }
        
        total_score = 0.0
        for finding in findings:
            if isinstance(finding, dict) and "severity" in finding:
                total_score += severity_weights.get(finding["severity"], 1.0)
        
        return min(total_score / len(findings), 10.0) if findings else 0.0
    
    async def get_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        """Get penetration test target"""
        try:
            with sqlite3.connect(self.pentest_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM pentest_targets WHERE target_id = ?",
                    (target_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    columns = [d[0] for d in cursor.description]
                    return dict(zip(columns, row))
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get target: {e}")
            return None
    
    async def _store_execution(self, execution: PentestExecution):
        """Store penetration test execution"""
        try:
            with sqlite3.connect(self.pentest_db_path) as conn:
                conn.execute("""
                INSERT INTO pentest_executions (
                    execution_id, test_type, target_id, attack_vectors, status,
                    started_at, completed_at, duration_minutes, tools_used,
                    findings, attack_paths, evidence, report_path, operator,
                    success_rate, risk_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.test_type.value,
                    execution.target_id,
                    json.dumps([v.value for v in execution.attack_vectors]),
                    execution.status.value,
                    execution.started_at.isoformat(),
                    execution.completed_at.isoformat() if execution.completed_at else None,
                    execution.duration_minutes,
                    json.dumps(execution.tools_used),
                    json.dumps(execution.findings),
                    json.dumps(execution.attack_paths),
                    json.dumps(execution.evidence),
                    execution.report_path,
                    execution.operator,
                    execution.success_rate,
                    execution.risk_score
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
            raise
    
    async def _update_execution(self, execution: PentestExecution):
        """Update penetration test execution"""
        try:
            with sqlite3.connect(self.pentest_db_path) as conn:
                conn.execute("""
                UPDATE pentest_executions SET
                    status = ?, completed_at = ?, duration_minutes = ?,
                    tools_used = ?, findings = ?, success_rate = ?, risk_score = ?
                WHERE execution_id = ?
                """, (
                    execution.status.value,
                    execution.completed_at.isoformat() if execution.completed_at else None,
                    execution.duration_minutes,
                    json.dumps(execution.tools_used),
                    json.dumps(execution.findings),
                    execution.success_rate,
                    execution.risk_score,
                    execution.execution_id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update execution: {e}")
            raise
    
    async def schedule_red_team_exercise(self, target_id: str, 
                                       schedule_time: datetime,
                                       attack_paths: List[str]) -> str:
        """Schedule automated red team exercise"""
        try:
            exercise_id = str(uuid.uuid4())
            
            # Store scheduled exercise (simplified implementation)
            # In production, this would integrate with a job scheduler
            logger.info(f"Scheduled red team exercise {exercise_id} for {schedule_time}")
            
            # Mock immediate execution for demonstration
            execution_id = await self.execute_red_team_simulation(target_id, attack_paths[0])
            
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to schedule red team exercise: {e}")
            raise
    
    async def get_execution_results(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get penetration test execution results"""
        try:
            with sqlite3.connect(self.pentest_db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM pentest_executions WHERE execution_id = ?",
                    (execution_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    columns = [d[0] for d in cursor.description]
                    result = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    result["attack_vectors"] = json.loads(result["attack_vectors"])
                    result["tools_used"] = json.loads(result["tools_used"])
                    result["findings"] = json.loads(result["findings"])
                    result["attack_paths"] = json.loads(result["attack_paths"])
                    result["evidence"] = json.loads(result["evidence"])
                    
                    return result
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get execution results: {e}")
            return None

# Export main classes
__all__ = [
    'PenetrationTestingEngine', 'PentestTarget', 'AttackPath', 'PentestExecution',
    'PentestType', 'AttackVector', 'TestStatus'
]
