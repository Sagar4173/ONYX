import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException

from config import settings
from models.report import GitMetadata, ScanReport, ScanStatus, WebhookEvent
from services.scanning.workflow import enhanced_workflow
from utils.error_handling import get_safe_error_detail
from utils.repo_clone import repo_cloner

logger = logging.getLogger(__name__)


class WebhookProcessor:
    async def process_webhook_event(
        self,
        event_data: Dict[str, Any],
        headers: Dict[str, str]
    ) -> str:
        event_id = str(uuid.uuid4())

        try:
            git_metadata = self._parse_webhook_data(event_data, headers)

            if not git_metadata:
                raise HTTPException(status_code=400, detail="Invalid webhook payload")

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

            asyncio.create_task(
                self._process_scan_workflow(webhook_event, git_metadata)
            )

            return event_id

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=500, detail=get_safe_error_detail(e))

    def _parse_webhook_data(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
        if 'X-GitHub-Event' in headers or 'github' in headers.get('User-Agent', '').lower():
            return self._parse_github_webhook(payload, headers)

        elif 'X-Gitlab-Event' in headers:
            return self._parse_gitlab_webhook(payload, headers)

        elif 'X-Event-Key' in headers:
            return self._parse_bitbucket_webhook(payload, headers)

        else:
            return self._parse_generic_webhook(payload, headers)

    def _parse_github_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[GitMetadata]:
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
        if not timestamp_str:
            return None

        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        if fmt.endswith('Z'):
                            clean_str = timestamp_str.replace('Z', '+00:00')
                            return datetime.fromisoformat(clean_str)
                        else:
                            return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
                return datetime.now(timezone.utc)
            except Exception:
                return datetime.now(timezone.utc)

    async def _process_scan_workflow(
        self,
        webhook_event: WebhookEvent,
        git_metadata: GitMetadata
    ):
        scan_report = None

        try:
            webhook_event.status = "processing"
            webhook_event.processed_at = datetime.now(timezone.utc)
            await webhook_event.save()

            logger.info(f"Starting scan workflow for {git_metadata.repository_url}")

            from models.project import Project
            project = await Project.find_one(
                Project.repository.url == git_metadata.repository_url
            )
            project_id = str(project.id) if project else None
            user_id = project.owner_id if project else None

            scan_report = ScanReport(
                project_name=self._extract_project_name(git_metadata.repository_url),
                project_id=project_id,
                user_id=user_id,
                scan_id=str(uuid.uuid4()),
                git_metadata=git_metadata,
                status=ScanStatus.PENDING
            )

            await scan_report.insert()
            webhook_event.scan_report_id = str(scan_report.id)
            await webhook_event.save()

            scan_report.status = ScanStatus.RUNNING
            await scan_report.save()

            logger.info("Cloning repository...")
            clone_info = await repo_cloner.clone_repository(
                git_metadata.repository_url,
                git_metadata.branch,
                git_metadata.commit_hash
            )

            local_path = clone_info['local_path']

            try:
                logger.info("Starting enhanced scanning workflow...")
                _updated_scan_report = await enhanced_workflow.execute_comprehensive_scan(
                    scan_report=scan_report,
                    repository_path=local_path,
                    target_url=None
                )

                logger.info(f"Enhanced scan workflow completed successfully for {git_metadata.repository_url}")

            finally:
                if settings.cleanup_after_scan:
                    await repo_cloner.cleanup_repository(local_path)

        except Exception as e:
            error_msg = f"Scan workflow failed: {e}"
            logger.error(error_msg)

            webhook_event.status = "failed"
            webhook_event.error_message = error_msg
            await webhook_event.save()

            if scan_report:
                scan_report.status = ScanStatus.FAILED
                scan_report.completed_at = datetime.now(timezone.utc)
                if scan_report.started_at:
                    # DB round-trips can yield naive UTC datetimes; normalize
                    # both sides before subtracting (tz-aware arithmetic only).
                    started_at = scan_report.started_at
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=timezone.utc)
                    completed_at = scan_report.completed_at
                    if completed_at.tzinfo is None:
                        completed_at = completed_at.replace(tzinfo=timezone.utc)
                    scan_report.duration_seconds = (
                        completed_at - started_at
                    ).total_seconds()
                await scan_report.save()

    def _extract_project_name(self, repository_url: str) -> str:
        if repository_url.endswith('.git'):
            repository_url = repository_url[:-4]

        parts = repository_url.rstrip('/').split('/')
        return parts[-1] if parts else 'unknown'


webhook_processor = WebhookProcessor()
