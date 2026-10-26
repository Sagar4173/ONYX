"""Shared, credential-redacted report payload used by exports and PDFs."""
from utils.report_metadata import redacted_report_metadata
from utils.url_redaction import strip_url_credentials


def build_report_data(report) -> dict:
    return {
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
            "repository_url": strip_url_credentials(report.git_metadata.repository_url)
            if report.git_metadata
            else "",
            "branch": report.git_metadata.branch if report.git_metadata else "main",
            "commit_hash": report.git_metadata.commit_hash if report.git_metadata else "",
            "commit_message": report.git_metadata.commit_message if report.git_metadata else "",
            "commit_author": report.git_metadata.commit_author if report.git_metadata else "",
            "event_type": report.git_metadata.event_type if report.git_metadata else "",
        },
        "tags": report.tags if report.tags else [],
        "metadata": redacted_report_metadata(report.metadata),
    }
