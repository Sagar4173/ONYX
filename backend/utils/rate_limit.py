"""
Shared SlowAPI rate limiter instance.

Defined in its own module so routes can import it without circular imports.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _client_ip_key(request: Request) -> str:
    """Key rate limits by client IP, honoring the proxy-set X-Forwarded-For header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip
    return get_remote_address(request)


limiter = Limiter(key_func=_client_ip_key)
