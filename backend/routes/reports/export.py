"""Report export/download endpoints."""
import csv
import io
import json
import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from models.report import ScanReport
from models.user import User
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_user_project_ids
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("json", pattern="^(json|pdf|csv)$"),
    current_user: User = Depends(get_current_user),
):
    """Download report in specified format"""
    try:
        report_data = None
        user_id = str(current_user.id)

        if ObjectId.is_valid(report_id):
            try:
                report = await ScanReport.get(ObjectId(report_id))
                if report:
                    accessible_project_ids = await get_user_project_ids(user_id)
                    report_user_id = getattr(report, "user_id", None)
                    report_project_id = getattr(report, "project_id", None)

                    has_access = (
                        report_user_id == user_id
                        or (report_project_id and report_project_id in accessible_project_ids)
                    )

                    if not has_access:
                        raise HTTPException(status_code=403, detail="Access denied to this report")

                    report_data = {
                        "id": str(report.id),
                        "project_name": report.project_name,
                        "scan_id": report.scan_id,
                        "status": report.status.value if hasattr(report.status, "value") else report.status,
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
                            "event_type": report.git_metadata.event_type if report.git_metadata else "",
                        },
                        "tags": report.tags if report.tags else [],
                        "metadata": report.metadata if report.metadata else {},
                    }
            except Exception as db_error:
                logger.warning(f"Database error when fetching report {report_id}: {db_error}")

        if not report_data:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        findings = []
        if report_data.get("findings"):
            findings.extend(report_data["findings"])
        elif report_data.get("scan_results"):
            for scan_result in report_data["scan_results"]:
                if hasattr(scan_result, "findings"):
                    if scan_result.findings:
                        for finding in scan_result.findings:
                            if hasattr(finding, "model_dump"):
                                finding_dict = finding.model_dump()
                            elif hasattr(finding, "dict"):
                                finding_dict = finding.dict()
                            else:
                                finding_dict = finding
                            findings.append(finding_dict)
                else:
                    findings.extend(scan_result.get("findings", []))

        if format == "json":
            json_content = json.dumps(report_data, indent=2, default=str)
            headers = {
                "Content-Disposition": f'attachment; filename="{report_id}_report.json"',
                "Content-Type": "application/json",
            }
            return StreamingResponse(
                io.BytesIO(json_content.encode()),
                media_type="application/json",
                headers=headers,
            )

        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Project", "Scan ID", "Status", "Created At", "Total Findings",
                "Critical", "High", "Medium", "Low", "Info", "Repository", "Branch",
            ])
            fbs = report_data.get("findings_by_severity", {})
            writer.writerow([
                report_data.get("project_name", ""),
                report_data.get("scan_id", ""),
                report_data.get("status", ""),
                report_data.get("created_at", ""),
                report_data.get("total_findings", 0),
                fbs.get("critical", 0),
                fbs.get("high", 0),
                fbs.get("medium", 0),
                fbs.get("low", 0),
                fbs.get("info", 0),
                report_data.get("git_metadata", {}).get("repository_url", ""),
                report_data.get("git_metadata", {}).get("branch", ""),
            ])

            csv_content = output.getvalue()
            headers = {
                "Content-Disposition": f'attachment; filename="{report_id}_report.csv"',
                "Content-Type": "text/csv",
            }
            return StreamingResponse(
                io.BytesIO(csv_content.encode()),
                media_type="text/csv",
                headers=headers,
            )

        elif format == "pdf":
            from utils.pdf_generator import generate_report_pdf

            pdf_content = await generate_report_pdf(report_id)
            if not pdf_content:
                raise HTTPException(status_code=500, detail="Failed to generate PDF report")

            date_str = datetime.now().strftime("%Y%m%d")
            project_name_safe = (
                report_data.get("project_name", "report")
                .replace(" ", "_")
                .replace("/", "_")[:30]
            )

            headers = {
                "Content-Disposition": f'attachment; filename="ONYX_Security_Report_{project_name_safe}_{date_str}.pdf"',
                "Content-Type": "application/pdf",
            }
            return StreamingResponse(
                io.BytesIO(pdf_content),
                media_type="application/pdf",
                headers=headers,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
