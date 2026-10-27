"""Remove credential userinfo from repository URLs for display."""
import re
from urllib.parse import urlparse, urlunparse

_QUERY_SECRET_RE = re.compile(
    r"([?&](?:access_token|private_token|token|api_key|key)=)[^&#\s]*",
    re.IGNORECASE,
)
_SCP_CREDENTIAL_RE = re.compile(r"^(?P<user>[^@/\s]+)@[^@/\s]+@(?P<rest>.+)$")


def strip_url_credentials(url: str) -> str:
    if not url:
        return url
    scp_match = _SCP_CREDENTIAL_RE.match(url)
    if scp_match:
        url = f"{scp_match.group('user')}@{scp_match.group('rest')}"
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    has_userinfo = parsed.username is not None or parsed.password is not None
    if has_userinfo and parsed.netloc:
        scheme = parsed.scheme.lower()
        if not (scheme == "ssh" and parsed.password is None):
            netloc = parsed.netloc.rsplit("@", 1)[1]
            url = urlunparse(parsed._replace(netloc=netloc))
    return _QUERY_SECRET_RE.sub(r"\1[REDACTED]", url)
