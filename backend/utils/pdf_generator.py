"""
PDF Report Generator Utility for ONYX Security Intelligence Platform

Generates the same professional PDF report used by the Download PDF button.
Can be called from both the API route (download endpoint) and the notification
service (email attachment).
"""
import io
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


async def generate_report_pdf(report_id: str) -> Optional[bytes]:
    """
    Generate the full professional PDF report for a given report/scan ID.

    This reuses the exact same PDF generation logic as the Download PDF button
    on the frontend. It fetches the report from the database and produces a
    complete PDF with cover page, executive summary, risk assessment, findings,
    remediation roadmap, etc.

    Args:
        report_id: The report ID (or scan_id) to generate the PDF for.

    Returns:
        PDF content as bytes, or None if the report was not found or generation failed.
    """
    try:
        from bson import ObjectId
        from models.report import ScanReport

        # Reportlab imports
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import red, green, orange, black, blue, white
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.graphics.shapes import Drawing, Rect, Line, Circle
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.lib import colors as reportlab_colors
        from reportlab.platypus import ListFlowable, ListItem, KeepTogether, HRFlowable
        from reportlab.platypus.tableofcontents import TableOfContents
        from reportlab.pdfbase import pdfmetrics

        # ---- Fetch report from database ----
        report = None
        report_data = None

        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
            except Exception:
                pass

        # Also try finding by scan_id field
        if not report:
            try:
                report = await ScanReport.find_one({"scan_id": report_id})
            except Exception:
                pass

        if not report:
            logger.warning(f"Report {report_id} not found for PDF generation")
            return None

        # Build report_data dict (same structure as the download route)
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
            "scan_results": report.scan_results if report.scan_results else [],
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

        # Extract findings
        findings = []
        if report_data.get('scan_results'):
            for scan_result in report_data['scan_results']:
                if hasattr(scan_result, 'findings'):
                    if scan_result.findings:
                        for finding in scan_result.findings:
                            if hasattr(finding, 'model_dump'):
                                findings.append(finding.model_dump())
                            elif hasattr(finding, 'dict'):
                                findings.append(finding.dict())
                            else:
                                findings.append(finding)
                else:
                    findings.extend(scan_result.get('findings', []))

        # ---- Generate PDF (same logic as the download route) ----
        pdf_buffer = io.BytesIO()

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

        # Create PDF document
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

        # Color scheme
        primary_color = reportlab_colors.HexColor('#1e40af')
        secondary_color = reportlab_colors.HexColor('#3b82f6')
        accent_color = reportlab_colors.HexColor('#10b981')
        warning_color = reportlab_colors.HexColor('#f59e0b')
        danger_color = reportlab_colors.HexColor('#ef4444')
        light_bg = reportlab_colors.HexColor('#f8fafc')
        border_color = reportlab_colors.HexColor('#e2e8f0')

        # Styles
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'], fontSize=28, spaceAfter=10,
            spaceBefore=0, alignment=TA_CENTER, textColor=primary_color, fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle', parent=styles['Heading2'], fontSize=14, spaceAfter=25,
            alignment=TA_CENTER, textColor=reportlab_colors.grey
        )
        heading_style = ParagraphStyle(
            'CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12,
            spaceBefore=25, textColor=white, fontName='Helvetica-Bold', borderWidth=0,
            borderPadding=10, backColor=primary_color, leftIndent=0, rightIndent=0
        )
        subheading_style = ParagraphStyle(
            'SubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=8,
            spaceBefore=15, textColor=primary_color, fontName='Helvetica-Bold',
            borderWidth=0, borderPadding=5, leftIndent=0
        )
        ai_style = ParagraphStyle(
            'AIAnalysis', parent=styles['Normal'], fontSize=10, spaceAfter=12,
            leftIndent=15, rightIndent=15, backColor=light_bg, borderWidth=1,
            borderColor=border_color, borderPadding=12, leading=14
        )
        callout_style = ParagraphStyle(
            'Callout', parent=styles['Normal'], fontSize=10, spaceAfter=10,
            leftIndent=10, backColor=reportlab_colors.HexColor('#fef3c7'),
            borderWidth=2, borderColor=warning_color, borderPadding=10, leading=14
        )
        action_style = ParagraphStyle(
            'ActionItem', parent=styles['Normal'], fontSize=10, spaceAfter=6,
            leftIndent=20, textColor=danger_color, fontName='Helvetica-Bold', leading=13
        )
        info_style = ParagraphStyle(
            'InfoBox', parent=styles['Normal'], fontSize=10, spaceAfter=10,
            leftIndent=15, rightIndent=15, backColor=reportlab_colors.HexColor('#ecfdf5'),
            borderWidth=1, borderColor=accent_color, borderPadding=10, leading=14
        )
        normal_style = ParagraphStyle(
            'CustomNormal', parent=styles['Normal'], fontSize=10, spaceAfter=8, leading=14
        )

        # Build PDF content
        story = []

        # ============ COVER PAGE ============
        story.append(Spacer(1, 80))

        logo_style = ParagraphStyle(
            'LogoStyle', parent=styles['Normal'], fontSize=48, alignment=TA_CENTER,
            textColor=primary_color, fontName='Helvetica-Bold'
        )
        story.append(Paragraph("ONYX", logo_style))
        story.append(Paragraph("Security Intelligence Platform", subtitle_style))
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="80%", thickness=2, color=primary_color, spaceAfter=30, spaceBefore=20))

        report_title_style = ParagraphStyle(
            'ReportTitle', parent=styles['Heading1'], fontSize=22, alignment=TA_CENTER,
            textColor=black, fontName='Helvetica-Bold', spaceAfter=20
        )
        story.append(Paragraph("Security Vulnerability Assessment Report", report_title_style))
        story.append(Paragraph(f"<b>Project:</b> {report_data.get('project_name', 'Unknown Project')}",
                               ParagraphStyle('ProjectName', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER, spaceAfter=30)))
        story.append(Spacer(1, 40))

        # Key metrics
        findings_by_severity = report_data.get('findings_by_severity', {})
        total_findings_count = report_data.get('total_findings', 0)
        critical_count = findings_by_severity.get('critical', 0)
        high_count = findings_by_severity.get('high', 0)
        medium_count = findings_by_severity.get('medium', 0)
        low_count = findings_by_severity.get('low', 0)

        # Security score
        if total_findings_count == 0:
            security_score = 100
        else:
            penalty = (critical_count * 25) + (high_count * 15) + (medium_count * 5) + (low_count * 1)
            security_score = max(0, 100 - penalty)

        # Risk level
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

        story.append(Paragraph(f"<b>Overall Risk Level: {risk_level}</b>",
                               ParagraphStyle('RiskLevel', parent=styles['Normal'], fontSize=12,
                                              textColor=risk_color, fontName='Helvetica-Bold')))
        story.append(Paragraph(risk_description, normal_style))
        story.append(Spacer(1, 15))

        # AI summary
        ai_summary = "Security analysis completed. Review detailed findings below for specific vulnerabilities and recommended actions."
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
            except Exception:
                pass

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

        if security_score >= 90:
            score_grade, score_description_text = "A", "Excellent security posture with minimal vulnerabilities."
        elif security_score >= 80:
            score_grade, score_description_text = "B", "Good security with some areas for improvement."
        elif security_score >= 70:
            score_grade, score_description_text = "C", "Fair security - several vulnerabilities need attention."
        elif security_score >= 60:
            score_grade, score_description_text = "D", "Poor security - significant vulnerabilities present."
        else:
            score_grade, score_description_text = "F", "Critical security issues - immediate action required."

        score_box = [
            ['Security Score', 'Grade', 'Assessment'],
            [f'{security_score}/100', score_grade, score_description_text]
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
                for i, pf in enumerate(priority_findings[:5], 1):
                    story.append(Paragraph(f"<b>{i}.</b> {pf}", normal_style))
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
            story.append(Paragraph("<b>Automated Security Assessment</b>", subheading_style))
            if findings:
                auto_critical = critical_count
                auto_high = high_count
                auto_medium = medium_count
                auto_low = low_count
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
                if hasattr(scan_result, 'scanner'):
                    scanner_name = scan_result.scanner.value if hasattr(scan_result.scanner, 'value') else str(scan_result.scanner)
                    scanner_name = scanner_name.replace('ScannerType.', '').replace('GITLEAKS', 'GitLeaks').replace('SEMGREP', 'Semgrep').replace('SAFETY', 'Safety').replace('BANDIT', 'Bandit').replace('TRIVY', 'Trivy')
                    status = scan_result.status.value if hasattr(scan_result.status, 'value') else str(scan_result.status)
                    status = status.replace('ScanStatus.', '').upper()
                    findings_count_sr = len(scan_result.findings) if scan_result.findings else 0
                    duration = scan_result.duration_seconds or 0
                else:
                    scanner_name = str(scan_result.get('scanner', 'Unknown')).replace('ScannerType.', '')
                    status = str(scan_result.get('status', 'Unknown')).upper()
                    findings_count_sr = scan_result.get('findings_count', len(scan_result.get('findings', [])))
                    duration = scan_result.get('duration_seconds', 0)

                if duration < 5:
                    performance = "Excellent"
                elif duration < 30:
                    performance = "Good"
                elif duration < 60:
                    performance = "Fair"
                else:
                    performance = "Slow"

                scanner_data.append([scanner_name, status, str(findings_count_sr), f"{duration:.1f}s", performance])

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
            max_findings = 20

            for i, finding in enumerate(findings_sorted[:max_findings], 1):
                if isinstance(finding, dict):
                    severity = str(finding.get('severity', 'unknown')).lower()
                    f_title = finding.get('title', 'Untitled Finding')
                    scanner = str(finding.get('scanner', 'Unknown')).replace('ScannerType.', '')
                    file_path = finding.get('file_path', 'N/A')
                    line_number = finding.get('line_number', finding.get('line_start', 'N/A'))
                    rule_id = finding.get('rule_id', 'N/A')
                    cwe_id = finding.get('cwe_id', 'N/A')
                    description = finding.get('description', '')
                    remediation = finding.get('remediation') or finding.get('recommendation', '')
                    fix_effort = finding.get('fix_effort', '')
                else:
                    severity = getattr(finding, 'severity', 'unknown')
                    if hasattr(severity, 'value'):
                        severity = severity.value
                    severity = str(severity).lower()
                    f_title = getattr(finding, 'title', 'Untitled Finding')
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

                severity_colors = {
                    'critical': danger_color,
                    'high': reportlab_colors.HexColor('#f97316'),
                    'medium': warning_color,
                    'low': reportlab_colors.HexColor('#84cc16'),
                    'info': secondary_color
                }
                sev_color = severity_colors.get(severity, reportlab_colors.grey)

                effort_label = ''
                if fix_effort:
                    effort_map = {'low': 'Quick Fix', 'medium': 'Moderate Effort', 'high': 'Complex Fix'}
                    effort_label = effort_map.get(fix_effort.lower(), '')

                finding_title_style = ParagraphStyle(
                    f'FindingTitle{i}', parent=styles['Heading3'], fontSize=11, spaceAfter=8,
                    spaceBefore=18, textColor=sev_color, fontName='Helvetica-Bold', leftIndent=0
                )
                story.append(Paragraph(f"Finding #{i}: {f_title}", finding_title_style))

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

                if description:
                    story.append(Spacer(1, 6))
                    desc_style = ParagraphStyle(
                        f'Desc{i}', parent=styles['Normal'], fontSize=9, spaceAfter=6, leftIndent=10, leading=12
                    )
                    story.append(Paragraph(f"<b>Description:</b> {description[:500]}{'...' if len(description) > 500 else ''}", desc_style))

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
            'FinalFooter', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=reportlab_colors.grey
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

        # Build PDF
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()

        return pdf_content

    except Exception as e:
        logger.error(f"Failed to generate PDF for report {report_id}: {e}")
        import traceback
        logger.error(f"PDF generation traceback: {traceback.format_exc()}")
        return None
