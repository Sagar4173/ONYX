"""
Security Trends Analytics Service
Track security posture over time, visualize trends, and measure improvement
Provides data for severity trends dashboard and security KPIs
"""
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Import canonical enums from models.base (SINGLE SOURCE OF TRUTH)
from models.base import TrendDirection, TrendPeriod

logger = logging.getLogger(__name__)


@dataclass
class SeverityCount:
    """Count of findings by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.info

    @property
    def weighted_score(self) -> float:
        """Calculate weighted security score (higher = more vulnerabilities = worse)"""
        return (
            self.critical * 10 +
            self.high * 5 +
            self.medium * 2 +
            self.low * 1 +
            self.info * 0.1
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            "critical": self.critical,
            "high": self.high,
            "medium": self.medium,
            "low": self.low,
            "info": self.info,
            "total": self.total
        }


@dataclass
class TrendDataPoint:
    """Single data point in a trend"""
    timestamp: datetime
    severity_counts: SeverityCount
    security_score: float  # 0-100, higher is better
    risk_score: float  # 0-100, lower is better
    scan_count: int = 0
    fixed_count: int = 0
    new_count: int = 0
    mean_time_to_fix: Optional[float] = None  # in hours
    scanner_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class TrendAnalysis:
    """Analysis of security trends"""
    period: TrendPeriod
    start_date: datetime
    end_date: datetime
    data_points: List[TrendDataPoint]
    
    # Overall metrics
    direction: TrendDirection
    improvement_percentage: float
    avg_security_score: float
    avg_risk_score: float
    
    # Velocity metrics
    avg_new_per_period: float
    avg_fixed_per_period: float
    fix_rate: float  # fixed / new ratio
    
    # Projections
    projected_security_score_30d: float
    time_to_target_score: Optional[int] = None  # days to reach target
    
    # Highlights
    best_period: Optional[TrendDataPoint] = None
    worst_period: Optional[TrendDataPoint] = None
    notable_changes: List[str] = field(default_factory=list)


@dataclass
class SecurityMetrics:
    """Current security metrics snapshot"""
    timestamp: datetime
    security_score: float
    risk_score: float
    severity_counts: SeverityCount
    open_findings: int
    fixed_last_7d: int
    fixed_last_30d: int
    new_last_7d: int
    new_last_30d: int
    mttr_hours: Optional[float] = None  # Mean Time To Remediate
    compliance_rate: float = 0.0
    coverage_percentage: float = 0.0


class SecurityTrendsService:
    """
    Security Trends Analytics Service
    Tracks security posture over time and provides trend analysis
    for dashboard visualizations and security KPIs.
    """

    def __init__(self, db=None):
        self.db = db
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=15)

    async def get_severity_trends(
        self,
        project_id: Optional[str] = None,
        period: TrendPeriod = TrendPeriod.WEEKLY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 12
    ) -> TrendAnalysis:
        """
        Get severity trend analysis over time.
        
        Args:
            project_id: Optional project filter
            period: Aggregation period (daily, weekly, monthly)
            start_date: Start of analysis period
            end_date: End of analysis period
            limit: Maximum number of data points
            
        Returns:
            TrendAnalysis with historical data and projections
        """
        # Set default date range
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = self._get_period_start(end_date, period, limit)

        # Get historical scan data
        data_points = await self._aggregate_scan_data(
            project_id=project_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )

        # Calculate trend metrics
        direction = self._calculate_trend_direction(data_points)
        improvement = self._calculate_improvement(data_points)
        
        # Calculate averages
        if data_points:
            avg_security = statistics.mean(dp.security_score for dp in data_points)
            avg_risk = statistics.mean(dp.risk_score for dp in data_points)
            avg_new = statistics.mean(dp.new_count for dp in data_points)
            avg_fixed = statistics.mean(dp.fixed_count for dp in data_points)
        else:
            avg_security = avg_risk = avg_new = avg_fixed = 0

        fix_rate = avg_fixed / avg_new if avg_new > 0 else 1.0

        # Project future score
        projected_score = self._project_future_score(data_points, days=30)
        time_to_target = self._estimate_time_to_target(data_points, target_score=90)

        # Find best/worst periods
        best_period = max(data_points, key=lambda dp: dp.security_score) if data_points else None
        worst_period = min(data_points, key=lambda dp: dp.security_score) if data_points else None

        # Generate notable changes
        notable_changes = self._identify_notable_changes(data_points)

        return TrendAnalysis(
            period=period,
            start_date=start_date,
            end_date=end_date,
            data_points=data_points,
            direction=direction,
            improvement_percentage=improvement,
            avg_security_score=avg_security,
            avg_risk_score=avg_risk,
            avg_new_per_period=avg_new,
            avg_fixed_per_period=avg_fixed,
            fix_rate=fix_rate,
            projected_security_score_30d=projected_score,
            time_to_target_score=time_to_target,
            best_period=best_period,
            worst_period=worst_period,
            notable_changes=notable_changes
        )

    async def get_current_metrics(
        self,
        project_id: Optional[str] = None
    ) -> SecurityMetrics:
        """Get current security metrics snapshot"""
        
        now = datetime.now(timezone.utc)
        
        # Get current severity counts
        severity_counts = await self._get_current_severity_counts(project_id)
        
        # Calculate scores
        security_score = self._calculate_security_score(severity_counts)
        risk_score = self._calculate_risk_score(severity_counts)
        
        # Get fix/new counts for last periods
        fixed_7d = await self._count_fixed_findings(project_id, days=7)
        fixed_30d = await self._count_fixed_findings(project_id, days=30)
        new_7d = await self._count_new_findings(project_id, days=7)
        new_30d = await self._count_new_findings(project_id, days=30)
        
        # Calculate MTTR
        mttr = await self._calculate_mttr(project_id)
        
        # Calculate compliance and coverage
        compliance_rate = await self._calculate_compliance_rate(project_id)
        coverage = await self._calculate_coverage(project_id)

        return SecurityMetrics(
            timestamp=now,
            security_score=security_score,
            risk_score=risk_score,
            severity_counts=severity_counts,
            open_findings=severity_counts.total,
            fixed_last_7d=fixed_7d,
            fixed_last_30d=fixed_30d,
            new_last_7d=new_7d,
            new_last_30d=new_30d,
            mttr_hours=mttr,
            compliance_rate=compliance_rate,
            coverage_percentage=coverage
        )

    async def get_scanner_trends(
        self,
        project_id: Optional[str] = None,
        period: TrendPeriod = TrendPeriod.WEEKLY,
        limit: int = 12
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get trends broken down by scanner type"""
        
        end_date = datetime.now(timezone.utc)
        start_date = self._get_period_start(end_date, period, limit)
        
        # Aggregate by scanner
        scanner_data = defaultdict(list)
        
        data_points = await self._aggregate_scan_data(
            project_id=project_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        for dp in data_points:
            for scanner, count in dp.scanner_breakdown.items():
                scanner_data[scanner].append({
                    "timestamp": dp.timestamp.isoformat(),
                    "count": count
                })

        return dict(scanner_data)

    async def get_comparison_report(
        self,
        project_id: Optional[str] = None,
        compare_periods: int = 2
    ) -> Dict[str, Any]:
        """
        Generate period-over-period comparison report.
        Compare current period with previous period.
        """
        now = datetime.now(timezone.utc)
        
        # Current period (last 30 days)
        current_start = now - timedelta(days=30)
        current_metrics = await self.get_severity_trends(
            project_id=project_id,
            period=TrendPeriod.DAILY,
            start_date=current_start,
            end_date=now,
            limit=30
        )
        
        # Previous period (30-60 days ago)
        prev_end = current_start
        prev_start = prev_end - timedelta(days=30)
        prev_metrics = await self.get_severity_trends(
            project_id=project_id,
            period=TrendPeriod.DAILY,
            start_date=prev_start,
            end_date=prev_end,
            limit=30
        )
        
        # Calculate changes
        security_change = current_metrics.avg_security_score - prev_metrics.avg_security_score
        risk_change = current_metrics.avg_risk_score - prev_metrics.avg_risk_score
        
        current_total = sum(dp.severity_counts.total for dp in current_metrics.data_points)
        prev_total = sum(dp.severity_counts.total for dp in prev_metrics.data_points)
        finding_change = ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
        
        return {
            "current_period": {
                "start": current_start.isoformat(),
                "end": now.isoformat(),
                "avg_security_score": current_metrics.avg_security_score,
                "avg_risk_score": current_metrics.avg_risk_score,
                "total_findings": current_total,
                "fix_rate": current_metrics.fix_rate
            },
            "previous_period": {
                "start": prev_start.isoformat(),
                "end": prev_end.isoformat(),
                "avg_security_score": prev_metrics.avg_security_score,
                "avg_risk_score": prev_metrics.avg_risk_score,
                "total_findings": prev_total,
                "fix_rate": prev_metrics.fix_rate
            },
            "changes": {
                "security_score": security_change,
                "security_score_pct": (security_change / prev_metrics.avg_security_score * 100) if prev_metrics.avg_security_score > 0 else 0,
                "risk_score": risk_change,
                "findings_pct": finding_change,
                "direction": current_metrics.direction.value
            },
            "insights": self._generate_comparison_insights(current_metrics, prev_metrics)
        }

    async def get_dashboard_data(
        self,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all data needed for the security trends dashboard.
        Single API call for dashboard rendering.
        """
        # Current metrics
        current = await self.get_current_metrics(project_id)
        
        # Weekly trends for sparklines
        weekly_trends = await self.get_severity_trends(
            project_id=project_id,
            period=TrendPeriod.WEEKLY,
            limit=12
        )
        
        # Daily trends for detailed chart
        daily_trends = await self.get_severity_trends(
            project_id=project_id,
            period=TrendPeriod.DAILY,
            limit=30
        )
        
        # Scanner breakdown
        scanner_trends = await self.get_scanner_trends(
            project_id=project_id,
            period=TrendPeriod.WEEKLY,
            limit=8
        )
        
        # Comparison report
        comparison = await self.get_comparison_report(project_id)

        return {
            "current": {
                "security_score": current.security_score,
                "risk_score": current.risk_score,
                "severity_counts": current.severity_counts.to_dict(),
                "open_findings": current.open_findings,
                "fixed_7d": current.fixed_last_7d,
                "fixed_30d": current.fixed_last_30d,
                "new_7d": current.new_last_7d,
                "new_30d": current.new_last_30d,
                "mttr_hours": current.mttr_hours,
                "compliance_rate": current.compliance_rate,
                "coverage": current.coverage_percentage
            },
            "trends": {
                "direction": weekly_trends.direction.value,
                "improvement_pct": weekly_trends.improvement_percentage,
                "projected_score_30d": weekly_trends.projected_security_score_30d,
                "time_to_target": weekly_trends.time_to_target_score,
                "fix_rate": weekly_trends.fix_rate
            },
            "charts": {
                "weekly": [
                    {
                        "date": dp.timestamp.isoformat(),
                        "security_score": dp.security_score,
                        "risk_score": dp.risk_score,
                        "critical": dp.severity_counts.critical,
                        "high": dp.severity_counts.high,
                        "medium": dp.severity_counts.medium,
                        "low": dp.severity_counts.low,
                        "total": dp.severity_counts.total,
                        "fixed": dp.fixed_count,
                        "new": dp.new_count
                    }
                    for dp in weekly_trends.data_points
                ],
                "daily": [
                    {
                        "date": dp.timestamp.isoformat(),
                        "security_score": dp.security_score,
                        "total": dp.severity_counts.total,
                        "fixed": dp.fixed_count,
                        "new": dp.new_count
                    }
                    for dp in daily_trends.data_points
                ],
                "by_scanner": scanner_trends
            },
            "comparison": comparison,
            "notable_changes": weekly_trends.notable_changes
        }

    # ============ Private Methods ============

    async def _aggregate_scan_data(
        self,
        project_id: Optional[str],
        period: TrendPeriod,
        start_date: datetime,
        end_date: datetime
    ) -> List[TrendDataPoint]:
        """Aggregate scan data into period buckets"""
        
        # This would normally query the database
        # For now, generate sample data for demonstration
        data_points = []
        current = start_date
        
        period_delta = self._get_period_delta(period)
        
        # Simulate getting data from database
        while current < end_date:
            # In real implementation, query DB for this period
            severity = await self._get_severity_for_period(project_id, current, current + period_delta)
            fixed = await self._get_fixed_for_period(project_id, current, current + period_delta)
            new = await self._get_new_for_period(project_id, current, current + period_delta)
            
            security_score = self._calculate_security_score(severity)
            risk_score = self._calculate_risk_score(severity)
            
            data_points.append(TrendDataPoint(
                timestamp=current,
                severity_counts=severity,
                security_score=security_score,
                risk_score=risk_score,
                scan_count=1,  # Would be from DB
                fixed_count=fixed,
                new_count=new,
                scanner_breakdown={
                    "semgrep": severity.high + severity.medium,
                    "trivy": severity.critical + severity.high,
                    "gitleaks": severity.low,
                    "bandit": severity.medium
                }
            ))
            
            current += period_delta

        return data_points

    async def _get_current_severity_counts(self, project_id: Optional[str]) -> SeverityCount:
        """Get current open findings by severity"""
        # In real implementation, query database
        # For demo, return sample data
        return SeverityCount(
            critical=2,
            high=8,
            medium=15,
            low=25,
            info=10
        )

    async def _get_severity_for_period(
        self, 
        project_id: Optional[str],
        start: datetime,
        end: datetime
    ) -> SeverityCount:
        """Get severity counts for a time period"""
        # Would query database in real implementation
        import random
        return SeverityCount(
            critical=random.randint(0, 5),
            high=random.randint(3, 15),
            medium=random.randint(10, 30),
            low=random.randint(15, 40),
            info=random.randint(5, 20)
        )

    async def _get_fixed_for_period(
        self,
        project_id: Optional[str],
        start: datetime,
        end: datetime
    ) -> int:
        """Count fixed findings in period"""
        import random
        return random.randint(5, 25)

    async def _get_new_for_period(
        self,
        project_id: Optional[str],
        start: datetime,
        end: datetime
    ) -> int:
        """Count new findings in period"""
        import random
        return random.randint(3, 20)

    async def _count_fixed_findings(self, project_id: Optional[str], days: int) -> int:
        """Count findings fixed in last N days"""
        import random
        return random.randint(10, 50) * (days // 7)

    async def _count_new_findings(self, project_id: Optional[str], days: int) -> int:
        """Count new findings in last N days"""
        import random
        return random.randint(5, 30) * (days // 7)

    async def _calculate_mttr(self, project_id: Optional[str]) -> Optional[float]:
        """Calculate Mean Time To Remediate in hours"""
        import random
        return random.uniform(24, 168)  # 1-7 days in hours

    async def _calculate_compliance_rate(self, project_id: Optional[str]) -> float:
        """Calculate overall compliance rate"""
        import random
        return random.uniform(0.7, 0.95)

    async def _calculate_coverage(self, project_id: Optional[str]) -> float:
        """Calculate scan coverage percentage"""
        import random
        return random.uniform(0.8, 1.0)

    def _calculate_security_score(self, severity: SeverityCount) -> float:
        """
        Calculate security score (0-100, higher is better).
        Based on weighted severity counts.
        """
        if severity.total == 0:
            return 100.0

        weighted = severity.weighted_score
        # Normalize: 0 vulns = 100, heavy vulns = low score
        # Max theoretical score for normalization
        max_weighted = 100  # Assume 10 critical vulns as worst case
        
        score = max(0, 100 - (weighted / max_weighted * 100))
        return round(min(100, score), 1)

    def _calculate_risk_score(self, severity: SeverityCount) -> float:
        """
        Calculate risk score (0-100, lower is better).
        Inverse of security score with focus on critical/high.
        """
        if severity.total == 0:
            return 0.0

        # Weight critical and high more heavily
        risk = (
            severity.critical * 25 +
            severity.high * 15 +
            severity.medium * 5 +
            severity.low * 1
        )
        
        # Normalize to 0-100
        score = min(100, risk)
        return round(score, 1)

    def _calculate_trend_direction(self, data_points: List[TrendDataPoint]) -> TrendDirection:
        """Determine overall trend direction"""
        if len(data_points) < 2:
            return TrendDirection.STABLE

        # Compare first half to second half
        mid = len(data_points) // 2
        first_half_avg = statistics.mean(dp.security_score for dp in data_points[:mid])
        second_half_avg = statistics.mean(dp.security_score for dp in data_points[mid:])
        
        diff = second_half_avg - first_half_avg
        
        if diff > 5:
            return TrendDirection.IMPROVING
        elif diff < -5:
            return TrendDirection.DEGRADING
        else:
            return TrendDirection.STABLE

    def _calculate_improvement(self, data_points: List[TrendDataPoint]) -> float:
        """Calculate improvement percentage"""
        if len(data_points) < 2:
            return 0.0

        first_score = data_points[0].security_score
        last_score = data_points[-1].security_score
        
        if first_score == 0:
            return 0.0
            
        return round(((last_score - first_score) / first_score) * 100, 1)

    def _project_future_score(self, data_points: List[TrendDataPoint], days: int) -> float:
        """Project security score N days into future using linear regression"""
        if len(data_points) < 3:
            return data_points[-1].security_score if data_points else 50.0

        # Simple linear projection
        scores = [dp.security_score for dp in data_points]
        n = len(scores)
        
        # Calculate slope using least squares
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(scores)
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Project forward
        periods_forward = days / 7  # Assuming weekly data
        projected = scores[-1] + (slope * periods_forward)
        
        return round(max(0, min(100, projected)), 1)

    def _estimate_time_to_target(
        self, 
        data_points: List[TrendDataPoint],
        target_score: float
    ) -> Optional[int]:
        """Estimate days to reach target security score"""
        if len(data_points) < 2:
            return None

        current_score = data_points[-1].security_score
        
        if current_score >= target_score:
            return 0

        # Calculate average improvement rate
        scores = [dp.security_score for dp in data_points]
        if len(scores) < 2:
            return None
            
        avg_improvement = (scores[-1] - scores[0]) / len(scores)
        
        if avg_improvement <= 0:
            return None  # Not improving

        points_needed = target_score - current_score
        periods_needed = points_needed / avg_improvement
        
        # Convert periods to days (assuming weekly)
        days = int(periods_needed * 7)
        return max(1, days)

    def _identify_notable_changes(self, data_points: List[TrendDataPoint]) -> List[str]:
        """Identify notable changes in the trend data"""
        changes = []
        
        if len(data_points) < 2:
            return changes

        # Check for significant score changes
        for i in range(1, len(data_points)):
            prev = data_points[i - 1]
            curr = data_points[i]
            
            score_diff = curr.security_score - prev.security_score
            
            if score_diff > 10:
                changes.append(f"Security score improved by {score_diff:.1f} points on {curr.timestamp.strftime('%Y-%m-%d')}")
            elif score_diff < -10:
                changes.append(f"Security score dropped by {abs(score_diff):.1f} points on {curr.timestamp.strftime('%Y-%m-%d')}")
            
            # Check for critical vulnerability spikes
            if curr.severity_counts.critical > prev.severity_counts.critical + 2:
                changes.append(f"Critical vulnerabilities increased on {curr.timestamp.strftime('%Y-%m-%d')}")

        return changes[:5]  # Limit to 5 most notable

    def _generate_comparison_insights(
        self,
        current: TrendAnalysis,
        previous: TrendAnalysis
    ) -> List[str]:
        """Generate insights from period comparison"""
        insights = []
        
        score_change = current.avg_security_score - previous.avg_security_score
        
        if score_change > 5:
            insights.append(f"Security posture improved by {score_change:.1f} points compared to last period")
        elif score_change < -5:
            insights.append(f"Security posture degraded by {abs(score_change):.1f} points - action recommended")
        
        if current.fix_rate > previous.fix_rate * 1.2:
            insights.append("Vulnerability remediation velocity has increased significantly")
        elif current.fix_rate < previous.fix_rate * 0.8:
            insights.append("Remediation velocity has decreased - consider allocating more resources")
        
        if current.avg_new_per_period < previous.avg_new_per_period * 0.7:
            insights.append("New vulnerabilities are being introduced at a lower rate")
        elif current.avg_new_per_period > previous.avg_new_per_period * 1.3:
            insights.append("New vulnerabilities are increasing - review recent changes")

        return insights

    def _get_period_start(
        self,
        end_date: datetime,
        period: TrendPeriod,
        limit: int
    ) -> datetime:
        """Calculate start date based on period and limit"""
        delta = self._get_period_delta(period)
        return end_date - (delta * limit)

    def _get_period_delta(self, period: TrendPeriod) -> timedelta:
        """Get timedelta for a period"""
        deltas = {
            TrendPeriod.DAILY: timedelta(days=1),
            TrendPeriod.WEEKLY: timedelta(weeks=1),
            TrendPeriod.MONTHLY: timedelta(days=30),
            TrendPeriod.QUARTERLY: timedelta(days=90),
            TrendPeriod.YEARLY: timedelta(days=365)
        }
        return deltas.get(period, timedelta(weeks=1))


# Singleton instance
_trends_service: Optional[SecurityTrendsService] = None


def get_security_trends_service(db=None) -> SecurityTrendsService:
    """Get security trends service instance"""
    global _trends_service
    if _trends_service is None:
        _trends_service = SecurityTrendsService(db)
    return _trends_service
