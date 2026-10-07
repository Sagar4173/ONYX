"""AI chat calls go through the LLM gateway."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from config import settings
from routes.ai_chat import _call_ai_chat, _get_active_model
from services.ai.gateway import GatewayError, GatewayResult


class FakeGateway:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete_messages(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="fake-1",
            usage={}, latency_ms=1,
        )


async def test_builds_messages_and_calls_gateway():
    gw = FakeGateway(text="Use parameterized queries.")
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        out = await _call_ai_chat(
            message="how do I fix SQLi?",
            scan_context={"project_name": "demo", "total_findings": 3},
            conversation_history=history,
        )
    assert out == "Use parameterized queries."
    call = gw.calls[0]
    assert call["purpose"] == "chat"
    assert call["max_tokens"] == 1500
    assert call["temperature"] == 0.3
    msgs = call["messages"]
    assert msgs[0]["role"] == "system"
    assert "ONYX Security AI" in msgs[0]["content"]
    assert "## Current Scan Context" in msgs[0]["content"]
    assert '"total_findings": 3' in msgs[0]["content"]
    assert msgs[1] == {"role": "user", "content": "hi"}
    assert msgs[2] == {"role": "assistant", "content": "hello"}
    assert msgs[-1] == {"role": "user", "content": "how do I fix SQLi?"}


async def test_history_capped_at_10_and_roles_sanitized():
    gw = FakeGateway(text="ok")
    history = [{"role": "system", "content": f"m{i}"} for i in range(15)]
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        await _call_ai_chat(message="q", scan_context={}, conversation_history=history)
    msgs = gw.calls[0]["messages"]
    # 1 system + 10 capped history + 1 user
    assert len(msgs) == 12
    assert all(m["role"] == "user" for m in msgs[1:-1])
    assert msgs[-1] == {"role": "user", "content": "q"}


async def test_gateway_error_raises_503_with_generic_detail():
    gw = FakeGateway(error=GatewayError("All AI providers failed: gemini: 401 INVALID_API_KEY sk-secret"))
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        with pytest.raises(HTTPException) as exc:
            await _call_ai_chat(message="q", scan_context={})
    assert exc.value.status_code == 503
    assert "temporarily unavailable" in exc.value.detail
    assert "sk-secret" not in exc.value.detail
    assert "gemini" not in exc.value.detail


async def test_no_history_still_calls_user_message():
    gw = FakeGateway(text="reply")
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        out = await _call_ai_chat(message="only question", scan_context={"a": 1})
    assert out == "reply"
    assert len(gw.calls[0]["messages"]) == 2


def test_get_active_model_first_configured(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini,groq")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "groq_api_key", "k" * 20)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash")
    assert _get_active_model() == "gemini/gemini-2.5-flash"


def test_get_active_model_unavailable_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)
    assert _get_active_model() == "unavailable"
