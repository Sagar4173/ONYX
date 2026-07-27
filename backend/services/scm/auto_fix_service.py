import logging
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from config import settings
from models.project import Project
from models.report import ScanReport, VulnerabilityFinding

logger = logging.getLogger(__name__)


class AutoFixError(Exception):
    pass


class AutoFixService:

    async def create_auto_fix_pr(
        self,
        scan_report: ScanReport,
        finding_id: str,
    ) -> Dict[str, Any]:
        finding = self._find_finding(scan_report, finding_id)
        if not finding:
            raise AutoFixError(f"Finding {finding_id} not found in scan report")
        if not finding.file_path or not finding.remediation_code:
            raise AutoFixError(
                f"Finding {finding_id} has no remediation code — cannot auto-fix"
            )

        repo_url = scan_report.git_metadata.repository_url
        branch = scan_report.git_metadata.branch
        token = await self._resolve_token(scan_report)

        local_path = None
        try:
            local_path = self._clone_repo(repo_url, branch, token)

            file_path = self._apply_fix(local_path, finding)

            branch_name = self._create_branch_and_commit(
                local_path=local_path,
                file_path=file_path,
                finding=finding,
                branch=branch,
            )

            self._push_branch(local_path, branch_name, token, repo_url)

            pr_url, pr_number = await self._create_pr(
                repo_url=repo_url,
                branch=branch,
                branch_name=branch_name,
                finding=finding,
                token=token,
                scan_report=scan_report,
            )

            return {
                "pr_url": pr_url,
                "pr_number": pr_number,
                "branch": branch_name,
                "finding_id": finding_id,
                "file_path": file_path,
            }
        finally:
            if local_path and os.path.exists(local_path):
                import shutil
                shutil.rmtree(local_path, ignore_errors=True)

    def _find_finding(
        self, scan_report: ScanReport, finding_id: str
    ) -> Optional[VulnerabilityFinding]:
        for scan_result in scan_report.scan_results:
            for finding in scan_result.findings:
                if finding.id == finding_id:
                    return finding
        return None

    async def _resolve_token(self, scan_report: ScanReport) -> Optional[str]:
        if scan_report.project_id:
            project = await Project.find_one({"project_id": scan_report.project_id})
            if project and project.repository and project.repository.access_token:
                return project.repository.access_token
        return settings.auto_fix_token

    def _clone_repo(self, repo_url: str, branch: str, token: Optional[str]) -> str:
        from git import Repo
        from git.exc import GitCommandError

        clone_url = repo_url
        if token:
            parsed = urlparse(repo_url)
            clone_url = f"https://{token}@{parsed.netloc}{parsed.path}"

        local_path = tempfile.mkdtemp(prefix="onyx-autofix-")
        try:
            Repo.clone_from(clone_url, local_path, branch=branch, depth=1)
            return local_path
        except GitCommandError as e:
            if os.path.exists(local_path):
                import shutil
                shutil.rmtree(local_path, ignore_errors=True)
            raise AutoFixError(f"Git clone failed: {e}")

    def _apply_fix(self, local_path: str, finding: VulnerabilityFinding) -> str:
        abs_path = os.path.join(local_path, finding.file_path)
        if not os.path.exists(abs_path):
            raise AutoFixError(f"File not found in repository: {finding.file_path}")

        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        line_start = finding.line_start or 1
        line_end = finding.line_end or line_start

        if line_start < 1 or line_start > len(lines):
            raise AutoFixError(
                f"Line range out of bounds: {line_start}-{line_end}, file has {len(lines)} lines"
            )

        fix_lines = finding.remediation_code.split("\n")
        fix_lines = [l + "\n" for l in fix_lines]

        new_lines = lines[: line_start - 1] + fix_lines + lines[line_end:]

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return finding.file_path

    def _create_branch_and_commit(
        self,
        local_path: str,
        file_path: str,
        finding: VulnerabilityFinding,
        branch: str,
    ) -> str:
        from git import Repo

        repo = Repo(local_path)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        branch_name = f"{settings.auto_fix_branch_prefix}{finding.id[:12]}-{timestamp}"

        new_branch = repo.create_head(branch_name)
        new_branch.checkout()

        commit_message = (
            f"{settings.auto_fix_pr_title_prefix}{finding.title}\n\n"
            f"Auto-generated fix for {finding.id}\n"
            f"Severity: {finding.severity.value if hasattr(finding.severity, 'value') else finding.severity}\n"
            f"File: {file_path}"
        )

        repo.index.add([file_path])
        repo.index.commit(commit_message)

        return branch_name

    def _push_branch(
        self,
        local_path: str,
        branch_name: str,
        token: Optional[str],
        repo_url: str,
    ):
        from git import Repo
        from git.exc import GitCommandError

        repo = Repo(local_path)
        origin = repo.remote(name="origin")

        push_url = repo_url
        if token:
            parsed = urlparse(repo_url)
            push_url = f"https://{token}@{parsed.netloc}{parsed.path}"

        try:
            origin.push(refspec=f"{branch_name}:{branch_name}", push_url=push_url)
        except GitCommandError as e:
            raise AutoFixError(f"Git push failed: {e}")

    async def _create_pr(
        self,
        repo_url: str,
        branch: str,
        branch_name: str,
        finding: VulnerabilityFinding,
        token: Optional[str],
        scan_report: ScanReport,
    ) -> tuple:
        if not token:
            raise AutoFixError(
                "No SCM token available — cannot create PR. "
                "Set per-project access_token or AUTO_FIX_TOKEN env var."
            )

        platform = self._detect_platform(repo_url)
        owner, repo_name = self._parse_repo_info(repo_url)

        title = f"{settings.auto_fix_pr_title_prefix}{finding.title}"
        body = (
            f"## Auto-Generated Fix\n\n"
            f"**Finding:** {finding.title}\n"
            f"**Severity:** {finding.severity.value if hasattr(finding.severity, 'value') else finding.severity}\n"
            f"**File:** `{finding.file_path}`\n"
            f"**Description:** {finding.description or 'No description'}\n\n"
            f"---\n\n"
            f"This PR was automatically generated by ONYX Security Intelligence Platform."
        )

        if platform == "github":
            return await self._create_github_pr(
                owner, repo_name, branch, branch_name, title, body, token
            )
        elif platform == "gitlab":
            return await self._create_gitlab_pr(
                repo_url, branch, branch_name, title, body, token
            )
        else:
            raise AutoFixError(f"Unsupported SCM platform: {platform}")

    def _detect_platform(self, repo_url: str) -> str:
        host = urlparse(repo_url).hostname or ""
        if "github" in host:
            return "github"
        elif "gitlab" in host:
            return "gitlab"
        elif "bitbucket" in host:
            return "bitbucket"
        raise AutoFixError(f"Unsupported SCM platform in URL: {repo_url}")

    def _parse_repo_info(self, repo_url: str) -> tuple:
        path = urlparse(repo_url).path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        parts = path.split("/")
        if len(parts) < 2:
            raise AutoFixError(f"Could not parse owner/repo from: {repo_url}")
        return parts[0], parts[1]

    async def _create_github_pr(
        self,
        owner: str,
        repo_name: str,
        base_branch: str,
        head_branch: str,
        title: str,
        body: str,
        token: str,
    ) -> tuple:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "onyx-security-platform",
        }
        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)

        if response.status_code not in (201,):
            raise AutoFixError(
                f"GitHub PR creation failed (HTTP {response.status_code}): {response.text}"
            )

        data = response.json()
        return data.get("html_url", ""), data.get("number", 0)

    async def _create_gitlab_pr(
        self,
        repo_url: str,
        base_branch: str,
        head_branch: str,
        title: str,
        body: str,
        token: str,
    ) -> tuple:
        from urllib.parse import quote

        full_path = urlparse(repo_url).path.strip("/")
        if full_path.endswith(".git"):
            full_path = full_path[:-4]
        encoded_path = quote(full_path, safe="")

        api_url = f"https://gitlab.com/api/v4/projects/{encoded_path}/merge_requests"
        headers = {
            "PRIVATE-TOKEN": token,
            "User-Agent": "onyx-security-platform",
        }
        payload = {
            "source_branch": head_branch,
            "target_branch": base_branch,
            "title": title,
            "description": body,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)

        if response.status_code not in (201,):
            raise AutoFixError(
                f"GitLab MR creation failed (HTTP {response.status_code}): {response.text}"
            )

        data = response.json()
        return data.get("web_url", ""), data.get("iid", 0)


auto_fix_service = AutoFixService()
