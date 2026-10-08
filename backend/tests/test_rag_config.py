"""Phase 2 config + sqlite capability."""
from config import Settings, settings


def _settings(**overrides):
    base = dict(
        _env_file=None,
        mongodb_uri="mongodb://localhost:27017/onyx",
        secret_key="test-secret-key-" + "x" * 16,
    )
    base.update(overrides)
    return Settings(**base)


def test_rag_settings_defaults():
    s = _settings()
    assert s.knowledge_db_path == "data/knowledge.db"
    assert s.ai_embed_model == "gemini-embedding-2"
    assert s.ai_embed_local_model == "nomic-embed-text"
    assert s.ai_embed_dimensions == 768
    assert s.ai_embed_batch_size == 16
    assert s.rag_top_k == 6
    assert s.rag_rrf_k == 60
    assert s.rag_max_context_chars == 6000


def test_settings_instance_exposes_rag_fields():
    assert settings.knowledge_db_path.endswith("knowledge.db")
    assert settings.rag_top_k >= 1


def test_sqlite_supports_fts5_and_vec0():
    import sqlite3

    import sqlite_vec

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute("CREATE VIRTUAL TABLE v USING vec0(embedding float[8])")
        version = conn.execute("SELECT vec_version()").fetchone()[0]
        assert version
    finally:
        conn.close()
