"""Triage AI calls go through the LLM gateway."""
from unittest.mock import patch

from services.ai.gateway import GatewayError, GatewayResult
from services.triage.triage_service import TriageService


class FakeGateway:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="fake-1",
            usage={}, latency_ms=1,
        )


async def test_call_ai_returns_gateway_text():
    gw = FakeGateway(text="Executive summary text")
    with patch("services.triage.triage_service.get_gateway", return_value=gw):
        out = await TriageService()._call_ai("rate this scan")
    assert out == "Executive summary text"
    assert gw.calls[0]["purpose"] == "triage"
    assert gw.calls[0]["temperature"] == 0.3
    assert "cybersecurity expert" in gw.calls[0]["system"]
    assert gw.calls[0]["user"] == "rate this scan"


async def test_call_ai_gateway_error_returns_none():
    gw = FakeGateway(error=GatewayError("All AI providers failed"))
    with patch("services.triage.triage_service.get_gateway", return_value=gw):
        assert await TriageService()._call_ai("p") is None


async def test_call_ai_unexpected_error_returns_none():
    gw = FakeGateway(error=RuntimeError("boom"))
    with patch("services.triage.triage_service.get_gateway", return_value=gw):
        assert await TriageService()._call_ai("p") is None


def test_legacy_httpx_client_removed():
    service = TriageService()
    assert not hasattr(TriageService, "_ensure_ai_client")
    assert not hasattr(service, "_ai_http_client")
    assert not hasattr(service, "_ai_client_initialized")
