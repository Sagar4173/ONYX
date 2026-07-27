"""
Git repository cloning utilities
"""
import asyncio
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo

from config import settings
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class RepoCloneError(Exception):
    """Custom exception for repository cloning errors"""
    pass


class GitRepoCloner:
    """Handles git repository cloning operations"""
    
    def __init__(self, base_temp_dir: Optional[str] = None):
        self.base_temp_dir = Path(base_temp_dir or settings.temp_dir)
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL"""
        # Handle various Git URL formats
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        if '/' in repo_url:
            return repo_url.split('/')[-1]
        
        return repo_url
    
    def _sanitize_path(self, path: str) -> str:
        """Sanitize path for filesystem safety"""
        # Remove or replace unsafe characters
        unsafe_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in unsafe_chars:
            path = path.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        path = path.strip('. ')
        
        return path
    
    async def clone_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        commit_hash: Optional[str] = None,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Clone a git repository with specified branch/commit
        
        Args:
            repo_url: Repository URL to clone
            branch: Specific branch to clone (optional)
            commit_hash: Specific commit to checkout (optional)
            depth: Clone depth (default: 1 for shallow clone)
            
        Returns:
            Dict containing clone information and local path
        """
        repo_name = self._get_repo_name(repo_url)
        sanitized_name = self._sanitize_path(repo_name)
        
        # Create unique directory with timestamp
        timestamp = utc_now().strftime("%Y%m%d_%H%M%S_%f")
        clone_dir = self.base_temp_dir / f"{sanitized_name}_{timestamp}"
        
        try:
            logger.info(f"Cloning repository {repo_url} to {clone_dir}")
            
            # Prepare clone options
            clone_kwargs = {
                'depth': depth if not commit_hash else None,  # Can't use depth with specific commit
                'single_branch': True if branch and not commit_hash else False,
                'branch': branch if branch and not commit_hash else None
            }
            
            # Remove None values
            clone_kwargs = {k: v for k, v in clone_kwargs.items() if v is not None}
            
            # Clone the repository
            repo = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: Repo.clone_from(repo_url, clone_dir, **clone_kwargs)
            )
            
            # Checkout specific commit if provided
            if commit_hash:
                logger.info(f"Checking out commit {commit_hash}")
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: repo.git.checkout(commit_hash)
                )
            
            # Get repository metadata
            head_commit = repo.head.commit
            metadata = {
                'repository_url': repo_url,
                'local_path': str(clone_dir),
                'branch': branch or repo.active_branch.name,
                'commit_hash': head_commit.hexsha,
                'commit_message': head_commit.message.strip(),
                'commit_author': str(head_commit.author),
                'commit_timestamp': datetime.fromtimestamp(
                    head_commit.committed_date, 
                    tz=timezone.utc
                ),
                'clone_timestamp': datetime.now(timezone.utc),
                'is_shallow': repo.git.rev_parse('--is-shallow-repository') == 'true'
            }
            
            logger.info(f"Successfully cloned repository to {clone_dir}")
            return metadata
            
        except GitCommandError as e:
            error_msg = f"Git command failed: {e}"
            logger.error(error_msg)
            self._cleanup_directory(clone_dir)
            raise RepoCloneError(error_msg) from e
            
        except InvalidGitRepositoryError as e:
            error_msg = f"Invalid git repository: {e}"
            logger.error(error_msg)
            self._cleanup_directory(clone_dir)
            raise RepoCloneError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error during clone: {e}"
            logger.error(error_msg)
            self._cleanup_directory(clone_dir)
            raise RepoCloneError(error_msg) from e
    
    def _cleanup_directory(self, directory: Path) -> None:
        """Safely remove directory and contents"""
        try:
            if directory.exists():
                shutil.rmtree(directory, ignore_errors=True)
                logger.info(f"Cleaned up directory: {directory}")
        except Exception as e:
            logger.warning(f"Failed to cleanup directory {directory}: {e}")
    
    async def cleanup_repository(self, local_path: str) -> bool:
        """
        Clean up cloned repository
        
        Args:
            local_path: Path to the cloned repository
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            path = Path(local_path)
            if path.exists():
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: shutil.rmtree(path, ignore_errors=True)
                )
                logger.info(f"Successfully cleaned up repository at {local_path}")
                return True
            else:
                logger.warning(f"Repository path does not exist: {local_path}")
                return True  # Consider it cleaned up
                
        except Exception as e:
            logger.error(f"Failed to cleanup repository at {local_path}: {e}")
            return False
    
    async def get_repository_info(self, local_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a cloned repository
        
        Args:
            local_path: Path to the cloned repository
            
        Returns:
            Dictionary with repository information
        """
        try:
            repo = Repo(local_path)
            head_commit = repo.head.commit
            
            # Get repository statistics
            total_commits = sum(1 for _ in repo.iter_commits())
            
            # Get file statistics
            repo_path = Path(local_path)
            all_files = list(repo_path.rglob('*'))
            code_files = [
                f for f in all_files 
                if f.is_file() and f.suffix in [
                    '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', 
                    '.rb', '.php', '.swift', '.kt', '.rs', '.scala', '.sh'
                ]
            ]
            
            return {
                'total_commits': total_commits,
                'total_files': len([f for f in all_files if f.is_file()]),
                'code_files': len(code_files),
                'languages': list(set(f.suffix[1:] for f in code_files if f.suffix)),
                'size_bytes': sum(f.stat().st_size for f in all_files if f.is_file()),
                'last_commit': {
                    'hash': head_commit.hexsha,
                    'message': head_commit.message.strip(),
                    'author': str(head_commit.author),
                    'timestamp': datetime.fromtimestamp(
                        head_commit.committed_date, 
                        tz=timezone.utc
                    )
                },
                'branches': [ref.name for ref in repo.refs if 'remotes' not in ref.name],
                'tags': [tag.name for tag in repo.tags]
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository info for {local_path}: {e}")
            return {}
    
    async def validate_repository(self, local_path: str) -> bool:
        """
        Validate that a cloned repository is accessible and valid
        
        Args:
            local_path: Path to the cloned repository
            
        Returns:
            True if repository is valid, False otherwise
        """
        try:
            path = Path(local_path)
            if not path.exists():
                logger.error(f"Repository path does not exist: {local_path}")
                return False
            
            repo = Repo(local_path)
            # Try to access basic repo information
            _ = repo.head.commit
            
            logger.info(f"Repository validation successful: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Repository validation failed for {local_path}: {e}")
            return False


# Convenience function for simple cloning
async def clone_repo_simple(
    repo_url: str,
    branch: Optional[str] = None,
    commit_hash: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simple wrapper for repository cloning
    
    Args:
        repo_url: Repository URL to clone
        branch: Specific branch to clone (optional)
        commit_hash: Specific commit to checkout (optional)
        
    Returns:
        Dict containing clone information and local path
    """
    cloner = GitRepoCloner()
    return await cloner.clone_repository(repo_url, branch, commit_hash)


# Global cloner instance
repo_cloner = GitRepoCloner()
