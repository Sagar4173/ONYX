"""
Metrics and KPI Engine
=======================

Comprehensive security metrics, KPIs, and SLA tracking for enterprise
vulnerability management and security operations.

Author: ONYX Platform
Date: August 2025
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityMetrics:
    """Security metrics and KPIs data structure"""
    vulnerability_metrics: Dict[str, Any]
    scan_metrics: Dict[str, Any]
    remediation_metrics: Dict[str, Any]
    sla_metrics: Dict[str, Any]
    trend_metrics: Dict[str, Any]
    compliance_metrics: Dict[str, Any]

@dataclass
class SLATarget:
    """SLA target configuration"""
    name: str
    description: str
    target_value: float
    unit: str
    threshold_type: str  # lower_is_better, higher_is_better
    critical_threshold: float
    warning_threshold: float

class MetricsKPIEngine:
    """Enterprise security metrics and KPI tracking engine"""
    
    def __init__(self, db_path: str = "security_metrics.db"):
        self.db_path = db_path
        self.sla_targets = self._define_sla_targets()
        self.init_database()
    
    def _define_sla_targets(self) -> Dict[str, SLATarget]:
        """Define standard security SLA targets"""
        return {
            'mttr_critical': SLATarget(
                name='Mean Time to Remediation (Critical)',
                description='Average time to fix critical vulnerabilities',
                target_value=24.0,  # hours
                unit='hours',
                threshold_type='lower_is_better',
                critical_threshold=48.0,
                warning_threshold=36.0
            ),
            'mttr_high': SLATarget(
                name='Mean Time to Remediation (High)',
                description='Average time to fix high severity vulnerabilities',
                target_value=168.0,  # 1 week
                unit='hours',
                threshold_type='lower_is_better',
                critical_threshold=336.0,  # 2 weeks
                warning_threshold=252.0   # 1.5 weeks
            ),
            'sla_breach_rate': SLATarget(
                name='SLA Breach Rate',
                description='Percentage of vulnerabilities that breach SLA',
                target_value=5.0,  # %
                unit='percentage',
                threshold_type='lower_is_better',
                critical_threshold=15.0,
                warning_threshold=10.0
            ),
            'scan_coverage': SLATarget(
                name='Scan Coverage',
                description='Percentage of assets scanned in last 30 days',
                target_value=95.0,  # %
                unit='percentage',
                threshold_type='higher_is_better',
                critical_threshold=80.0,
                warning_threshold=90.0
            ),
            'false_positive_rate': SLATarget(
                name='False Positive Rate',
                description='Percentage of findings marked as false positives',
                target_value=10.0,  # %
                unit='percentage',
                threshold_type='lower_is_better',
                critical_threshold=25.0,
                warning_threshold=20.0
            ),
            'vulnerability_density': SLATarget(
                name='Vulnerability Density',
                description='Average vulnerabilities per 1000 lines of code',
                target_value=5.0,
                unit='per_kloc',
                threshold_type='lower_is_better',
                critical_threshold=20.0,
                warning_threshold=15.0
            )
        }
    
    def init_database(self):
        """Initialize metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily metrics snapshot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE NOT NULL,
                total_vulnerabilities INTEGER,
                critical_vulnerabilities INTEGER,
                high_vulnerabilities INTEGER,
                medium_vulnerabilities INTEGER,
                low_vulnerabilities INTEGER,
                open_vulnerabilities INTEGER,
                fixed_vulnerabilities INTEGER,
                mttr_critical_hours REAL,
                mttr_high_hours REAL,
                mttr_medium_hours REAL,
                sla_breach_count INTEGER,
                sla_breach_rate REAL,
                scan_count INTEGER,
                assets_scanned INTEGER,
                total_assets INTEGER,
                scan_coverage_rate REAL,
                false_positive_count INTEGER,
                false_positive_rate REAL,
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(metric_date)
            )
        ''')
        
        # Scan execution metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                asset_id TEXT,
                repository TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL,
                findings_count INTEGER,
                critical_count INTEGER,
                high_count INTEGER,
                medium_count INTEGER,
                low_count INTEGER,
                scanner_errors INTEGER,
                scan_status TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Remediation tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remediation_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vulnerability_id TEXT NOT NULL,
                discovered_date TIMESTAMP,
                triaged_date TIMESTAMP,
                assigned_date TIMESTAMP,
                in_progress_date TIMESTAMP,
                fixed_date TIMESTAMP,
                verified_date TIMESTAMP,
                closed_date TIMESTAMP,
                severity TEXT,
                business_criticality TEXT,
                environment TEXT,
                mttr_hours REAL,
                sla_hours REAL,
                sla_breach BOOLEAN,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Team performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                assignee TEXT,
                metric_date DATE,
                vulnerabilities_assigned INTEGER,
                vulnerabilities_fixed INTEGER,
                avg_mttr_hours REAL,
                sla_breach_count INTEGER,
                productivity_score REAL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # SLA performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sla_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sla_name TEXT NOT NULL,
                target_value REAL,
                actual_value REAL,
                performance_percentage REAL,
                status TEXT,  -- green, amber, red
                metric_date DATE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("📊 Metrics database initialized")
    
    async def capture_daily_metrics(self, vulnerability_db: str, 
                                  threat_intelligence_db: str) -> Dict[str, Any]:
        """Capture daily security metrics snapshot"""
        today = datetime.now().date()
        
        # Connect to source databases
        vuln_conn = sqlite3.connect(vulnerability_db)
        ti_conn = sqlite3.connect(threat_intelligence_db)
        metrics_conn = sqlite3.connect(self.db_path)
        
        try:
            metrics = await self._calculate_daily_metrics(vuln_conn, ti_conn, today)
            
            # Store metrics
            cursor = metrics_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO daily_metrics 
                (metric_date, total_vulnerabilities, critical_vulnerabilities, high_vulnerabilities,
                 medium_vulnerabilities, low_vulnerabilities, open_vulnerabilities, fixed_vulnerabilities,
                 mttr_critical_hours, mttr_high_hours, mttr_medium_hours, sla_breach_count, sla_breach_rate,
                 scan_count, assets_scanned, total_assets, scan_coverage_rate, 
                 false_positive_count, false_positive_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today,
                metrics['total_vulnerabilities'],
                metrics['by_severity'].get('critical', 0),
                metrics['by_severity'].get('high', 0),
                metrics['by_severity'].get('medium', 0),
                metrics['by_severity'].get('low', 0),
                metrics['by_state'].get('open', 0),
                metrics['by_state'].get('fixed', 0),
                metrics['mttr_by_severity'].get('critical', 0),
                metrics['mttr_by_severity'].get('high', 0),
                metrics['mttr_by_severity'].get('medium', 0),
                metrics['sla_breach_count'],
                metrics['sla_breach_rate'],
                metrics['scan_count'],
                metrics['assets_scanned'],
                metrics['total_assets'],
                metrics['scan_coverage_rate'],
                metrics['false_positive_count'],
                metrics['false_positive_rate']
            ))
            
            metrics_conn.commit()
            logger.info(f"📊 Daily metrics captured for {today}")
            return metrics
            
        finally:
            vuln_conn.close()
            ti_conn.close()
            metrics_conn.close()
    
    async def _calculate_daily_metrics(self, vuln_conn: sqlite3.Connection, 
                                     ti_conn: sqlite3.Connection, 
                                     target_date: datetime.date) -> Dict[str, Any]:
        """Calculate comprehensive daily metrics"""
        metrics = {}
        
        # Vulnerability counts
        cursor = vuln_conn.cursor()
        
        # Total vulnerabilities
        cursor.execute('SELECT COUNT(*) FROM vulnerability_records')
        metrics['total_vulnerabilities'] = cursor.fetchone()[0]
        
        # By severity
        cursor.execute('''
            SELECT severity, COUNT(*) 
            FROM vulnerability_records 
            GROUP BY severity
        ''')
        metrics['by_severity'] = dict(cursor.fetchall())
        
        # By state
        cursor.execute('''
            SELECT lifecycle_state, COUNT(*) 
            FROM vulnerability_records 
            GROUP BY lifecycle_state
        ''')
        metrics['by_state'] = dict(cursor.fetchall())
        
        # MTTR by severity
        metrics['mttr_by_severity'] = {}
        for severity in ['critical', 'high', 'medium', 'low']:
            cursor.execute('''
                SELECT AVG(
                    (julianday(
                        COALESCE(
                            (SELECT changed_date FROM state_history 
                             WHERE vulnerability_id = v.vulnerability_id 
                             AND to_state = 'fixed' 
                             ORDER BY changed_date DESC LIMIT 1),
                            datetime('now')
                        )
                    ) - julianday(v.created_date)) * 24
                ) as mttr_hours
                FROM vulnerability_records v
                WHERE v.severity = ?
                AND v.lifecycle_state IN ('fixed', 'verified', 'closed')
            ''', (severity,))
            result = cursor.fetchone()
            metrics['mttr_by_severity'][severity] = result[0] if result[0] else 0
        
        # SLA metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sla_breach = TRUE THEN 1 ELSE 0 END) as breached
            FROM vulnerability_records
        ''')
        total, breached = cursor.fetchone()
        metrics['sla_breach_count'] = breached
        metrics['sla_breach_rate'] = (breached / total * 100) if total > 0 else 0
        
        # Scan metrics (last 24 hours)
        yesterday = target_date - timedelta(days=1)
        cursor.execute('''
            SELECT COUNT(*) FROM scan_metrics 
            WHERE DATE(created_date) = ?
        ''', (target_date,))
        metrics['scan_count'] = cursor.fetchone()[0]
        
        # Asset coverage
        cursor.execute('SELECT COUNT(DISTINCT asset_id) FROM vulnerability_records')
        metrics['assets_scanned'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        metrics['total_assets'] = cursor.fetchone()[0]
        
        metrics['scan_coverage_rate'] = (
            metrics['assets_scanned'] / metrics['total_assets'] * 100
            if metrics['total_assets'] > 0 else 0
        )
        
        # False positive metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN lifecycle_state = 'false_positive' THEN 1 ELSE 0 END) as fp
            FROM vulnerability_records
        ''')
        total, fp = cursor.fetchone()
        metrics['false_positive_count'] = fp
        metrics['false_positive_rate'] = (fp / total * 100) if total > 0 else 0
        
        return metrics
    
    async def record_scan_metrics(self, scan_data: Dict[str, Any]) -> bool:
        """Record scan execution metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate duration
            start_time = datetime.fromisoformat(scan_data['start_time'])
            end_time = datetime.fromisoformat(scan_data['end_time'])
            duration = (end_time - start_time).total_seconds()
            
            # Count findings by severity
            findings = scan_data.get('findings', [])
            severity_counts = {
                'critical': len([f for f in findings if f.get('severity') == 'critical']),
                'high': len([f for f in findings if f.get('severity') == 'high']),
                'medium': len([f for f in findings if f.get('severity') == 'medium']),
                'low': len([f for f in findings if f.get('severity') == 'low'])
            }
            
            cursor.execute('''
                INSERT INTO scan_metrics 
                (scan_id, scan_type, asset_id, repository, start_time, end_time,
                 duration_seconds, findings_count, critical_count, high_count,
                 medium_count, low_count, scanner_errors, scan_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scan_data['scan_id'],
                scan_data['scan_type'],
                scan_data.get('asset_id'),
                scan_data.get('repository'),
                scan_data['start_time'],
                scan_data['end_time'],
                duration,
                len(findings),
                severity_counts['critical'],
                severity_counts['high'],
                severity_counts['medium'],
                severity_counts['low'],
                scan_data.get('errors', 0),
                scan_data.get('status', 'completed')
            ))
            
            conn.commit()
            logger.info(f"📊 Scan metrics recorded: {scan_data['scan_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording scan metrics: {str(e)}")
            return False
        finally:
            conn.close()
    
    async def record_remediation_metrics(self, vulnerability_id: str, 
                                       vulnerability_db: str) -> bool:
        """Record remediation lifecycle metrics"""
        # Get vulnerability data and state history
        vuln_conn = sqlite3.connect(vulnerability_db)
        cursor = vuln_conn.cursor()
        
        # Get vulnerability details
        cursor.execute('''
            SELECT v.vulnerability_id, v.severity, v.created_date, v.due_date, v.sla_breach,
                   a.business_criticality, a.environment
            FROM vulnerability_records v
            JOIN assets a ON v.asset_id = a.asset_id
            WHERE v.vulnerability_id = ?
        ''', (vulnerability_id,))
        
        vuln_data = cursor.fetchone()
        if not vuln_data:
            vuln_conn.close()
            return False
        
        # Get state transitions
        cursor.execute('''
            SELECT to_state, changed_date 
            FROM state_history 
            WHERE vulnerability_id = ?
            ORDER BY changed_date
        ''', (vulnerability_id,))
        
        state_changes = cursor.fetchall()
        vuln_conn.close()
        
        # Calculate metrics
        discovered_date = vuln_data[2]  # created_date
        severity = vuln_data[1]
        business_criticality = vuln_data[5]
        environment = vuln_data[6]
        
        # Build timeline
        timeline = {'discovered': discovered_date}
        for state, change_date in state_changes:
            if state == 'triaged':
                timeline['triaged'] = change_date
            elif state == 'in_progress':
                timeline['in_progress'] = change_date
            elif state == 'fixed':
                timeline['fixed'] = change_date
            elif state == 'verified':
                timeline['verified'] = change_date
            elif state == 'closed':
                timeline['closed'] = change_date
        
        # Calculate MTTR if fixed
        mttr_hours = None
        if 'fixed' in timeline:
            discovered = datetime.fromisoformat(discovered_date)
            fixed = datetime.fromisoformat(timeline['fixed'])
            mttr_hours = (fixed - discovered).total_seconds() / 3600
        
        # Store metrics
        metrics_conn = sqlite3.connect(self.db_path)
        cursor = metrics_conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO remediation_metrics 
                (vulnerability_id, discovered_date, triaged_date, assigned_date,
                 in_progress_date, fixed_date, verified_date, closed_date,
                 severity, business_criticality, environment, mttr_hours,
                 sla_hours, sla_breach)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vulnerability_id,
                timeline.get('discovered'),
                timeline.get('triaged'),
                timeline.get('assigned'),
                timeline.get('in_progress'),
                timeline.get('fixed'),
                timeline.get('verified'),
                timeline.get('closed'),
                severity,
                business_criticality,
                environment,
                mttr_hours,
                0,  # SLA hours calculation would go here
                vuln_data[4]  # sla_breach
            ))
            
            metrics_conn.commit()
            logger.info(f"📊 Remediation metrics recorded: {vulnerability_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording remediation metrics: {str(e)}")
            return False
        finally:
            metrics_conn.close()
    
    async def calculate_sla_performance(self) -> Dict[str, Any]:
        """Calculate SLA performance against targets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sla_performance = {}
        today = datetime.now().date()
        
        # Get latest daily metrics
        cursor.execute('''
            SELECT * FROM daily_metrics 
            ORDER BY metric_date DESC 
            LIMIT 1
        ''')
        latest_metrics = cursor.fetchone()
        
        if not latest_metrics:
            conn.close()
            return {}
        
        # Map column names
        columns = [desc[0] for desc in cursor.description]
        metrics_dict = dict(zip(columns, latest_metrics))
        
        # Calculate performance for each SLA target
        for sla_name, target in self.sla_targets.items():
            actual_value = None
            
            if sla_name == 'mttr_critical':
                actual_value = metrics_dict.get('mttr_critical_hours', 0)
            elif sla_name == 'mttr_high':
                actual_value = metrics_dict.get('mttr_high_hours', 0)
            elif sla_name == 'sla_breach_rate':
                actual_value = metrics_dict.get('sla_breach_rate', 0)
            elif sla_name == 'scan_coverage':
                actual_value = metrics_dict.get('scan_coverage_rate', 0)
            elif sla_name == 'false_positive_rate':
                actual_value = metrics_dict.get('false_positive_rate', 0)
            
            if actual_value is not None:
                # Calculate performance percentage
                if target.threshold_type == 'lower_is_better':
                    performance = max(0, (target.target_value - actual_value) / target.target_value * 100)
                else:  # higher_is_better
                    performance = min(100, actual_value / target.target_value * 100)
                
                # Determine status
                if target.threshold_type == 'lower_is_better':
                    if actual_value <= target.target_value:
                        status = 'green'
                    elif actual_value <= target.warning_threshold:
                        status = 'amber'
                    else:
                        status = 'red'
                else:  # higher_is_better
                    if actual_value >= target.target_value:
                        status = 'green'
                    elif actual_value >= target.warning_threshold:
                        status = 'amber'
                    else:
                        status = 'red'
                
                sla_performance[sla_name] = {
                    'name': target.name,
                    'target_value': target.target_value,
                    'actual_value': actual_value,
                    'performance_percentage': performance,
                    'status': status,
                    'unit': target.unit
                }
                
                # Store in database
                cursor.execute('''
                    INSERT INTO sla_performance 
                    (sla_name, target_value, actual_value, performance_percentage, status, metric_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (sla_name, target.target_value, actual_value, performance, status, today))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 SLA performance calculated for {len(sla_performance)} targets")
        return sla_performance
    
    async def generate_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Generate trend analysis for key metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get historical data
        cursor.execute('''
            SELECT metric_date, total_vulnerabilities, critical_vulnerabilities,
                   high_vulnerabilities, sla_breach_rate, scan_coverage_rate,
                   mttr_critical_hours, mttr_high_hours
            FROM daily_metrics 
            WHERE metric_date >= date('now', '-{} days')
            ORDER BY metric_date
        '''.format(days))
        
        historical_data = cursor.fetchall()
        conn.close()
        
        if len(historical_data) < 2:
            return {'error': 'Insufficient historical data for trend analysis'}
        
        # Process trends
        trends = {}
        
        # Organize data by metric
        metrics_data = defaultdict(list)
        dates = []
        
        for row in historical_data:
            dates.append(row[0])
            metrics_data['total_vulnerabilities'].append(row[1])
            metrics_data['critical_vulnerabilities'].append(row[2])
            metrics_data['high_vulnerabilities'].append(row[3])
            metrics_data['sla_breach_rate'].append(row[4])
            metrics_data['scan_coverage_rate'].append(row[5])
            metrics_data['mttr_critical_hours'].append(row[6])
            metrics_data['mttr_high_hours'].append(row[7])
        
        # Calculate trends
        for metric_name, values in metrics_data.items():
            if len(values) >= 2:
                # Calculate trend direction and percentage change
                start_value = values[0] if values[0] else 0
                end_value = values[-1] if values[-1] else 0
                
                if start_value > 0:
                    percentage_change = ((end_value - start_value) / start_value) * 100
                else:
                    percentage_change = 0
                
                # Determine trend direction
                if percentage_change > 5:
                    trend_direction = 'increasing'
                elif percentage_change < -5:
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
                
                # Calculate average and standard deviation
                avg_value = statistics.mean(values)
                std_dev = statistics.stdev(values) if len(values) > 1 else 0
                
                trends[metric_name] = {
                    'start_value': start_value,
                    'end_value': end_value,
                    'percentage_change': round(percentage_change, 2),
                    'trend_direction': trend_direction,
                    'average': round(avg_value, 2),
                    'std_deviation': round(std_dev, 2),
                    'data_points': len(values)
                }
        
        logger.info(f"📈 Trend analysis generated for {len(trends)} metrics over {days} days")
        return {
            'period_days': days,
            'date_range': f"{dates[0]} to {dates[-1]}",
            'trends': trends
        }
    
    async def get_executive_dashboard(self) -> Dict[str, Any]:
        """Generate executive-level security dashboard"""
        # Get latest metrics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Latest daily metrics
        cursor.execute('''
            SELECT * FROM daily_metrics 
            ORDER BY metric_date DESC 
            LIMIT 1
        ''')
        latest_metrics = cursor.fetchone()
        
        if not latest_metrics:
            conn.close()
            return {'error': 'No metrics data available'}
        
        columns = [desc[0] for desc in cursor.description]
        metrics_dict = dict(zip(columns, latest_metrics))
        
        # SLA performance
        sla_performance = await self.calculate_sla_performance()
        
        # 30-day trends
        trends = await self.generate_trend_analysis(30)
        
        # Risk score distribution
        vuln_conn = sqlite3.connect("vulnerability_management.db")
        vuln_cursor = vuln_conn.cursor()
        
        vuln_cursor.execute('''
            SELECT 
                CASE 
                    WHEN risk_score >= 9.0 THEN 'Critical Risk'
                    WHEN risk_score >= 7.0 THEN 'High Risk'
                    WHEN risk_score >= 5.0 THEN 'Medium Risk'
                    ELSE 'Low Risk'
                END as risk_category,
                COUNT(*) as count
            FROM vulnerability_records
            WHERE lifecycle_state NOT IN ('closed', 'verified', 'false_positive')
            GROUP BY risk_category
        ''')
        risk_distribution = dict(vuln_cursor.fetchall())
        vuln_conn.close()
        
        conn.close()
        
        # Build executive dashboard
        dashboard = {
            'summary': {
                'total_vulnerabilities': metrics_dict.get('total_vulnerabilities', 0),
                'critical_vulnerabilities': metrics_dict.get('critical_vulnerabilities', 0),
                'high_vulnerabilities': metrics_dict.get('high_vulnerabilities', 0),
                'sla_breach_rate': metrics_dict.get('sla_breach_rate', 0),
                'scan_coverage': metrics_dict.get('scan_coverage_rate', 0),
                'mttr_critical': metrics_dict.get('mttr_critical_hours', 0)
            },
            'sla_performance': sla_performance,
            'risk_distribution': risk_distribution,
            'trends': trends.get('trends', {}),
            'generated_at': datetime.now().isoformat(),
            'period': 'Last 30 days'
        }
        
        logger.info("📊 Executive dashboard generated")
        return dashboard

# Export main class
__all__ = ['MetricsKPIEngine', 'SecurityMetrics', 'SLATarget']
