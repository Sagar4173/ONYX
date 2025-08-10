"""
Webhook routes for handling repository events
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from models.report import (
    ScanReport, WebhookEvent, GitMetadata, ScanStatus, ScannerType
)
from services.scanner import security_scanner
from services.ai_processor import ai_processor
from services.notifier import notification_service
from utils.repo_clone import repo_cloner
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


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
                # Try other common formats
                from dateutil.parser import parse
                return parse(timestamp_str)
            except Exception:
                return None
    
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
                # Run security scans
                logger.info("Running security scans...")
                scan_results = await security_scanner.run_all_scans(local_path)
                
                # Update scan report with results
                scan_report.scan_results = scan_results
                scan_report.update_summary()
                
                # Generate AI analysis if there are findings
                if scan_report.total_findings > 0:
                    logger.info("Generating AI analysis...")
                    ai_analysis = await ai_processor.analyze_scan_results(
                        scan_results,
                        project_context={'project_name': scan_report.project_name}
                    )
                    scan_report.ai_analysis = ai_analysis
                
                # Update scan status
                scan_report.status = ScanStatus.COMPLETED
                scan_report.completed_at = datetime.now(timezone.utc)
                scan_report.duration_seconds = (
                    scan_report.completed_at - scan_report.started_at
                ).total_seconds()
                
                await scan_report.save()
                
                # Send notifications
                logger.info("Sending notifications...")
                notification_status = await notification_service.send_scan_notification(scan_report)
                scan_report.notifications = notification_status
                await scan_report.save()
                
                # Update webhook status
                webhook_event.status = "completed"
                await webhook_event.save()
                
                logger.info(f"Scan workflow completed successfully for {git_metadata.repository_url}")
                
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


@router.post("/test")
async def test_webhook():
    """Test webhook endpoint with sample data"""
    sample_payload = {
        "repository_url": "https://github.com/example/test-repo.git",
        "branch": "main",
        "commit_hash": "abc123def456",
        "commit_message": "Test commit",
        "commit_author": "Test User",
        "event_type": "push"
    }
    
    headers = {"content-type": "application/json"}
    
    try:
        event_id = await webhook_processor.process_webhook_event(sample_payload, headers)
        
        return {
            "status": "success",
            "event_id": event_id,
            "message": "Test webhook processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Test webhook failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test webhook failed: {e}")
