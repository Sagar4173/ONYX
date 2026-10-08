"""Embedding provider chain (Gemini -> Ollama)."""
from unittest.mock import patch

import pytest

import services.ai.embeddings as emb
from services.ai.embeddings import EmbeddingError, embed_query, embed_texts


def _vec(seed: int, dim: int = 8):
    return [round(((seed + i) % 7) / 7.0, 4) for i in range(dim)]


class FakeLane:
    """Returns one dim-8 vector per text; deterministic from index+length."""

    def __init__(self, error=None, dim=8):
        self.error = error
        self.dim = dim
        self.calls = []

    async def embed(self, texts):
        self.calls.append(list(texts))
        if self.error is not None:
            raise self.error
        return [_vec(len(t) + i, self.dim) for i, t in enumerate(texts)]


async def test_empty_input_returns_empty_without_provider_calls():
    assert await embed_texts([]) == []


async def test_batches_are_split_and_joined():
    lane = FakeLane()
    with (
        patch.object(emb.settings, "ai_embed_batch_size", 4),
        patch.object(emb.settings, "ai_embed_dimensions", 8),
        patch.object(emb, "_gemini_lane", return_value=lane),
    ):
        out = await embed_texts([f"t{i}" for i in range(10)])
    assert len(out) == 10
    assert all(len(v) == 8 for v in out)
    assert [len(c) for c in lane.calls] == [4, 4, 2]


async def test_falls_back_to_ollama_when_gemini_fails():
    g = FakeLane(error=RuntimeError("403 quota"))
    o = FakeLane()
    with (
        patch.object(emb.settings, "ai_embed_dimensions", 8),
        patch.object(emb, "_gemini_lane", return_value=g),
        patch.object(emb, "_ollama_lane", return_value=o),
    ):
        out = await embed_texts(["hello"])
    assert len(out) == 1 and len(out[0]) == 8
    assert o.calls == [["hello"]]


async def test_both_lanes_fail_raises_scrubbed_error():
    g = FakeLane(error=RuntimeError("401 sk-abc123ABC456def7890"))
    o = FakeLane(error=ConnectionError("refused"))
    with (
        patch.object(emb, "_gemini_lane", return_value=g),
        patch.object(emb, "_ollama_lane", return_value=o),
    ):
        with pytest.raises(EmbeddingError) as exc:
            await embed_texts(["hello"])
    assert "sk-abc123ABC456def7890" not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


async def test_wrong_dimension_counts_as_lane_failure():
    g = FakeLane(dim=3)  # dim 3 != configured 8
    o = FakeLane(dim=8)
    with (
        patch.object(emb.settings, "ai_embed_dimensions", 8),
        patch.object(emb, "_gemini_lane", return_value=g),
        patch.object(emb, "_ollama_lane", return_value=o),
    ):
        out = await embed_texts(["hello"])
    assert len(out[0]) == 8


async def test_embed_query_never_raises():
    g = FakeLane(error=RuntimeError("down"))
    o = FakeLane(error=ConnectionError("down"))
    with (
        patch.object(emb, "_gemini_lane", return_value=g),
        patch.object(emb, "_ollama_lane", return_value=o),
    ):
        assert await embed_query("q") is None


async def test_embed_query_returns_vector():
    g = FakeLane()
    with (
        patch.object(emb.settings, "ai_embed_dimensions", 8),
        patch.object(emb, "_gemini_lane", return_value=g),
    ):
        out = await embed_query("q")
    assert out is not None and len(out) == 8
