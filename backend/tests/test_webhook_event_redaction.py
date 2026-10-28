"""Webhook event responses must not expose credential-bearing repository URLs."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from models.user import User
from routes.dependencies import get_current_user

CREDENTIAL_URL = "https://ghp_secret@github.com/owner/repo.git"
REDACTED_URL = "https://github.com/owner/repo.git"


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def _client():
    user = MagicMock(spec=User)
    user.id = "user-test-123"

    async def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    return TestClient(app)


def _event():
    event = MagicMock()
    event.event_id = "evt-1"
    event.event_type = "push"
    event.repository_url = CREDENTIAL_URL
    event.branch = "main"
    event.commit_hash = "abc123"
    event.status = "received"
    event.created_at = datetime.now(timezone.utc)
    event.processed_at = None
    event.error_message = None
    event.scan_report_id = None
    return event


def test_get_event_redacts_repository_url():
    client = _client()
    with patch("routes.webhook.events.WebhookEvent") as mock_event_cls:
        mock_event_cls.find_one = AsyncMock(return_value=_event())
        response = client.get("/api/webhook/events/evt-1")

    assert response.status_code == 200
    assert response.json()["repository_url"] == REDACTED_URL


def test_list_events_redacts_repository_url():
    client = _client()
    query = MagicMock()
    query.find.return_value = query
    query.count = AsyncMock(return_value=1)
    query.sort.return_value = query
    query.skip.return_value = query
    query.limit.return_value = query
    query.to_list = AsyncMock(return_value=[_event()])

    with patch("routes.webhook.events.WebhookEvent") as mock_event_cls:
        mock_event_cls.find.return_value = query
        response = client.get("/api/webhook/events")

    assert response.status_code == 200
    assert response.json()["events"][0]["repository_url"] == REDACTED_URL
