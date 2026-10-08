"""knowledge.db - one SQLite file: chunks + vec0 vectors + FTS5 + meta + embed cache.

All read methods swallow errors and return empty results: a missing or
corrupt knowledge DB must never break a request (Phase 2 global constraint).
Writes raise normally (ingest path only).
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import settings

logger = logging.getLogger(__name__)

_CHUNK_COLS = (
    "source, source_id, title, text, header, "
    "cwe_id, severity, language, vuln_class"
)
_OPTIONAL = ("cwe_id", "severity", "language", "vuln_class")
_EMBED_CACHE_DDL = (
    "CREATE TABLE IF NOT EXISTS embed_cache ("
    "text_hash TEXT PRIMARY KEY, model TEXT NOT NULL, "
    "dim INTEGER NOT NULL, embedding TEXT NOT NULL)"
)


class KnowledgeStore:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path or settings.knowledge_db_path)

    # --- connection helpers -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.debug("knowledge.db parent not creatable: %s", e)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            conn.enable_load_extension(True)
            try:
                import sqlite_vec

                sqlite_vec.load(conn)
            finally:
                conn.enable_load_extension(False)
        except Exception as e:  # noqa: BLE001 - app must import even without sqlite-vec
            logger.debug("sqlite-vec unavailable (FTS-only mode): %s", e)
        return conn

    def exists(self) -> bool:
        return self.db_path.is_file()

    # --- schema -------------------------------------------------------------

    def initialize(self, dim: Optional[int] = None) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id INTEGER PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    header TEXT NOT NULL,
                    cwe_id TEXT,
                    severity TEXT,
                    language TEXT,
                    vuln_class TEXT
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
                    USING fts5(title, header, text, content='');
                """
            )
            if dim is not None:
                try:
                    conn.execute(
                        f"CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec "
                        f"USING vec0(embedding float[{int(dim)}])"
                    )
                except sqlite3.Error as e:
                    logger.warning("Vector table unavailable (FTS-only build): %s", e)
            conn.execute(_EMBED_CACHE_DDL)

    def reset(self) -> None:
        # Corpus is rebuildable; embed_cache is content-addressed and costly to
        # regenerate, so reset preserves it (ingest reuses cache across rebuilds).
        if not self.exists():
            return
        with self._connect() as conn:
            for table in ("chunks_vec", "chunks_fts", "chunks", "meta"):
                try:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
                except sqlite3.Error as e:
                    # e.g. vec0 module unavailable but chunks_vec exists
                    logger.warning("Could not drop %s (continuing rebuild): %s", table, e)

    # --- meta ---------------------------------------------------------------

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def get_meta(self, key: str) -> Optional[str]:
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
                return row["value"] if row else None
        except Exception:  # noqa: BLE001 - read contract: never raise
            return None

    # --- chunks -------------------------------------------------------------

    def add_chunks(self, rows: List[Dict]) -> List[int]:
        chunk_ids: List[int] = []
        with self._connect() as conn:
            use_vec = False
            if any(row.get("_embedding") is not None for row in rows):
                try:
                    conn.execute("SELECT rowid FROM chunks_vec LIMIT 1").fetchall()
                    use_vec = True
                except sqlite3.Error:
                    logger.warning("chunks_vec unavailable; storing chunks without vectors")
            for row in rows:
                values = tuple(row.get(c) for c in ("source", "source_id", "title", "text", "header"))
                optional = tuple(row.get(c) for c in _OPTIONAL)
                cur = conn.execute(
                    f"INSERT INTO chunks ({_CHUNK_COLS}) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    values + optional,
                )
                chunk_id = int(cur.lastrowid)
                chunk_ids.append(chunk_id)
                conn.execute(
                    "INSERT INTO chunks_fts(rowid, title, header, text) VALUES (?, ?, ?, ?)",
                    (chunk_id, row["title"], row["header"], row["text"]),
                )
                embedding = row.get("_embedding")
                if use_vec and embedding is not None:
                    conn.execute(
                        "INSERT INTO chunks_vec(rowid, embedding) VALUES (?, ?)",
                        (chunk_id, json.dumps([float(v) for v in embedding])),
                    )
        return chunk_ids

    def chunk_count(self) -> int:
        try:
            with self._connect() as conn:
                return int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        except Exception:  # noqa: BLE001 - read contract: never raise
            return 0

    def has_vectors(self) -> bool:
        try:
            with self._connect() as conn:
                return int(conn.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]) > 0
        except Exception:  # noqa: BLE001 - read contract: never raise
            return False

    # --- search -------------------------------------------------------------

    def search_fts(self, match: str, limit: int) -> List[Tuple[int, float]]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT rowid, bm25(chunks_fts) AS score FROM chunks_fts "
                    "WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?",
                    (match, int(limit)),
                ).fetchall()
                return [(int(r["rowid"]), float(r["score"])) for r in rows]
        except Exception as e:  # noqa: BLE001 - read contract: never raise
            logger.debug("FTS search skipped: %s", e)
            return []

    def search_vec(self, vec: List[float], limit: int) -> List[Tuple[int, float]]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT rowid, distance FROM chunks_vec "
                    "WHERE embedding MATCH ? AND k = ? ORDER BY distance",
                    (json.dumps([float(v) for v in vec]), int(limit)),
                ).fetchall()
                return [(int(r["rowid"]), float(r["distance"])) for r in rows]
        except Exception as e:  # noqa: BLE001 - read contract: never raise
            logger.debug("Vector search skipped: %s", e)
            return []

    def hydrate(self, ids: List[int]) -> List[Dict]:
        if not ids:
            return []
        try:
            with self._connect() as conn:
                marks = ",".join("?" * len(ids))
                rows = conn.execute(
                    f"SELECT chunk_id, source, source_id, title, text, header, "
                    f"cwe_id, severity, language, vuln_class FROM chunks "
                    f"WHERE chunk_id IN ({marks})",
                    tuple(ids),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:  # noqa: BLE001 - read contract: never raise
            return []

    # --- embedding cache ----------------------------------------------------

    def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT embedding FROM embed_cache WHERE text_hash = ?", (text_hash,)
                ).fetchone()
                return json.loads(row["embedding"]) if row else None
        except Exception:  # noqa: BLE001 - read contract: never raise
            return None

    def put_cached_embedding(self, text_hash: str, model: str, dim: int, vec: List[float]) -> None:
        with self._connect() as conn:
            conn.execute(_EMBED_CACHE_DDL)
            conn.execute(
                "INSERT INTO embed_cache(text_hash, model, dim, embedding) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(text_hash) DO UPDATE SET "
                "model = excluded.model, dim = excluded.dim, embedding = excluded.embedding",
                (text_hash, model, int(dim), json.dumps([float(v) for v in vec])),
            )
