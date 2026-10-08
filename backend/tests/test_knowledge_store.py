"""knowledge.db: schema, FTS5, vec0, embedding cache."""
from services.ai.knowledge_store import KnowledgeStore


def _row(i: int, **over):
    base = {
        "source": "cwe",
        "source_id": f"CWE-{100 + i}",
        "title": f"Example weakness {i}",
        "text": f"Example body {i} about injection and configuration.",
        "header": f"CWE-{100 + i}: Example weakness {i}",
        "cwe_id": f"CWE-{100 + i}",
    }
    base.update(over)
    return base


def _vec(seed: int, dim: int = 4):
    # near-orthogonal one-hots so nearest-neighbor is deterministic
    v = [0.0] * dim
    v[seed % dim] = 1.0
    return v


def test_initialize_creates_schema(tmp_path):
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize(dim=4)
    assert store.chunk_count() == 0
    assert store.has_vectors() is False
    assert store.get_meta("schema_version") is None


def test_add_chunks_with_and_without_vectors(tmp_path):
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize(dim=4)
    ids = store.add_chunks([
        {**_row(0), "_embedding": _vec(0)},
        _row(1),
    ])
    assert len(ids) == 2
    assert store.chunk_count() == 2
    assert store.has_vectors() is True


def test_fts_search_ranks_matching_chunk_first(tmp_path):
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize(dim=4)
    store.add_chunks([
        _row(0, text="completely unrelated gardening advice", header="x gardening"),
        _row(1, text="sql injection allows attackers to alter queries", header="y injection"),
    ])
    hits = store.search_fts("injection", limit=5)
    assert hits
    assert hits[0][0] == 2  # chunk_ids are 1-based rowids: second chunk


def test_vector_search_returns_nearest(tmp_path):
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize(dim=4)
    store.add_chunks([
        {**_row(0), "_embedding": _vec(0)},  # matches axis 0
        {**_row(1), "_embedding": _vec(1)},  # matches axis 1
    ])
    hits = store.search_vec(_vec(1), limit=2)
    assert hits[0][0] == 2  # nearest to axis-1 vector is chunk 2


def test_search_on_missing_db_returns_empty(tmp_path):
    store = KnowledgeStore(tmp_path / "missing.db")
    assert store.search_fts("anything", limit=5) == []
    assert store.search_vec([0.0, 0.0], limit=5) == []
    assert store.chunk_count() == 0
    assert store.has_vectors() is False


def test_embedding_cache_roundtrip(tmp_path):
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize()
    assert store.get_cached_embedding("h1") is None
    store.put_cached_embedding("h1", "gemini-embedding-2", 4, [0.1, 0.2, 0.3, 0.4])
    assert store.get_cached_embedding("h1") == [0.1, 0.2, 0.3, 0.4]
    store.put_cached_embedding("h1", "gemini-embedding-2", 4, [9.0, 9.0, 9.0, 9.0])
    assert store.get_cached_embedding("h1") == [9.0, 9.0, 9.0, 9.0]


def test_reset_clears_everything(tmp_path):
    store = KnowledgeStore(tmp_path / "k.db")
    store.initialize(dim=4)
    store.add_chunks([{**_row(0), "_embedding": _vec(0)}])
    store.set_meta("dim", "4")
    store.put_cached_embedding("keep-me", "model", 4, [1.0, 0.0, 0.0, 0.0])
    store.reset()
    assert store.chunk_count() == 0
    assert store.has_vectors() is False
    assert store.get_meta("dim") is None
    assert store.get_cached_embedding("keep-me") == [1.0, 0.0, 0.0, 0.0]  # cache survives
    store.initialize(dim=4)  # schema can be recreated after reset
    assert store.chunk_count() == 0
