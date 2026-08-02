import pytest

from utils.repo_clone import RepoCloneError, validate_repo_url


class TestValidateRepoUrl:
    """SSRF guard: only remote git URLs to public hosts may be cloned."""

    def test_accepts_https_github(self):
        validate_repo_url("https://github.com/owner/repo.git")

    def test_accepts_scp_like_syntax(self):
        validate_repo_url("git@github.com:owner/repo.git")

    def test_accepts_ssh_scheme(self):
        validate_repo_url("ssh://git@github.com/owner/repo.git")

    def test_rejects_file_scheme(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("file:///etc/passwd")

    def test_rejects_local_path(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("/tmp/localrepo")

    def test_rejects_relative_path(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("./repo")

    def test_rejects_windows_path(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("C:\\Users\\me\\repo")

    def test_rejects_loopback_ip(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("http://127.0.0.1:27017/")

    def test_rejects_localhost_hostname(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("https://localhost/repo.git")

    def test_rejects_link_local_metadata(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("http://169.254.169.254/latest/meta-data/")

    def test_rejects_private_ip(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("https://192.168.1.1/repo.git")

    def test_rejects_private_hostname_resolving_to_loopback(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("https://foo.localhost/repo.git")

    def test_rejects_unsupported_scheme(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("ftp://example.com/repo.git")

    def test_rejects_empty_url(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("")
