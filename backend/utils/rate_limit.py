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


limiter = Limiter(key_func=_client_ip_key)
