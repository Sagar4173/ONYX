"""Factory for the unified AI processor."""
import logging

from config import settings

logger = logging.getLogger(__name__)


def create_ai_processor():
    """Create the unified AI processor.

    Provider selection: uses Settings.configured_provider_chain() - for
    ai_provider=auto that is the configured subset of ai_provider_chain
    (legacy OPENAI_API_KEY appended last); for an explicit provider, just it.

    Raises ValueError when no provider in the chain has credentials.
    """
    configured = settings.configured_provider_chain()
    if not configured:
        raise ValueError(
            "No AI provider available. Configure at least one of:\n"
            "  - GEMINI_API_KEY (primary, free tier)\n"
            "  - GROQ_API_KEY / OPENROUTER_API_KEY (free-tier fallbacks)\n"
            "  - OPENAI_API_KEY (legacy fallback)\n"
            "  - AI_PROVIDER=ollama with a running Ollama server"
        )
    logger.info("Creating unified AI processor (chain: %s)", " -> ".join(configured))
    from .ai_processor import VulnerabilityAIProcessor

    return VulnerabilityAIProcessor()
