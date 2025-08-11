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
from bson import ObjectId

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import red, green, orange, black, blue, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from models.report import ScanReport, ScanStatus, SeverityLevel, ScannerType
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


@router.get("/")
@router.get("")  # Handle both /api/reports/ and /api/reports
async def list_reports(
    limit: int = Query(50, ge=1, le=1000, description="Number of reports to return"),
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
        logger.info(f"📊 Fetching reports - limit: {limit}, skip: {skip}")
        
        # Build query filters for database
        filters = {}
        
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
        # Try to find in database first
        report = None
        
        # Check if it's a valid ObjectId (for real database documents)
        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
            except Exception as db_error:
                logger.warning(f"Database error when fetching report {report_id}: {db_error}")
        
        # If not found in database, return 404
        if not report:
            logger.info(f"Report {report_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
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
                                "severity": finding.severity.value,
                                "confidence": finding.confidence.value if finding.confidence else None,
                                "category": finding.category,
                                "file_path": finding.location.file_path if finding.location else "",
                                "line_number": finding.location.line_number if finding.location else None,
                                "column_number": finding.location.column_number if finding.location else None,
                                "code_snippet": finding.location.code_snippet if finding.location else "",
                                "remediation": finding.remediation
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
async def download_report(report_id: str, format: str = Query("json", regex="^(json|pdf|csv)$")):
    """
    Download report in specified format
    
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
        
        # Check if it's a valid ObjectId (for real database documents)
        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
                if report:
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
            # Generate PDF report
            pdf_buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=blue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=12,
                textColor=black
            )
            
            normal_style = styles['Normal']
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("Security Scan Report", title_style))
            story.append(Spacer(1, 12))
            
            # Project Information
            story.append(Paragraph("Project Information", heading_style))
            project_data = [
                ['Project Name:', report_data.get('project_name', 'N/A')],
                ['Scan ID:', report_data.get('scan_id', 'N/A')],
                ['Status:', report_data.get('status', 'N/A')],
                ['Created:', report_data.get('created_at', 'N/A')],
                ['Completed:', report_data.get('completed_at', 'N/A')],
                ['Duration:', f"{report_data.get('duration_seconds', 0)} seconds"],
                ['Repository:', report_data.get('git_metadata', {}).get('repository_url', 'N/A')],
                ['Branch:', report_data.get('git_metadata', {}).get('branch', 'N/A')],
                ['Commit:', report_data.get('git_metadata', {}).get('commit_hash', 'N/A')[:8] + '...' if report_data.get('git_metadata', {}).get('commit_hash') else 'N/A']
            ]
            
            project_table = Table(project_data, colWidths=[2*inch, 4*inch])
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), blue),
                ('TEXTCOLOR', (0, 0), (0, -1), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), white),
                ('TEXTCOLOR', (1, 0), (1, -1), black),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            story.append(project_table)
            story.append(Spacer(1, 20))
            
            # Summary Statistics
            story.append(Paragraph("Security Summary", heading_style))
            findings_by_severity = report_data.get('findings_by_severity', {})
            total_findings = report_data.get('total_findings', 0)
            
            summary_data = [
                ['Severity', 'Count', 'Percentage'],
                ['Critical', str(findings_by_severity.get('critical', 0)), f"{(findings_by_severity.get('critical', 0) / max(total_findings, 1)) * 100:.1f}%"],
                ['High', str(findings_by_severity.get('high', 0)), f"{(findings_by_severity.get('high', 0) / max(total_findings, 1)) * 100:.1f}%"],
                ['Medium', str(findings_by_severity.get('medium', 0)), f"{(findings_by_severity.get('medium', 0) / max(total_findings, 1)) * 100:.1f}%"],
                ['Low', str(findings_by_severity.get('low', 0)), f"{(findings_by_severity.get('low', 0) / max(total_findings, 1)) * 100:.1f}%"],
                ['Info', str(findings_by_severity.get('info', 0)), f"{(findings_by_severity.get('info', 0) / max(total_findings, 1)) * 100:.1f}%"],
                ['Total', str(total_findings), '100.0%']
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (0, 1), red),      # Critical
                ('BACKGROUND', (0, 2), (0, 2), orange),  # High
                ('BACKGROUND', (0, 3), (0, 3), orange),  # Medium
                ('BACKGROUND', (0, 4), (0, 4), green),   # Low
                ('BACKGROUND', (0, 5), (0, 5), green),   # Info
                ('BACKGROUND', (0, 6), (0, 6), blue),    # Total
                ('TEXTCOLOR', (0, 1), (0, 6), white),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Findings Details (if available in metadata)
            findings = report_data.get('metadata', {}).get('findings', [])
            if findings:
                story.append(Paragraph("Detailed Findings", heading_style))
                
                for i, finding in enumerate(findings[:20]):  # Limit to first 20 findings
                    finding_title = f"Finding {i+1}: {finding.get('title', 'Untitled Finding')}"
                    story.append(Paragraph(finding_title, ParagraphStyle(
                        'FindingTitle',
                        parent=styles['Heading3'],
                        fontSize=12,
                        spaceAfter=6,
                        spaceBefore=12,
                        textColor=red if finding.get('severity') in ['critical', 'high'] else orange
                    )))
                    
                    finding_details = [
                        ['Severity:', finding.get('severity', 'Unknown').title()],
                        ['Scanner:', finding.get('scanner', 'Unknown')],
                        ['File:', finding.get('file_path', 'N/A')],
                        ['Line:', str(finding.get('line_number', 'N/A'))],
                        ['Rule:', finding.get('rule_id', 'N/A')]
                    ]
                    
                    finding_table = Table(finding_details, colWidths=[1.2*inch, 4.3*inch])
                    finding_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP')
                    ]))
                    story.append(finding_table)
                    
                    if finding.get('description'):
                        story.append(Paragraph(f"<b>Description:</b> {finding['description']}", normal_style))
                    
                    story.append(Spacer(1, 12))
                
                if len(findings) > 20:
                    story.append(Paragraph(f"<i>... and {len(findings) - 20} more findings. Download CSV for complete details.</i>", normal_style))
            
            # Footer with timestamp
            story.append(PageBreak())
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                  ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)))
            
            # Build PDF
            doc.build(story)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            headers = {
                'Content-Disposition': f'attachment; filename="{report_id}_report.pdf"',
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
