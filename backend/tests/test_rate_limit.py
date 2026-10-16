"""
Rate-limit header contract tests.

slowapi 429 responses must carry Retry-After (and X-RateLimit-* headers):
the frontend QuotaNotice countdown drives off it, per UX Track Phase 0
binding chat/features contract (Plan 1 Global Constraints).
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.usefixtures("test_app")
class TestRateLimitHeaders:
    """429 from a slowapi-limited route must include Retry-After."""

    @pytest.fixture(autouse=True)
    def _rate_limit_test_env(self, test_app):
        """Hermetic: reset shared limiter state; bypass the router-level DB guard
        (require_beanie 503s before the endpoint, so limits would never count)."""
        from app import app
        from database import require_beanie
        from utils.rate_limit import limiter

        limiter.reset()
        app.dependency_overrides[require_beanie] = lambda: None
        yield
        app.dependency_overrides.pop(require_beanie, None)
        limiter.reset()

    def test_429_carries_retry_after(self, test_app):
        from services.auth.auth_service import auth_service

        with patch.object(auth_service, "login", new_callable=AsyncMock) as mock_login:
            mock_login.side_effect = HTTPException(
                status_code=401, detail="Invalid credentials"
            )

            response_429 = None
            last_status = None
            for _ in range(40):
                response = test_app.post(
                    "/api/auth/login",
                    json={
                        "username_or_email": "nobody@example.com",
                        "password": "wrong-password",
                    },
                )
                last_status = response.status_code
                if response.status_code == 429:
                    response_429 = response
                    break

            assert response_429 is not None, (
                f"expected 429 after exceeding 30/minute login limit "
                f"(last status {last_status})"
            )
            retry_after = response_429.headers.get("Retry-After")
            assert retry_after is not None, "429 must carry Retry-After"
            assert int(retry_after) >= 0
            assert response_429.headers.get("X-RateLimit-Limit") is not None
            assert response_429.headers.get("X-RateLimit-Remaining") is not None
