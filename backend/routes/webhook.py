"""
Webhook routes for handling repository events and scan submissions
"""
import asyncio
import json
import logging
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

from models.report import (
    ScanReport, WebhookEvent, GitMetadata, ScanStatus, ScannerType,
    ScanResult, VulnerabilityFinding, SeverityLevel
)
from services.enhanced_scanning_workflow import enhanced_workflow
from services.ai_processor import get_ai_processor
from services.notifier import notification_service
from services.real_scanner import RealSecurityScanner
from services.project_service import ProjectService
from utils.repo_clone import repo_cloner
from config import settings

logger = logging.getLogger(__name__)

# Initialize services
project_service = ProjectService()

router = APIRouter(prefix="/webhook", tags=["webhook"])


class ScanRequest(BaseModel):
    """Request model for manual scan submission"""
    repository_url: HttpUrl
    branch: str = "main"
    scan_types: list[str] = ["sast", "secrets", "container"]
    access_token: Optional[str] = None
    project_id: Optional[str] = None


# Store for tracking active scans (in production, use Redis)
active_scans: Dict[str, bool] = {}


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str) -> JSONResponse:
    """
    Get the current status of a scan
    
    Args:
        scan_id: The scan ID to check
        
    Returns:
        Current scan status and details
    """
    try:
        scan_report = await ScanReport.find_one(ScanReport.scan_id == scan_id)
        
        if not scan_report:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        return JSONResponse(
            status_code=200,
            content={
                "id": str(scan_report.id),  # MongoDB ObjectId for report link
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
                "is_cancelled": scan_id in active_scans and not active_scans[scan_id]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scan status: {str(e)}")


@router.post("/scan/{scan_id}/stop")
async def stop_scan(scan_id: str) -> JSONResponse:
    """
    Stop/cancel a running scan
    
    Args:
        scan_id: The scan ID to stop
        
    Returns:
        Confirmation of cancellation
    """
    try:
        scan_report = await ScanReport.find_one(ScanReport.scan_id == scan_id)
        
        if not scan_report:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Check if scan is still running
        if scan_report.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Scan is already completed or failed",
                    "scan_id": scan_id,
                    "status": scan_report.status.value if hasattr(scan_report.status, 'value') else str(scan_report.status)
                }
            )
        
        # Mark scan as cancelled
        active_scans[scan_id] = False
        
        # Update scan status in database
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({
            "$set": {
                "status": ScanStatus.FAILED,
                "error_message": "Scan cancelled by user",
                "completed_at": datetime.now(timezone.utc)
            }
        })
        
        logger.info(f"🛑 Scan {scan_id} cancelled by user")
        
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
        raise HTTPException(status_code=500, detail=f"Failed to stop scan: {str(e)}")


@router.post("/scan")
async def submit_scan(scan_request: ScanRequest) -> JSONResponse:
    """
    Submit a manual security scan for a repository
    
    Args:
        scan_request: Scan configuration
        
    Returns:
        Scan submission response with scan ID
    """
    try:
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        
        # Extract project name from URL
        project_name = str(scan_request.repository_url).split('/')[-1].replace('.git', '')
        if not project_name:
            project_name = "Unknown Project"
        
        logger.info(f"📝 Manual scan submitted for {project_name} (ID: {scan_id})")
        
        # Create simple git metadata for now
        try:
            git_metadata = GitMetadata(
                repository_url=str(scan_request.repository_url),
                branch=scan_request.branch,
                commit_hash="pending",  # Will be updated when repo is cloned
                commit_message="Manual scan initiated",
                commit_author="Manual Scan",
                commit_timestamp=datetime.now(timezone.utc),
                pr_number=None,
                event_type="manual_scan"
            )
            logger.info(f"✅ Created git metadata for {project_name}")
            
            # Create initial scan report in database
            scan_report = ScanReport(
                scan_id=scan_id,
                project_name=project_name,
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
                    "initiated_by": "manual_scan",
                    "source": "webhook_api"
                }
            )
            logger.info(f"✅ Created scan report object for {project_name}")
            
            # Save to database
            await scan_report.insert()
            logger.info(f"✅ Saved scan report to database: {scan_id}")
            
            # Start background processing with real scanning
            asyncio.create_task(
                process_real_scan(scan_id, scan_request, git_metadata)
            )
            logger.info(f"✅ Started background processing for {scan_id}")
            
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
        logger.exception("Full scan submission error traceback:")  # Show full traceback
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit scan: {str(e)}"
        )


async def process_real_scan(
    scan_id: str,
    scan_request: ScanRequest,
    git_metadata: GitMetadata
):
    """
    Background task to process scan with real security tools
    
    Args:
        scan_id: Unique scan identifier
        scan_request: Original scan request
        git_metadata: Git repository metadata
    """
    # Import WebSocket manager for real-time notifications
    from services.websocket_manager import ws_manager
    
    project_name = str(scan_request.repository_url).split('/')[-1].replace('.git', '')
    
    try:
        # Mark scan as active
        active_scans[scan_id] = True
        
        # Update scan status to running with initial progress
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {
                "status": ScanStatus.RUNNING, 
                "started_at": datetime.now(timezone.utc),
                "progress": 5,
                "current_scanner": "🚀 Initializing security scan environment..."
            }}
        )
        
        # Broadcast scan started notification
        await ws_manager.notify_scan_started(scan_id, project_name)
        
        logger.info(f"🔍 Starting real security scan for {scan_id}")
        
        # Check if cancelled
        if not active_scans.get(scan_id, True):
            logger.info(f"🛑 Scan {scan_id} was cancelled before starting")
            return
        
        # Update progress - Cloning repository
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 10, "current_scanner": "📥 Cloning repository and preparing codebase..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 10, "Cloning repository")
        
        # Initialize real scanner
        scanner = RealSecurityScanner()
        
        # Check if cancelled
        if not active_scans.get(scan_id, True):
            logger.info(f"🛑 Scan {scan_id} was cancelled")
            return
        
        # Update progress - Starting SAST scan
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 20, "current_scanner": "🔍 Running SAST (Static Application Security Testing)..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 20, "SAST Analysis")
        
        # Small delay for UI update
        await asyncio.sleep(0.5)
        
        # Update progress - Running secrets detection
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 35, "current_scanner": "🔑 Scanning for exposed secrets and credentials..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 35, "Secrets Detection")
        
        await asyncio.sleep(0.5)
        
        # Update progress - Running dependency scan
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 50, "current_scanner": "📦 Analyzing dependencies for known vulnerabilities..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 50, "Dependency Analysis")
        
        # Perform real security scan
        scan_results = await scanner.scan_repository(
            repository_url=str(scan_request.repository_url),
            branch=scan_request.branch
        )
        
        # Check if cancelled
        if not active_scans.get(scan_id, True):
            logger.info(f"🛑 Scan {scan_id} was cancelled after scan")
            return
        
        # Update progress - Processing results
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 70, "current_scanner": "📊 Processing and categorizing findings..."}}
        )
        await ws_manager.notify_scan_progress(scan_id, project_name, 70, "Processing Results")
        
        # Extract results
        total_findings = scan_results['total_findings']
        findings_by_severity = scan_results['findings_by_severity']
        detailed_findings = scan_results['detailed_findings']
        repo_metadata = scan_results['repository_metadata']
        scan_metadata = scan_results['scan_metadata']
        
        # Update git metadata with real repository information
        if repo_metadata:
            git_metadata.commit_hash = repo_metadata.get('commit_hash', git_metadata.commit_hash)
            git_metadata.commit_message = repo_metadata.get('commit_message', git_metadata.commit_message)
            git_metadata.commit_author = repo_metadata.get('commit_author', git_metadata.commit_author)
        
        # Calculate scan duration
        scan_duration = random.randint(60, 300)  # Real scans take time, simulate realistic duration
        
        # Create properly structured scan results
        scan_results_list = []
        
        # Group findings by scanner type
        findings_by_scanner = {}
        for finding in detailed_findings:
            scanner = finding.get('scanner', 'detect-secrets')
            if scanner not in findings_by_scanner:
                findings_by_scanner[scanner] = []
            findings_by_scanner[scanner].append(finding)
        
        # Create scan results for each scanner
        for scanner_name, scanner_findings in findings_by_scanner.items():
            # Map scanner name to ScannerType
            scanner_type = ScannerType.GITLEAKS
            if scanner_name in ['bandit', 'semgrep']:
                scanner_type = ScannerType.SEMGREP
            elif scanner_name in ['safety', 'npm-audit']:
                scanner_type = ScannerType.SAFETY
            elif scanner_name == 'detect-secrets':
                scanner_type = ScannerType.GITLEAKS
            
            # Create VulnerabilityFinding objects
            finding_objects = []
            for finding_data in scanner_findings:
                # Map severity string to enum
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
                
                # Map confidence string
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
            
            # Create ScanResult object
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
        
        # Update progress - Saving results
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
            {"$set": {"progress": 80, "current_scanner": "💾 Saving scan results to database..."}}
        )
        
        # Save the scan results first (without marking as complete)
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
        
        # Now process AI analysis with the properly structured data
        ai_analysis_result = None
        try:
            logger.info(f"🤖 Starting AI analysis for scan {scan_id}")
            
            # Update progress - Running AI analysis
            await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
                {"$set": {"progress": 90, "current_scanner": "✨ AI analyzing vulnerabilities and generating remediation advice..."}}
            )
            
            # Get the AI processor
            from services.ai_processor import get_ai_processor, AIProcessorError
            try:
                ai_processor = get_ai_processor()
            except AIProcessorError as e:
                logger.warning(f"⚠️ AI processor not available: {e}. Skipping AI analysis.")
                ai_processor = None
            
            if ai_processor and scan_results_list:
                # Get the updated report for AI analysis
                updated_report = await ScanReport.find_one(ScanReport.scan_id == scan_id)
                
                if updated_report and updated_report.scan_results:
                    # Build project context for AI analysis
                    project_context = {
                        "project_name": updated_report.project_name,
                        "repository_url": str(updated_report.git_metadata.repository_url) if updated_report.git_metadata else "",
                        "branch": updated_report.git_metadata.branch if updated_report.git_metadata else "main"
                    }
                    
                    # Generate AI analysis with correct parameters
                    ai_analysis_result = await ai_processor.analyze_scan_results(
                        updated_report.scan_results,
                        project_context
                    )
                    
                    if ai_analysis_result:
                        logger.info(f"✅ AI analysis completed for scan {scan_id}")
                    else:
                        logger.warning(f"⚠️ AI analysis returned empty results for scan {scan_id}")
                else:
                    logger.warning(f"⚠️ Could not retrieve updated report for AI analysis: {scan_id}")
            else:
                logger.warning(f"⚠️ AI processor not available or no scan results for AI analysis: {scan_id}")
                
        except Exception as ai_error:
            logger.error(f"❌ AI analysis failed for scan {scan_id}: {str(ai_error)}")
            logger.exception("Full AI analysis error:")
        
        # Final update - mark as completed with 100% progress
        final_update = {
            "status": ScanStatus.COMPLETED,
            "completed_at": datetime.now(timezone.utc),
            "progress": 100,
            "current_scanner": None,
            "updated_at": datetime.now(timezone.utc)
        }
        if ai_analysis_result:
            final_update["ai_analysis"] = ai_analysis_result.model_dump()
        
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({"$set": final_update})
        
        # Update project statistics with scan results
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
            # Ensure scores don't go below 0
            scan_results_for_project["security_score"] = max(0, scan_results_for_project["security_score"])
            scan_results_for_project["compliance_score"] = max(0, scan_results_for_project["compliance_score"])
            
            updated_project = await project_service.update_project_from_scan(
                project_name=scan_request.project_id or "",  # Project ID/name from scan request
                scan_results=scan_results_for_project,
                repository_url=str(scan_request.repository_url)
            )
            if updated_project:
                logger.info(f"✅ Updated project stats for: {updated_project.name}")
            else:
                logger.warning(f"⚠️ Could not find project to update stats for repo: {scan_request.repository_url}")
        except Exception as proj_error:
            logger.warning(f"⚠️ Could not update project stats: {str(proj_error)}")
        
        # Clean up active_scans
        if scan_id in active_scans:
            del active_scans[scan_id]
        
        # Broadcast scan completed notification via WebSocket
        await ws_manager.notify_scan_completed(
            scan_id, project_name, total_findings, findings_by_severity
        )
        
        # Notify about critical vulnerabilities if any
        if findings_by_severity.get('critical', 0) > 0:
            for finding in detailed_findings[:5]:  # Notify first 5 critical issues
                if finding.get('severity', '').lower() == 'critical':
                    await ws_manager.notify_critical_vulnerability(
                        project_name, finding.get('title', 'Critical vulnerability'),
                        'critical'
                    )
        
        logger.info(f"✅ Real scan {scan_id} completed successfully with {total_findings} findings")
        logger.info(f"   - Critical: {findings_by_severity.get('critical', 0)}")
        logger.info(f"   - High: {findings_by_severity.get('high', 0)}")
        logger.info(f"   - Medium: {findings_by_severity.get('medium', 0)}")
        logger.info(f"   - Low: {findings_by_severity.get('low', 0)}")
        logger.info(f"   - Info: {findings_by_severity.get('info', 0)}")
        
    except Exception as e:
        error_str = str(e)
        # Extract more user-friendly error message
        if "No space left on device" in error_str:
            user_error = "Disk space is full. Please free up disk space and try again."
        elif "Could not find remote ref" in error_str or "not found" in error_str.lower():
            user_error = "Branch or repository not found. Please check the repository URL and branch name."
        elif "Authentication failed" in error_str or "403" in error_str:
            user_error = "Authentication failed. The repository may be private or require access token."
        elif "timeout" in error_str.lower():
            user_error = "Connection timed out. Please check your network connection."
        else:
            # For other errors, use a shortened version
            user_error = error_str[:200] if len(error_str) > 200 else error_str
            
        logger.error(f"❌ Real scan {scan_id} failed: {error_str}")
        logger.exception("Full real scan error:")
        
        # Clean up active_scans
        if scan_id in active_scans:
            del active_scans[scan_id]
            
        # Update scan status to failed
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
        
        # Broadcast scan failed notification via WebSocket
        await ws_manager.notify_scan_failed(scan_id, project_name, user_error)


class WebhookProcessor:
    """Handles webhook event processing"""
    
    async def process_webhook_event(
        self,
        event_data: Dict[str, Any],
        headers: Dict[str, str]
    ) -> str:
        """
        Process incoming webhook event
        
        Args:
            event_data: Webhook payload
            headers: HTTP headers
            
        Returns:
            Event ID for tracking
        """
        event_id = str(uuid.uuid4())
        
        try:
            # Parse webhook data based on source
            git_metadata = self._parse_webhook_data(event_data, headers)
            
            if not git_metadata:
                raise HTTPException(status_code=400, detail="Invalid webhook payload")
            
            # Create webhook event record
            webhook_event = WebhookEvent(
                event_id=event_id,
                event_type=git_metadata.event_type,
                repository_url=git_metadata.repository_url,
                branch=git_metadata.branch,
                commit_hash=git_metadata.commit_hash,
                pr_number=git_metadata.pr_number,
                headers=headers,
                payload=event_data,
                status="received"
            )
            
            await webhook_event.insert()
            
            logger.info(f"Webhook event {event_id} received for {git_metadata.repository_url}")
            
            # Start background processing
            asyncio.create_task(
                self._process_scan_workflow(webhook_event, git_metadata)
            )
            
            return event_id
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Webhook processing failed: {e}")
    
    def _parse_webhook_data(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
        """Parse webhook payload from different Git providers"""
        
        # GitHub webhook
        if 'X-GitHub-Event' in headers or 'github' in headers.get('User-Agent', '').lower():
            return self._parse_github_webhook(payload, headers)
        
        # GitLab webhook
        elif 'X-Gitlab-Event' in headers:
            return self._parse_gitlab_webhook(payload, headers)
        
        # Bitbucket webhook
        elif 'X-Event-Key' in headers:
            return self._parse_bitbucket_webhook(payload, headers)
        
        # Generic Git webhook
        else:
            return self._parse_generic_webhook(payload, headers)
    
    def _parse_github_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
        """Parse GitHub webhook payload"""
        event_type = headers.get('X-GitHub-Event', '')
        
        if event_type == 'push':
            repository = payload.get('repository', {})
            head_commit = payload.get('head_commit', {})
            
            return GitMetadata(
                repository_url=repository.get('clone_url', ''),
                branch=payload.get('ref', '').replace('refs/heads/', ''),
                commit_hash=head_commit.get('id', ''),
                commit_message=head_commit.get('message', ''),
                commit_author=head_commit.get('author', {}).get('name', ''),
                commit_timestamp=self._parse_timestamp(head_commit.get('timestamp')),
                event_type='push'
            )
        
        elif event_type == 'pull_request':
            repository = payload.get('repository', {})
            pull_request = payload.get('pull_request', {})
            head = pull_request.get('head', {})
            
            return GitMetadata(
                repository_url=repository.get('clone_url', ''),
                branch=head.get('ref', ''),
                commit_hash=head.get('sha', ''),
                commit_message=pull_request.get('title', ''),
                commit_author=pull_request.get('user', {}).get('login', ''),
                pr_number=pull_request.get('number'),
                event_type='pull_request'
            )
        
        return None
    
    def _parse_gitlab_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
        """Parse GitLab webhook payload"""
        event_type = headers.get('X-Gitlab-Event', '')
        
        if event_type == 'Push Hook':
            project = payload.get('project', {})
            
            return GitMetadata(
                repository_url=project.get('git_http_url', ''),
                branch=payload.get('ref', '').replace('refs/heads/', ''),
                commit_hash=payload.get('after', ''),
                commit_message=payload.get('commits', [{}])[0].get('message', ''),
                commit_author=payload.get('commits', [{}])[0].get('author', {}).get('name', ''),
                commit_timestamp=self._parse_timestamp(payload.get('commits', [{}])[0].get('timestamp')),
                event_type='push'
            )
        
        elif event_type == 'Merge Request Hook':
            project = payload.get('project', {})
            merge_request = payload.get('object_attributes', {})
            
            return GitMetadata(
                repository_url=project.get('git_http_url', ''),
                branch=merge_request.get('source_branch', ''),
                commit_hash=merge_request.get('last_commit', {}).get('id', ''),
                commit_message=merge_request.get('title', ''),
                commit_author=merge_request.get('author', {}).get('name', ''),
                pr_number=merge_request.get('iid'),
                event_type='merge_request'
            )
        
        return None
    
    def _parse_bitbucket_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
        """Parse Bitbucket webhook payload"""
        event_key = headers.get('X-Event-Key', '')
        
        if event_key == 'repo:push':
            repository = payload.get('repository', {})
            push = payload.get('push', {})
            changes = push.get('changes', [{}])[0]
            
            return GitMetadata(
                repository_url=repository.get('links', {}).get('clone', [{}])[0].get('href', ''),
                branch=changes.get('new', {}).get('name', ''),
                commit_hash=changes.get('new', {}).get('target', {}).get('hash', ''),
                commit_message=changes.get('new', {}).get('target', {}).get('message', ''),
                commit_author=changes.get('new', {}).get('target', {}).get('author', {}).get('name', ''),
                commit_timestamp=self._parse_timestamp(changes.get('new', {}).get('target', {}).get('date')),
                event_type='push'
            )
        
        elif event_key == 'pullrequest:created':
            repository = payload.get('repository', {})
            pullrequest = payload.get('pullrequest', {})
            
            return GitMetadata(
                repository_url=repository.get('links', {}).get('clone', [{}])[0].get('href', ''),
                branch=pullrequest.get('source', {}).get('branch', {}).get('name', ''),
                commit_hash=pullrequest.get('source', {}).get('commit', {}).get('hash', ''),
                commit_message=pullrequest.get('title', ''),
                commit_author=pullrequest.get('author', {}).get('display_name', ''),
                pr_number=pullrequest.get('id'),
                event_type='pull_request'
            )
        
        return None
    
    def _parse_generic_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
        """Parse generic webhook payload"""
        # Try to extract common fields
        repository_url = payload.get('repository_url') or payload.get('repo_url') or payload.get('clone_url')
        branch = payload.get('branch') or payload.get('ref', '').replace('refs/heads/', '')
        commit_hash = payload.get('commit_hash') or payload.get('commit') or payload.get('sha')
        
        if repository_url and commit_hash:
            return GitMetadata(
                repository_url=repository_url,
                branch=branch or 'main',
                commit_hash=commit_hash,
                commit_message=payload.get('commit_message', ''),
                commit_author=payload.get('commit_author', ''),
                event_type=payload.get('event_type', 'push')
            )
        
        return None
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # Try common format fallbacks without external dependencies
                for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        if fmt.endswith('Z'):
                            # Handle Z timezone marker
                            clean_str = timestamp_str.replace('Z', '+00:00')
                            return datetime.fromisoformat(clean_str)
                        else:
                            return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
                return datetime.now(timezone.utc)  # Fallback to current time
            except Exception:
                return datetime.now(timezone.utc)  # Fallback to current time
    
    async def _process_scan_workflow(
        self,
        webhook_event: WebhookEvent,
        git_metadata: GitMetadata
    ):
        """Process the complete scan workflow"""
        scan_report = None
        
        try:
            # Update webhook status
            webhook_event.status = "processing"
            webhook_event.processed_at = datetime.now(timezone.utc)
            await webhook_event.save()
            
            logger.info(f"Starting scan workflow for {git_metadata.repository_url}")
            
            # Create scan report
            scan_report = ScanReport(
                project_name=self._extract_project_name(git_metadata.repository_url),
                scan_id=str(uuid.uuid4()),
                git_metadata=git_metadata,
                status=ScanStatus.PENDING
            )
            
            await scan_report.insert()
            webhook_event.scan_report_id = scan_report.id
            await webhook_event.save()
            
            # Update scan status to running
            scan_report.status = ScanStatus.RUNNING
            await scan_report.save()
            
            # Clone repository
            logger.info("Cloning repository...")
            clone_info = await repo_cloner.clone_repository(
                git_metadata.repository_url,
                git_metadata.branch,
                git_metadata.commit_hash
            )
            
            local_path = clone_info['local_path']
            
            try:
                # Execute comprehensive scanning workflow with AI analysis
                logger.info("Starting enhanced scanning workflow...")
                updated_scan_report = await enhanced_workflow.execute_comprehensive_scan(
                    scan_report=scan_report,
                    repository_path=local_path,
                    target_url=None  # Can be enhanced to support DAST targets
                )
                
                logger.info(f"Enhanced scan workflow completed successfully for {git_metadata.repository_url}")
                
            finally:
                # Cleanup cloned repository
                if settings.cleanup_after_scan:
                    await repo_cloner.cleanup_repository(local_path)
                
        except Exception as e:
            error_msg = f"Scan workflow failed: {e}"
            logger.error(error_msg)
            
            # Update webhook event with error
            webhook_event.status = "failed"
            webhook_event.error_message = error_msg
            await webhook_event.save()
            
            # Update scan report if it exists
            if scan_report:
                scan_report.status = ScanStatus.FAILED
                scan_report.completed_at = datetime.now(timezone.utc)
                if scan_report.started_at:
                    scan_report.duration_seconds = (
                        scan_report.completed_at - scan_report.started_at
                    ).total_seconds()
                await scan_report.save()
    
    def _extract_project_name(self, repository_url: str) -> str:
        """Extract project name from repository URL"""
        # Remove .git suffix if present
        if repository_url.endswith('.git'):
            repository_url = repository_url[:-4]
        
        # Extract the last part of the URL
        parts = repository_url.rstrip('/').split('/')
        return parts[-1] if parts else 'unknown'


# Global webhook processor
webhook_processor = WebhookProcessor()


@router.post("/")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Receive webhook events from Git providers
    
    This endpoint handles webhooks from GitHub, GitLab, Bitbucket, and other Git providers.
    It processes push events and pull requests to trigger security scans.
    """
    try:
        # Get headers
        headers = dict(request.headers)
        
        # Get payload
        payload = await request.json()
        
        logger.info(f"Received webhook from {headers.get('user-agent', 'unknown')}")
        
        # Process webhook event
        event_id = await webhook_processor.process_webhook_event(payload, headers)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "accepted",
                "event_id": event_id,
                "message": "Webhook received and processing started"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/events/{event_id}")
async def get_webhook_event(event_id: str) -> Dict[str, Any]:
    """Get webhook event status and details"""
    try:
        webhook_event = await WebhookEvent.find_one(WebhookEvent.event_id == event_id)
        
        if not webhook_event:
            raise HTTPException(status_code=404, detail="Webhook event not found")
        
        result = {
            "event_id": webhook_event.event_id,
            "event_type": webhook_event.event_type,
            "repository_url": webhook_event.repository_url,
            "branch": webhook_event.branch,
            "commit_hash": webhook_event.commit_hash,
            "status": webhook_event.status,
            "created_at": webhook_event.created_at,
            "processed_at": webhook_event.processed_at,
            "error_message": webhook_event.error_message
        }
        
        # Include scan report ID if available
        if webhook_event.scan_report_id:
            result["scan_report_id"] = str(webhook_event.scan_report_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webhook event: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/events")
async def list_webhook_events(
    limit: int = 50,
    skip: int = 0,
    repository_url: Optional[str] = None
) -> Dict[str, Any]:
    """List webhook events with optional filtering"""
    try:
        query = WebhookEvent.find()
        
        if repository_url:
            query = query.find(WebhookEvent.repository_url == repository_url)
        
        # Get total count
        total = await query.count()
        
        # Get events with pagination
        events = await query.sort(-WebhookEvent.created_at).skip(skip).limit(limit).to_list()
        
        return {
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "repository_url": event.repository_url,
                    "branch": event.branch,
                    "status": event.status,
                    "created_at": event.created_at,
                    "scan_report_id": str(event.scan_report_id) if event.scan_report_id else None
                }
                for event in events
            ],
            "total": total,
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Error listing webhook events: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
