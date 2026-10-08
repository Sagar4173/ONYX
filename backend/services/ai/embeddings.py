"""Embedding chain for Phase 2 RAG: Gemini free tier -> Ollama local.

embed_texts() batches and raises EmbeddingError (scrubbed) when every lane
fails or returns wrong-dimension vectors. embed_query() never raises.
"""
import asyncio
import logging
from typing import List, Optional

from config import settings
from services.ai.gateway import _scrub

logger = logging.getLogger(__name__)

_LANE_TIMEOUT_S = 10.0


class EmbeddingError(Exception):
    """No embedding lane produced usable vectors."""


class GeminiLane:
    """google-genai embed_content, batched."""

    def __init__(self, model: str, dimensions: int, api_key: str):
        self.model = model
        self.dimensions = dimensions
        self.api_key = api_key

    async def embed(self, texts: List[str]) -> List[List[float]]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        resp = await client.aio.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=self.dimensions),
        )
        return [list(e.values) for e in resp.embeddings]


class OllamaLane:
    """OpenAI-compatible embeddings endpoint served by Ollama."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(base_url=self.base_url, api_key="ollama", max_retries=0)
        resp = await client.embeddings.create(model=self.model, input=texts)
        data = sorted(resp.data, key=lambda d: d.index)
        return [list(d.embedding) for d in data]


def _gemini_lane():
    if not settings.gemini_api_key:
        return None
    return GeminiLane(
        model=settings.ai_embed_model,
        dimensions=settings.ai_embed_dimensions,
        api_key=settings.gemini_api_key,
    )


def _ollama_lane():
    if not settings.ai_local_base_url:
        return None
    return OllamaLane(base_url=settings.ai_local_base_url, model=settings.ai_embed_local_model)


async def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    dim = settings.ai_embed_dimensions
    batch_size = max(1, settings.ai_embed_batch_size)
    errors: List[str] = []
    lanes = [lane for lane in (_gemini_lane(), _ollama_lane()) if lane is not None]
    if not lanes:
        raise EmbeddingError("no embedding provider configured")

    for lane in lanes:
        try:
            vectors: List[List[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                got = await asyncio.wait_for(lane.embed(batch), timeout=_LANE_TIMEOUT_S)
                if len(got) != len(batch):
                    raise EmbeddingError(
                        f"{type(lane).__name__} returned {len(got)} vectors for {len(batch)} texts"
                    )
                vectors.extend(got)
            if any(len(v) != dim for v in vectors):
                raise EmbeddingError(
                    f"{type(lane).__name__} returned dim {len(vectors[0])}, expected {dim}"
                )
            return vectors
        except Exception as e:  # noqa: BLE001 - lane isolation by design
            errors.append(f"{type(lane).__name__}: {e}")
            logger.warning("Embedding lane %s failed: %s", type(lane).__name__, _scrub(str(e)))
    raise EmbeddingError(_scrub(" | ".join(errors)))


async def embed_query(text: str) -> Optional[List[float]]:
    try:
        vectors = await embed_texts([text])
        return vectors[0] if vectors else None
    except Exception as e:  # noqa: BLE001 - queries degrade to FTS-only upstream
        logger.info("Query embedding unavailable (FTS-only fallback): %s", e)
        return None
