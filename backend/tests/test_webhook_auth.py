from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(autouse=True)
def _webhook_secret():
    """Require a shared secret for the webhook endpoint in these tests."""
    from config import settings
    with patch.object(settings, "webhook_secret", "test-webhook-secret"):
        yield


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    app.dependency_overrides.clear()


class TestWebhookAuth:
    """POST /api/webhook/ must reject requests without a valid shared secret."""

    def test_webhook_rejected_without_secret(self):
        client = TestClient(app)
        response = client.post(
            "/api/webhook/",
            json={"repository_url": "https://github.com/test/repo"},
        )
        assert response.status_code == 401

    def test_webhook_rejected_with_wrong_secret(self):
        client = TestClient(app)
        response = client.post(
            "/api/webhook/",
            json={},
            headers={"x-onyx-webhook-secret": "wrong-secret"},
        )
        assert response.status_code == 401

    def test_webhook_rejected_with_invalid_hub_signature(self):
        client = TestClient(app)
        response = client.post(
            "/api/webhook/",
            json={},
            headers={"x-hub-signature-256": "sha256=deadbeef"},
        )
        assert response.status_code == 401

    def test_webhook_accepted_with_shared_secret(self):
        from routes.webhook.processor import webhook_processor

        client = TestClient(app)
        with patch.object(
            webhook_processor,
            "process_webhook_event",
            new_callable=AsyncMock,
            return_value="event-123",
        ):
            response = client.post(
                "/api/webhook/",
                json={"ref": "refs/heads/main", "repository": {"clone_url": "https://github.com/test/repo"}},
                headers={"x-onyx-webhook-secret": "test-webhook-secret"},
            )

        assert response.status_code == 200
        assert response.json()["event_id"] == "event-123"

    def test_webhook_unavailable_when_secret_unset(self):
        """Without WEBHOOK_SECRET the endpoint must fail closed (503), not accept unauthenticated events."""
        from config import settings

        client = TestClient(app)
        with patch.object(settings, "webhook_secret", None):
            response = client.post(
                "/api/webhook/",
                json={"repository_url": "https://github.com/test/repo"},
            )
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]

    def test_webhook_secret_never_persisted_in_event_headers(self):
        """Only safe headers may be stored with a webhook event - never the shared secret."""
        from routes.webhook.processor import webhook_processor

        client = TestClient(app)
        with patch.object(
            webhook_processor,
            "process_webhook_event",
            new_callable=AsyncMock,
            return_value="event-999",
        ) as proc:
            response = client.post(
                "/api/webhook/",
                json={"ref": "refs/heads/main", "repository": {"clone_url": "https://github.com/test/repo"}},
                headers={
                    "x-onyx-webhook-secret": "test-webhook-secret",
                    "x-webhook-secret": "test-webhook-secret",
                    "x-github-event": "push",
                    "user-agent": "curl/8.0",
                    "x-custom-internal": "leak-me",
                },
            )

        assert response.status_code == 200
        stored_headers = proc.await_args.args[1]
        assert "x-onyx-webhook-secret" not in stored_headers
        assert "x-webhook-secret" not in stored_headers
        assert "x-custom-internal" not in stored_headers
        assert stored_headers.get("x-github-event") == "push"
        assert stored_headers.get("user-agent") == "curl/8.0"

    def test_webhook_events_require_auth(self):
        """GET /api/webhook/events must not be anonymously queryable."""
        client = TestClient(app)
        response = client.get("/api/webhook/events")
        assert response.status_code == 401

        response = client.get("/api/webhook/events/evt-123")
        assert response.status_code == 401

    def test_webhook_events_authenticated_with_token(self):
        """Authenticated users can list webhook events."""
        from unittest.mock import AsyncMock, MagicMock

        from routes.dependencies import get_current_user

        fake_user = MagicMock(id="user-1", role="admin")

        async def _override():
            return fake_user

        app.dependency_overrides[get_current_user] = _override
        try:
            client = TestClient(app)
            query_mock = MagicMock()
            query_mock.count = AsyncMock(return_value=0)
            query_mock.sort = MagicMock(return_value=query_mock)
            query_mock.skip = MagicMock(return_value=query_mock)
            query_mock.limit = MagicMock(return_value=query_mock)
            query_mock.to_list = AsyncMock(return_value=[])

            event_cls = MagicMock()
            event_cls.find = MagicMock(return_value=query_mock)
            event_cls.created_at = MagicMock()

            with patch("routes.webhook.events.WebhookEvent", new=event_cls):
                response = client.get("/api/webhook/events")
            assert response.status_code == 200
            assert response.json()["total"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_webhook_accepted_with_valid_hub_signature(self):
        import hashlib
        import hmac

        from routes.webhook.processor import webhook_processor

        body = b'{"ref": "refs/heads/main"}'
        digest = hmac.new(b"test-webhook-secret", body, hashlib.sha256).hexdigest()

        client = TestClient(app)
        with patch.object(
            webhook_processor,
            "process_webhook_event",
            new_callable=AsyncMock,
            return_value="event-456",
        ):
            response = client.post(
                "/api/webhook/",
                content=body,
                headers={"x-hub-signature-256": f"sha256={digest}"},
            )

        assert response.status_code == 200
        assert response.json()["event_id"] == "event-456"
