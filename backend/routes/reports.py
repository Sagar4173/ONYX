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
            # Generate Professional Enhanced PDF report with AI analysis
            pdf_buffer = io.BytesIO()
            
            # Import additional PDF libraries for enhanced formatting
            from reportlab.graphics.shapes import Drawing, Rect, Line, Circle
            from reportlab.graphics.charts.piecharts import Pie
            from reportlab.graphics.charts.barcharts import VerticalBarChart
            from reportlab.lib import colors as reportlab_colors
            from reportlab.platypus import ListFlowable, ListItem, KeepTogether, HRFlowable
            from reportlab.platypus.tableofcontents import TableOfContents
            from reportlab.pdfbase import pdfmetrics
            
            # Custom page template for headers/footers
            def add_page_number(canvas, doc):
                """Add page numbers and header/footer to each page"""
                page_num = canvas.getPageNumber()
                canvas.saveState()
                
                # Footer line
                canvas.setStrokeColor(reportlab_colors.HexColor('#1e40af'))
                canvas.setLineWidth(1)
                canvas.line(50, 40, 545, 40)
                
                # Page number
                canvas.setFont('Helvetica', 9)
                canvas.setFillColor(reportlab_colors.grey)
                canvas.drawString(50, 25, f"Page {page_num}")
                
                # Report ID in footer
                canvas.drawRightString(545, 25, f"Report: {report_id[:12]}...")
                
                # Confidential watermark on each page
                canvas.setFont('Helvetica', 8)
                canvas.drawCentredString(297.5, 25, "CONFIDENTIAL - Security Report")
                
                # Header on pages after first
                if page_num > 1:
                    canvas.setStrokeColor(reportlab_colors.HexColor('#1e40af'))
                    canvas.line(50, 800, 545, 800)
                    canvas.setFont('Helvetica-Bold', 10)
                    canvas.setFillColor(reportlab_colors.HexColor('#1e40af'))
                    canvas.drawString(50, 808, "ONYX Security Intelligence Platform")
                    canvas.setFont('Helvetica', 9)
                    canvas.setFillColor(reportlab_colors.grey)
                    canvas.drawRightString(545, 808, report_data.get('project_name', 'Security Report'))
                
                canvas.restoreState()
            
            # Create PDF document with better margins and page template
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=60,
                bottomMargin=60,
                title=f"ONYX Security Report - {report_data.get('project_name', 'Unknown')}",
                author="ONYX Security Intelligence Platform",
                subject="Security Vulnerability Analysis Report",
                creator="ONYX AI-Powered Security Scanner"
            )
            
            # Enhanced professional styles
            styles = getSampleStyleSheet()
            
            # Color scheme - professional blue theme
            primary_color = reportlab_colors.HexColor('#1e40af')  # Deep blue
            secondary_color = reportlab_colors.HexColor('#3b82f6')  # Bright blue
            accent_color = reportlab_colors.HexColor('#10b981')  # Green for success
            warning_color = reportlab_colors.HexColor('#f59e0b')  # Amber for warnings
            danger_color = reportlab_colors.HexColor('#ef4444')  # Red for critical
            light_bg = reportlab_colors.HexColor('#f8fafc')  # Light background
            border_color = reportlab_colors.HexColor('#e2e8f0')  # Light border
            
            # Professional title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                spaceAfter=10,
                spaceBefore=0,
                alignment=TA_CENTER,
                textColor=primary_color,
                fontName='Helvetica-Bold'
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=25,
                alignment=TA_CENTER,
                textColor=reportlab_colors.grey
            )
            
            # Section heading style with modern look
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=25,
                textColor=white,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=10,
                backColor=primary_color,
                leftIndent=0,
                rightIndent=0
            )
            
            # Sub-section heading
            subheading_style = ParagraphStyle(
                'SubHeading',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=15,
                textColor=primary_color,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=5,
                leftIndent=0
            )
            
            # AI analysis style with better formatting
            ai_style = ParagraphStyle(
                'AIAnalysis',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                leftIndent=15,
                rightIndent=15,
                backColor=light_bg,
                borderWidth=1,
                borderColor=border_color,
                borderPadding=12,
                leading=14
            )
            
            # Callout/highlight style for important info
            callout_style = ParagraphStyle(
                'Callout',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=10,
                leftIndent=10,
                backColor=reportlab_colors.HexColor('#fef3c7'),
                borderWidth=2,
                borderColor=warning_color,
                borderPadding=10,
                leading=14
            )
            
            # Action item style
            action_style = ParagraphStyle(
                'ActionItem',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leftIndent=20,
                textColor=danger_color,
                fontName='Helvetica-Bold',
                leading=13
            )
            
            # Success/info style
            info_style = ParagraphStyle(
                'InfoBox',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=10,
                leftIndent=15,
                rightIndent=15,
                backColor=reportlab_colors.HexColor('#ecfdf5'),
                borderWidth=1,
                borderColor=accent_color,
                borderPadding=10,
                leading=14
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=8,
                leading=14
            )
            
            # Build enhanced PDF content
            story = []
            
            # ============ COVER PAGE ============
            story.append(Spacer(1, 80))
            
            # Logo placeholder (text-based)
            logo_style = ParagraphStyle(
                'LogoStyle',
                parent=styles['Normal'],
                fontSize=48,
                alignment=TA_CENTER,
                textColor=primary_color,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph("ONYX", logo_style))
            story.append(Paragraph("Security Intelligence Platform", subtitle_style))
            story.append(Spacer(1, 40))
            
            # Horizontal line
            story.append(HRFlowable(width="80%", thickness=2, color=primary_color, spaceAfter=30, spaceBefore=20))
            
            # Report title
            report_title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=22,
                alignment=TA_CENTER,
                textColor=black,
                fontName='Helvetica-Bold',
                spaceAfter=20
            )
            story.append(Paragraph("Security Vulnerability Assessment Report", report_title_style))
            story.append(Paragraph(f"<b>Project:</b> {report_data.get('project_name', 'Unknown Project')}", 
                                   ParagraphStyle('ProjectName', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER, spaceAfter=30)))
            
            story.append(Spacer(1, 40))
            
            # Key metrics boxes on cover
            findings_by_severity = report_data.get('findings_by_severity', {})
            total_findings_count = report_data.get('total_findings', 0)
            critical_count = findings_by_severity.get('critical', 0)
            high_count = findings_by_severity.get('high', 0)
            medium_count = findings_by_severity.get('medium', 0)
            low_count = findings_by_severity.get('low', 0)
            
            # Calculate security score (0-100)
            if total_findings_count == 0:
                security_score = 100
            else:
                # Weighted score: critical=-25, high=-15, medium=-5, low=-1 per finding
                penalty = (critical_count * 25) + (high_count * 15) + (medium_count * 5) + (low_count * 1)
                security_score = max(0, 100 - penalty)
            
            # Risk level based on findings
            if critical_count > 0:
                risk_level = "CRITICAL"
                risk_color = danger_color
                risk_description = "Immediate action required - Critical vulnerabilities detected"
            elif high_count > 3:
                risk_level = "HIGH"
                risk_color = reportlab_colors.HexColor('#f97316')
                risk_description = "Priority remediation needed - Multiple high-severity issues"
            elif high_count > 0:
                risk_level = "MEDIUM"
                risk_color = warning_color
                risk_description = "Schedule remediation - High-severity issues present"
            elif medium_count > 0:
                risk_level = "LOW"
                risk_color = reportlab_colors.HexColor('#84cc16')
                risk_description = "Monitor - Minor issues identified"
            else:
                risk_level = "SECURE"
                risk_color = accent_color
                risk_description = "Excellent - No significant vulnerabilities detected"
            
            # Cover page metrics table
            cover_metrics = [
                ['Security Score', 'Risk Level', 'Total Findings', 'Scan Status'],
                [f'{security_score}/100', risk_level, str(total_findings_count), report_data.get('status', 'N/A').upper()]
            ]
            
            cover_table = Table(cover_metrics, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            cover_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, 1), 14),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, border_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Color code the risk level cell
                ('TEXTCOLOR', (1, 1), (1, 1), risk_color),
            ]))
            story.append(cover_table)
            
            story.append(Spacer(1, 40))
            
            # Report metadata
            meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=reportlab_colors.grey)
            story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", meta_style))
            story.append(Paragraph(f"<b>Report ID:</b> {report_id}", meta_style))
            if report_data.get('git_metadata', {}).get('repository_url'):
                story.append(Paragraph(f"<b>Repository:</b> {report_data.get('git_metadata', {}).get('repository_url', 'N/A')}", meta_style))
            
            story.append(Spacer(1, 60))
            
            # Confidentiality notice
            notice_style = ParagraphStyle('NoticeStyle', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, 
                                          textColor=reportlab_colors.grey, backColor=light_bg, borderPadding=15)
            story.append(Paragraph(
                "<b>CONFIDENTIAL</b><br/>"
                "This report contains sensitive security information about your application. "
                "Handle with appropriate care and restrict distribution to authorized personnel only.",
                notice_style
            ))
            
            # Page break for main content
            story.append(PageBreak())
            
            # ============ TABLE OF CONTENTS ============
            story.append(Paragraph("Table of Contents", heading_style))
            story.append(Spacer(1, 15))
            
            toc_style = ParagraphStyle('TOCStyle', parent=styles['Normal'], fontSize=11, spaceAfter=8, leftIndent=20)
            toc_items = [
                ("1. Executive Summary", "Overview of security assessment findings"),
                ("2. Risk Assessment", "Detailed risk analysis and scoring"),
                ("3. Project Information", "Repository and scan metadata"),
                ("4. Vulnerability Summary", "Breakdown by severity level"),
                ("5. AI-Powered Analysis", "Machine learning insights and recommendations"),
                ("6. Scanner Results", "Individual scanner performance"),
                ("7. Detailed Findings", "Comprehensive vulnerability details"),
                ("8. Remediation Roadmap", "Prioritized action items"),
                ("9. Appendix", "Glossary and methodology")
            ]
            
            for title, desc in toc_items:
                story.append(Paragraph(f"<b>{title}</b> - <i>{desc}</i>", toc_style))
            
            story.append(PageBreak())
            
            # ============ SECTION 1: EXECUTIVE SUMMARY ============
            story.append(Paragraph("1. Executive Summary", heading_style))
            story.append(Spacer(1, 10))
            
            # Quick stats row
            quick_stats = [
                ['Total Findings', 'Critical', 'High', 'Medium', 'Low'],
                [str(total_findings_count), str(critical_count), str(high_count), str(medium_count), str(low_count)]
            ]
            quick_stats_table = Table(quick_stats, colWidths=[1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
            quick_stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('BACKGROUND', (1, 1), (1, 1), danger_color if critical_count > 0 else light_bg),
                ('TEXTCOLOR', (1, 1), (1, 1), white if critical_count > 0 else black),
                ('BACKGROUND', (2, 1), (2, 1), reportlab_colors.HexColor('#f97316') if high_count > 0 else light_bg),
                ('TEXTCOLOR', (2, 1), (2, 1), white if high_count > 0 else black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, 1), 16),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, border_color),
            ]))
            story.append(quick_stats_table)
            story.append(Spacer(1, 15))
            
            # Risk level callout
            story.append(Paragraph(f"<b>Overall Risk Level: {risk_level}</b>", 
                                   ParagraphStyle('RiskLevel', parent=styles['Normal'], fontSize=12, 
                                                  textColor=risk_color, fontName='Helvetica-Bold')))
            story.append(Paragraph(risk_description, normal_style))
            story.append(Spacer(1, 15))
            
            # Get AI analysis for executive summary
            ai_summary = "Security analysis completed. Review detailed findings below for specific vulnerabilities and recommended actions."
            
            # Generate real AI analysis based on findings
            if findings:
                try:
                    severity_counts = {}
                    finding_types = set()
                    for finding in findings:
                        if isinstance(finding, dict):
                            sev = finding.get('severity', 'unknown').lower()
                            ftype = finding.get('type', finding.get('category', finding.get('rule_id', '')))
                        else:
                            sev = getattr(finding, 'severity', 'unknown')
                            if hasattr(sev, 'value'):
                                sev = sev.value.lower()
                            ftype = getattr(finding, 'category', getattr(finding, 'rule_id', ''))
                        
                        severity_counts[sev] = severity_counts.get(sev, 0) + 1
                        if ftype:
                            finding_types.add(str(ftype)[:30])
                    
                    types_list = list(finding_types)[:3]
                    types_str = ', '.join(types_list) if types_list else 'various security concerns'
                    
                    ai_summary = f"""This security assessment identified <b>{total_findings_count} vulnerabilities</b> across the scanned codebase. 
                    
The analysis detected <b>{critical_count} critical</b> and <b>{high_count} high-severity</b> issues that require immediate attention. 
Primary vulnerability categories include: {types_str}.

<b>Key Recommendations:</b>
1. Address all critical vulnerabilities within 24 hours
2. Schedule high-severity fixes for the current sprint
3. Review medium-severity issues in the next maintenance window
4. Implement automated security scanning in CI/CD pipeline"""
                    
                except Exception as e:
                    logger.warning(f"Error generating AI summary: {e}")
            
            # Try to get existing AI analysis
            if report and hasattr(report, 'ai_analysis') and report.ai_analysis:
                ai_summary = report.ai_analysis.executive_summary or ai_summary
            elif report_data.get('ai_analysis'):
                ai_summary = report_data['ai_analysis'].get('executive_summary', ai_summary)
            
            story.append(Paragraph("<b>Assessment Overview:</b>", subheading_style))
            story.append(Paragraph(ai_summary, ai_style))
            story.append(Spacer(1, 20))
            
            # ============ SECTION 2: RISK ASSESSMENT ============
            story.append(Paragraph("2. Risk Assessment", heading_style))
            story.append(Spacer(1, 10))
            
            # Security score visualization (text-based)
            score_description = ""
            if security_score >= 90:
                score_grade = "A"
                score_description = "Excellent security posture with minimal vulnerabilities."
            elif security_score >= 80:
                score_grade = "B"
                score_description = "Good security with some areas for improvement."
            elif security_score >= 70:
                score_grade = "C"
                score_description = "Fair security - several vulnerabilities need attention."
            elif security_score >= 60:
                score_grade = "D"
                score_description = "Poor security - significant vulnerabilities present."
            else:
                score_grade = "F"
                score_description = "Critical security issues - immediate action required."
            
            score_box = [
                ['Security Score', 'Grade', 'Assessment'],
                [f'{security_score}/100', score_grade, score_description]
            ]
            score_table = Table(score_box, colWidths=[1.5*inch, 1*inch, 4*inch])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (0, 1), 18),
                ('FONTSIZE', (1, 1), (1, 1), 24),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, border_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 20))
            
            # ============ SECTION 3: PROJECT INFORMATION ============
            story.append(Paragraph("3. Project Information", heading_style))
            story.append(Spacer(1, 10))
            
            project_data = [
                ['Property', 'Value'],
                ['Project Name', report_data.get('project_name', 'N/A')],
                ['Report ID', str(report_id)],
                ['Scan ID', report_data.get('scan_id', 'N/A')],
                ['Status', report_data.get('status', 'N/A').upper()],
                ['Created', report_data.get('created_at', 'N/A')[:19] if report_data.get('created_at') else 'N/A'],
                ['Completed', report_data.get('completed_at', 'N/A')[:19] if report_data.get('completed_at') else 'N/A'],
                ['Duration', f"{report_data.get('duration_seconds', 0):.1f} seconds"],
                ['Repository', report_data.get('git_metadata', {}).get('repository_url', 'N/A')],
                ['Branch', report_data.get('git_metadata', {}).get('branch', 'N/A')],
                ['Commit', report_data.get('git_metadata', {}).get('commit_hash', 'N/A')[:12] + '...' if report_data.get('git_metadata', {}).get('commit_hash') else 'N/A']
            ]
            
            project_table = Table(project_data, colWidths=[2*inch, 4.5*inch])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('BACKGROUND', (0, 1), (0, -1), light_bg),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, border_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(project_table)
            story.append(Spacer(1, 20))
            
            # ============ SECTION 4: VULNERABILITY SUMMARY ============
            story.append(Paragraph("4. Vulnerability Summary", heading_style))
            story.append(Spacer(1, 10))
            
            # Enhanced severity breakdown table
            summary_data = [
                ['Severity', 'Count', 'Percentage', 'SLA', 'Action Required'],
                ['CRITICAL', str(critical_count), f"{(critical_count / max(total_findings_count, 1)) * 100:.1f}%", '24 hours', 'Immediate remediation'],
                ['HIGH', str(high_count), f"{(high_count / max(total_findings_count, 1)) * 100:.1f}%", '7 days', 'Priority fix'],
                ['MEDIUM', str(medium_count), f"{(medium_count / max(total_findings_count, 1)) * 100:.1f}%", '30 days', 'Schedule fix'],
                ['LOW', str(low_count), f"{(low_count / max(total_findings_count, 1)) * 100:.1f}%", '90 days', 'Monitor'],
                ['INFO', str(findings_by_severity.get('info', 0)), f"{(findings_by_severity.get('info', 0) / max(total_findings_count, 1)) * 100:.1f}%", 'N/A', 'Informational'],
                ['TOTAL', str(total_findings_count), '100%', '-', f'{total_findings_count} issues identified']
            ]
            
            summary_table = Table(summary_data, colWidths=[1.1*inch, 0.7*inch, 0.9*inch, 0.8*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (4, 0), (4, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                # Severity color coding
                ('BACKGROUND', (0, 1), (0, 1), danger_color),
                ('TEXTCOLOR', (0, 1), (0, 1), white),
                ('BACKGROUND', (0, 2), (0, 2), reportlab_colors.HexColor('#f97316')),
                ('TEXTCOLOR', (0, 2), (0, 2), white),
                ('BACKGROUND', (0, 3), (0, 3), warning_color),
                ('BACKGROUND', (0, 4), (0, 4), reportlab_colors.HexColor('#84cc16')),
                ('BACKGROUND', (0, 5), (0, 5), secondary_color),
                ('TEXTCOLOR', (0, 5), (0, 5), white),
                ('BACKGROUND', (0, 6), (-1, 6), light_bg),
                ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, border_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # ============ SECTION 5: AI-POWERED ANALYSIS ============
            story.append(Paragraph("5. AI-Powered Security Analysis", heading_style))
            story.append(Spacer(1, 10))
            
            # Get AI analysis from report
            ai_analysis = None
            if report and hasattr(report, 'ai_analysis') and report.ai_analysis:
                ai_analysis = report.ai_analysis
            elif report_data.get('ai_analysis'):
                ai_analysis = report_data.get('ai_analysis')
            
            if ai_analysis:
                # Risk Assessment subsection
                risk_assessment = None
                if hasattr(ai_analysis, 'risk_assessment') and ai_analysis.risk_assessment:
                    risk_assessment = ai_analysis.risk_assessment
                elif isinstance(ai_analysis, dict) and ai_analysis.get('risk_assessment'):
                    risk_assessment = ai_analysis.get('risk_assessment')
                
                if risk_assessment:
                    story.append(Paragraph("<b>Risk Assessment</b>", subheading_style))
                    story.append(Paragraph(risk_assessment, ai_style))
                    story.append(Spacer(1, 12))
                
                # Priority Findings
                priority_findings = None
                if hasattr(ai_analysis, 'priority_findings') and ai_analysis.priority_findings:
                    priority_findings = ai_analysis.priority_findings
                elif isinstance(ai_analysis, dict) and ai_analysis.get('priority_findings'):
                    priority_findings = ai_analysis.get('priority_findings')
                
                if priority_findings:
                    story.append(Paragraph("<b>Priority Findings</b>", subheading_style))
                    for i, finding in enumerate(priority_findings[:5], 1):
                        story.append(Paragraph(f"<b>{i}.</b> {finding}", normal_style))
                    story.append(Spacer(1, 12))
                
                # Recommendations
                recommendations = None
                if hasattr(ai_analysis, 'recommendations') and ai_analysis.recommendations:
                    recommendations = ai_analysis.recommendations
                elif isinstance(ai_analysis, dict) and ai_analysis.get('recommendations'):
                    recommendations = ai_analysis.get('recommendations')
                
                if recommendations:
                    story.append(Paragraph("<b>AI Recommendations</b>", subheading_style))
                    for i, rec in enumerate(recommendations[:5], 1):
                        story.append(Paragraph(f"<b>{i}.</b> {rec}", normal_style))
                    story.append(Spacer(1, 12))
                
                # Compliance Impact
                compliance_impact = None
                if hasattr(ai_analysis, 'compliance_impact') and ai_analysis.compliance_impact:
                    compliance_impact = ai_analysis.compliance_impact
                elif isinstance(ai_analysis, dict) and ai_analysis.get('compliance_impact'):
                    compliance_impact = ai_analysis.get('compliance_impact')
                
                if compliance_impact:
                    story.append(Paragraph("<b>Compliance Impact</b>", subheading_style))
                    if isinstance(compliance_impact, dict):
                        compliance_rows = [['Framework', 'Impact']]
                        for framework, impact in compliance_impact.items():
                            compliance_rows.append([framework, str(impact)[:80]])
                        if len(compliance_rows) > 1:
                            comp_table = Table(compliance_rows, colWidths=[2*inch, 4.5*inch])
                            comp_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, -1), 9),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('GRID', (0, 0), (-1, -1), 1, border_color),
                            ]))
                            story.append(comp_table)
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
                    story.append(Paragraph("<b>Estimated Remediation Time</b>", subheading_style))
                    story.append(Paragraph(f"Based on the identified vulnerabilities, the estimated time to complete all remediations is: <b>{estimated_fix_time}</b>", info_style))
                    story.append(Spacer(1, 12))
                
            else:
                # Fallback AI analysis if none exists
                story.append(Paragraph("<b>Automated Security Assessment</b>", subheading_style))
                
                if findings:
                    # Generate basic analysis based on findings
                    auto_critical = severity_counts.get('critical', 0) if 'severity_counts' in dir() else critical_count
                    auto_high = severity_counts.get('high', 0) if 'severity_counts' in dir() else high_count
                    auto_medium = severity_counts.get('medium', 0) if 'severity_counts' in dir() else medium_count
                    auto_low = severity_counts.get('low', 0) if 'severity_counts' in dir() else low_count
                    
                    if auto_critical > 0:
                        auto_risk_level = "CRITICAL - Immediate action required"
                    elif auto_high > 0:
                        auto_risk_level = "HIGH - Prompt remediation needed"
                    elif auto_medium > 0:
                        auto_risk_level = "MEDIUM - Scheduled remediation recommended"
                    else:
                        auto_risk_level = "LOW - Monitor and address during maintenance"
                    
                    basic_analysis = f"""Security scan identified <b>{total_findings_count}</b> findings requiring attention.

<b>Risk Level:</b> {auto_risk_level}

<b>Severity Breakdown:</b>
- Critical: {auto_critical} findings (fix within 24 hours)
- High: {auto_high} findings (fix within 7 days)
- Medium: {auto_medium} findings (fix within 30 days)
- Low: {auto_low} findings (monitor and address as needed)

<b>Recommendations:</b>
1. Prioritize critical and high-severity findings for immediate remediation
2. Review medium-severity findings during the next maintenance window
3. Implement automated security scanning in your CI/CD pipeline
4. Consider security training for the development team"""
                    
                    story.append(Paragraph(basic_analysis, ai_style))
                else:
                    story.append(Paragraph("Excellent! No security vulnerabilities were detected in this scan. Continue maintaining current security practices and run regular scans to ensure ongoing protection.", info_style))
                
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 10))
            
            # ============ SECTION 6: SCANNER RESULTS ============
            if report_data.get('scan_results'):
                story.append(Paragraph("6. Scanner Results", heading_style))
                story.append(Spacer(1, 10))
                
                scanner_data = [['Scanner', 'Status', 'Findings', 'Duration', 'Performance']]
                for scan_result in report_data.get('scan_results', []):
                    # Handle both dict and ScanResult object formats
                    if hasattr(scan_result, 'scanner'):
                        # ScanResult object
                        scanner_name = scan_result.scanner.value if hasattr(scan_result.scanner, 'value') else str(scan_result.scanner)
                        # Clean up scanner name
                        scanner_name = scanner_name.replace('ScannerType.', '').replace('GITLEAKS', 'GitLeaks').replace('SEMGREP', 'Semgrep').replace('SAFETY', 'Safety').replace('BANDIT', 'Bandit').replace('TRIVY', 'Trivy')
                        
                        status = scan_result.status.value if hasattr(scan_result.status, 'value') else str(scan_result.status)
                        status = status.replace('ScanStatus.', '').upper()
                        findings_count = len(scan_result.findings) if scan_result.findings else 0
                        duration = scan_result.duration_seconds or 0
                    else:
                        # Dictionary format
                        scanner_name = str(scan_result.get('scanner', 'Unknown')).replace('ScannerType.', '')
                        status = str(scan_result.get('status', 'Unknown')).upper()
                        findings_count = scan_result.get('findings_count', len(scan_result.get('findings', [])))
                        duration = scan_result.get('duration_seconds', 0)
                    
                    # Performance rating based on duration
                    if duration < 5:
                        performance = "Excellent"
                    elif duration < 30:
                        performance = "Good"
                    elif duration < 60:
                        performance = "Fair"
                    else:
                        performance = "Slow"
                    
                    scanner_data.append([
                        scanner_name,
                        status,
                        str(findings_count),
                        f"{duration:.1f}s",
                        performance
                    ])
                
                scanner_table = Table(scanner_data, colWidths=[1.6*inch, 1*inch, 0.9*inch, 0.9*inch, 1.1*inch])
                scanner_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, border_color),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BACKGROUND', (0, 1), (0, -1), light_bg),
                ]))
                story.append(scanner_table)
                story.append(Spacer(1, 20))
            
            # Page break before detailed findings
            story.append(PageBreak())
            
            # ============ SECTION 7: DETAILED FINDINGS ============
            if findings:
                story.append(Paragraph("7. Detailed Security Findings", heading_style))
                story.append(Spacer(1, 10))
                story.append(Paragraph(f"This section contains detailed information about the <b>{len(findings)}</b> security findings identified during the scan. Findings are sorted by severity (critical first).", normal_style))
                story.append(Spacer(1, 15))
                
                # Sort findings by severity
                severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
                
                def get_severity_value(f):
                    if isinstance(f, dict):
                        sev = f.get('severity', 'info')
                    else:
                        sev = getattr(f, 'severity', 'info')
                        if hasattr(sev, 'value'):
                            sev = sev.value
                    return severity_order.get(str(sev).lower(), 4)
                
                findings_sorted = sorted(findings, key=get_severity_value)
                
                # Show up to 20 findings for better coverage
                max_findings = 20
                for i, finding in enumerate(findings_sorted[:max_findings], 1):
                    # Handle both dict and object formats
                    if isinstance(finding, dict):
                        severity = str(finding.get('severity', 'unknown')).lower()
                        title = finding.get('title', 'Untitled Finding')
                        scanner = str(finding.get('scanner', 'Unknown')).replace('ScannerType.', '')
                        file_path = finding.get('file_path', 'N/A')
                        line_number = finding.get('line_number', finding.get('line_start', 'N/A'))
                        rule_id = finding.get('rule_id', 'N/A')
                        cwe_id = finding.get('cwe_id', 'N/A')
                        description = finding.get('description', '')
                        remediation = finding.get('remediation') or finding.get('recommendation', '')
                        fix_effort = finding.get('fix_effort', '')
                    else:
                        # Object format
                        severity = getattr(finding, 'severity', 'unknown')
                        if hasattr(severity, 'value'):
                            severity = severity.value
                        severity = str(severity).lower()
                        title = getattr(finding, 'title', 'Untitled Finding')
                        scanner = getattr(finding, 'scanner', 'Unknown')
                        if hasattr(scanner, 'value'):
                            scanner = scanner.value
                        scanner = str(scanner).replace('ScannerType.', '')
                        file_path = getattr(finding, 'file_path', 'N/A')
                        line_number = getattr(finding, 'line_start', getattr(finding, 'line_number', 'N/A'))
                        rule_id = getattr(finding, 'rule_id', 'N/A')
                        cwe_id = getattr(finding, 'cwe_id', getattr(finding, 'cwe', 'N/A'))
                        description = getattr(finding, 'description', '')
                        remediation = getattr(finding, 'remediation', '')
                        fix_effort = getattr(finding, 'fix_effort', '')
                    
                    # Severity styling
                    severity_colors = {
                        'critical': danger_color, 
                        'high': reportlab_colors.HexColor('#f97316'), 
                        'medium': warning_color, 
                        'low': reportlab_colors.HexColor('#84cc16'), 
                        'info': secondary_color
                    }
                    sev_color = severity_colors.get(severity, reportlab_colors.grey)
                    
                    # Fix effort label
                    effort_label = ''
                    if fix_effort:
                        effort_map = {'low': 'Quick Fix', 'medium': 'Moderate Effort', 'high': 'Complex Fix'}
                        effort_label = effort_map.get(fix_effort.lower(), '')
                    
                    # Finding header with severity badge
                    finding_title_style = ParagraphStyle(
                        f'FindingTitle{i}',
                        parent=styles['Heading3'],
                        fontSize=11,
                        spaceAfter=8,
                        spaceBefore=18,
                        textColor=sev_color,
                        fontName='Helvetica-Bold',
                        leftIndent=0
                    )
                    story.append(Paragraph(f"Finding #{i}: {title}", finding_title_style))
                    
                    # Finding details table with better styling
                    finding_details = [
                        ['Property', 'Details'],
                        ['Severity', f"{severity.upper()}{' (' + effort_label + ')' if effort_label else ''}"],
                        ['Scanner', scanner],
                        ['File', file_path if file_path != 'N/A' else 'Not specified'],
                        ['Line', str(line_number) if line_number and line_number != 'N/A' else 'N/A'],
                        ['Rule ID', str(rule_id) if rule_id and rule_id != 'N/A' else 'N/A'],
                        ['CWE', str(cwe_id) if cwe_id and cwe_id != 'N/A' else 'N/A']
                    ]
                    
                    detail_table = Table(finding_details, colWidths=[1.2*inch, 5.3*inch])
                    detail_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('BACKGROUND', (0, 1), (0, -1), light_bg),
                        ('BACKGROUND', (0, 1), (1, 1), sev_color),
                        ('TEXTCOLOR', (0, 1), (1, 1), white if severity in ['critical', 'high', 'info'] else black),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.5, border_color)
                    ]))
                    story.append(detail_table)
                    
                    # Description
                    if description:
                        story.append(Spacer(1, 6))
                        desc_style = ParagraphStyle(
                            f'Desc{i}',
                            parent=styles['Normal'],
                            fontSize=9,
                            spaceAfter=6,
                            leftIndent=10,
                            leading=12
                        )
                        story.append(Paragraph(f"<b>Description:</b> {description[:500]}{'...' if len(description) > 500 else ''}", desc_style))
                    
                    # Remediation advice with highlight
                    if remediation:
                        story.append(Spacer(1, 4))
                        story.append(Paragraph(f"<b>Recommended Fix:</b> {remediation[:400]}{'...' if len(remediation) > 400 else ''}", info_style))
                    
                    story.append(Spacer(1, 10))
                
                if len(findings) > max_findings:
                    story.append(Spacer(1, 15))
                    story.append(Paragraph(
                        f"<b>Note:</b> {len(findings) - max_findings} additional findings are not shown in this PDF. "
                        f"Download the JSON or CSV format for complete details of all {len(findings)} findings.",
                        callout_style
                    ))
            
            # ============ SECTION 8: REMEDIATION ROADMAP ============
            story.append(PageBreak())
            story.append(Paragraph("8. Remediation Roadmap", heading_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("Based on the identified vulnerabilities, here is a prioritized remediation plan:", normal_style))
            story.append(Spacer(1, 10))
            
            # Create remediation timeline
            roadmap_data = [
                ['Priority', 'Timeframe', 'Action Items', 'Count'],
                ['P1 - CRITICAL', 'Within 24 hours', 'Address all critical vulnerabilities immediately', str(critical_count)],
                ['P2 - HIGH', 'Within 7 days', 'Fix high-severity issues in current sprint', str(high_count)],
                ['P3 - MEDIUM', 'Within 30 days', 'Schedule medium issues for next maintenance window', str(medium_count)],
                ['P4 - LOW', 'Within 90 days', 'Monitor and address during regular updates', str(low_count)],
            ]
            
            roadmap_table = Table(roadmap_data, colWidths=[1.2*inch, 1.2*inch, 3*inch, 0.8*inch])
            roadmap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('BACKGROUND', (0, 1), (0, 1), danger_color),
                ('TEXTCOLOR', (0, 1), (0, 1), white),
                ('BACKGROUND', (0, 2), (0, 2), reportlab_colors.HexColor('#f97316')),
                ('TEXTCOLOR', (0, 2), (0, 2), white),
                ('BACKGROUND', (0, 3), (0, 3), warning_color),
                ('BACKGROUND', (0, 4), (0, 4), reportlab_colors.HexColor('#84cc16')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, border_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(roadmap_table)
            story.append(Spacer(1, 20))
            
            # Next steps
            story.append(Paragraph("<b>Recommended Next Steps:</b>", subheading_style))
            next_steps = [
                "1. Review all critical and high-severity findings with your development team",
                "2. Create tickets/issues for each vulnerability in your project tracker",
                "3. Assign owners and set realistic deadlines based on the remediation SLAs",
                "4. Implement fixes following secure coding best practices",
                "5. Re-scan after remediation to verify fixes are effective",
                "6. Consider implementing automated security scanning in your CI/CD pipeline"
            ]
            for step in next_steps:
                story.append(Paragraph(step, normal_style))
            
            story.append(Spacer(1, 25))
            
            # ============ SECTION 9: APPENDIX ============
            story.append(Paragraph("9. Appendix", heading_style))
            story.append(Spacer(1, 10))
            
            # Glossary
            story.append(Paragraph("<b>Glossary of Terms</b>", subheading_style))
            glossary_data = [
                ['Term', 'Definition'],
                ['SAST', 'Static Application Security Testing - analyzes source code for vulnerabilities'],
                ['DAST', 'Dynamic Application Security Testing - tests running applications'],
                ['CWE', 'Common Weakness Enumeration - standardized list of software weaknesses'],
                ['CVE', 'Common Vulnerabilities and Exposures - known security vulnerabilities'],
                ['SLA', 'Service Level Agreement - target timeframe for addressing issues'],
                ['OWASP', 'Open Web Application Security Project - security standards organization'],
            ]
            
            glossary_table = Table(glossary_data, colWidths=[1*inch, 5.5*inch])
            glossary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('BACKGROUND', (0, 1), (0, -1), light_bg),
            ]))
            story.append(glossary_table)
            story.append(Spacer(1, 20))
            
            # Methodology
            story.append(Paragraph("<b>Scan Methodology</b>", subheading_style))
            story.append(Paragraph(
                "This security assessment was performed using ONYX Security Intelligence Platform's automated scanning engine. "
                "The scan included multiple security analyzers covering static code analysis, dependency vulnerability checking, "
                "secret detection, and infrastructure configuration review. AI-powered analysis provides additional context "
                "and prioritization recommendations based on threat intelligence and industry best practices.",
                normal_style
            ))
            story.append(Spacer(1, 30))
            
            # Professional Footer
            story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=15, spaceBefore=15))
            
            footer_style = ParagraphStyle(
                'FinalFooter',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=reportlab_colors.grey
            )
            
            story.append(Paragraph("<b>ONYX Security Intelligence Platform</b>", footer_style))
            story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S UTC')}", footer_style))
            story.append(Paragraph(f"Report ID: {report_id}", footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                "This document contains confidential security information. "
                "Distribution should be limited to authorized personnel only. "
                "For questions or support, contact your security team.",
                footer_style
            ))
            
            # Build PDF with page numbers
            doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            # Generate filename with date
            date_str = datetime.now().strftime('%Y%m%d')
            project_name_safe = report_data.get('project_name', 'report').replace(' ', '_').replace('/', '_')[:30]
            
            headers = {
                'Content-Disposition': f'attachment; filename="ONYX_Security_Report_{project_name_safe}_{date_str}.pdf"',
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
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
