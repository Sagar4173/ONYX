"""Tests for credential scrubbing of client-visible error text."""
import pytest

from utils.scrub import scrub_text


class TestUrlUserinfo:
    def test_redacts_token_userinfo(self):
        result = scrub_text("clone failed: https://ghp_secret123456@github.com/owner/repo.git")
        assert "https://[REDACTED]@github.com/owner/repo.git" in result
        assert "ghp_secret123456" not in result

    def test_redacts_user_and_password_userinfo(self):
        result = scrub_text("clone failed: https://user:pass@example.com/owner/repo.git")
        assert result == "clone failed: https://[REDACTED]@example.com/owner/repo.git"


@pytest.mark.parametrize(
    "secret",
    [
        "ghp_abcdefghij1234567890",
        "ghs_abcdefghij1234567890",
        "gho_abcdefghij1234567890",
        "ghu_abcdefghij1234567890",
        "github_pat_abcdefghij1234567890",
        "glpat-abcdefghij1234567890",
        "sk-abcdefgh12345678",
        "AIzaABCDEFGHIJ1234567890",
        "Bearer abc.def-123",
        "Authorization: Basic dXNlcjpwYXNz",
    ],
)
def test_redacts_known_token_shapes(secret):
    result = scrub_text(f"provider error: {secret}")
    assert secret not in result
    assert "[REDACTED]" in result


@pytest.mark.parametrize(
    "url",
    [
        "https://x.test/repo?access_token=secret123",
        "https://x.test/repo?private_token=secret123&x=1",
        "https://x.test/repo?api_key=secret123",
    ],
)
def test_redacts_query_credentials(url):
    result = scrub_text(url)
    assert "secret123" not in result
    assert "[REDACTED]" in result


def test_plain_text_unchanged():
    text = "Git clone failed - check repository access and try again"
    assert scrub_text(text) == text


def test_basic_authentication_prose_unchanged():
    text = "Basic authentication failed"
    assert scrub_text(text) == text


def test_capitalized_basic_prose_unchanged():
    text = "Basic Authentication failed"
    assert scrub_text(text) == text


def test_authorization_basic_short_token_redacted():
    assert (
        scrub_text("401 Authorization: Basic YTpi")
        == "401 Authorization: Basic [REDACTED]"
    )


@pytest.mark.parametrize(
    "text",
    [
        "Basic dXNlcjpwYXNz",
        "Basic ABCDEFGH",
        "Basic YTpi",
    ],
)
def test_redacts_unlabeled_basic_tokens(text):
    assert scrub_text(text) == "[REDACTED]"


def test_url_without_userinfo_unchanged():
    text = "https://github.com/owner/repo.git"
    assert scrub_text(text) == text


def test_bounds_length():
    assert len(scrub_text("a" * 1000)) == 300
    assert len(scrub_text("a" * 1000, limit=50)) == 50


def test_accepts_non_string_input():
    assert scrub_text(RuntimeError("boom")) == "boom"
