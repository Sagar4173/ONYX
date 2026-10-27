"""Tests for display-time credential removal from repository URLs."""
from utils.url_redaction import strip_url_credentials


class TestStripUrlCredentials:
    def test_removes_token_userinfo(self):
        assert (
            strip_url_credentials("https://ghp_secret@github.com/test/repo.git")
            == "https://github.com/test/repo.git"
        )

    def test_removes_user_and_password(self):
        assert (
            strip_url_credentials("https://user:pass@github.com/test/repo.git")
            == "https://github.com/test/repo.git"
        )

    def test_preserves_host_port_path_and_query(self):
        assert (
            strip_url_credentials("https://user:pass@github.com:8443/test/repo.git?x=1")
            == "https://github.com:8443/test/repo.git?x=1"
        )

    def test_leaves_scp_style_unchanged(self):
        url = "git@github.com:owner/repo.git"
        assert strip_url_credentials(url) == url

    def test_leaves_url_without_credentials_unchanged(self):
        url = "https://github.com/owner/repo.git"
        assert strip_url_credentials(url) == url

    def test_preserves_ssh_username(self):
        url = "ssh://git@github.com/owner/repo.git"
        assert strip_url_credentials(url) == url

    def test_removes_ssh_password(self):
        assert (
            strip_url_credentials("ssh://git:secret@github.com/owner/repo.git")
            == "ssh://github.com/owner/repo.git"
        )

    def test_removes_non_ssh_username(self):
        assert (
            strip_url_credentials("git://token@github.com/owner/repo.git")
            == "git://github.com/owner/repo.git"
        )

    def test_removes_scp_style_credentials(self):
        assert (
            strip_url_credentials("git@user:pass@github.com:owner/repo.git")
            == "git@github.com:owner/repo.git"
        )

    def test_removes_protocol_relative_userinfo(self):
        assert (
            strip_url_credentials("//user:pass@host/owner/repo.git")
            == "//host/owner/repo.git"
        )

    def test_redacts_query_credentials(self):
        assert (
            strip_url_credentials(
                "https://github.com/owner/repo.git?access_token=secret&x=1"
            )
            == "https://github.com/owner/repo.git?access_token=[REDACTED]&x=1"
        )

    def test_malformed_url_returns_empty(self):
        assert strip_url_credentials("https://user:pass@[not-ipv6/repo.git") == ""

    def test_leaves_empty_unchanged(self):
        assert strip_url_credentials("") == ""
