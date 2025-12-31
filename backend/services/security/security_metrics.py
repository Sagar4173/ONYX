"""
Security Metrics & KPIs System
Posture scoring, compliance readiness, and risk trend analysis

NOTE: This module uses SQLite for metrics storage.
Future versions should migrate to MongoDB for consistency.
"""
import asyncio
import logging
import json
import sqlite3
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
from collections import defaultdict

# Import canonical enums from models.base (SINGLE SOURCE OF TRUTH)
from models.base import (
    MetricType, TrendDirection, ComplianceFramework, ThreatSeverity,
    VulnerabilityStatus, VulnerabilityPriority
)
from services.scanning.vulnerability import VulnerabilityManager, RiskMetrics
from services.security.threat_intelligence import ThreatIntelligenceEngine

logger = logging.getLogger(__name__)

@dataclass
class SecurityScore:
    """Security posture score"""
    overall_score: float  # 0-100
    vulnerability_score: float
    compliance_score: float
    threat_score: float
    configuration_score: float
    trend: TrendDirection
    last_updated: datetime
    components: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ComplianceResult:
    """Compliance assessment result"""
    framework: ComplianceFramework
    total_controls: int
    passed_controls: int
    failed_controls: int
    not_applicable_controls: int
    pass_percentage: float
    score: float  # 0-100
    status: str  # compliant, non_compliant, partial
    last_assessment: datetime
    next_assessment: Optional[datetime]
    findings: List[Dict[str, Any]] = field(default_factory=list)
    gaps: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TrendData:
    """Time series trend data"""
    timestamps: List[datetime]
    values: List[float]
    trend_direction: TrendDirection
    slope: float
    r_squared: float
    forecast_7d: Optional[float] = None
    forecast_30d: Optional[float] = None

@dataclass
class SecurityKPI:
    """Key Performance Indicator"""
    name: str
    value: float
    target: float
    unit: str
    trend: TrendDirection
    last_period_value: Optional[float]
    change_percentage: float
    status: str  # on_target, at_risk, critical
    description: str
    recommendations: List[str] = field(default_factory=list)

@dataclass
class RiskTrend:
    """Risk trend analysis"""
    period: str  # daily, weekly, monthly
    critical_trend: TrendData
    high_trend: TrendData
    medium_trend: TrendData
    low_trend: TrendData
    overall_risk_trend: TrendData
    new_vulnerabilities_trend: TrendData
    resolved_vulnerabilities_trend: TrendData

class SecurityMetricsEngine:
    """Security metrics and KPIs calculation engine"""
    
    def __init__(self, data_dir: str = "data/metrics"):
        """Initialize security metrics engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.metrics_db_path = self.data_dir / "security_metrics.db"
        self.compliance_db_path = self.data_dir / "compliance_data.db"
        
        # Initialize databases
        self._init_databases()
        
        # Component managers
        self.vuln_manager: Optional[VulnerabilityManager] = None
        self.threat_intel: Optional[ThreatIntelligenceEngine] = None
        
        # Scoring weights for overall security posture
        self.posture_weights = {
            "vulnerability_score": 0.35,
            "compliance_score": 0.25,
            "threat_score": 0.20,
            "configuration_score": 0.20
        }
        
        # Compliance framework definitions
        self.compliance_frameworks = {
            ComplianceFramework.PCI_DSS: {
                "name": "PCI DSS",
                "total_controls": 12,
                "critical_controls": [1, 2, 3, 4],
                "weight_multiplier": 1.2
            },
            ComplianceFramework.HIPAA: {
                "name": "HIPAA",
                "total_controls": 18,
                "critical_controls": [1, 3, 5, 7, 9],
                "weight_multiplier": 1.1
            },
            ComplianceFramework.SOX: {
                "name": "SOX",
                "total_controls": 15,
                "critical_controls": [2, 4, 6, 8],
                "weight_multiplier": 1.0
            },
            ComplianceFramework.GDPR: {
                "name": "GDPR",
                "total_controls": 25,
                "critical_controls": [6, 7, 17, 25, 32],
                "weight_multiplier": 1.3
            }
        }
        
        # KPI thresholds
        self.kpi_thresholds = {
            "mean_time_to_fix": {"target": 168, "critical": 336},  # hours
            "vulnerability_backlog": {"target": 50, "critical": 100},
            "critical_vulns_open": {"target": 0, "critical": 5},
            "compliance_score": {"target": 95, "critical": 80},
            "security_posture": {"target": 85, "critical": 70}
        }
    
    def _init_databases(self):
        """Initialize SQLite databases"""
        try:
            # Security metrics database
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS security_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    overall_score REAL,
                    vulnerability_score REAL,
                    compliance_score REAL,
                    threat_score REAL,
                    configuration_score REAL,
                    components TEXT,        -- JSON
                    recommendations TEXT,   -- JSON
                    metadata TEXT          -- JSON
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS kpi_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    kpi_name TEXT,
                    value REAL,
                    target REAL,
                    status TEXT,
                    metadata TEXT          -- JSON
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS trend_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    period TEXT,
                    timestamp TEXT,
                    value REAL,
                    metadata TEXT          -- JSON
                )
                """)
                
                # Indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_timestamp ON security_scores(timestamp);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_kpi_name_timestamp ON kpi_history(kpi_name, timestamp);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_trend_metric_period ON trend_data(metric_name, period);")
            
            # Compliance database
            with sqlite3.connect(self.compliance_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    framework TEXT,
                    assessment_date TEXT,
                    total_controls INTEGER,
                    passed_controls INTEGER,
                    failed_controls INTEGER,
                    not_applicable_controls INTEGER,
                    pass_percentage REAL,
                    score REAL,
                    status TEXT,
                    findings TEXT,          -- JSON
                    gaps TEXT,             -- JSON
                    assessor TEXT,
                    metadata TEXT          -- JSON
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_controls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    framework TEXT,
                    control_id TEXT,
                    control_name TEXT,
                    description TEXT,
                    category TEXT,
                    mandatory INTEGER,
                    implementation_status TEXT,
                    evidence TEXT,
                    last_reviewed TEXT,
                    reviewer TEXT,
                    metadata TEXT          -- JSON
                )
                """)
                
                # Indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_compliance_framework_date ON compliance_assessments(framework, assessment_date);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_controls_framework ON compliance_controls(framework);")
            
            logger.info("Security metrics databases initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            raise
    
    def set_components(self, vuln_manager: VulnerabilityManager, threat_intel: ThreatIntelligenceEngine):
        """Set component managers"""
        self.vuln_manager = vuln_manager
        self.threat_intel = threat_intel
    
    async def calculate_security_posture(self, repository: Optional[str] = None) -> SecurityScore:
        """Calculate overall security posture score"""
        try:
            # Calculate component scores
            vulnerability_score = await self._calculate_vulnerability_score(repository)
            compliance_score = await self._calculate_compliance_score(repository)
            threat_score = await self._calculate_threat_score(repository)
            configuration_score = await self._calculate_configuration_score(repository)
            
            # Calculate weighted overall score
            overall_score = (
                vulnerability_score * self.posture_weights["vulnerability_score"] +
                compliance_score * self.posture_weights["compliance_score"] +
                threat_score * self.posture_weights["threat_score"] +
                configuration_score * self.posture_weights["configuration_score"]
            )
            
            # Determine trend
            trend = await self._calculate_posture_trend()
            
            # Generate recommendations
            recommendations = await self._generate_posture_recommendations(
                vulnerability_score, compliance_score, threat_score, configuration_score
            )
            
            security_score = SecurityScore(
                overall_score=round(overall_score, 2),
                vulnerability_score=round(vulnerability_score, 2),
                compliance_score=round(compliance_score, 2),
                threat_score=round(threat_score, 2),
                configuration_score=round(configuration_score, 2),
                trend=trend,
                last_updated=datetime.now(timezone.utc),
                components={
                    "vulnerabilities": vulnerability_score,
                    "compliance": compliance_score,
                    "threats": threat_score,
                    "configuration": configuration_score
                },
                recommendations=recommendations
            )
            
            # Store the score
            await self._store_security_score(security_score)
            
            return security_score
            
        except Exception as e:
            logger.error(f"Failed to calculate security posture: {e}")
            return SecurityScore(
                overall_score=0.0,
                vulnerability_score=0.0,
                compliance_score=0.0,
                threat_score=0.0,
                configuration_score=0.0,
                trend=TrendDirection.UNKNOWN,
                last_updated=datetime.now(timezone.utc)
            )
    
    async def _calculate_vulnerability_score(self, repository: Optional[str] = None) -> float:
        """Calculate vulnerability-based security score"""
        if not self.vuln_manager:
            return 50.0  # Default score when no data available
        
        try:
            # Get vulnerability metrics
            metrics = await self.vuln_manager.calculate_risk_metrics()
            
            # Base score starts at 100
            score = 100.0
            
            # Deduct points for vulnerabilities by severity
            if metrics.total_vulnerabilities > 0:
                critical_penalty = metrics.critical_count * 25
                high_penalty = metrics.high_count * 15
                medium_penalty = metrics.medium_count * 5
                low_penalty = metrics.low_count * 1
                
                total_penalty = critical_penalty + high_penalty + medium_penalty + low_penalty
                
                # Scale penalty based on total vulnerabilities
                if metrics.total_vulnerabilities <= 10:
                    penalty_multiplier = 1.0
                elif metrics.total_vulnerabilities <= 50:
                    penalty_multiplier = 1.2
                elif metrics.total_vulnerabilities <= 100:
                    penalty_multiplier = 1.5
                else:
                    penalty_multiplier = 2.0
                
                score -= min(total_penalty * penalty_multiplier, 80)  # Cap at 80 point reduction
            
            # Additional penalties
            if metrics.overdue_count > 0:
                score -= min(metrics.overdue_count * 5, 20)  # Up to 20 points for overdue items
            
            # Bonus for good SLA compliance
            if metrics.sla_compliance_rate > 95:
                score += 5
            elif metrics.sla_compliance_rate > 90:
                score += 2
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate vulnerability score: {e}")
            return 50.0
    
    async def _calculate_compliance_score(self, repository: Optional[str] = None) -> float:
        """Calculate compliance-based security score"""
        try:
            # Get latest compliance assessments
            compliance_results = await self.get_compliance_results()
            
            if not compliance_results:
                return 50.0  # Default score when no assessments available
            
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for result in compliance_results:
                framework_config = self.compliance_frameworks.get(result.framework, {})
                weight = framework_config.get("weight_multiplier", 1.0)
                
                total_weighted_score += result.score * weight
                total_weight += weight
            
            if total_weight > 0:
                return total_weighted_score / total_weight
            else:
                return 50.0
            
        except Exception as e:
            logger.error(f"Failed to calculate compliance score: {e}")
            return 50.0
    
    async def _calculate_threat_score(self, repository: Optional[str] = None) -> float:
        """Calculate threat-based security score"""
        if not self.threat_intel:
            return 75.0  # Default score when no threat data available
        
        try:
            # Get active threat alerts
            alerts = await self.threat_intel.get_active_alerts()
            
            # Base score starts at 100
            score = 100.0
            
            # Deduct points for active threats
            for alert in alerts:
                if alert.severity == ThreatSeverity.CRITICAL:
                    score -= 20
                elif alert.severity == ThreatSeverity.HIGH:
                    score -= 10
                elif alert.severity == ThreatSeverity.MEDIUM:
                    score -= 5
                else:
                    score -= 1
            
            # Additional deductions for threat patterns
            zero_day_alerts = [a for a in alerts if "zero" in a.title.lower()]
            if zero_day_alerts:
                score -= len(zero_day_alerts) * 15
            
            kev_alerts = [a for a in alerts if "kev" in a.title.lower()]
            if kev_alerts:
                score -= len(kev_alerts) * 10
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate threat score: {e}")
            return 75.0
    
    async def _calculate_configuration_score(self, repository: Optional[str] = None) -> float:
        """Calculate configuration-based security score"""
        # This would integrate with configuration scanners (Checkov, etc.)
        # For now, return a baseline score
        try:
            # TODO: Integrate with actual configuration scanning results
            # This should pull from Checkov/other IaC scanning results
            
            # Placeholder scoring logic
            base_score = 80.0
            
            # In a real implementation, this would:
            # 1. Check for security misconfigurations
            # 2. Validate security policies
            # 3. Assess infrastructure security
            # 4. Check for hardening compliance
            
            return base_score
            
        except Exception as e:
            logger.error(f"Failed to calculate configuration score: {e}")
            return 80.0
    
    async def _calculate_posture_trend(self) -> TrendDirection:
        """Calculate security posture trend"""
        try:
            # Get last 30 days of scores
            with sqlite3.connect(self.metrics_db_path) as conn:
                cursor = conn.execute("""
                SELECT overall_score, timestamp FROM security_scores 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
                LIMIT 30
                """, (
                    (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                ))
                
                scores = [(row[0], datetime.fromisoformat(row[1])) for row in cursor.fetchall()]
            
            if len(scores) < 3:
                return TrendDirection.UNKNOWN
            
            # Calculate trend using linear regression
            timestamps = [(s[1] - scores[-1][1]).total_seconds() for s in scores]
            values = [s[0] for s in scores]
            
            if len(set(values)) == 1:
                return TrendDirection.STABLE
            
            # Simple trend calculation
            recent_avg = statistics.mean(values[:10]) if len(values) >= 10 else statistics.mean(values[:len(values)//2])
            older_avg = statistics.mean(values[10:]) if len(values) >= 10 else statistics.mean(values[len(values)//2:])
            
            difference = recent_avg - older_avg
            
            if difference > 2:
                return TrendDirection.IMPROVING
            elif difference < -2:
                return TrendDirection.DEGRADING
            else:
                return TrendDirection.STABLE
            
        except Exception as e:
            logger.error(f"Failed to calculate posture trend: {e}")
            return TrendDirection.UNKNOWN
    
    async def _generate_posture_recommendations(
        self,
        vuln_score: float,
        compliance_score: float,
        threat_score: float,
        config_score: float
    ) -> List[str]:
        """Generate security posture improvement recommendations"""
        recommendations = []
        
        # Vulnerability recommendations
        if vuln_score < 70:
            recommendations.append("CRITICAL: Address high-severity vulnerabilities immediately")
            recommendations.append("Implement automated vulnerability scanning")
            recommendations.append("Establish vulnerability SLA targets")
        elif vuln_score < 85:
            recommendations.append("Improve vulnerability remediation processes")
            recommendations.append("Consider risk-based prioritization")
        
        # Compliance recommendations
        if compliance_score < 70:
            recommendations.append("URGENT: Review compliance framework implementation")
            recommendations.append("Conduct compliance gap analysis")
            recommendations.append("Implement missing security controls")
        elif compliance_score < 90:
            recommendations.append("Enhance compliance monitoring and reporting")
            recommendations.append("Review control effectiveness")
        
        # Threat recommendations
        if threat_score < 60:
            recommendations.append("HIGH: Active threats detected - investigate immediately")
            recommendations.append("Enable real-time threat monitoring")
            recommendations.append("Update threat intelligence feeds")
        elif threat_score < 80:
            recommendations.append("Monitor threat landscape more closely")
            recommendations.append("Consider additional threat detection tools")
        
        # Configuration recommendations
        if config_score < 70:
            recommendations.append("Review security configuration standards")
            recommendations.append("Implement Infrastructure as Code scanning")
            recommendations.append("Establish configuration baselines")
        elif config_score < 85:
            recommendations.append("Automate configuration compliance checks")
            recommendations.append("Review security hardening guidelines")
        
        return recommendations
    
    async def _store_security_score(self, score: SecurityScore):
        """Store security score in database"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.execute("""
                INSERT INTO security_scores (
                    timestamp, overall_score, vulnerability_score, compliance_score,
                    threat_score, configuration_score, components, recommendations, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    score.last_updated.isoformat(),
                    score.overall_score,
                    score.vulnerability_score,
                    score.compliance_score,
                    score.threat_score,
                    score.configuration_score,
                    json.dumps(score.components),
                    json.dumps(score.recommendations),
                    json.dumps({"trend": score.trend.value})
                ))
            
        except Exception as e:
            logger.error(f"Failed to store security score: {e}")
    
    async def assess_compliance_framework(
        self,
        framework: ComplianceFramework,
        assessor: str = "system"
    ) -> ComplianceResult:
        """Assess compliance against a specific framework"""
        try:
            framework_config = self.compliance_frameworks.get(framework)
            if not framework_config:
                raise ValueError(f"Unknown compliance framework: {framework}")
            
            # Get existing controls for this framework
            controls = await self._get_compliance_controls(framework)
            
            # If no controls exist, create default ones
            if not controls:
                controls = await self._create_default_controls(framework)
            
            # Assess each control
            passed = 0
            failed = 0
            not_applicable = 0
            findings = []
            gaps = []
            
            for control in controls:
                status = control.get("implementation_status", "not_implemented")
                
                if status == "implemented":
                    passed += 1
                elif status == "not_applicable":
                    not_applicable += 1
                else:
                    failed += 1
                    gaps.append({
                        "control_id": control["control_id"],
                        "control_name": control["control_name"],
                        "status": status,
                        "gap_description": control.get("gap_description", "Control not implemented")
                    })
            
            total_applicable = passed + failed
            pass_percentage = (passed / total_applicable * 100) if total_applicable > 0 else 0
            
            # Calculate score with weighted critical controls
            score = pass_percentage
            critical_controls = framework_config.get("critical_controls", [])
            
            # Boost score for critical control compliance
            critical_passed = 0
            critical_total = 0
            for control in controls:
                control_num = int(control["control_id"].split(".")[-1]) if "." in control["control_id"] else 0
                if control_num in critical_controls:
                    critical_total += 1
                    if control.get("implementation_status") == "implemented":
                        critical_passed += 1
            
            if critical_total > 0:
                critical_compliance = critical_passed / critical_total
                score = (score * 0.7) + (critical_compliance * 100 * 0.3)
            
            # Determine compliance status
            if score >= 95:
                status = "compliant"
            elif score >= 80:
                status = "partial"
            else:
                status = "non_compliant"
            
            assessment_date = datetime.now(timezone.utc)
            
            result = ComplianceResult(
                framework=framework,
                total_controls=len(controls),
                passed_controls=passed,
                failed_controls=failed,
                not_applicable_controls=not_applicable,
                pass_percentage=round(pass_percentage, 2),
                score=round(score, 2),
                status=status,
                last_assessment=assessment_date,
                next_assessment=assessment_date + timedelta(days=90),  # Quarterly assessment
                findings=findings,
                gaps=gaps
            )
            
            # Store assessment result
            await self._store_compliance_assessment(result, assessor)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to assess compliance framework: {e}")
            return ComplianceResult(
                framework=framework,
                total_controls=0,
                passed_controls=0,
                failed_controls=0,
                not_applicable_controls=0,
                pass_percentage=0.0,
                score=0.0,
                status="unknown",
                last_assessment=datetime.now(timezone.utc),
                findings=[],
                gaps=[]
            )
    
    async def _get_compliance_controls(self, framework: ComplianceFramework) -> List[Dict[str, Any]]:
        """Get compliance controls for framework"""
        try:
            with sqlite3.connect(self.compliance_db_path) as conn:
                cursor = conn.execute("""
                SELECT control_id, control_name, description, category, mandatory,
                       implementation_status, evidence, last_reviewed, reviewer, metadata
                FROM compliance_controls WHERE framework = ?
                """, (framework.value,))
                
                controls = []
                for row in cursor.fetchall():
                    control = {
                        "control_id": row[0],
                        "control_name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "mandatory": bool(row[4]),
                        "implementation_status": row[5],
                        "evidence": row[6],
                        "last_reviewed": row[7],
                        "reviewer": row[8],
                        "metadata": json.loads(row[9]) if row[9] else {}
                    }
                    controls.append(control)
                
                return controls
            
        except Exception as e:
            logger.error(f"Failed to get compliance controls: {e}")
            return []
    
    async def _create_default_controls(self, framework: ComplianceFramework) -> List[Dict[str, Any]]:
        """Create default controls for a compliance framework"""
        default_controls = {
            ComplianceFramework.PCI_DSS: [
                {"id": "1", "name": "Firewall Configuration", "category": "Network Security"},
                {"id": "2", "name": "Default Passwords", "category": "Access Control"},
                {"id": "3", "name": "Cardholder Data Protection", "category": "Data Protection"},
                {"id": "4", "name": "Encrypted Transmission", "category": "Cryptography"},
                {"id": "5", "name": "Antivirus Software", "category": "Malware Protection"},
                {"id": "6", "name": "Secure Systems", "category": "System Security"},
                {"id": "7", "name": "Access Control", "category": "Access Control"},
                {"id": "8", "name": "User Authentication", "category": "Identity Management"},
                {"id": "9", "name": "Physical Access", "category": "Physical Security"},
                {"id": "10", "name": "Network Monitoring", "category": "Monitoring"},
                {"id": "11", "name": "Security Testing", "category": "Testing"},
                {"id": "12", "name": "Security Policy", "category": "Governance"}
            ],
            ComplianceFramework.HIPAA: [
                {"id": "164.308", "name": "Administrative Safeguards", "category": "Administrative"},
                {"id": "164.310", "name": "Physical Safeguards", "category": "Physical"},
                {"id": "164.312", "name": "Technical Safeguards", "category": "Technical"},
                {"id": "164.314", "name": "Organizational Requirements", "category": "Organizational"},
                {"id": "164.316", "name": "Policies and Procedures", "category": "Documentation"}
            ]
        }
        
        controls_data = default_controls.get(framework, [])
        controls = []
        
        for control_data in controls_data:
            control = {
                "control_id": f"{framework.value}.{control_data['id']}",
                "control_name": control_data["name"],
                "description": f"Default control for {control_data['name']}",
                "category": control_data["category"],
                "mandatory": True,
                "implementation_status": "not_implemented",
                "evidence": "",
                "last_reviewed": None,
                "reviewer": "",
                "metadata": {}
            }
            controls.append(control)
            
            # Store in database
            await self._store_compliance_control(framework, control)
        
        return controls
    
    async def _store_compliance_control(self, framework: ComplianceFramework, control: Dict[str, Any]):
        """Store compliance control in database"""
        try:
            with sqlite3.connect(self.compliance_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO compliance_controls (
                    framework, control_id, control_name, description, category,
                    mandatory, implementation_status, evidence, last_reviewed,
                    reviewer, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    framework.value,
                    control["control_id"],
                    control["control_name"],
                    control["description"],
                    control["category"],
                    int(control["mandatory"]),
                    control["implementation_status"],
                    control["evidence"],
                    control["last_reviewed"],
                    control["reviewer"],
                    json.dumps(control["metadata"])
                ))
            
        except Exception as e:
            logger.error(f"Failed to store compliance control: {e}")
    
    async def _store_compliance_assessment(self, result: ComplianceResult, assessor: str):
        """Store compliance assessment result"""
        try:
            with sqlite3.connect(self.compliance_db_path) as conn:
                conn.execute("""
                INSERT INTO compliance_assessments (
                    framework, assessment_date, total_controls, passed_controls,
                    failed_controls, not_applicable_controls, pass_percentage,
                    score, status, findings, gaps, assessor, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.framework.value,
                    result.last_assessment.isoformat(),
                    result.total_controls,
                    result.passed_controls,
                    result.failed_controls,
                    result.not_applicable_controls,
                    result.pass_percentage,
                    result.score,
                    result.status,
                    json.dumps(result.findings),
                    json.dumps(result.gaps),
                    assessor,
                    json.dumps({"next_assessment": result.next_assessment.isoformat() if result.next_assessment else None})
                ))
            
        except Exception as e:
            logger.error(f"Failed to store compliance assessment: {e}")
    
    async def get_compliance_results(
        self,
        framework: Optional[ComplianceFramework] = None
    ) -> List[ComplianceResult]:
        """Get compliance assessment results"""
        try:
            conditions = []
            params = []
            
            if framework:
                conditions.append("framework = ?")
                params.append(framework.value)
            
            where_clause = ""
            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"
            
            # Get latest assessment for each framework
            query = f"""
            SELECT framework, assessment_date, total_controls, passed_controls,
                   failed_controls, not_applicable_controls, pass_percentage,
                   score, status, findings, gaps, assessor, metadata
            FROM compliance_assessments 
            {where_clause}
            ORDER BY assessment_date DESC
            """
            
            results = []
            with sqlite3.connect(self.compliance_db_path) as conn:
                cursor = conn.execute(query, params)
                
                seen_frameworks = set()
                for row in cursor.fetchall():
                    framework_val = row[0]
                    if framework_val not in seen_frameworks:
                        seen_frameworks.add(framework_val)
                        
                        metadata = json.loads(row[12]) if row[12] else {}
                        
                        result = ComplianceResult(
                            framework=ComplianceFramework(framework_val),
                            total_controls=row[2],
                            passed_controls=row[3],
                            failed_controls=row[4],
                            not_applicable_controls=row[5],
                            pass_percentage=row[6],
                            score=row[7],
                            status=row[8],
                            last_assessment=datetime.fromisoformat(row[1]),
                            next_assessment=datetime.fromisoformat(metadata["next_assessment"]) if metadata.get("next_assessment") else None,
                            findings=json.loads(row[9]),
                            gaps=json.loads(row[10])
                        )
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get compliance results: {e}")
            return []
    
    async def calculate_kpis(self) -> List[SecurityKPI]:
        """Calculate security KPIs"""
        kpis = []
        
        try:
            if self.vuln_manager:
                # Vulnerability KPIs
                metrics = await self.vuln_manager.calculate_risk_metrics()
                
                # Mean Time to Fix
                mttf_kpi = SecurityKPI(
                    name="Mean Time to Fix",
                    value=metrics.mean_time_to_fix,
                    target=self.kpi_thresholds["mean_time_to_fix"]["target"],
                    unit="hours",
                    trend=await self._calculate_kpi_trend("mean_time_to_fix"),
                    last_period_value=None,
                    change_percentage=0.0,
                    status=self._get_kpi_status(metrics.mean_time_to_fix, "mean_time_to_fix", lower_is_better=True),
                    description="Average time to resolve vulnerabilities",
                    recommendations=self._get_mttf_recommendations(metrics.mean_time_to_fix)
                )
                kpis.append(mttf_kpi)
                
                # Vulnerability Backlog
                backlog_kpi = SecurityKPI(
                    name="Vulnerability Backlog",
                    value=float(metrics.total_vulnerabilities),
                    target=self.kpi_thresholds["vulnerability_backlog"]["target"],
                    unit="count",
                    trend=await self._calculate_kpi_trend("vulnerability_backlog"),
                    last_period_value=None,
                    change_percentage=0.0,
                    status=self._get_kpi_status(metrics.total_vulnerabilities, "vulnerability_backlog", lower_is_better=True),
                    description="Total open vulnerabilities",
                    recommendations=self._get_backlog_recommendations(metrics.total_vulnerabilities)
                )
                kpis.append(backlog_kpi)
                
                # Critical Vulnerabilities Open
                critical_kpi = SecurityKPI(
                    name="Critical Vulnerabilities Open",
                    value=float(metrics.critical_count),
                    target=self.kpi_thresholds["critical_vulns_open"]["target"],
                    unit="count",
                    trend=await self._calculate_kpi_trend("critical_vulns_open"),
                    last_period_value=None,
                    change_percentage=0.0,
                    status=self._get_kpi_status(metrics.critical_count, "critical_vulns_open", lower_is_better=True),
                    description="Number of open critical vulnerabilities",
                    recommendations=self._get_critical_vuln_recommendations(metrics.critical_count)
                )
                kpis.append(critical_kpi)
            
            # Compliance KPI
            compliance_results = await self.get_compliance_results()
            if compliance_results:
                avg_compliance = statistics.mean([r.score for r in compliance_results])
                
                compliance_kpi = SecurityKPI(
                    name="Compliance Score",
                    value=avg_compliance,
                    target=self.kpi_thresholds["compliance_score"]["target"],
                    unit="percentage",
                    trend=await self._calculate_kpi_trend("compliance_score"),
                    last_period_value=None,
                    change_percentage=0.0,
                    status=self._get_kpi_status(avg_compliance, "compliance_score"),
                    description="Average compliance framework score",
                    recommendations=self._get_compliance_recommendations(avg_compliance)
                )
                kpis.append(compliance_kpi)
            
            # Security Posture KPI
            posture_score = await self.calculate_security_posture()
            
            posture_kpi = SecurityKPI(
                name="Security Posture Score",
                value=posture_score.overall_score,
                target=self.kpi_thresholds["security_posture"]["target"],
                unit="score",
                trend=posture_score.trend,
                last_period_value=None,
                change_percentage=0.0,
                status=self._get_kpi_status(posture_score.overall_score, "security_posture"),
                description="Overall security posture assessment",
                recommendations=posture_score.recommendations[:3]  # Top 3 recommendations
            )
            kpis.append(posture_kpi)
            
            # Store KPI values
            for kpi in kpis:
                await self._store_kpi_value(kpi)
            
            return kpis
            
        except Exception as e:
            logger.error(f"Failed to calculate KPIs: {e}")
            return []
    
    def _get_kpi_status(self, value: float, kpi_name: str, lower_is_better: bool = False) -> str:
        """Determine KPI status based on thresholds"""
        thresholds = self.kpi_thresholds.get(kpi_name, {})
        target = thresholds.get("target", 0)
        critical = thresholds.get("critical", 0)
        
        if lower_is_better:
            if value <= target:
                return "on_target"
            elif value <= critical:
                return "at_risk"
            else:
                return "critical"
        else:
            if value >= target:
                return "on_target"
            elif value >= critical:
                return "at_risk"
            else:
                return "critical"
    
    def _get_mttf_recommendations(self, mttf: float) -> List[str]:
        """Get recommendations for Mean Time to Fix"""
        recommendations = []
        
        if mttf > 336:  # > 2 weeks
            recommendations.extend([
                "Implement automated vulnerability remediation",
                "Establish dedicated security response team",
                "Create vulnerability triage procedures"
            ])
        elif mttf > 168:  # > 1 week
            recommendations.extend([
                "Improve vulnerability prioritization",
                "Streamline patch management process"
            ])
        else:
            recommendations.append("Maintain current remediation processes")
        
        return recommendations
    
    def _get_backlog_recommendations(self, backlog: int) -> List[str]:
        """Get recommendations for vulnerability backlog"""
        recommendations = []
        
        if backlog > 100:
            recommendations.extend([
                "Implement risk-based vulnerability management",
                "Increase remediation team capacity",
                "Focus on critical and high-severity vulnerabilities"
            ])
        elif backlog > 50:
            recommendations.extend([
                "Optimize vulnerability scanning frequency",
                "Improve false positive filtering"
            ])
        else:
            recommendations.append("Maintain current vulnerability management process")
        
        return recommendations
    
    def _get_critical_vuln_recommendations(self, count: int) -> List[str]:
        """Get recommendations for critical vulnerabilities"""
        if count > 0:
            return [
                "IMMEDIATE: Address all critical vulnerabilities",
                "Implement emergency patch procedures",
                "Consider compensating controls"
            ]
        else:
            return ["Excellent - maintain zero critical vulnerabilities"]
    
    def _get_compliance_recommendations(self, score: float) -> List[str]:
        """Get recommendations for compliance score"""
        recommendations = []
        
        if score < 80:
            recommendations.extend([
                "Conduct compliance gap analysis",
                "Implement missing security controls",
                "Engage compliance specialists"
            ])
        elif score < 95:
            recommendations.extend([
                "Review control effectiveness",
                "Enhance compliance documentation"
            ])
        else:
            recommendations.append("Maintain excellent compliance posture")
        
        return recommendations
    
    async def _calculate_kpi_trend(self, kpi_name: str) -> TrendDirection:
        """Calculate KPI trend direction"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                cursor = conn.execute("""
                SELECT value, timestamp FROM kpi_history 
                WHERE kpi_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 10
                """, (
                    kpi_name,
                    (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                ))
                
                values = [row[0] for row in cursor.fetchall()]
            
            if len(values) < 3:
                return TrendDirection.UNKNOWN
            
            # Simple trend calculation
            recent_avg = statistics.mean(values[:3])
            older_avg = statistics.mean(values[3:])
            
            threshold = older_avg * 0.05  # 5% threshold
            
            if recent_avg > older_avg + threshold:
                return TrendDirection.IMPROVING
            elif recent_avg < older_avg - threshold:
                return TrendDirection.DEGRADING
            else:
                return TrendDirection.STABLE
            
        except Exception as e:
            logger.error(f"Failed to calculate KPI trend: {e}")
            return TrendDirection.UNKNOWN
    
    async def _store_kpi_value(self, kpi: SecurityKPI):
        """Store KPI value in database"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.execute("""
                INSERT INTO kpi_history (timestamp, kpi_name, value, target, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    kpi.name,
                    kpi.value,
                    kpi.target,
                    kpi.status,
                    json.dumps({
                        "unit": kpi.unit,
                        "trend": kpi.trend.value,
                        "description": kpi.description,
                        "recommendations": kpi.recommendations
                    })
                ))
            
        except Exception as e:
            logger.error(f"Failed to store KPI value: {e}")
    
    async def generate_risk_trend_analysis(self, days: int = 30) -> RiskTrend:
        """Generate comprehensive risk trend analysis"""
        try:
            if not self.vuln_manager:
                raise ValueError("Vulnerability manager not set")
            
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get vulnerability counts by severity over time
            # This would query vulnerability history
            # For now, generate sample trend data
            
            # Generate sample data points
            dates = [start_date + timedelta(days=i) for i in range(days)]
            
            # Sample trend data (in real implementation, this would come from historical data)
            critical_values = [max(0, 5 + np.random.randint(-2, 3)) for _ in range(days)]
            high_values = [max(0, 15 + np.random.randint(-5, 5)) for _ in range(days)]
            medium_values = [max(0, 30 + np.random.randint(-10, 10)) for _ in range(days)]
            low_values = [max(0, 50 + np.random.randint(-15, 15)) for _ in range(days)]
            
            # Calculate overall risk (weighted sum)
            overall_values = [
                c * 4 + h * 3 + m * 2 + l * 1
                for c, h, m, l in zip(critical_values, high_values, medium_values, low_values)
            ]
            
            # New/resolved vulnerability trends
            new_vuln_values = [max(0, 8 + np.random.randint(-3, 5)) for _ in range(days)]
            resolved_vuln_values = [max(0, 6 + np.random.randint(-2, 4)) for _ in range(days)]
            
            return RiskTrend(
                period="daily",
                critical_trend=self._create_trend_data(dates, critical_values),
                high_trend=self._create_trend_data(dates, high_values),
                medium_trend=self._create_trend_data(dates, medium_values),
                low_trend=self._create_trend_data(dates, low_values),
                overall_risk_trend=self._create_trend_data(dates, overall_values),
                new_vulnerabilities_trend=self._create_trend_data(dates, new_vuln_values),
                resolved_vulnerabilities_trend=self._create_trend_data(dates, resolved_vuln_values)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate risk trend analysis: {e}")
            # Return empty trend data
            empty_dates = []
            empty_values = []
            empty_trend = self._create_trend_data(empty_dates, empty_values)
            
            return RiskTrend(
                period="daily",
                critical_trend=empty_trend,
                high_trend=empty_trend,
                medium_trend=empty_trend,
                low_trend=empty_trend,
                overall_risk_trend=empty_trend,
                new_vulnerabilities_trend=empty_trend,
                resolved_vulnerabilities_trend=empty_trend
            )
    
    def _create_trend_data(self, timestamps: List[datetime], values: List[float]) -> TrendData:
        """Create trend data with statistical analysis"""
        if len(values) < 2:
            return TrendData(
                timestamps=timestamps,
                values=values,
                trend_direction=TrendDirection.UNKNOWN,
                slope=0.0,
                r_squared=0.0
            )
        
        # Calculate linear regression
        x = np.array(range(len(values)))
        y = np.array(values)
        
        if len(set(values)) == 1:
            # All values are the same
            slope = 0.0
            r_squared = 1.0
            trend_direction = TrendDirection.STABLE
        else:
            # Calculate slope and R-squared
            coeffs = np.polyfit(x, y, 1)
            slope = coeffs[0]
            
            # Calculate R-squared
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Determine trend direction
            if abs(slope) < 0.1:
                trend_direction = TrendDirection.STABLE
            elif slope > 0:
                trend_direction = TrendDirection.DEGRADING  # Increasing vulnerabilities is bad
            else:
                trend_direction = TrendDirection.IMPROVING  # Decreasing vulnerabilities is good
        
        # Simple forecasting (linear extrapolation)
        if len(values) >= 3:
            forecast_7d = values[-1] + (slope * 7)
            forecast_30d = values[-1] + (slope * 30)
        else:
            forecast_7d = None
            forecast_30d = None
        
        return TrendData(
            timestamps=timestamps,
            values=values,
            trend_direction=trend_direction,
            slope=slope,
            r_squared=r_squared,
            forecast_7d=forecast_7d,
            forecast_30d=forecast_30d
        )

# Export main classes
__all__ = [
    'SecurityMetricsEngine', 'SecurityScore', 'ComplianceResult', 'SecurityKPI',
    'RiskTrend', 'TrendData', 'MetricType', 'TrendDirection', 'ComplianceFramework'
]
