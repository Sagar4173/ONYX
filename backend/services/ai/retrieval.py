"""Hybrid retrieval: FTS5 BM25 + vec0 kNN fused with Reciprocal Rank Fusion.

FTS queries are sanitized to quoted AND-terms so untrusted chat input can
never trigger FTS5 syntax errors. A natural-language question rarely has every
term present in one chunk, so an empty AND result is retried as an OR query
(bm25 still ranks multi-term matches first). Vector lane activates only when
the knowledge db has vectors and embed_query() succeeds; otherwise retrieval
silently degrades to FTS-only.
"""
import asyncio
import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from config import settings
from services.ai.embeddings import embed_query
from services.ai.knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)

_TERM_RE = re.compile(r"[A-Za-z0-9_+#]{3,}")
_MAX_TERMS = 12
_CANDIDATE_FACTOR = 4
_FTS_OPS = ("AND", "OR")
_QUERY_TIMEOUT_S = 8.0


def build_fts_query(text: str, *, op: str = "AND") -> str:
    if op not in _FTS_OPS:
        raise ValueError(f"unsupported FTS op: {op!r}")
    terms: List[str] = []
    seen: set = set()
    for match in _TERM_RE.finditer(text or ""):
        term = match.group(0)
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        terms.append(term)
        if len(terms) >= _MAX_TERMS:
            break
    return f" {op} ".join(f'"{t}"' for t in terms)


def _fts_search(
    store: KnowledgeStore, query: str, limit: int
) -> List[Tuple[int, float]]:
    match = build_fts_query(query)
    if not match:
        return []
    hits = store.search_fts(match, limit=limit)
    if hits:
        return hits
    fallback = build_fts_query(query, op="OR")
    if fallback != match:
        hits = store.search_fts(fallback, limit=limit)
    return hits


def rrf_fuse(rankings: List[List[int]], k: int) -> List[Tuple[int, float]]:
    scores: Dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[int(chunk_id)] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def _hydrate_fused(
    fused: List[Tuple[int, float]],
    store: KnowledgeStore,
    top_k: int,
    cwe_id: Optional[str],
) -> List[Dict]:
    if not fused:
        return []
    chunks = store.hydrate([cid for cid, _ in fused])
    by_id = {c["chunk_id"]: c for c in chunks}
    results: List[Dict] = []
    for chunk_id, score in fused:
        chunk = by_id.get(chunk_id)
        if chunk is None:
            continue
        if cwe_id is not None and chunk.get("cwe_id") != cwe_id:
            continue
        results.append({**chunk, "score": round(score, 6), "rank": len(results) + 1})
        if len(results) >= top_k:
            break
    return results


def retrieve_fts_only(
    query: str,
    *,
    top_k: Optional[int] = None,
    cwe_id: Optional[str] = None,
    store: Optional[KnowledgeStore] = None,
) -> List[Dict]:
    top_k = top_k or settings.rag_top_k
    store = store or KnowledgeStore()
    if not store.exists():
        return []
    hits = _fts_search(store, query, top_k * _CANDIDATE_FACTOR)
    fused = rrf_fuse([[cid for cid, _ in hits]], k=settings.rag_rrf_k)
    return _hydrate_fused(fused, store, top_k, cwe_id)


async def retrieve(
    query: str,
    *,
    top_k: Optional[int] = None,
    cwe_id: Optional[str] = None,
    store: Optional[KnowledgeStore] = None,
) -> List[Dict]:
    top_k = top_k or settings.rag_top_k
    store = store or KnowledgeStore()
    if not query or not query.strip() or not store.exists():
        return []

    rankings: List[List[int]] = []

    fts_hits = _fts_search(store, query, top_k * _CANDIDATE_FACTOR)
    if fts_hits:
        rankings.append([cid for cid, _ in fts_hits])

    if store.has_vectors():
        try:
            vector = await asyncio.wait_for(
                embed_query(query), timeout=_QUERY_TIMEOUT_S
            )
        except Exception as e:  # noqa: BLE001 - hung or failed embedding must not stall chat
            logger.debug("Query embedding timed out/failed (FTS-only): %s", e)
            vector = None
        if vector is not None:
            vec_hits = store.search_vec(vector, limit=top_k * _CANDIDATE_FACTOR)
            rankings.append([cid for cid, _ in vec_hits])
        else:
            logger.debug("Vector lane skipped: query embedding unavailable")

    fused = rrf_fuse(rankings, k=settings.rag_rrf_k)
    return _hydrate_fused(fused, store, top_k, cwe_id)
