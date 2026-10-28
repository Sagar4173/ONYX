"""Remove credential userinfo from repository URLs for display."""
import re
from urllib.parse import urlparse, urlunparse

SENSITIVE_QUERY_KEYS = (
    "access_token",
    "access-token",
    "private_token",
    "private-token",
    "oauth_token",
    "oauth-token",
    "refresh_token",
    "refresh-token",
    "id_token",
    "id-token",
    "session_token",
    "session-token",
    "auth_token",
    "auth-token",
    "api_key",
    "api-key",
    "apikey",
    "client_secret",
    "client-secret",
    "x-amz-security-token",
    "x-amz-credential",
    "x-amz-signature",
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "key",
    "auth",
    "authorization",
    "signature",
    "sig",
    "credential",
    "credentials",
)
SENSITIVE_QUERY_PARAM_RE = re.compile(
    r"([?&](?:" + "|".join(SENSITIVE_QUERY_KEYS) + r")=)[^&#\s]*",
    re.IGNORECASE,
)
_SCP_CREDENTIAL_RE = re.compile(
    r"^(?P<prefix>(?:[^@/\s]+@)+)(?P<rest>[^@/\s]+[:/][^\s]*)$"
)


def has_embedded_credentials(url: str) -> bool:
    """Return True when a URL carries userinfo or a known secret query parameter."""
    if not url:
        return False
    return strip_url_credentials(url) != url


def _select_scp_username(prefix: str) -> str:
    for candidate in prefix.rstrip("@").split("@"):
        if ":" not in candidate and "%40" not in candidate.lower():
            return candidate
    return ""


def strip_url_credentials(url: str) -> str:
    if not url:
        return url
    scp_match = _SCP_CREDENTIAL_RE.match(url)
    if scp_match:
        username = _select_scp_username(scp_match.group("prefix"))
        rest = scp_match.group("rest")
        url = f"{username}@{rest}" if username else rest
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    has_userinfo = parsed.username is not None or parsed.password is not None
    if has_userinfo and parsed.netloc:
        scheme = parsed.scheme.lower()
        preserve_ssh_user = (
            scheme == "ssh"
            and parsed.password is None
            and parsed.netloc.count("@") == 1
            and "%40" not in parsed.netloc.lower()
        )
        if not preserve_ssh_user:
            netloc = parsed.netloc.rsplit("@", 1)[1]
            url = urlunparse(parsed._replace(netloc=netloc))
    return SENSITIVE_QUERY_PARAM_RE.sub(r"\1[REDACTED]", url)
