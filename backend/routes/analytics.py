import logging
import traceback
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from models.report import ScanReport, ScanStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics"])


@router.get("/analytics/overview")
async def get_analytics_overview(days_back: int = 30):
    """Get analytics overview from database - fetches real scan data"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)

        reports = await ScanReport.find(
            ScanReport.created_at >= cutoff_date
        ).to_list()

        total_scans = len(reports)
        completed_scans = len([r for r in reports if r.status == ScanStatus.COMPLETED])
        failed_scans = len([r for r in reports if r.status == ScanStatus.FAILED])

        vulnerability_summary = {
            "critical": sum(r.findings_by_severity.get("critical", 0) for r in reports),
            "high": sum(r.findings_by_severity.get("high", 0) for r in reports),
            "medium": sum(r.findings_by_severity.get("medium", 0) for r in reports),
            "low": sum(r.findings_by_severity.get("low", 0) for r in reports),
            "info": sum(r.findings_by_severity.get("info", 0) for r in reports),
        }

        scanner_performance = {}
        for report in reports:
            for scan_result in report.scan_results:
                scanner = scan_result.scanner.value if hasattr(scan_result.scanner, 'value') else str(scan_result.scanner)
                if scanner not in scanner_performance:
                    scanner_performance[scanner] = {
                        "total_runs": 0,
                        "successful_runs": 0,
                        "total_findings": 0,
                        "avg_duration": 0,
                        "total_duration": 0,
                    }

                scanner_performance[scanner]["total_runs"] += 1
                if scan_result.status == ScanStatus.COMPLETED:
                    scanner_performance[scanner]["successful_runs"] += 1
                    scanner_performance[scanner]["total_findings"] += len(scan_result.findings)
                    if scan_result.duration_seconds:
                        scanner_performance[scanner]["total_duration"] += scan_result.duration_seconds

        for scanner, stats in scanner_performance.items():
            if stats["successful_runs"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["successful_runs"]
            del stats["total_duration"]

        project_findings = {}
        for report in reports:
            project = report.project_name
            if project not in project_findings:
                project_findings[project] = {
                    "project_name": project,
                    "total_findings": 0,
                    "scans_count": 0,
                    "critical_findings": 0,
                    "high_findings": 0,
                }

            project_findings[project]["total_findings"] += report.total_findings
            project_findings[project]["scans_count"] += 1
            project_findings[project]["critical_findings"] += report.findings_by_severity.get("critical", 0)
            project_findings[project]["high_findings"] += report.findings_by_severity.get("high", 0)

        top_projects = sorted(
            project_findings.values(),
            key=lambda x: x["total_findings"],
            reverse=True,
        )[:10]

        return {
            "period": {
                "days_back": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat(),
            },
            "scan_summary": {
                "total_scans": total_scans,
                "completed_scans": completed_scans,
                "failed_scans": failed_scans,
                "success_rate": (completed_scans / total_scans * 100) if total_scans > 0 else 0,
            },
            "vulnerability_summary": vulnerability_summary,
            "scanner_performance": scanner_performance,
            "top_projects": top_projects,
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        logger.error(f"Analytics error traceback: {traceback.format_exc()}")
        return {
            "period": {"days_back": days_back},
            "scan_summary": {
                "total_scans": 0,
                "completed_scans": 0,
                "failed_scans": 0,
                "success_rate": 0,
            },
            "vulnerability_summary": {
                "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0,
            },
            "scanner_performance": {},
            "top_projects": [],
        }
