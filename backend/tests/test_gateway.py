"""Tests for the LLM gateway: failover, rate limits, circuit breaker, cache, structured output."""
import json
import time

import pytest

from config import settings
from services.ai.gateway import (
    GatewayError,
    LLMGateway,
    complete_structured,
    get_gateway,
    reset_gateway,
)
from services.ai.schemas import AnalysisNarrative
from services.ai.stores import QuotaLedger, ResponseCache
from services.ai.trace import InvocationTracer

VALID_NARRATIVE = {
    "executive_summary": "Summary text",
    "risk_assessment": "Assessment text",
    "priority_findings": ["SQL Injection"],
    "recommendations": ["Use parameterized queries"],
    "secure_code_examples": {},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated scanners"],
}


@pytest.fixture
def gw_settings(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini,groq")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "groq_api_key", "k" * 20)
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "ai_rate_limit_rpm", 15)
    monkeypatch.setattr(settings, "ai_rate_limit_rpd", 500)
    return settings


def _gateway(adapters, quota=None, cache=None, tracer=None):
    if quota is None:
        quota = QuotaLedger(db=None)
        quota._db_disabled = True
    if cache is None:
        cache = ResponseCache(db=None)
        cache._db_disabled = True
    if tracer is None:
        tracer = InvocationTracer(db=None)
        tracer._db_disabled = True
    return LLMGateway(adapters=adapters, quota=quota, cache=cache, tracer=tracer)


async def test_failover_to_second_provider(gw_settings):
    calls = []

    async def fail_gemini(spec, messages, max_tokens, temperature, json_mode):
        calls.append(spec.name)
        raise RuntimeError("gemini down")

    async def ok_groq(spec, messages, max_tokens, temperature, json_mode):
        calls.append(spec.name)
        return '{"ok": true}', {"prompt_tokens": 1, "completion_tokens": 1}

    gw = _gateway({"gemini": fail_gemini, "groq": ok_groq})
    result = await gw.complete(system="sys", user="usr", purpose="analysis")
    assert result.provider == "groq"
    assert result.text == '{"ok": true}'
    assert calls == ["gemini", "groq"]


async def test_all_providers_fail_raises_with_details(gw_settings):
    async def boom(spec, messages, max_tokens, temperature, json_mode):
        raise RuntimeError(f"{spec.name} exploded")

    gw = _gateway({"gemini": boom, "groq": boom})
    with pytest.raises(GatewayError) as excinfo:
        await gw.complete(system="s", user="u", purpose="analysis")
    msg = str(excinfo.value)
    assert "gemini" in msg and "groq" in msg


async def test_no_configured_provider_raises(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "groq_api_key", None)
    gw = _gateway({})
    with pytest.raises(GatewayError, match="No AI provider configured"):
        await gw.complete(system="s", user="u", purpose="analysis")


async def test_rate_limit_blocks_second_call(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    monkeypatch.setattr(settings, "ai_rate_limit_rpm", 1)

    async def ok(spec, messages, max_tokens, temperature, json_mode):
        return "ok", {}

    gw = _gateway({"gemini": ok})
    first = await gw.complete(system="s", user="u", purpose="chat")
    assert first.text == "ok"
    with pytest.raises(GatewayError, match="rate limit"):
        await gw.complete(system="s", user="u", purpose="chat")


async def test_circuit_opens_after_three_failures(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    calls = 0

    async def always_fail(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        calls += 1
        raise RuntimeError("nope")

    gw = _gateway({"gemini": always_fail})
    for _ in range(3):
        with pytest.raises(GatewayError):
            await gw.complete(system="s", user="u", purpose="analysis")
    assert calls == 3
    with pytest.raises(GatewayError, match="circuit"):
        await gw.complete(system="s", user="u", purpose="analysis")
    assert calls == 3  # circuit open: adapter not invoked again


async def test_cache_hit_skips_adapter(gw_settings):
    calls = 0

    async def counting(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        calls += 1
        return '{"a": 1}', {}

    gw = _gateway({"gemini": counting})
    r1 = await gw.complete(system="s", user="u", purpose="remediation", use_cache=True)
    r2 = await gw.complete(system="s", user="u", purpose="remediation", use_cache=True)
    assert r1.cached is False
    assert r2.cached is True
    assert r2.text == r1.text
    assert calls == 1


async def test_quota_exhausted_blocks_provider(gw_settings):
    class DenyQuota:
        async def try_consume(self, provider):
            return False

        def remaining(self, provider):
            return 0

    async def ok(spec, messages, max_tokens, temperature, json_mode):
        return "ok", {}

    gw = _gateway({"gemini": ok}, quota=DenyQuota())
    with pytest.raises(GatewayError, match="quota"):
        await gw.complete(system="s", user="u", purpose="analysis")


async def test_json_schema_enables_json_mode(gw_settings):
    seen = {}

    async def capture(spec, messages, max_tokens, temperature, json_mode):
        seen["json_mode"] = json_mode
        return '{"a": 1}', {}

    gw = _gateway({"gemini": capture})
    await gw.complete(system="s", user="u", purpose="analysis")
    assert seen["json_mode"] is False
    await gw.complete(system="s", user="u", purpose="analysis", json_schema=AnalysisNarrative)
    assert seen["json_mode"] is True


async def test_complete_messages_passes_messages_verbatim(gw_settings):
    captured = {}

    async def capture(spec, messages, max_tokens, temperature, json_mode):
        captured["messages"] = messages
        return "ok", {}

    gw = _gateway({"gemini": capture})
    msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "u1"}]
    await gw.complete_messages(messages=msgs, purpose="chat")
    assert captured["messages"] == msgs


async def test_complete_structured_parses_valid_json(gw_settings):
    async def returns_narrative(spec, messages, max_tokens, temperature, json_mode):
        return json.dumps(VALID_NARRATIVE), {}

    gw = _gateway({"gemini": returns_narrative})
    parsed, result = await complete_structured(
        gw, system="s", user="u", purpose="analysis", schema=AnalysisNarrative
    )
    assert parsed is not None
    assert parsed.executive_summary == "Summary text"
    assert result.provider == "gemini"


async def test_complete_structured_retries_invalid_json_once(gw_settings):
    texts = iter(["definitely not json", json.dumps(VALID_NARRATIVE)])

    async def two_responses(spec, messages, max_tokens, temperature, json_mode):
        return next(texts), {}

    gw = _gateway({"gemini": two_responses})
    parsed, _ = await complete_structured(
        gw, system="s", user="u", purpose="analysis", schema=AnalysisNarrative
    )
    assert parsed is not None


async def test_complete_structured_gives_up_returns_none(gw_settings):
    async def always_bad(spec, messages, max_tokens, temperature, json_mode):
        return "garbage", {}

    gw = _gateway({"gemini": always_bad})
    parsed, result = await complete_structured(
        gw, system="s", user="u", purpose="analysis", schema=AnalysisNarrative, retries=1
    )
    assert parsed is None
    assert result.text == "garbage"


def test_get_gateway_singleton():
    reset_gateway()
    a = get_gateway()
    b = get_gateway()
    assert a is b
    reset_gateway()


async def test_structured_cache_heals_after_parse_failure(gw_settings):
    responses = ["garbage", json.dumps(VALID_NARRATIVE), json.dumps(VALID_NARRATIVE)]
    calls = 0

    async def adapter(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        text = responses[calls]
        calls += 1
        return text, {}

    gw = _gateway({"gemini": adapter})
    parsed1, result1 = await complete_structured(
        gw, system="s", user="u", purpose="analysis",
        schema=AnalysisNarrative, use_cache=True,
    )
    assert parsed1 is not None
    assert result1.cached is False
    assert calls == 2  # garbage attempt + retry; garbage must NOT have been cached
    parsed2, result2 = await complete_structured(
        gw, system="s", user="u", purpose="analysis",
        schema=AnalysisNarrative, use_cache=True,
    )
    assert parsed2 is not None
    assert result2.cached is True
    assert calls == 2  # validated response was cached under the original key


async def test_cache_key_includes_model_name(gw_settings, monkeypatch):
    calls = 0

    async def counting(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        calls += 1
        return "{}", {}

    gw = _gateway({"gemini": counting})
    await gw.complete(system="s", user="u", purpose="keytest", use_cache=True)
    monkeypatch.setattr(settings, "gemini_model", "totally-different-model")
    await gw.complete(system="s", user="u", purpose="keytest", use_cache=True)
    assert calls == 2  # model change must invalidate the cached response


async def test_url_userinfo_is_scrubbed(gw_settings):
    async def leaky(spec, messages, max_tokens, temperature, json_mode):
        raise RuntimeError(
            "clone failed: https://ghp_secret1234567890@github.com/owner/repo.git"
        )

    gw = _gateway({"gemini": leaky})
    with pytest.raises(GatewayError) as excinfo:
        await gw.complete(system="s", user="u", purpose="analysis")

    msg = str(excinfo.value)
    assert "ghp_secret1234567890" not in msg
    assert "https://[REDACTED]@github.com/owner/repo.git" in msg


async def test_error_strings_are_scrubbed(gw_settings):
    async def leaky(spec, messages, max_tokens, temperature, json_mode):
        raise RuntimeError("401 Bearer sk-abc1234567890DEF authorization failed")

    gw = _gateway({"gemini": leaky})
    with pytest.raises(GatewayError) as excinfo:
        await gw.complete(system="s", user="u", purpose="analysis")
    msg = str(excinfo.value)
    assert "sk-abc1234567890DEF" not in msg
    assert "REDACTED" in msg
    recent = gw._tracer.recent()
    assert "sk-abc1234567890DEF" not in recent[0].get("error", "")
    assert len(msg) < 1000  # bounded error message


async def test_circuit_cools_down_and_resets_counter(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    calls = 0

    async def always_fail(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        calls += 1
        raise RuntimeError("nope")

    gw = _gateway({"gemini": always_fail})
    for _ in range(3):
        with pytest.raises(GatewayError):
            await gw.complete(system="s", user="u", purpose="analysis")
    assert gw._failures["gemini"] == 3
    assert calls == 3
    gw._open_until["gemini"] = time.monotonic() - 1  # simulate cooldown expiry
    with pytest.raises(GatewayError):
        await gw.complete(system="s", user="u", purpose="analysis")
    assert calls == 4  # half-open probe ran
    assert gw._failures["gemini"] == 1  # counter was reset before the probe
