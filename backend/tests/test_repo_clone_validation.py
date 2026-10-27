import socket
from unittest.mock import patch

import pytest

from utils.repo_clone import GitRepoCloner, RepoCloneError, validate_repo_url


class TestValidateRepoUrl:
    """SSRF guard: only remote git URLs to public hosts may be cloned."""

    def test_accepts_https_github(self):
        validate_repo_url("https://github.com/owner/repo.git")

    def test_accepts_scp_like_syntax(self):
        validate_repo_url("git@github.com:owner/repo.git")

    def test_accepts_ssh_scheme(self):
        validate_repo_url("ssh://git@github.com/owner/repo.git")

    def test_rejects_https_user_and_password(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("https://user:pass@github.com/owner/repo.git")

    def test_rejects_https_token_userinfo(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("https://ghp_secret@github.com/owner/repo.git")

    def test_rejects_ssh_password(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("ssh://git:secret@github.com/owner/repo.git")

    def test_rejects_git_scheme_userinfo(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("git://user:pass@github.com/owner/repo.git")

    def test_rejects_uppercase_https_userinfo(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("HTTPS://ghp_secret@github.com/owner/repo.git")

    def test_rejects_encoded_userinfo(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("https://user%40token@github.com/owner/repo.git")

    def test_rejects_malformed_url(self):
        with pytest.raises(RepoCloneError, match="Invalid repository URL"):
            validate_repo_url("https://[bad")


class TestRepoName:
    def test_query_credentials_do_not_reach_repo_name(self):
        cloner = GitRepoCloner.__new__(GitRepoCloner)
        name = cloner._get_repo_name(
            "https://github.com/owner/repo.git?access_token=secret"
        )
        assert name == "repo"

    def test_backslash_traversal_does_not_reach_repo_name(self):
        cloner = GitRepoCloner.__new__(GitRepoCloner)
        name = cloner._get_repo_name("https://github.com/..\\..\\evil")
        assert name == "evil"

    def test_sanitize_path_removes_separators_and_dot_segments(self):
        cloner = GitRepoCloner.__new__(GitRepoCloner)
        sanitized = cloner._sanitize_path("..\\..\\evil")
        assert "\\" not in sanitized
        assert "/" not in sanitized
        assert sanitized not in {".", ".."}

    def test_rejects_scp_style_embedded_credentials(self):
        with pytest.raises(RepoCloneError, match="must not embed credentials"):
            validate_repo_url("git@user:pass@github.com:owner/repo.git")

    def test_rejects_scp_style_loopback_ipv6(self):
        with pytest.raises(RepoCloneError, match="host is not allowed"):
            validate_repo_url("git@[::1]:owner/repo.git")

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
        loopback_resolution = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))
        ]
        with patch(
            "utils.repo_clone.socket.getaddrinfo",
            return_value=loopback_resolution,
        ):
            with pytest.raises(RepoCloneError):
                validate_repo_url("https://foo.localhost/repo.git")

    def test_rejects_unsupported_scheme(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("ftp://example.com/repo.git")

    def test_rejects_empty_url(self):
        with pytest.raises(RepoCloneError):
            validate_repo_url("")
