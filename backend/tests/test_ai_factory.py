"""Tests for the AI processor factory and package exports."""
import pytest

from config import settings


def test_create_returns_unified_processor(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini,groq")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "groq_api_key", "k" * 20)
    monkeypatch.setattr(settings, "openai_api_key", None)

    from services.ai.factory import create_ai_processor
    from services.ai.ai_processor import VulnerabilityAIProcessor

    processor = create_ai_processor()
    assert isinstance(processor, VulnerabilityAIProcessor)


def test_create_raises_when_explicit_provider_lacks_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)

    from services.ai.factory import create_ai_processor

    with pytest.raises(ValueError, match="No AI provider available"):
        create_ai_processor()


def test_create_raises_when_chain_unusable(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)

    from services.ai.factory import create_ai_processor

    with pytest.raises(ValueError, match="No AI provider available"):
        create_ai_processor()


def test_package_exports():
    from services.ai import AIProcessorError, get_ai_processor

    assert callable(get_ai_processor)
    assert issubclass(AIProcessorError, Exception)


def test_get_ai_processor_uses_factory(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "openai_api_key", None)

    import services.ai.ai_processor as mod

    monkeypatch.setattr(mod, "_ai_processor", None)
    from services.ai.ai_processor import get_ai_processor

    processor = get_ai_processor()
    from services.ai.ai_processor import VulnerabilityAIProcessor

    assert isinstance(processor, VulnerabilityAIProcessor)
