"""Tests for AI provider chain configuration and validation."""
from config import Settings


def _settings(**overrides):
    base = dict(
        _env_file=None,
        mongodb_uri="mongodb://localhost:27017/onyx",
        secret_key="test-secret-key-" + "x" * 16,
        ai_provider="auto",
        ai_provider_chain="gemini,groq,openrouter,ollama",
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        gemini_api_key=None,
        gemini_model="gemini-2.5-flash",
        groq_api_key=None,
        groq_model="openai/gpt-oss-120b",
        openrouter_api_key=None,
        openrouter_model="google/gemma-4-27b-it:free",
        ai_local_base_url="http://localhost:11434/v1",
        ai_local_model="qwen2.5-coder:7b",
        ai_rate_limit_rpm=15,
        ai_rate_limit_rpd=500,
        ai_cache_ttl_days=7,
        ai_enrich_top_n=10,
        ai_post_scan_concurrency=2,
    )
    base.update(overrides)
    return Settings(**base)


def test_provider_chain_defaults():
    s = _settings()
    assert s.provider_chain() == ["gemini", "groq", "openrouter", "ollama"]


def test_provider_chain_explicit_single():
    s = _settings(ai_provider="groq")
    assert s.provider_chain() == ["groq"]


def test_configured_chain_filters_missing_keys():
    s = _settings(gemini_api_key="x" * 20)
    assert s.configured_provider_chain() == ["gemini", "ollama"]


def test_configured_chain_appends_legacy_openai_when_unchained():
    s = _settings(openai_api_key="sk-legacy" + "x" * 15)
    assert s.configured_provider_chain() == ["ollama", "openai"]


def test_validate_auto_reports_configured_chain():
    s = _settings(groq_api_key="g" * 20)
    ok, msg = s.validate_ai_config()
    assert ok is True
    assert "groq" in msg
    assert "ollama" in msg


def test_validate_explicit_openai_missing_key():
    s = _settings(ai_provider="openai", openai_api_key=None)
    ok, msg = s.validate_ai_config()
    assert ok is False
    assert "OPENAI_API_KEY" in msg


def test_validate_unknown_provider():
    s = _settings(ai_provider="azure")
    ok, msg = s.validate_ai_config()
    assert ok is False
    assert "Unknown AI provider" in msg


def test_model_defaults_are_current():
    s = _settings()
    assert s.gemini_model == "gemini-2.5-flash"
    assert s.openai_model == "gpt-4o-mini"
    assert s.groq_model == "openai/gpt-oss-120b"
    assert s.openrouter_model == "google/gemma-4-27b-it:free"


def test_governance_defaults():
    s = _settings()
    assert s.ai_rate_limit_rpm == 15
    assert s.ai_rate_limit_rpd == 500
    assert s.ai_cache_ttl_days == 7
    assert s.ai_enrich_top_n == 10
    assert s.ai_post_scan_concurrency == 2


def test_ai_available_single_explicit_provider():
    s = _settings(ai_provider="gemini", gemini_api_key="k" * 20)
    assert s.ai_available is True
    s2 = _settings(ai_provider="gemini", gemini_api_key=None)
    assert s2.ai_available is False
