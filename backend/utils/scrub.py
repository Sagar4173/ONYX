"""Scrub credential-looking substrings from error and log text."""
import re
from typing import Any

_URL_USERINFO_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9+.\-]*://)[^\s/@]+@")
_QUERY_SECRET_RE = re.compile(
    r"([?&](?:access_token|private_token|token|api_key|key)=)[^&\s]+",
    re.IGNORECASE,
)
_AUTH_BASIC_RE = re.compile(
    r"(Authorization:\s*Basic\s+)[A-Za-z0-9+/]{4,}={0,2}", re.IGNORECASE
)
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}|AIza[A-Za-z0-9_\-]{10,}|Bearer\s+[A-Za-z0-9._\-]+|"
    r"Basic\s+(?=[A-Za-z0-9+/]*[0-9+/=A-Z])[A-Za-z0-9+/]{4,}={0,2}"
    r"(?=$|[\n\"'()\[\]{}.,;:])|"
    r"gh[pousr]_[A-Za-z0-9]{10,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_\-]{10,})"
)


def scrub_text(text: Any, limit: int = 300) -> str:
    scrubbed = _URL_USERINFO_RE.sub(r"\1[REDACTED]@", str(text))
    scrubbed = _QUERY_SECRET_RE.sub(r"\1[REDACTED]", scrubbed)
    scrubbed = _AUTH_BASIC_RE.sub(r"\1[REDACTED]", scrubbed)
    scrubbed = _SECRET_RE.sub("[REDACTED]", scrubbed)
    return scrubbed[:limit]
