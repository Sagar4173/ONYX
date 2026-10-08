"""Hybrid retrieval: query sanitizing, RRF, FTS/vector lanes, filters."""
from unittest.mock import AsyncMock, patch

import services.ai.retrieval as ret
from services.ai.knowledge_store import KnowledgeStore
from services.ai.retrieval import build_fts_query, retrieve, retrieve_fts_only, rrf_fuse


def _vec(axis: int, dim: int = 4):
    v = [0.0] * dim
    v[axis] = 1.0
    return v


def _seed_store(tmp_path, with_vectors: bool = True) -> KnowledgeStore:
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize(dim=4 if with_vectors else None)
    rows = [
        {
            "source": "cwe", "source_id": "CWE-79", "title": "XSS",
            "header": "CWE-79: Cross-site scripting",
            "text": "Improper neutralization of input during web page generation enables cross-site scripting.",
            "cwe_id": "CWE-79",
        },
        {
            "source": "cwe", "source_id": "CWE-89", "title": "SQLi",
            "header": "CWE-89: SQL injection",
            "text": "Improper neutralization of special elements used in an SQL command.",
            "cwe_id": "CWE-89",
        },
    ]
    if with_vectors:
        rows[0]["_embedding"] = _vec(0)
        rows[1]["_embedding"] = _vec(1)
    store.add_chunks(rows)
    return store


def test_build_fts_query_sanitizes_hostile_input():
    q = build_fts_query("SQL injection' OR 1=1; -- drop table")
    assert "'" not in q and ";" not in q
    assert '"' in q
    assert " AND " in q
    assert q == build_fts_query("SQL injection' OR 1=1; -- drop table")


def test_build_fts_query_too_short_returns_empty():
    assert build_fts_query("a of to") == ""
    assert build_fts_query("   ") == ""
    assert build_fts_query('""') == ""


def test_build_fts_query_or_mode_and_op_validation():
    assert build_fts_query("sql injection", op="OR") == '"sql" OR "injection"'
    assert build_fts_query("sql injection") == '"sql" AND "injection"'
    try:
        build_fts_query("sql", op="XOR")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid op must raise ValueError")


def test_rrf_fuse_orders_by_consensus():
    fused = rrf_fuse([[1, 2, 3], [1, 2]], k=60)
    assert [cid for cid, _ in fused] == [1, 2, 3]
    assert fused[0][1] > fused[1][1] > fused[2][1]


async def test_hybrid_retrieval_finds_match_via_fts(tmp_path):
    store = _seed_store(tmp_path)
    with patch.object(ret, "embed_query", new=AsyncMock(return_value=None)):
        hits = await retrieve("cross-site scripting neutralization", store=store)
    assert hits
    assert hits[0]["source_id"] == "CWE-79"
    assert hits[0]["rank"] == 1
    assert "score" in hits[0]


async def test_vector_lane_covers_text_mismatch(tmp_path):
    store = _seed_store(tmp_path)
    with patch.object(ret, "embed_query", new=AsyncMock(return_value=_vec(1))):
        hits = await retrieve("zzz unrelated gibberish", store=store)
    assert hits, "vector lane alone must return the nearest chunk"
    assert hits[0]["source_id"] == "CWE-89"


async def test_missing_db_returns_empty(tmp_path):
    store = KnowledgeStore(tmp_path / "missing.db")
    with patch.object(ret, "embed_query", new=AsyncMock(return_value=None)):
        assert await retrieve("anything", store=store) == []
    assert retrieve_fts_only("anything", store=store) == []


def test_fts_only_never_calls_embeddings(tmp_path):
    store = _seed_store(tmp_path)
    with patch.object(ret, "embed_query", new=AsyncMock(side_effect=AssertionError("no embeds"))):
        hits = retrieve_fts_only("sql injection special elements", store=store)
    assert hits and hits[0]["source_id"] == "CWE-89"


def test_realistic_nl_query_finds_match_via_or_fallback(tmp_path):
    store = _seed_store(tmp_path)
    hits = retrieve_fts_only("How do I fix SQL injection in my login form?", store=store)
    assert hits, "natural-language query must fall back to OR and match"
    assert hits[0]["source_id"] == "CWE-89"


def test_cwe_filter_is_strict(tmp_path):
    store = _seed_store(tmp_path)
    hits = retrieve_fts_only("improper neutralization", cwe_id="CWE-79", store=store)
    assert hits
    assert all(h["cwe_id"] == "CWE-79" for h in hits)
    assert retrieve_fts_only("improper neutralization", cwe_id="CWE-404", store=store) == []


async def test_hung_query_embedding_times_out_and_degrades(tmp_path):
    import asyncio
    import time as _time

    store = _seed_store(tmp_path)

    async def slow_embed(_text):
        await asyncio.sleep(2)
        return _vec(0)

    with (
        patch.object(ret, "embed_query", new=slow_embed),
        patch.object(ret, "_QUERY_TIMEOUT_S", 0.05),
    ):
        start = _time.monotonic()
        hits = await retrieve("cross-site scripting neutralization", store=store)
        elapsed = _time.monotonic() - start
    assert isinstance(hits, list)
    assert elapsed < 1.0, f"retrieve waited {elapsed:.2f}s for a hung embedding lane"
