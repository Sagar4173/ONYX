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
