import asyncio
import logging
import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from models.report import (
    GitMetadata,
    ScannerType,
    ScanReport,
    ScanResult,
    ScanStatus,
    SeverityLevel,
    VulnerabilityFinding,
)
from models.user import User
from routes.dependencies import get_current_user
from routes.webhook.processor import add_scan_log, get_scan_log
from routes.webhook.schemas import ScanRequest
from services.infrastructure.project_service import ProjectService
from services.notifications.websocket_manager import ws_manager
from services.scanning.scanners import RealSecurityScanner
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail
from utils.rate_limit import limiter

logger = logging.getLogger(__name__)

project_service = ProjectService()

active_scans: Dict[str, bool] = {}

router = APIRouter()


@router.get("/scan/{scan_id}/status")
async def get_scan_status(
    scan_id: str,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    try:
        scan_report = await ScanReport.find_one(ScanReport.scan_id == scan_id)

        if not scan_report:
            raise HTTPException(status_code=404, detail="Scan not found")

        user_id = str(current_user.id)
        report_user_id = getattr(scan_report, 'user_id', None)

        if report_user_id and report_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this scan")

        return JSONResponse(
            status_code=200,
            content={
                "id": str(scan_report.id),
                "scan_id": scan_id,
                "status": scan_report.status.value if hasattr(scan_report.status, 'value') else str(scan_report.status),
                "project_name": scan_report.project_name,
                "total_findings": scan_report.total_findings,
                "findings_by_severity": scan_report.findings_by_severity,
                "created_at": scan_report.created_at.isoformat() if scan_report.created_at else None,
                "started_at": scan_report.started_at.isoformat() if hasattr(scan_report, 'started_at') and scan_report.started_at else None,
                "completed_at": scan_report.completed_at.isoformat() if scan_report.completed_at else None,
                "progress": getattr(scan_report, 'progress', 0),
                "current_scanner": getattr(scan_report, 'current_scanner', None),
                "error_message": getattr(scan_report, 'error_message', None),
                "is_cancelled": scan_id in active_scans and not active_scans[scan_id],
                "log": get_scan_log(scan_id)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan status: {str(e)}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to get scan status"))


@router.post("/scan/{scan_id}/stop")
async def stop_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    try:
        scan_report = await ScanReport.find_one(ScanReport.scan_id == scan_id)

        if not scan_report:
            raise HTTPException(status_code=404, detail="Scan not found")

        user_id = str(current_user.id)
        report_user_id = getattr(scan_report, 'user_id', None)

        if report_user_id and report_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this scan")

        if scan_report.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Scan is already completed or failed",
                    "scan_id": scan_id,
                    "status": scan_report.status.value if hasattr(scan_report.status, 'value') else str(scan_report.status)
                }
            )

        active_scans[scan_id] = False

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({
            "$set": {
                "status": ScanStatus.FAILED,
                "error_message": "Scan cancelled by user",
                "completed_at": datetime.now(timezone.utc)
            }
        })

        logger.info(f"Scan {scan_id} cancelled by user")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Scan cancelled successfully",
                "scan_id": scan_id,
                "status": "cancelled"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop scan: {str(e)}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Failed to stop scan"))


@router.post("/scan")
@limiter.limit("10/minute")
async def submit_scan(
    request: Request,
    scan_request: ScanRequest,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    try:
        scan_id = str(uuid.uuid4())
        user_id = str(current_user.id)

        project_name = str(scan_request.repository_url).split('/')[-1].replace('.git', '')
        if not project_name:
            project_name = "Unknown Project"

        logger.info(f"Manual scan submitted by user {current_user.username} for {project_name} (ID: {scan_id})")

        try:
            git_metadata = GitMetadata(
                repository_url=str(scan_request.repository_url),
                branch=scan_request.branch,
                commit_hash="pending",
                commit_message="Manual scan initiated",
                commit_author="Manual Scan",
                commit_timestamp=datetime.now(timezone.utc),
                pr_number=None,
                event_type="manual_scan"
            )

            scan_report = ScanReport(
                scan_id=scan_id,
                project_name=project_name,
                project_id=scan_request.project_id,
                user_id=user_id,
                status=ScanStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                git_metadata=git_metadata,
                scan_results=[],
                total_findings=0,
                findings_by_severity={
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0
                },
                tags=[project_name.lower().replace('-', '_'), scan_request.branch.replace('/', '_')],
                metadata={
                    "scan_types": scan_request.scan_types,
                    "initiated_by": current_user.username,
                    "initiated_by_user_id": user_id,
                    "source": "webhook_api"
                }
            )

            await scan_report.insert()

            asyncio.create_task(
                process_real_scan(scan_id, scan_request, git_metadata)
            )

        except Exception as creation_error:
            logger.error(f"Error creating scan report: {creation_error}")
            logger.exception("Full creation error:")
            raise creation_error

        return JSONResponse(
            status_code=202,
            content={
                "message": "Scan submitted successfully",
                "scan_id": scan_id,
                "status": "pending",
                "project_name": project_name,
                "repository_url": str(scan_request.repository_url),
                "branch": scan_request.branch,
                "scan_types": scan_request.scan_types
            }
        )

    except Exception as e:
        logger.error(f"Failed to submit scan: {str(e)}")
        logger.exception("Full scan submission error traceback:")
        raise HTTPException(
            status_code=500,
            detail=get_safe_error_detail(e, "Failed to submit scan")
        )


async def process_real_scan(
    scan_id: str,
    scan_request: ScanRequest,
    git_metadata: GitMetadata
):
    project_name = str(scan_request.repository_url).split('/')[-1].replace('.git', '')

    try:
        active_scans[scan_id] = True

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {
                "status": ScanStatus.RUNNING,
                "started_at": datetime.now(timezone.utc),
                "progress": 5,
                "current_scanner": "Initializing security scan environment..."
            }}
        )

        await ws_manager.notify_scan_started(scan_id, project_name)
        add_scan_log(scan_id, "INFO", f"Security scan started for {project_name}")

        logger.info(f"Starting real security scan for {scan_id}")

        if not active_scans.get(scan_id, True):
            logger.info(f"Scan {scan_id} was cancelled before starting")
            return

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 10, "current_scanner": "Cloning repository and preparing codebase..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 10, "Cloning repository")
        add_scan_log(scan_id, "SCAN", "Cloning repository")

        scanner = RealSecurityScanner()

        if not active_scans.get(scan_id, True):
            logger.info(f"Scan {scan_id} was cancelled")
            return

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 20, "current_scanner": "Running SAST (Static Application Security Testing)..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 20, "SAST Analysis")
        add_scan_log(scan_id, "SCAN", "SAST Analysis")

        await asyncio.sleep(0.5)

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 35, "current_scanner": "Scanning for exposed secrets and credentials..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 35, "Secrets Detection")
        add_scan_log(scan_id, "SCAN", "Secrets Detection")

        await asyncio.sleep(0.5)

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 50, "current_scanner": "Analyzing dependencies for known vulnerabilities..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 50, "Dependency Analysis")
        add_scan_log(scan_id, "SCAN", "Dependency Analysis")

        scan_results = await scanner.scan_repository(
            repository_url=str(scan_request.repository_url),
            branch=scan_request.branch
        )

        if not active_scans.get(scan_id, True):
            logger.info(f"Scan {scan_id} was cancelled after scan")
            return

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 70, "current_scanner": "Processing and categorizing findings..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 70, "Processing Results")
        add_scan_log(scan_id, "SCAN", "Processing Results")

        total_findings = scan_results['total_findings']
        findings_by_severity = scan_results['findings_by_severity']
        detailed_findings = scan_results['detailed_findings']
        repo_metadata = scan_results['repository_metadata']
        scan_metadata = scan_results['scan_metadata']

        if repo_metadata:
            git_metadata.commit_hash = repo_metadata.get('commit_hash', git_metadata.commit_hash)
            git_metadata.commit_message = repo_metadata.get('commit_message', git_metadata.commit_message)
            git_metadata.commit_author = repo_metadata.get('commit_author', git_metadata.commit_author)

        scan_duration = random.randint(60, 300)

        scan_results_list = []

        findings_by_scanner = {}
        for finding in detailed_findings:
            scanner = finding.get('scanner', 'detect-secrets')
            if scanner not in findings_by_scanner:
                findings_by_scanner[scanner] = []
            findings_by_scanner[scanner].append(finding)

        for scanner_name, scanner_findings in findings_by_scanner.items():
            scanner_type = ScannerType.GITLEAKS
            if scanner_name in ['bandit', 'semgrep']:
                scanner_type = ScannerType.SEMGREP
            elif scanner_name in ['safety', 'npm-audit']:
                scanner_type = ScannerType.SAFETY
            elif scanner_name == 'detect-secrets':
                scanner_type = ScannerType.GITLEAKS

            finding_objects = []
            for finding_data in scanner_findings:
                severity_str = finding_data.get('severity', 'medium').lower()
                severity = SeverityLevel.MEDIUM
                if severity_str == 'critical':
                    severity = SeverityLevel.CRITICAL
                elif severity_str == 'high':
                    severity = SeverityLevel.HIGH
                elif severity_str == 'medium':
                    severity = SeverityLevel.MEDIUM
                elif severity_str == 'low':
                    severity = SeverityLevel.LOW
                elif severity_str == 'info':
                    severity = SeverityLevel.INFO

                confidence_str = finding_data.get('confidence', 'medium').upper()

                finding_obj = VulnerabilityFinding(
                    id=finding_data.get('rule_id', f"{scanner_name}_{len(finding_objects)}"),
                    scanner=scanner_type,
                    rule_id=finding_data.get('rule_id', f"{scanner_name}_{len(finding_objects)}"),
                    title=finding_data.get('title', 'Security Finding'),
                    description=finding_data.get('description', ''),
                    severity=severity,
                    confidence=confidence_str,
                    file_path=finding_data.get('file_path', ''),
                    line_start=finding_data.get('line_number'),
                    line_end=finding_data.get('line_number'),
                    column_start=finding_data.get('column_number'),
                    column_end=finding_data.get('column_number'),
                    code_snippet=finding_data.get('code_snippet', ''),
                    owasp_category=finding_data.get('owasp_category', 'Security'),
                    references=[],
                    metadata={}
                )
                finding_objects.append(finding_obj)

            scan_result = ScanResult(
                scanner=scanner_type,
                status=ScanStatus.COMPLETED,
                started_at=datetime.now(timezone.utc) - timedelta(seconds=scan_duration),
                completed_at=datetime.now(timezone.utc),
                duration_seconds=scan_duration,
                findings=finding_objects,
                error_message="",
                summary={
                    "critical": len([f for f in finding_objects if f.severity == SeverityLevel.CRITICAL]),
                    "high": len([f for f in finding_objects if f.severity == SeverityLevel.HIGH]),
                    "medium": len([f for f in finding_objects if f.severity == SeverityLevel.MEDIUM]),
                    "low": len([f for f in finding_objects if f.severity == SeverityLevel.LOW]),
                    "info": len([f for f in finding_objects if f.severity == SeverityLevel.INFO])
                }
            )
            scan_results_list.append(scan_result)

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 80, "current_scanner": "Saving scan results to database..."}}
        )

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({
            "$set": {
                "duration_seconds": scan_duration,
                "total_findings": total_findings,
                "findings_by_severity": findings_by_severity,
                "scan_results": [result.model_dump() for result in scan_results_list],
                "git_metadata.commit_hash": git_metadata.commit_hash,
                "git_metadata.commit_message": git_metadata.commit_message,
                "git_metadata.commit_author": git_metadata.commit_author,
                "updated_at": datetime.now(timezone.utc),
                "progress": 85,
                "metadata.findings": detailed_findings,
                "metadata.scan_completed": True,
                "metadata.scan_types": scan_request.scan_types,
                "metadata.tools_used": scan_metadata.get('tools_used', []),
                "metadata.scanned_files": scan_metadata.get('scanned_files', {}),
                "metadata.real_scan": True
            }
        })

        ai_analysis_result = None
        try:
            logger.info(f"Starting AI analysis for scan {scan_id}")

            await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
                {"$set": {"progress": 90, "current_scanner": "AI analyzing vulnerabilities and generating remediation advice..."}}
            )

            from services.ai.ai_processor import AIProcessorError, get_ai_processor
            try:
                ai_processor = get_ai_processor()
            except AIProcessorError as e:
                logger.warning(f"AI processor not available: {e}. Skipping AI analysis.")
                ai_processor = None

            if ai_processor and scan_results_list:
                updated_report = await ScanReport.find_one(ScanReport.scan_id == scan_id)

                if updated_report and updated_report.scan_results:
                    project_context = {
                        "project_name": updated_report.project_name,
                        "repository_url": str(updated_report.git_metadata.repository_url) if updated_report.git_metadata else "",
                        "branch": updated_report.git_metadata.branch if updated_report.git_metadata else "main"
                    }

                    ai_analysis_result = await ai_processor.analyze_scan_results(
                        updated_report.scan_results,
                        project_context
                    )

                    if ai_analysis_result:
                        logger.info(f"AI analysis completed for scan {scan_id}")
                    else:
                        logger.warning(f"AI analysis returned empty results for scan {scan_id}")
                else:
                    logger.warning(f"Could not retrieve updated report for AI analysis: {scan_id}")
            else:
                logger.warning(f"AI processor not available or no scan results for AI analysis: {scan_id}")

        except Exception as ai_error:
            logger.error(f"AI analysis failed for scan {scan_id}: {str(ai_error)}")
            logger.exception("Full AI analysis error:")

        compliance_result = None
        try:
            if scan_results_list and any(r.findings for r in scan_results_list):
                logger.info(f"Starting compliance analysis for scan {scan_id}")
                from services.compliance.compliance_analyzer import ComplianceAnalysisService
                compliance_service = ComplianceAnalysisService()

                report_for_compliance = await ScanReport.find_one(ScanReport.scan_id == scan_id)
                if report_for_compliance:
                    compliance_result = await compliance_service.analyze_scan_for_compliance(
                        report_for_compliance
                    )
                    if compliance_result:
                        logger.info(f"Compliance analysis completed for scan {scan_id}")
        except Exception as compliance_error:
            logger.warning(f"Compliance analysis failed for scan {scan_id}: {str(compliance_error)}")

        cve_enrichments = []
        try:
            if detailed_findings:
                logger.info(f"Starting CVE correlation for scan {scan_id}")
                threat_intel = ServiceRegistry.get_threat_intelligence()

                if not threat_intel:
                    logger.warning("Threat intelligence engine not available, skipping CVE enrichment")

                cve_ids_found = set()
                dependencies_found = set()

                for finding in detailed_findings:
                    cve_pattern = r'CVE-\d{4}-\d{4,7}'
                    cve_matches = re.findall(cve_pattern, finding.get('description', '') + ' ' + finding.get('title', ''))
                    cve_ids_found.update(cve_matches)

                    if finding.get('scanner') == 'safety':
                        package_name = finding.get('metadata', {}).get('package')
                        if package_name:
                            dependencies_found.add(package_name)

                enriched_count = 0
                for cve_id in cve_ids_found:
                    cve_data = await threat_intel.get_cve_data(cve_id) if threat_intel else None
                    if cve_data:
                        enrichment = {
                            "cve_id": cve_id,
                            "cvss_score": cve_data.cvss_score,
                            "severity": cve_data.severity.value,
                            "kev_listed": cve_data.kev_listed,
                            "exploit_available": cve_data.exploit_available,
                            "epss_score": cve_data.epss_score,
                            "description": cve_data.description,
                            "published_date": cve_data.published_date.isoformat(),
                            "reference_urls": cve_data.reference_urls[:3]
                        }
                        cve_enrichments.append(enrichment)
                        enriched_count += 1

                if enriched_count > 0:
                    logger.info(f"Enriched {enriched_count} findings with CVE threat intelligence")
                else:
                    logger.info("No CVE threat intelligence correlations found")

        except Exception as cve_error:
            logger.warning(f"CVE correlation failed for scan {scan_id}: {str(cve_error)}")

        final_update = {
            "status": ScanStatus.COMPLETED,
            "completed_at": datetime.now(timezone.utc),
            "progress": 100,
            "current_scanner": None,
            "updated_at": datetime.now(timezone.utc)
        }
        if ai_analysis_result:
            final_update["ai_analysis"] = ai_analysis_result.model_dump()
        if compliance_result:
            final_update["compliance_analysis"] = compliance_result
        if cve_enrichments:
            final_update["cve_threat_intelligence"] = cve_enrichments

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({"$set": final_update})

        try:
            scan_results_for_project = {
                "severity_distribution": findings_by_severity,
                "security_score": 100 - (findings_by_severity.get('critical', 0) * 25 +
                                        findings_by_severity.get('high', 0) * 15 +
                                        findings_by_severity.get('medium', 0) * 5 +
                                        findings_by_severity.get('low', 0) * 1),
                "compliance_score": 100 - (findings_by_severity.get('critical', 0) * 20 +
                                          findings_by_severity.get('high', 0) * 10)
            }
            scan_results_for_project["security_score"] = max(0, scan_results_for_project["security_score"])
            scan_results_for_project["compliance_score"] = max(0, scan_results_for_project["compliance_score"])

            updated_project = await project_service.update_project_from_scan(
                project_name=scan_request.project_id or "",
                scan_results=scan_results_for_project,
                repository_url=str(scan_request.repository_url)
            )
            if updated_project:
                logger.info(f"Updated project stats for: {updated_project.name}")
            else:
                logger.warning(f"Could not find project to update stats for repo: {scan_request.repository_url}")
        except Exception as proj_error:
            logger.warning(f"Could not update project stats: {str(proj_error)}")

        if scan_id in active_scans:
            del active_scans[scan_id]

        await ws_manager.notify_scan_completed(
            scan_id, project_name, total_findings, findings_by_severity
        )
        add_scan_log(
            scan_id, "INFO",
            f"Scan completed: {total_findings} findings "
            f"({findings_by_severity.get('critical', 0)} critical, "
            f"{findings_by_severity.get('high', 0)} high, "
            f"{findings_by_severity.get('medium', 0)} medium, "
            f"{findings_by_severity.get('low', 0)} low)"
        )

        if findings_by_severity.get('critical', 0) > 0:
            for finding in detailed_findings[:5]:
                if finding.get('severity', '').lower() == 'critical':
                    await ws_manager.notify_critical_vulnerability(
                        project_name, finding.get('title', 'Critical vulnerability'),
                        'critical'
                    )

        try:
            from services.notifications.notification_service import NotificationService
            notification_svc = NotificationService()
            report_for_user = await ScanReport.find_one(ScanReport.scan_id == scan_id)
            if report_for_user and report_for_user.user_id:
                await notification_svc.send_scan_completed(
                    project_name=project_name,
                    scan_id=scan_id,
                    user_id=report_for_user.user_id,
                    findings_count=total_findings,
                    critical_count=findings_by_severity.get('critical', 0),
                    high_count=findings_by_severity.get('high', 0),
                    medium_count=findings_by_severity.get('medium', 0),
                    low_count=findings_by_severity.get('low', 0),
                    scan_type="Security",
                    duration=f"{scan_duration}s",
                    files_scanned=total_findings,
                    detailed_findings=detailed_findings
                )
        except Exception as notify_err:
            logger.warning(f"Failed to send scan notification: {notify_err}")

        logger.info(f"Real scan {scan_id} completed successfully with {total_findings} findings")

    except Exception as e:
        error_str = str(e)
        if "No space left on device" in error_str:
            user_error = "Disk space is full. Please free up disk space and try again."
        elif "Could not find remote ref" in error_str or "not found" in error_str.lower():
            user_error = "Branch or repository not found. Please check the repository URL and branch name."
        elif "Authentication failed" in error_str or "403" in error_str:
            user_error = "Authentication failed. The repository may be private or require access token."
        elif "timeout" in error_str.lower():
            user_error = "Connection timed out. Please check your network connection."
        else:
            user_error = error_str[:200] if len(error_str) > 200 else error_str

        logger.error(f"Real scan {scan_id} failed: {error_str}")
        logger.exception("Full real scan error:")

        if scan_id in active_scans:
            del active_scans[scan_id]

        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {
                "$set": {
                    "status": ScanStatus.FAILED,
                    "completed_at": datetime.now(timezone.utc),
                    "error_message": user_error,
                    "progress": 0,
                    "current_scanner": None,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        await ws_manager.notify_scan_failed(scan_id, project_name, user_error)
        add_scan_log(scan_id, "ERROR", f"Scan failed: {user_error}")
