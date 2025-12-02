"""
Reports routes for retrieving scan results and analytics
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import json
import csv
import io

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import red, green, orange, black, blue, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from models.report import ScanReport, ScanStatus, SeverityLevel, ScannerType
from models.user import User
from models.project import Project
from services.auth.auth_service import AuthService
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)


async def get_user_project_ids(user_id: str) -> List[str]:
    """Get list of project IDs accessible to the user"""
    from beanie.operators import Or
    projects = await Project.find(
        Or(
            Project.owner_id == user_id,
            Project.team_members.user_id == user_id
        )
    ).to_list()
    return [str(p.id) for p in projects]


@router.get("/")
@router.get("")  # Handle both /api/reports/ and /api/reports
async def list_reports(
    limit: int = Query(50, ge=1, le=1000, description="Number of reports to return"),
    skip: int = Query(0, ge=0, description="Number of reports to skip"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    status: Optional[ScanStatus] = Query(None, description="Filter by scan status"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    severity_filter: Optional[SeverityLevel] = Query(None, description="Filter by minimum severity"),
    days_back: Optional[int] = Query(None, ge=1, le=365, description="Filter by days back from now"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List scan reports with filtering and pagination
    
    Returns a paginated list of scan reports with optional filtering by:
    - Project ID
    - Project name
    - Scan status
    - Branch
    - Minimum severity level
    - Time range (days back from current time)
    
    Only returns reports for projects the user has access to.
    """
    try:
        user_id = str(current_user.id)
        logger.info(f"📊 Fetching reports for user {current_user.username} - limit: {limit}, skip: {skip}, project_id: {project_id}")
        
        # Get list of project IDs the user has access to
        accessible_project_ids = await get_user_project_ids(user_id)
        logger.info(f"👤 User has access to {len(accessible_project_ids)} projects")
        
        # Build query filters for database
        filters = {}
        
        # CRITICAL: Filter by user's accessible projects OR by user_id directly
        # This ensures data isolation between users
        if accessible_project_ids:
            filters["$or"] = [
                {"project_id": {"$in": accessible_project_ids}},
                {"user_id": user_id}
            ]
        else:
            # User has no projects, only show reports they created directly
            filters["user_id"] = user_id
        
        # Apply project_id filter if provided (must still be accessible)
        if project_id:
            if project_id not in accessible_project_ids:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to this project"
                )
            filters["project_id"] = project_id
            # Remove the $or filter since we're filtering by specific project
            filters.pop("$or", None)
        
        # Apply filters if provided
        if project_name:
            filters["project_name"] = {"$regex": project_name, "$options": "i"}
        
        if status:
            filters["status"] = status.value if hasattr(status, 'value') else status
        
        if branch:
            filters["git_metadata.branch"] = branch
        
        if days_back:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            filters["created_at"] = {"$gte": cutoff_date}
        
        # Apply severity filter
        if severity_filter:
            severity_key = f"findings_by_severity.{severity_filter.value if hasattr(severity_filter, 'value') else severity_filter}"
            filters[severity_key] = {"$gt": 0}
        
        try:
            # Try to get from database first
            logger.info(f"🔍 Querying database with filters: {filters}")
            db_reports = await ScanReport.find(filters).sort([("created_at", -1)]).skip(skip).limit(limit).to_list()
            total = await ScanReport.find(filters).count()
            
            logger.info(f"📊 Database query returned {len(db_reports)} reports, total: {total}")
            
            # Format database reports for frontend
            formatted_reports = []
            for report in db_reports:
                formatted_report = {
                    "id": str(report.id),
                    "project_name": report.project_name,
                    "scan_id": report.scan_id,
                    "repository_url": report.git_metadata.repository_url if report.git_metadata else "",
                    "branch": report.git_metadata.branch if report.git_metadata else "main",
                    "status": report.status.value if hasattr(report.status, 'value') else report.status,
                    "created_at": report.created_at.isoformat() if report.created_at else datetime.now(timezone.utc).isoformat(),
                    "total_findings": report.total_findings,
                    "findings_by_severity": report.findings_by_severity,
                    "duration_seconds": report.duration_seconds or 0,
                    "commit_hash": report.git_metadata.commit_hash if report.git_metadata else ""
                }
                formatted_reports.append(formatted_report)
            
            if formatted_reports:
                logger.info(f"✅ Found {len(formatted_reports)} reports in database")
                return {
                    "reports": formatted_reports,
                    "pagination": {
                        "total": total,
                        "skip": skip,
                        "limit": limit,
                        "has_more": skip + len(formatted_reports) < total
                    },
                    "filters": {
                        "project_id": project_id,
                        "project_name": project_name,
                        "status": status,
                        "branch": branch,
                        "severity_filter": severity_filter,
                        "days_back": days_back
                    }
                }
            else:
                logger.info("📭 No reports found in database")
                
        except Exception as db_error:
            logger.warning(f"Database error: {db_error}")
            logger.exception("Full database error traceback:")
        
        # Return empty results if no data found
        return {
            "reports": [],
            "pagination": {
                "total": 0,
                "skip": skip,
                "limit": limit,
                "has_more": False
            },
            "filters": {
                "project_id": project_id,
                "project_name": project_name,
                "status": status,
                "branch": branch,
                "severity_filter": severity_filter,
                "days_back": days_back
            }
        }
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve reports: {str(e)}"
        )


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed scan report by ID
    
    Requires authentication. User can only access reports for their own projects.
    
    Returns complete scan report including:
    - Basic report information
    - Git metadata
    - All scan results from each scanner
    - Individual vulnerability findings
    - AI analysis (if available)
    - Notification status
    """
    try:
        # Try to find in database first
        report = None
        user_id = str(current_user.id)
        
        # Check if it's a valid ObjectId (for real database documents)
        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
            except Exception as db_error:
                logger.warning(f"Database error when fetching report by ObjectId {report_id}: {db_error}")
        
        # If not found by ObjectId, try searching by scan_id (UUID format)
        if not report:
            try:
                report = await ScanReport.find_one(ScanReport.scan_id == report_id)
                if report:
                    logger.info(f"Found report by scan_id: {report_id}")
            except Exception as db_error:
                logger.warning(f"Database error when fetching report by scan_id {report_id}: {db_error}")
        
        # If not found in database, return 404
        if not report:
            logger.info(f"Report {report_id} not found in database (tried ObjectId and scan_id)")
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Verify user has access to this report
        accessible_project_ids = await get_user_project_ids(user_id)
        report_user_id = getattr(report, 'user_id', None)
        report_project_id = getattr(report, 'project_id', None)
        
        has_access = (
            report_user_id == user_id or  # User owns the report
            (report_project_id and report_project_id in accessible_project_ids)  # User has access to the project
        )
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this report")
        
        # If we have a real database report, format it properly
        if report:
            # Format detailed response for real database report
            response_data = {
                "id": str(report.id),
                "project_name": report.project_name,
                "scan_id": report.scan_id,
                "status": report.status.value,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "started_at": report.started_at.isoformat() if report.started_at else None,
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                "updated_at": report.updated_at.isoformat() if report.updated_at else None,
                "duration_seconds": report.duration_seconds,
                
                # Git metadata
                "git_metadata": {
                    "repository_url": report.git_metadata.repository_url if report.git_metadata else "",
                    "branch": report.git_metadata.branch if report.git_metadata else "",
                    "commit_hash": report.git_metadata.commit_hash if report.git_metadata else "",
                    "commit_message": report.git_metadata.commit_message if report.git_metadata else "",
                    "commit_author": report.git_metadata.commit_author if report.git_metadata else "",
                    "commit_timestamp": report.git_metadata.commit_timestamp.isoformat() if report.git_metadata and report.git_metadata.commit_timestamp else None,
                    "pr_number": report.git_metadata.pr_number if report.git_metadata else None,
                    "event_type": report.git_metadata.event_type if report.git_metadata else ""
                },
                
                # Summary statistics
                "summary": {
                    "total_findings": report.total_findings,
                    "findings_by_severity": report.findings_by_severity,
                    "scanners_run": len(report.scan_results) if report.scan_results else 0,
                    "successful_scans": len([r for r in report.scan_results if r.status == ScanStatus.COMPLETED]) if report.scan_results else 0,
                    "failed_scans": len([r for r in report.scan_results if r.status == ScanStatus.FAILED]) if report.scan_results else 0
                },
                
                # Scan results from each scanner
                "scan_results": [],
                
                # Tags and metadata
                "tags": report.tags if report.tags else [],
                "metadata": report.metadata if report.metadata else {}
            }
            
            # Add detailed scan results for real database report
            if report.scan_results:
                for scan_result in report.scan_results:
                    scanner_data = {
                        "scanner": scan_result.scanner.value,
                        "status": scan_result.status.value,
                        "started_at": scan_result.started_at.isoformat() if scan_result.started_at else None,
                        "completed_at": scan_result.completed_at.isoformat() if scan_result.completed_at else None,
                        "duration_seconds": scan_result.duration_seconds,
                        "summary": scan_result.summary,
                        "error_message": scan_result.error_message,
                        "findings_count": len(scan_result.findings) if scan_result.findings else 0,
                        "findings": []
                    }
                    
                    # Add individual findings if available
                    if scan_result.findings:
                        for finding in scan_result.findings:
                            finding_data = {
                                "id": finding.id,
                                "title": finding.title,
                                "description": finding.description,
                                "severity": finding.severity.value if hasattr(finding.severity, 'value') else finding.severity,
                                "confidence": finding.confidence if isinstance(finding.confidence, str) else (finding.confidence.value if finding.confidence and hasattr(finding.confidence, 'value') else finding.confidence),
                                "category": getattr(finding, 'category', None),
                                "file_path": getattr(finding, 'file_path', '') or (finding.location.file_path if hasattr(finding, 'location') and finding.location else ''),
                                "line_number": getattr(finding, 'line_start', None) or (finding.location.line_number if hasattr(finding, 'location') and finding.location else None),
                                "column_number": getattr(finding, 'column_start', None) or (finding.location.column_number if hasattr(finding, 'location') and finding.location else None),
                                "code_snippet": getattr(finding, 'code_snippet', '') or (finding.location.code_snippet if hasattr(finding, 'location') and finding.location else ''),
                                "remediation": getattr(finding, 'remediation', None),
                                "cwe_id": getattr(finding, 'cwe_id', None),
                                "cve_id": getattr(finding, 'cve_id', None),
                                "owasp_category": getattr(finding, 'owasp_category', None),
                                "references": getattr(finding, 'references', [])
                            }
                            scanner_data["findings"].append(finding_data)
                    
                    response_data["scan_results"].append(scanner_data)
            
            return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {e}")


@router.get("/{report_id}/download")
async def download_report(
    report_id: str, 
    format: str = Query("json", regex="^(json|pdf|csv)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Download report in specified format
    
    Requires authentication. User can only download reports for their own projects.
    
    Supports:
    - json: Complete report data as JSON
    - pdf: Formatted PDF report (requires report generation)
    - csv: Findings exported as CSV
    """
    from fastapi.responses import JSONResponse, StreamingResponse
    import json
    import io
    import csv
    
    try:
        # Get the report data (reuse the logic from get_report)
        report_data = None
        user_id = str(current_user.id)
        
        # Check if it's a valid ObjectId (for real database documents)
        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
                if report:
                    # Verify user has access to this report
                    accessible_project_ids = await get_user_project_ids(user_id)
                    report_user_id = getattr(report, 'user_id', None)
                    report_project_id = getattr(report, 'project_id', None)
                    
                    has_access = (
                        report_user_id == user_id or  # User owns the report
                        (report_project_id and report_project_id in accessible_project_ids)  # User has access to the project
                    )
                    
                    if not has_access:
                        raise HTTPException(status_code=403, detail="Access denied to this report")
                    
                    # Convert to the same format as get_report endpoint with full data
                    report_data = {
                        "id": str(report.id),
                        "project_name": report.project_name,
                        "scan_id": report.scan_id,
                        "status": report.status.value if hasattr(report.status, 'value') else report.status,
                        "created_at": report.created_at.isoformat() if report.created_at else None,
                        "started_at": report.started_at.isoformat() if report.started_at else None,
                        "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                        "duration_seconds": report.duration_seconds,
                        "total_findings": report.total_findings,
                        "findings_by_severity": report.findings_by_severity,
                        "scan_results": report.scan_results if report.scan_results else [],  # Add scan results
                        "git_metadata": {
                            "repository_url": report.git_metadata.repository_url if report.git_metadata else "",
                            "branch": report.git_metadata.branch if report.git_metadata else "main",
                            "commit_hash": report.git_metadata.commit_hash if report.git_metadata else "",
                            "commit_message": report.git_metadata.commit_message if report.git_metadata else "",
                            "commit_author": report.git_metadata.commit_author if report.git_metadata else "",
                            "event_type": report.git_metadata.event_type if report.git_metadata else ""
                        },
                        "tags": report.tags if report.tags else [],
                        "metadata": report.metadata if report.metadata else {}
                    }
            except Exception as db_error:
                logger.warning(f"Database error when fetching report {report_id}: {db_error}")
        
        # If not found in database, return 404
        if not report_data:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Extract findings early for AI analysis
        findings = []
        if report_data.get('findings'):
            findings.extend(report_data['findings'])
        elif report_data.get('scan_results'):
            for scan_result in report_data['scan_results']:
                # Handle both dict and ScanResult object formats
                if hasattr(scan_result, 'findings'):
                    # ScanResult object
                    if scan_result.findings:
                        for finding in scan_result.findings:
                            # Convert VulnerabilityFinding object to dict for compatibility
                            if hasattr(finding, 'model_dump'):
                                finding_dict = finding.model_dump()
                            elif hasattr(finding, 'dict'):
                                finding_dict = finding.dict()
                            else:
                                # Already a dict
                                finding_dict = finding
                            findings.append(finding_dict)
                else:
                    # Dictionary format
                    findings.extend(scan_result.get('findings', []))
        
        # Handle different download formats
        if format == "json":
            # Return JSON format
            json_content = json.dumps(report_data, indent=2, default=str)
            headers = {
                'Content-Disposition': f'attachment; filename="{report_id}_report.json"',
                'Content-Type': 'application/json'
            }
            return StreamingResponse(
                io.BytesIO(json_content.encode()),
                media_type="application/json",
                headers=headers
            )
        
        elif format == "csv":
            # Export findings as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # CSV headers
            writer.writerow([
                'Project', 'Scan ID', 'Status', 'Created At', 'Total Findings', 
                'Critical', 'High', 'Medium', 'Low', 'Info', 'Repository', 'Branch'
            ])
            
            # CSV data
            findings = report_data.get('findings_by_severity', {})
            writer.writerow([
                report_data.get('project_name', ''),
                report_data.get('scan_id', ''),
                report_data.get('status', ''),
                report_data.get('created_at', ''),
                report_data.get('total_findings', 0),
                findings.get('critical', 0),
                findings.get('high', 0),
                findings.get('medium', 0),
                findings.get('low', 0),
                findings.get('info', 0),
                report_data.get('git_metadata', {}).get('repository_url', ''),
                report_data.get('git_metadata', {}).get('branch', '')
            ])
            
            csv_content = output.getvalue()
            headers = {
                'Content-Disposition': f'attachment; filename="{report_id}_report.csv"',
                'Content-Type': 'text/csv'
            }
            return StreamingResponse(
                io.BytesIO(csv_content.encode()),
                media_type="text/csv",
                headers=headers
            )
        
        elif format == "pdf":
            # Generate Enhanced PDF report with AI analysis
            pdf_buffer = io.BytesIO()
            
            # Import additional PDF libraries for enhanced formatting
            from reportlab.graphics.shapes import Drawing, Rect
            from reportlab.lib import colors as reportlab_colors
            
            # Create PDF document with better margins
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50
            )
            
            # Enhanced styles
            styles = getSampleStyleSheet()
            
            # Professional title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                spaceBefore=0,
                alignment=TA_CENTER,
                textColor=blue,
                fontName='Helvetica-Bold'
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=black
            )
            
            # Section heading style
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=blue,
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=blue,
                borderPadding=5,
                backColor=reportlab_colors.lightblue
            )
            
            # AI analysis style
            ai_style = ParagraphStyle(
                'AIAnalysis',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leftIndent=20,
                backColor=reportlab_colors.lightgrey,
                borderWidth=1,
                borderColor=reportlab_colors.grey,
                borderPadding=10
            )
            
            normal_style = styles['Normal']
            
            # Build enhanced PDF content
            story = []
            
            # Professional Header
            story.append(Paragraph("🛡️ ONYX Security Intelligence Platform", title_style))
            story.append(Paragraph("Comprehensive Security Analysis Report", subtitle_style))
            story.append(Spacer(1, 20))
            
            # Executive Summary Box
            story.append(Paragraph("🎯 Executive Summary", heading_style))
            
            # Get AI analysis for executive summary - generate real analysis
            ai_summary = "Comprehensive security analysis completed successfully."
            
            # Generate real AI analysis based on findings
            if findings:
                try:
                    # Count findings by severity
                    severity_counts = {}
                    finding_types = []
                    for finding in findings:
                        # Handle both dict and object formats
                        if isinstance(finding, dict):
                            severity = finding.get('severity', 'unknown')
                            finding_type = finding.get('type', '')
                        else:
                            severity = getattr(finding, 'severity', 'unknown')
                            if hasattr(severity, 'value'):
                                severity = severity.value
                            finding_type = getattr(finding, 'category', '')
                        
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                        if finding_type:
                            finding_types.append(finding_type)
                    
                    # Generate contextual summary
                    total_findings = len(findings)
                    critical_count = severity_counts.get('critical', 0)
                    high_count = severity_counts.get('high', 0)
                    
                    if critical_count > 0:
                        risk_level = "CRITICAL"
                        urgency = "immediate attention required"
                    elif high_count > 0:
                        risk_level = "HIGH"
                        urgency = "prompt remediation needed"
                    else:
                        risk_level = "MODERATE"
                        urgency = "scheduled remediation recommended"
                    
                    # Generate detailed AI summary
                    ai_summary = f"""Security analysis revealed {total_findings} findings requiring attention. 
                    Risk assessment indicates {risk_level} priority level with {urgency}. 
                    Critical issues: {critical_count}, High severity: {high_count}. 
                    Primary concerns include {', '.join(set(finding_types[:3]))} requiring immediate review. 
                    Recommend prioritizing critical and high-severity findings for immediate remediation."""
                    
                except Exception as e:
                    logger.warning(f"Error generating AI summary: {e}")
            
            # Try to get existing AI analysis
            if report and hasattr(report, 'ai_analysis') and report.ai_analysis:
                ai_summary = report.ai_analysis.executive_summary or ai_summary
            elif report_data.get('ai_analysis'):
                ai_summary = report_data['ai_analysis'].get('executive_summary', ai_summary)
            
            story.append(Paragraph(f"<b>AI-Generated Summary:</b><br/>{ai_summary}", ai_style))
            story.append(Spacer(1, 15))
            
            # Project Information in a more professional layout
            story.append(Paragraph("📋 Project Information", heading_style))
            project_data = [
                ['Project Name', report_data.get('project_name', 'N/A')],
                ['Report ID', str(report_id)],  # Use the actual report ID being requested
                ['Scan ID', report_data.get('scan_id', 'N/A')],
                ['Status', report_data.get('status', 'N/A').title()],
                ['Created', report_data.get('created_at', 'N/A')[:19] if report_data.get('created_at') else 'N/A'],
                ['Completed', report_data.get('completed_at', 'N/A')[:19] if report_data.get('completed_at') else 'N/A'],
                ['Duration', f"{report_data.get('duration_seconds', 0):.1f} seconds"],
                ['Repository', report_data.get('git_metadata', {}).get('repository_url', 'N/A')],
                ['Branch', report_data.get('git_metadata', {}).get('branch', 'N/A')],
                ['Commit Hash', report_data.get('git_metadata', {}).get('commit_hash', 'N/A')[:12] + '...' if report_data.get('git_metadata', {}).get('commit_hash') else 'N/A']
            ]
            
            project_table = Table(project_data, colWidths=[2.2*inch, 4.3*inch])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), blue),
                ('TEXTCOLOR', (0, 0), (0, -1), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, -1), reportlab_colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(project_table)
            story.append(Spacer(1, 25))
            
            # Enhanced Security Summary with visuals
            story.append(Paragraph("📊 Security Summary", heading_style))
            findings_by_severity = report_data.get('findings_by_severity', {})
            total_findings = report_data.get('total_findings', 0)
            
            # Risk level assessment
            critical_count = findings_by_severity.get('critical', 0)
            high_count = findings_by_severity.get('high', 0)
            
            risk_level = "🟢 LOW"
            if critical_count > 0:
                risk_level = "🔴 CRITICAL"
            elif high_count > 5:
                risk_level = "🟠 HIGH"
            elif high_count > 0:
                risk_level = "🟡 MEDIUM"
            
            story.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level}", ai_style))
            story.append(Spacer(1, 10))
            
            summary_data = [
                ['Severity Level', 'Count', 'Percentage', 'Risk Impact'],
                ['🔴 Critical', str(findings_by_severity.get('critical', 0)), f"{(findings_by_severity.get('critical', 0) / max(total_findings, 1)) * 100:.1f}%", 'Immediate Action Required'],
                ['🟠 High', str(findings_by_severity.get('high', 0)), f"{(findings_by_severity.get('high', 0) / max(total_findings, 1)) * 100:.1f}%", 'Priority Fix Needed'],
                ['🟡 Medium', str(findings_by_severity.get('medium', 0)), f"{(findings_by_severity.get('medium', 0) / max(total_findings, 1)) * 100:.1f}%", 'Schedule Fix'],
                ['🟢 Low', str(findings_by_severity.get('low', 0)), f"{(findings_by_severity.get('low', 0) / max(total_findings, 1)) * 100:.1f}%", 'Monitor'],
                ['ℹ️ Info', str(findings_by_severity.get('info', 0)), f"{(findings_by_severity.get('info', 0) / max(total_findings, 1)) * 100:.1f}%", 'Informational'],
                ['📊 Total', str(total_findings), '100.0%', f'{total_findings} Total Issues']
            ]
            
            summary_table = Table(summary_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 2.2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, 1), reportlab_colors.mistyrose),  # Critical
                ('BACKGROUND', (0, 2), (-1, 2), reportlab_colors.orange),     # High
                ('BACKGROUND', (0, 3), (-1, 3), reportlab_colors.lightyellow), # Medium
                ('BACKGROUND', (0, 4), (-1, 4), reportlab_colors.lightgreen),  # Low
                ('BACKGROUND', (0, 5), (-1, 5), reportlab_colors.lightblue),   # Info
                ('BACKGROUND', (0, 6), (-1, 6), reportlab_colors.lightgrey),   # Total
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 25))
            
            # Enhanced AI Analysis Section
            story.append(Paragraph("🤖 AI-Powered Security Analysis", heading_style))
            
            # Get AI analysis from report
            ai_analysis = None
            if report and hasattr(report, 'ai_analysis') and report.ai_analysis:
                ai_analysis = report.ai_analysis
            elif report_data.get('ai_analysis'):
                ai_analysis = report_data.get('ai_analysis')
            
            if ai_analysis:
                # Executive Summary
                if hasattr(ai_analysis, 'executive_summary') and ai_analysis.executive_summary:
                    story.append(Paragraph("📋 Executive Summary", normal_style))
                    story.append(Paragraph(ai_analysis.executive_summary, ai_style))
                    story.append(Spacer(1, 12))
                elif isinstance(ai_analysis, dict) and ai_analysis.get('executive_summary'):
                    story.append(Paragraph("📋 Executive Summary", normal_style))
                    story.append(Paragraph(ai_analysis.get('executive_summary'), ai_style))
                    story.append(Spacer(1, 12))
                
                # Risk Assessment
                risk_assessment = None
                if hasattr(ai_analysis, 'risk_assessment') and ai_analysis.risk_assessment:
                    risk_assessment = ai_analysis.risk_assessment
                elif isinstance(ai_analysis, dict) and ai_analysis.get('risk_assessment'):
                    risk_assessment = ai_analysis.get('risk_assessment')
                
                if risk_assessment:
                    story.append(Paragraph("⚠️ Risk Assessment", normal_style))
                    story.append(Paragraph(risk_assessment, ai_style))
                    story.append(Spacer(1, 12))
                
                # Priority Findings
                priority_findings = None
                if hasattr(ai_analysis, 'priority_findings') and ai_analysis.priority_findings:
                    priority_findings = ai_analysis.priority_findings
                elif isinstance(ai_analysis, dict) and ai_analysis.get('priority_findings'):
                    priority_findings = ai_analysis.get('priority_findings')
                
                if priority_findings:
                    story.append(Paragraph("🎯 Priority Findings", normal_style))
                    for i, finding in enumerate(priority_findings[:5], 1):
                        story.append(Paragraph(f"{i}. {finding}", normal_style))
                    story.append(Spacer(1, 12))
                
                # Recommendations
                recommendations = None
                if hasattr(ai_analysis, 'recommendations') and ai_analysis.recommendations:
                    recommendations = ai_analysis.recommendations
                elif isinstance(ai_analysis, dict) and ai_analysis.get('recommendations'):
                    recommendations = ai_analysis.get('recommendations')
                
                if recommendations:
                    story.append(Paragraph("💡 AI Recommendations", normal_style))
                    for i, rec in enumerate(recommendations[:5], 1):
                        story.append(Paragraph(f"{i}. {rec}", normal_style))
                    story.append(Spacer(1, 12))
                
                # Compliance Impact
                compliance_impact = None
                if hasattr(ai_analysis, 'compliance_impact') and ai_analysis.compliance_impact:
                    compliance_impact = ai_analysis.compliance_impact
                elif isinstance(ai_analysis, dict) and ai_analysis.get('compliance_impact'):
                    compliance_impact = ai_analysis.get('compliance_impact')
                
                if compliance_impact:
                    story.append(Paragraph("📋 Compliance Impact", normal_style))
                    if isinstance(compliance_impact, dict):
                        for framework, impact in compliance_impact.items():
                            story.append(Paragraph(f"<b>{framework}:</b> {impact}", normal_style))
                    else:
                        story.append(Paragraph(str(compliance_impact), ai_style))
                    story.append(Spacer(1, 12))
                
                # Estimated Fix Time
                estimated_fix_time = None
                if hasattr(ai_analysis, 'estimated_fix_time') and ai_analysis.estimated_fix_time:
                    estimated_fix_time = ai_analysis.estimated_fix_time
                elif isinstance(ai_analysis, dict) and ai_analysis.get('estimated_fix_time'):
                    estimated_fix_time = ai_analysis.get('estimated_fix_time')
                
                if estimated_fix_time:
                    story.append(Paragraph("⏰ Estimated Remediation Time", normal_style))
                    story.append(Paragraph(estimated_fix_time, ai_style))
                    story.append(Spacer(1, 12))
                
            else:
                # Fallback AI analysis if none exists
                story.append(Paragraph("📋 Automated Security Assessment", normal_style))
                
                if findings:
                    # Generate basic analysis based on findings
                    total_findings = len(findings)
                    severity_counts = {}
                    for finding in findings:
                        severity = finding.get('severity', 'unknown').lower()
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    critical_count = severity_counts.get('critical', 0)
                    high_count = severity_counts.get('high', 0)
                    medium_count = severity_counts.get('medium', 0)
                    
                    if critical_count > 0:
                        risk_level = "CRITICAL - Immediate action required"
                    elif high_count > 0:
                        risk_level = "HIGH - Prompt remediation needed"
                    elif medium_count > 0:
                        risk_level = "MEDIUM - Scheduled remediation recommended"
                    else:
                        risk_level = "LOW - Monitor and address during maintenance"
                    
                    basic_analysis = f"""
                    Security scan identified {total_findings} findings requiring attention.
                    Risk Level: {risk_level}
                    
                    Breakdown:
                    • Critical: {critical_count} findings
                    • High: {high_count} findings  
                    • Medium: {medium_count} findings
                    • Low: {severity_counts.get('low', 0)} findings
                    
                    Recommendation: Prioritize critical and high-severity findings for immediate remediation.
                    Review medium-severity findings during next maintenance window.
                    """
                    
                    story.append(Paragraph(basic_analysis, ai_style))
                else:
                    story.append(Paragraph("No security findings detected. Maintain current security practices.", ai_style))
                
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 20))
            
            # Scanner Results Summary
            if report_data.get('scan_results'):
                story.append(Paragraph("🔍 Scanner Results", heading_style))
                
                scanner_data = [['Scanner', 'Status', 'Findings', 'Duration']]
                for scan_result in report_data.get('scan_results', []):
                    # Handle both dict and ScanResult object formats
                    if hasattr(scan_result, 'scanner'):
                        # ScanResult object
                        scanner_name = scan_result.scanner.value if hasattr(scan_result.scanner, 'value') else str(scan_result.scanner)
                        # Clean up scanner name
                        if scanner_name.startswith('ScannerType.'):
                            scanner_name = scanner_name.replace('ScannerType.', '').replace('GITLEAKS', 'GitLeaks').replace('SEMGREP', 'Semgrep').replace('SAFETY', 'Safety')
                        elif scanner_name in ['GITLEAKS', 'gitleaks']:
                            scanner_name = 'GitLeaks'
                        elif scanner_name in ['SEMGREP', 'semgrep']:
                            scanner_name = 'Semgrep'
                        elif scanner_name in ['SAFETY', 'safety']:
                            scanner_name = 'Safety'
                        
                        status = scan_result.status.value if hasattr(scan_result.status, 'value') else str(scan_result.status)
                        status = status.replace('ScanStatus.', '').title()
                        findings_count = len(scan_result.findings) if scan_result.findings else 0
                        duration = scan_result.duration_seconds or 0
                    else:
                        # Dictionary format
                        scanner_name = scan_result.get('scanner', 'Unknown')
                        status = scan_result.get('status', 'Unknown')
                        findings_count = scan_result.get('findings_count', 0)
                        duration = scan_result.get('duration_seconds', 0)
                    
                    scanner_data.append([
                        scanner_name,
                        status,
                        str(findings_count),
                        f"{duration:.1f}s"
                    ])
                
                scanner_table = Table(scanner_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
                scanner_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                story.append(scanner_table)
                story.append(Spacer(1, 20))
            
            # Page break before detailed findings
            story.append(PageBreak())
            
            # Detailed Findings Section (findings already extracted earlier)
            
            if findings:
                story.append(Paragraph("🔍 Detailed Security Findings", heading_style))
                story.append(Paragraph(f"This section contains detailed information about {len(findings)} security findings identified during the scan.", normal_style))
                story.append(Spacer(1, 15))
                
                # Sort findings by severity
                severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
                findings_sorted = sorted(findings, key=lambda x: severity_order.get(x.get('severity', 'info') if isinstance(x, dict) else getattr(x, 'severity', 'info'), 4))
                
                for i, finding in enumerate(findings_sorted[:15], 1):  # Limit to first 15 findings
                    # Handle both dict and object formats
                    if isinstance(finding, dict):
                        severity = finding.get('severity', 'unknown')
                        title = finding.get('title', 'Untitled Finding')
                        scanner = finding.get('scanner', 'Unknown')
                        file_path = finding.get('file_path', 'N/A')
                        line_number = finding.get('line_number', finding.get('line_start', 'N/A'))
                        rule_id = finding.get('rule_id', 'N/A')
                        cwe_id = finding.get('cwe_id', 'N/A')
                        description = finding.get('description', '')
                        remediation = finding.get('remediation') or finding.get('recommendation', '')
                    else:
                        # Object format
                        severity = getattr(finding, 'severity', 'unknown')
                        if hasattr(severity, 'value'):
                            severity = severity.value
                        title = getattr(finding, 'title', 'Untitled Finding')
                        scanner = getattr(finding, 'scanner', 'Unknown')
                        if hasattr(scanner, 'value'):
                            scanner = scanner.value
                        # Clean up scanner name
                        if scanner.startswith('ScannerType.'):
                            scanner = scanner.replace('ScannerType.', '').replace('GITLEAKS', 'GitLeaks').replace('SEMGREP', 'Semgrep').replace('SAFETY', 'Safety')
                        elif scanner in ['GITLEAKS', 'gitleaks']:
                            scanner = 'GitLeaks'
                        elif scanner in ['SEMGREP', 'semgrep']:
                            scanner = 'Semgrep'
                        elif scanner in ['SAFETY', 'safety']:
                            scanner = 'Safety'
                        file_path = getattr(finding, 'file_path', 'N/A')
                        line_number = getattr(finding, 'line_start', getattr(finding, 'line_number', 'N/A'))
                        rule_id = getattr(finding, 'rule_id', 'N/A')
                        cwe_id = getattr(finding, 'cwe_id', getattr(finding, 'cwe', 'N/A'))
                        description = getattr(finding, 'description', '')
                        remediation = getattr(finding, 'remediation', '')
                    
                    severity_icon = {
                        'critical': '🔴', 'high': '🟠', 'medium': '🟡', 
                        'low': '🟢', 'info': 'ℹ️'
                    }.get(severity, '❓')
                    
                    finding_title = f"{severity_icon} Finding {i}: {title}"
                    
                    title_color = red if severity in ['critical', 'high'] else orange if severity == 'medium' else black
                    finding_title_style = ParagraphStyle(
                        'FindingTitle',
                        parent=styles['Heading3'],
                        fontSize=12,
                        spaceAfter=8,
                        spaceBefore=15,
                        textColor=title_color,
                        fontName='Helvetica-Bold'
                    )
                    story.append(Paragraph(finding_title, finding_title_style))
                    
                    # Finding details table
                    finding_details = [
                        ['Severity', severity.title()],
                        ['Scanner', scanner],
                        ['File Path', file_path],
                        ['Line Number', str(line_number) if line_number != 'N/A' else 'Not Available'],
                        ['Rule ID', rule_id if rule_id != 'N/A' else 'Not Available'],
                        ['CWE ID', str(cwe_id) if cwe_id and cwe_id != 'N/A' else 'Not Available']
                    ]
                    
                    detail_table = Table(finding_details, colWidths=[1.3*inch, 4.2*inch])
                    detail_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BACKGROUND', (0, 0), (0, -1), reportlab_colors.lightgrey)
                    ]))
                    story.append(detail_table)
                    
                    # Description
                    if description:
                        story.append(Spacer(1, 8))
                        story.append(Paragraph(f"<b>Description:</b><br/>{description}", normal_style))
                    
                    # Remediation advice
                    if remediation:
                        story.append(Spacer(1, 8))
                        story.append(Paragraph(f"<b>💡 Remediation:</b><br/>{remediation}", ai_style))
                    
                    story.append(Spacer(1, 15))
                
                if len(findings) > 15:
                    story.append(Paragraph(f"<i>... and {len(findings) - 15} more findings not shown in this PDF. Download JSON/CSV format for complete details.</i>", normal_style))
            
            # Professional Footer
            story.append(PageBreak())
            story.append(Spacer(1, 40))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=reportlab_colors.grey
            )
            
            story.append(Paragraph("🛡️ ONYX Security Intelligence Platform", footer_style))
            story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", footer_style))
            story.append(Paragraph(f"Report ID: {report_data.get('scan_id', report_id)} | Project: {report_data.get('project_name', 'Unknown')}", footer_style))
            story.append(Paragraph("This report contains confidential security information. Handle with appropriate care.", footer_style))
            
            # Build PDF
            doc.build(story)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            headers = {
                'Content-Disposition': f'attachment; filename="{report_id}_enhanced_security_report.pdf"',
                'Content-Type': 'application/pdf'
            }
            return StreamingResponse(
                io.BytesIO(pdf_content),
                media_type="application/pdf",
                headers=headers
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download report: {e}")


@router.get("/{report_id}/summary")
async def get_report_summary(
    report_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get summary information for a specific report
    
    Requires authentication. User can only access reports for their own projects.
    
    Returns condensed report information without detailed findings
    """
    try:
        if not ObjectId.is_valid(report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")
        
        report = await ScanReport.get(ObjectId(report_id))
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify user has access to this report
        user_id = str(current_user.id)
        accessible_project_ids = await get_user_project_ids(user_id)
        report_user_id = getattr(report, 'user_id', None)
        report_project_id = getattr(report, 'project_id', None)
        
        has_access = (
            report_user_id == user_id or
            (report_project_id and report_project_id in accessible_project_ids)
        )
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this report")
        
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


@router.get("/{report_id}/ai-analysis")
async def get_ai_analysis(
    report_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get AI analysis for a specific report
    
    Requires authentication. User can only access reports for their own projects.
    
    Returns AI-generated analysis including:
    - Executive summary
    - Risk assessment
    - Priority findings
    - Remediation recommendations
    - Secure code examples
    - Compliance impact
    """
    try:
        # Try to find by ObjectId first
        report = None
        user_id = str(current_user.id)
        
        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
            except Exception as db_error:
                logger.warning(f"Database error when fetching report by ObjectId {report_id}: {db_error}")
        
        # If not found by ObjectId, try searching by scan_id
        if not report:
            try:
                report = await ScanReport.find_one(ScanReport.scan_id == report_id)
            except Exception as db_error:
                logger.warning(f"Database error when fetching report by scan_id {report_id}: {db_error}")
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify user has access to this report
        accessible_project_ids = await get_user_project_ids(user_id)
        report_user_id = getattr(report, 'user_id', None)
        report_project_id = getattr(report, 'project_id', None)
        
        has_access = (
            report_user_id == user_id or
            (report_project_id and report_project_id in accessible_project_ids)
        )
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this report")
        
        if not report.ai_analysis:
            return {
                "has_analysis": False,
                "message": "AI analysis not available for this report",
                "report_id": report_id
            }
        
        # Format AI analysis response
        ai_data = report.ai_analysis
        
        # Build findings analysis mapping for individual vulnerabilities
        findings_analysis = {}
        if report.scan_results:
            for scan_result in report.scan_results:
                if scan_result.findings:
                    for i, finding in enumerate(scan_result.findings):
                        finding_id = getattr(finding, 'id', f"{scan_result.scanner.value}_{i}")
                        findings_analysis[finding_id] = {
                            "ai_explanation": f"This {finding.severity.value if hasattr(finding.severity, 'value') else finding.severity} severity issue requires attention.",
                            "risk_context": ai_data.risk_assessment[:200] if ai_data.risk_assessment else "Risk context not available",
                            "remediation_priority": "high" if finding.severity.value in ["critical", "high"] else "medium",
                            "secure_code_example": ai_data.secure_code_examples.get(finding.title, "") if ai_data.secure_code_examples else ""
                        }
        
        return {
            "has_analysis": True,
            "report_id": report_id,
            "model_used": ai_data.model_used,
            "generated_at": ai_data.generated_at.isoformat() if ai_data.generated_at else None,
            "executive_summary": ai_data.executive_summary,
            "overall_risk_assessment": ai_data.risk_assessment,
            "risk_score": getattr(ai_data, 'risk_score', None),
            "risk_level": getattr(ai_data, 'risk_level', None),
            "security_score": getattr(ai_data, 'security_score', None),
            "priority_findings": ai_data.priority_findings,
            "priority_recommendations": ai_data.recommendations,
            "secure_code_examples": ai_data.secure_code_examples,
            "compliance_impact": ai_data.compliance_impact,
            "estimated_fix_time": ai_data.estimated_fix_time,
            "attack_vectors": getattr(ai_data, 'attack_vectors', []),
            "threat_categories": getattr(ai_data, 'threat_categories', {}),
            "remediation_roadmap": getattr(ai_data, 'remediation_roadmap', []),
            "findings_analysis": findings_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AI analysis for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI analysis: {e}")


@router.get("/analytics/overview")
async def get_analytics_overview(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get analytics overview for the specified time period
    
    Requires authentication. Only shows analytics for user's accessible projects.
    
    Returns aggregated statistics including:
    - Total scans performed
    - Vulnerability trends
    - Scanner performance
    - Top projects by findings
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        user_id = str(current_user.id)
        
        # Get accessible project IDs
        accessible_project_ids = await get_user_project_ids(user_id)
        
        # Build base query with user access filter
        from beanie.operators import Or, In
        
        # Build query conditions
        query_conditions = [ScanReport.created_at >= cutoff_date]
        
        # Add user access filter
        user_access_conditions = [ScanReport.user_id == user_id]
        if accessible_project_ids:
            user_access_conditions.append(In(ScanReport.project_id, accessible_project_ids))
        
        query = ScanReport.find(
            *query_conditions,
            Or(*user_access_conditions)
        )
        
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
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all reports for a specific project
    
    Requires authentication. User must have access to the project.
    """
    try:
        user_id = str(current_user.id)
        
        # Verify user has access to this project
        accessible_project_ids = await get_user_project_ids(user_id)
        
        # Also check if user owns any reports for this project name
        from beanie.operators import Or, In
        
        # Build user access conditions
        user_access_conditions = [ScanReport.user_id == user_id]
        if accessible_project_ids:
            user_access_conditions.append(In(ScanReport.project_id, accessible_project_ids))
        
        query = ScanReport.find(
            ScanReport.project_name == project_name,
            Or(*user_access_conditions)
        )
        
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
