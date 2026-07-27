"""Analytics overview endpoint."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.report import ScanReport, ScanStatus
from models.user import User
from routes.dependencies import get_current_user
from routes.reports.dependencies import get_user_project_ids
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analytics/overview")
async def get_analytics_overview(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get analytics overview for the specified time period"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        user_id = str(current_user.id)

        accessible_project_ids = await get_user_project_ids(user_id)

        from beanie.operators import In, Or

        query_conditions = [ScanReport.created_at >= cutoff_date]
        user_access_conditions = [ScanReport.user_id == user_id]
        if accessible_project_ids:
            user_access_conditions.append(In(ScanReport.project_id, accessible_project_ids))

        query = ScanReport.find(*query_conditions, Or(*user_access_conditions))

        if project_name:
            query = query.find(ScanReport.project_name == project_name)

        reports = await query.to_list()

        total_scans = len(reports)
        completed_scans = len([r for r in reports if r.status == ScanStatus.COMPLETED])
        failed_scans = len([r for r in reports if r.status == ScanStatus.FAILED])

        total_findings = {
            "critical": sum(r.findings_by_severity.get("critical", 0) for r in reports),
            "high": sum(r.findings_by_severity.get("high", 0) for r in reports),
            "medium": sum(r.findings_by_severity.get("medium", 0) for r in reports),
            "low": sum(r.findings_by_severity.get("low", 0) for r in reports),
            "info": sum(r.findings_by_severity.get("info", 0) for r in reports),
        }

        scanner_stats = {}
        for report in reports:
            for scan_result in report.scan_results:
                scanner = scan_result.scanner.value
                if scanner not in scanner_stats:
                    scanner_stats[scanner] = {"total_runs": 0, "successful_runs": 0, "total_findings": 0, "avg_duration": 0}
                scanner_stats[scanner]["total_runs"] += 1
                if scan_result.status == ScanStatus.COMPLETED:
                    scanner_stats[scanner]["successful_runs"] += 1
                    scanner_stats[scanner]["total_findings"] += len(scan_result.findings)
                    if scan_result.duration_seconds:
                        scanner_stats[scanner]["avg_duration"] += scan_result.duration_seconds

        for stats in scanner_stats.values():
            if stats["successful_runs"] > 0:
                stats["avg_duration"] = stats["avg_duration"] / stats["successful_runs"]

        project_findings = {}
        for report in reports:
            project = report.project_name
            if project not in project_findings:
                project_findings[project] = {"total_findings": 0, "scans_count": 0, "critical_findings": 0, "high_findings": 0}
            project_findings[project]["total_findings"] += report.total_findings
            project_findings[project]["scans_count"] += 1
            project_findings[project]["critical_findings"] += report.findings_by_severity.get("critical", 0)
            project_findings[project]["high_findings"] += report.findings_by_severity.get("high", 0)

        top_projects = sorted(
            project_findings.items(), key=lambda x: x[1]["total_findings"], reverse=True
        )[:10]

        return {
            "period": {
                "days_back": days_back,
                "start_date": cutoff_date,
                "end_date": datetime.now(timezone.utc),
            },
            "scan_summary": {
                "total_scans": total_scans,
                "completed_scans": completed_scans,
                "failed_scans": failed_scans,
                "success_rate": (completed_scans / total_scans * 100) if total_scans > 0 else 0,
            },
            "vulnerability_summary": total_findings,
            "scanner_performance": scanner_stats,
            "top_projects": [
                {
                    "project_name": project,
                    "total_findings": stats["total_findings"],
                    "scans_count": stats["scans_count"],
                    "critical_findings": stats["critical_findings"],
                    "high_findings": stats["high_findings"],
                    "avg_findings_per_scan": stats["total_findings"] / stats["scans_count"] if stats["scans_count"] > 0 else 0,
                }
                for project, stats in top_projects
            ],
        }

    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
