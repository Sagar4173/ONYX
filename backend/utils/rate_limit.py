"""
Shared SlowAPI rate limiter instance.

Defined in its own module so routes can import it without circular imports.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _client_ip_key(request: Request) -> str:
    """
    Key rate limits by client IP, honoring the proxy-set X-Forwarded-For header.

    Uses the LAST entry: proxies append the real client IP after any
    client-supplied values, so `X-Forwarded-For: 1.2.3.4` from an attacker
    cannot spoof the limit key when a trusted proxy (nginx with
    `proxy_set_header X-Forwarded-For $remote_addr`) is in front.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[-1].strip()
        if client_ip:
            return client_ip
    return get_remote_address(request)


class _FastAPILimiter(Limiter):
    """
    Limiter tuned for FastAPI's dict-returning endpoints.

    With headers_enabled=True, slowapi's per-response injection calls
    _inject_headers(kwargs.get("response"), ...) after the endpoint runs.
    FastAPI only injects a `response: Response` kwarg when the endpoint
    signature declares one, so plain dict returns would raise
    "parameter `response` must be an instance of starlette.responses.Response".
    Skip injection when there is no Response object; the 429 handler and
    Response-returning endpoints (e.g. streaming chat) still get headers.
    """

    def _inject_headers(self, response, current_limit):
        if response is None:
            return response
        return super()._inject_headers(response, current_limit)


limiter = _FastAPILimiter(key_func=_client_ip_key, headers_enabled=True)
