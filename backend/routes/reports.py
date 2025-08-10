"""
Reports routes for retrieving scan results and analytics
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from bson import ObjectId

from models.report import ScanReport, ScanStatus, SeverityLevel, ScannerType
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/")
async def list_reports(
    limit: int = Query(50, ge=1, le=100, description="Number of reports to return"),
    skip: int = Query(0, ge=0, description="Number of reports to skip"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    status: Optional[ScanStatus] = Query(None, description="Filter by scan status"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    severity_filter: Optional[SeverityLevel] = Query(None, description="Filter by minimum severity"),
    days_back: Optional[int] = Query(None, ge=1, le=365, description="Filter by days back from now")
) -> Dict[str, Any]:
    """
    List scan reports with filtering and pagination
    
    Returns a paginated list of scan reports with optional filtering by:
    - Project name
    - Scan status
    - Branch
    - Minimum severity level
    - Time range (days back from current time)
    """
    try:
        # Build query
        query = ScanReport.find()
        
        # Apply filters
        if project_name:
            query = query.find(ScanReport.project_name == project_name)
        
        if status:
            query = query.find(ScanReport.status == status)
        
        if branch:
            query = query.find(ScanReport.git_metadata.branch == branch)
        
        if days_back:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            query = query.find(ScanReport.created_at >= cutoff_date)
        
        # Apply severity filter by checking if any findings have the minimum severity
        if severity_filter:
            severity_order = {
                SeverityLevel.CRITICAL: 4,
                SeverityLevel.HIGH: 3,
                SeverityLevel.MEDIUM: 2,
                SeverityLevel.LOW: 1,
                SeverityLevel.INFO: 0
            }
            min_severity_level = severity_order[severity_filter]
            
            # Filter reports that have findings with at least the minimum severity
            if severity_filter == SeverityLevel.CRITICAL:
                query = query.find(ScanReport.findings_by_severity.critical > 0)
            elif severity_filter == SeverityLevel.HIGH:
                query = query.find({
                    "$or": [
                        {"findings_by_severity.critical": {"$gt": 0}},
                        {"findings_by_severity.high": {"$gt": 0}}
                    ]
                })
            elif severity_filter == SeverityLevel.MEDIUM:
                query = query.find({
                    "$or": [
                        {"findings_by_severity.critical": {"$gt": 0}},
                        {"findings_by_severity.high": {"$gt": 0}},
                        {"findings_by_severity.medium": {"$gt": 0}}
                    ]
                })
        
        # Get total count for pagination
        total = await query.count()
        
        # Get reports with pagination, sorted by creation date (newest first)
        reports = await query.sort(-ScanReport.created_at).skip(skip).limit(limit).to_list()
        
        # Format response
        report_list = []
        for report in reports:
            report_data = {
                "id": str(report.id),
                "project_name": report.project_name,
                "scan_id": report.scan_id,
                "status": report.status.value,
                "repository_url": report.git_metadata.repository_url,
                "branch": report.git_metadata.branch,
                "commit_hash": report.git_metadata.commit_hash,
                "total_findings": report.total_findings,
                "findings_by_severity": report.findings_by_severity,
                "created_at": report.created_at,
                "completed_at": report.completed_at,
                "duration_seconds": report.duration_seconds,
                "has_ai_analysis": report.ai_analysis is not None
            }
            report_list.append(report_data)
        
        return {
            "reports": report_list,
            "pagination": {
                "total": total,
                "limit": limit,
                "skip": skip,
                "has_next": skip + limit < total,
                "has_previous": skip > 0
            },
            "filters_applied": {
                "project_name": project_name,
                "status": status.value if status else None,
                "branch": branch,
                "severity_filter": severity_filter.value if severity_filter else None,
                "days_back": days_back
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reports: {e}")


@router.get("/{report_id}")
async def get_report(report_id: str) -> Dict[str, Any]:
    """
    Get detailed scan report by ID
    
    Returns complete scan report including:
    - Basic report information
    - Git metadata
    - All scan results from each scanner
    - Individual vulnerability findings
    - AI analysis (if available)
    - Notification status
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        # Find the report
        report = await ScanReport.get(ObjectId(report_id))
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Format detailed response
        response_data = {
            "id": str(report.id),
            "project_name": report.project_name,
            "scan_id": report.scan_id,
            "status": report.status.value,
            "created_at": report.created_at,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
            "updated_at": report.updated_at,
            "duration_seconds": report.duration_seconds,
            
            # Git metadata
            "git_metadata": {
                "repository_url": report.git_metadata.repository_url,
                "branch": report.git_metadata.branch,
                "commit_hash": report.git_metadata.commit_hash,
                "commit_message": report.git_metadata.commit_message,
                "commit_author": report.git_metadata.commit_author,
                "commit_timestamp": report.git_metadata.commit_timestamp,
                "pr_number": report.git_metadata.pr_number,
                "event_type": report.git_metadata.event_type
            },
            
            # Summary statistics
            "summary": {
                "total_findings": report.total_findings,
                "findings_by_severity": report.findings_by_severity,
                "scanners_run": len(report.scan_results),
                "successful_scans": len([r for r in report.scan_results if r.status == ScanStatus.COMPLETED]),
                "failed_scans": len([r for r in report.scan_results if r.status == ScanStatus.FAILED])
            },
            
            # Scan results from each scanner
            "scan_results": [],
            
            # Tags and metadata
            "tags": report.tags,
            "metadata": report.metadata
        }
        
        # Add detailed scan results
        for scan_result in report.scan_results:
            scanner_data = {
                "scanner": scan_result.scanner.value,
                "status": scan_result.status.value,
                "started_at": scan_result.started_at,
                "completed_at": scan_result.completed_at,
                "duration_seconds": scan_result.duration_seconds,
                "summary": scan_result.summary,
                "error_message": scan_result.error_message,
                "findings_count": len(scan_result.findings),
                "findings": []
            }
            
            # Add individual findings
            for finding in scan_result.findings:
                finding_data = {
                    "id": finding.id,
                    "rule_id": finding.rule_id,
                    "title": finding.title,
                    "description": finding.description,
                    "severity": finding.severity.value,
                    "confidence": finding.confidence,
                    "file_path": finding.file_path,
                    "line_start": finding.line_start,
                    "line_end": finding.line_end,
                    "column_start": finding.column_start,
                    "column_end": finding.column_end,
                    "code_snippet": finding.code_snippet,
                    "cwe_id": finding.cwe_id,
                    "cve_id": finding.cve_id,
                    "owasp_category": finding.owasp_category,
                    "references": finding.references,
                    "metadata": finding.metadata
                }
                scanner_data["findings"].append(finding_data)
            
            response_data["scan_results"].append(scanner_data)
        
        # Add AI analysis if available
        if report.ai_analysis:
            response_data["ai_analysis"] = {
                "model_used": report.ai_analysis.model_used,
                "generated_at": report.ai_analysis.generated_at,
                "executive_summary": report.ai_analysis.executive_summary,
                "risk_assessment": report.ai_analysis.risk_assessment,
                "priority_findings": report.ai_analysis.priority_findings,
                "recommendations": report.ai_analysis.recommendations,
                "secure_code_examples": report.ai_analysis.secure_code_examples,
                "compliance_impact": report.ai_analysis.compliance_impact,
                "estimated_fix_time": report.ai_analysis.estimated_fix_time
            }
        
        # Add notification status
        response_data["notifications"] = {
            "slack_sent": report.notifications.slack_sent,
            "slack_timestamp": report.notifications.slack_timestamp,
            "teams_sent": report.notifications.teams_sent,
            "teams_timestamp": report.notifications.teams_timestamp,
            "email_sent": report.notifications.email_sent,
            "email_timestamp": report.notifications.email_timestamp,
            "errors": report.notifications.errors
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {e}")


@router.get("/{report_id}/summary")
async def get_report_summary(report_id: str) -> Dict[str, Any]:
    """
    Get summary information for a specific report
    
    Returns condensed report information without detailed findings
    """
    try:
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        report = await ScanReport.get(ObjectId(report_id))
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "id": str(report.id),
            "project_name": report.project_name,
            "scan_id": report.scan_id,
            "status": report.status.value,
            "repository_url": report.git_metadata.repository_url,
            "branch": report.git_metadata.branch,
            "commit_hash": report.git_metadata.commit_hash,
            "created_at": report.created_at,
            "completed_at": report.completed_at,
            "duration_seconds": report.duration_seconds,
            "total_findings": report.total_findings,
            "findings_by_severity": report.findings_by_severity,
            "scanners_summary": [
                {
                    "scanner": result.scanner.value,
                    "status": result.status.value,
                    "findings_count": len(result.findings),
                    "duration_seconds": result.duration_seconds
                }
                for result in report.scan_results
            ],
            "has_ai_analysis": report.ai_analysis is not None,
            "ai_risk_level": _extract_risk_level(report.ai_analysis.risk_assessment) if report.ai_analysis else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report summary {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report summary: {e}")


@router.get("/analytics/overview")
async def get_analytics_overview(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    project_name: Optional[str] = Query(None, description="Filter by project name")
) -> Dict[str, Any]:
    """
    Get analytics overview for the specified time period
    
    Returns aggregated statistics including:
    - Total scans performed
    - Vulnerability trends
    - Scanner performance
    - Top projects by findings
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Build base query
        query = ScanReport.find(ScanReport.created_at >= cutoff_date)
        
        if project_name:
            query = query.find(ScanReport.project_name == project_name)
        
        reports = await query.to_list()
        
        # Calculate analytics
        total_scans = len(reports)
        completed_scans = len([r for r in reports if r.status == ScanStatus.COMPLETED])
        failed_scans = len([r for r in reports if r.status == ScanStatus.FAILED])
        
        # Aggregate findings by severity
        total_findings = {
            "critical": sum(r.findings_by_severity.get("critical", 0) for r in reports),
            "high": sum(r.findings_by_severity.get("high", 0) for r in reports),
            "medium": sum(r.findings_by_severity.get("medium", 0) for r in reports),
            "low": sum(r.findings_by_severity.get("low", 0) for r in reports),
            "info": sum(r.findings_by_severity.get("info", 0) for r in reports)
        }
        
        # Scanner performance
        scanner_stats = {}
        for report in reports:
            for scan_result in report.scan_results:
                scanner = scan_result.scanner.value
                if scanner not in scanner_stats:
                    scanner_stats[scanner] = {
                        "total_runs": 0,
                        "successful_runs": 0,
                        "total_findings": 0,
                        "avg_duration": 0
                    }
                
                scanner_stats[scanner]["total_runs"] += 1
                if scan_result.status == ScanStatus.COMPLETED:
                    scanner_stats[scanner]["successful_runs"] += 1
                    scanner_stats[scanner]["total_findings"] += len(scan_result.findings)
                    if scan_result.duration_seconds:
                        scanner_stats[scanner]["avg_duration"] += scan_result.duration_seconds
        
        # Calculate average durations
        for scanner, stats in scanner_stats.items():
            if stats["successful_runs"] > 0:
                stats["avg_duration"] = stats["avg_duration"] / stats["successful_runs"]
            else:
                stats["avg_duration"] = 0
        
        # Top projects by findings
        project_findings = {}
        for report in reports:
            project = report.project_name
            if project not in project_findings:
                project_findings[project] = {
                    "total_findings": 0,
                    "scans_count": 0,
                    "critical_findings": 0,
                    "high_findings": 0
                }
            
            project_findings[project]["total_findings"] += report.total_findings
            project_findings[project]["scans_count"] += 1
            project_findings[project]["critical_findings"] += report.findings_by_severity.get("critical", 0)
            project_findings[project]["high_findings"] += report.findings_by_severity.get("high", 0)
        
        # Sort top projects by total findings
        top_projects = sorted(
            project_findings.items(),
            key=lambda x: x[1]["total_findings"],
            reverse=True
        )[:10]
        
        return {
            "period": {
                "days_back": days_back,
                "start_date": cutoff_date,
                "end_date": datetime.now(timezone.utc)
            },
            "scan_summary": {
                "total_scans": total_scans,
                "completed_scans": completed_scans,
                "failed_scans": failed_scans,
                "success_rate": (completed_scans / total_scans * 100) if total_scans > 0 else 0
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
                    "avg_findings_per_scan": stats["total_findings"] / stats["scans_count"] if stats["scans_count"] > 0 else 0
                }
                for project, stats in top_projects
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {e}")


@router.get("/project/{project_name}")
async def get_project_reports(
    project_name: str,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Get all reports for a specific project"""
    try:
        query = ScanReport.find(ScanReport.project_name == project_name)
        
        total = await query.count()
        reports = await query.sort(-ScanReport.created_at).skip(skip).limit(limit).to_list()
        
        if not reports:
            raise HTTPException(status_code=404, detail="No reports found for this project")
        
        # Calculate project statistics
        latest_report = reports[0]
        total_scans = total
        
        # Get recent trends (last 10 reports)
        recent_reports = reports[:10]
        trend_data = [
            {
                "scan_date": report.created_at,
                "total_findings": report.total_findings,
                "critical_count": report.findings_by_severity.get("critical", 0),
                "high_count": report.findings_by_severity.get("high", 0)
            }
            for report in recent_reports
        ]
        
        return {
            "project_name": project_name,
            "project_statistics": {
                "total_scans": total_scans,
                "latest_scan": {
                    "id": str(latest_report.id),
                    "created_at": latest_report.created_at,
                    "status": latest_report.status.value,
                    "total_findings": latest_report.total_findings,
                    "findings_by_severity": latest_report.findings_by_severity
                }
            },
            "recent_trend": trend_data,
            "reports": [
                {
                    "id": str(report.id),
                    "scan_id": report.scan_id,
                    "created_at": report.created_at,
                    "status": report.status.value,
                    "branch": report.git_metadata.branch,
                    "commit_hash": report.git_metadata.commit_hash,
                    "total_findings": report.total_findings,
                    "findings_by_severity": report.findings_by_severity
                }
                for report in reports
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "skip": skip
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project reports for {project_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project reports: {e}")


def _extract_risk_level(risk_assessment: str) -> Optional[str]:
    """Extract risk level from AI risk assessment text"""
    if not risk_assessment:
        return None
    
    risk_assessment_lower = risk_assessment.lower()
    
    if "critical" in risk_assessment_lower:
        return "CRITICAL"
    elif "high" in risk_assessment_lower:
        return "HIGH"
    elif "medium" in risk_assessment_lower:
        return "MEDIUM"
    elif "low" in risk_assessment_lower:
        return "LOW"
    
    return None
