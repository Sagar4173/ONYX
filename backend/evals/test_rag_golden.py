r"""Golden retrieval evals - FTS-only, deterministic, offline.

Run: .venv\Scripts\python.exe -m pytest evals/ -v -m eval
"""
import asyncio

import pytest

from services.ai.ingest import build
from services.ai.knowledge_store import KnowledgeStore
from services.ai.retrieval import retrieve_fts_only

pytestmark = pytest.mark.eval

# (query, [acceptable top-level source_ids], window for recall metric)
GOLDEN_PAIRS = [
    ("hard-coded credentials", ["CWE-798"], 1),
    ("cross-site scripting content security policy", ["CWE-79"], 1),
    ("deserialization untrusted data yaml safe loaders", ["CWE-502"], 1),
    ("server-side request forgery allow-list outbound destinations", ["CWE-918"], 1),
    ("broken access control deny by default", ["owasp-a01"], 1),
    ("parameterized queries SQL database", ["CWE-89", "snip-sql_injection-python"], 2),
    ("authentication critical function deny-by-default", ["CWE-306"], 1),
]

CWE_FILTER_CASE = ("input validation schemas malformed data", "CWE-1176")

# Realistic phrasing a user would actually type (exercises the OR fallback).
NATURAL_LANGUAGE_CASES = [
    ("How do I fix SQL injection in my login form?", "CWE-89"),
    ("what is cross-site scripting and how can I prevent it?", "CWE-79"),
    ("why am I getting a hard-coded credentials finding", "CWE-798"),
]

# Exact shape produced by ai_processor._lookup_guidance (cwe_id + rule_id + title).
GUIDANCE_QUERY_CASES = [
    ("CWE-89 SQL Injection in login handler", "CWE-89"),
    ("CWE-798 Use of Hard-coded Credentials", "CWE-798"),
    ("CWE-918 Server-side request forgery in webhook handler", "CWE-918"),
]


@pytest.fixture(scope="module")
def eval_store(tmp_path_factory):
    db = tmp_path_factory.mktemp("rag-eval") / "knowledge.db"
    asyncio.run(build(db_path=db, embed=False))
    store = KnowledgeStore(db)
    assert store.chunk_count() > 0, "corpus build produced no chunks"
    return store


def test_recall_at_window(eval_store):
    misses = []
    for query, accepted, window in GOLDEN_PAIRS:
        hits = retrieve_fts_only(query, top_k=max(window, 5), store=eval_store)
        got = [h["source_id"] for h in hits[:window]]
        if not any(source_id in got for source_id in accepted):
            misses.append((query, got))
    assert not misses, f"recall@window failed for: {misses}"


def test_anchor_queries_rank_expected_doc_first(eval_store):
    for query, accepted, window in GOLDEN_PAIRS:
        if window != 1:
            continue
        hits = retrieve_fts_only(query, top_k=5, store=eval_store)
        assert hits, f"no results for {query!r}"
        assert hits[0]["source_id"] == accepted[0], (
            f"{query!r} -> rank1 {hits[0]['source_id']}, expected {accepted[0]}; "
            f"top5: {[h['source_id'] for h in hits]}"
        )


def test_cwe_filter_returns_only_requested_cwe(eval_store):
    query, cwe_id = CWE_FILTER_CASE
    hits = retrieve_fts_only(query, top_k=10, cwe_id=cwe_id, store=eval_store)
    assert hits, "filter too strict: no candidates"
    assert all(h["cwe_id"] == cwe_id for h in hits)
    assert hits[0]["source_id"] == cwe_id


def test_hostile_query_is_safe_and_does_not_drop_rows(eval_store):
    before = eval_store.chunk_count()
    for hostile in ("'; DROP TABLE chunks; --", 'x" OR 1=1 --', "(((((", "***"):
        result = retrieve_fts_only(hostile, top_k=5, store=eval_store)
        assert isinstance(result, list)
    assert eval_store.chunk_count() == before
    assert retrieve_fts_only("", store=eval_store) == []


def test_natural_language_queries_return_results(eval_store):
    for query, expected in NATURAL_LANGUAGE_CASES:
        hits = retrieve_fts_only(query, top_k=5, store=eval_store)
        assert hits, f"no results for natural-language query {query!r}"
        got = [h["source_id"] for h in hits]
        assert expected in got, (
            f"{query!r} -> top5 {got}, expected {expected} among them"
        )


def test_realistic_guidance_queries_rank_expected_doc_in_top3(eval_store):
    for query, expected in GUIDANCE_QUERY_CASES:
        hits = retrieve_fts_only(query, top_k=3, store=eval_store)
        got = [h["source_id"] for h in hits]
        assert expected in got, (
            f"{query!r} -> top3 {got}, expected {expected} (lookup_guidance uses top_k=3)"
        )
