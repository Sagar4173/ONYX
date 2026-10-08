# ONYX Phase 2 - RAG (Grounded Knowledge) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the spec's Phase 2 RAG scope: a single-file `knowledge.db` (sqlite-vec vectors + FTS5 BM25), a committed seed corpus plus an optional full-CWE ingest path, hybrid retrieval with Reciprocal Rank Fusion, grounded chat that injects numbered knowledge blocks and returns resolvable `[[n]]` citations, grounded remediation enrichment, and deterministic retrieval evals (recall@window, rank-1 anchors, hostile-query safety).

**Architecture:** `services/ai/embeddings.py` embeds texts through a free-tier lane chain (Gemini `gemini-embedding-2` -> Ollama `nomic-embed-text`; batched, dimension-checked, scrubbed errors) with an `embed_cache` table inside `knowledge.db` so rebuilds cost ~0 tokens. An ingest CLI (`python -m services.ai.ingest`) loads the committed JSON corpus (plus an optional official CWE XML dump), chunks each doc into section-aware chunks (title/header/text all indexed), and builds `knowledge.db` idempotently (`chunks` table + vec0 `chunks_vec` + FTS5 `chunks_fts`). Retrieval fuses FTS5 BM25 and vector KNN rankings with Reciprocal Rank Fusion (RRF, k=60), degrading to FTS-only whenever the db is missing, has no vectors, or the query embedding fails. Chat retrieves top-k blocks per message, injects them as `[n]`-numbered knowledge context in the system prompt, instructs the model to cite with `[[n]]`, parses markers post-hoc into `ChatResponse.citations`, and stays fully functional when retrieval fails. Remediation enrichment appends FTS-only retrieved guidance (zero embedding calls per finding).

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, `sqlite-vec` (the ONLY new dependency, spec §2.4), stdlib `sqlite3` (FTS5 verified available: SQLite 3.50.4), `google-genai` (embeddings), `openai` SDK (Ollama embeddings), `xmltodict` (already installed - optional CWE XML ingest), pytest + pytest-asyncio (`asyncio_mode=auto`).

## Global Constraints

- **Test command** (from `E:\Projects\ONYX\backend`): `.venv\Scripts\python.exe -m pytest tests/ -v` - every task must leave this suite green.
- **Eval command**: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval` (Phase 1's 28 evals must stay green; this phase adds RAG evals).
- **Allowed new dependency: `sqlite-vec` ONLY** (spec §2.4 "Add: ... `sqlite-vec` (Phase 2)"). `git diff backend/requirements.txt` must show nothing except the `sqlite-vec` line. Never add: LangChain, LangGraph, LiteLLM, Chroma, guardrails frameworks, CrewAI, pgvector, hosted vector DBs (spec §2.4/§3.2).
- **$0 AI budget.** Free-tier providers only. Embeddings: `gemini-embedding-2` (AI Studio free) primary → Ollama `nomic-embed-text` fallback (spec §5.3; model IDs are unverified assumptions, env-configurable). No paid APIs, no hosted rerankers.
- **Corpus rules (spec §3.1):** embed only CWE/OWASP/remediation knowledge. NEVER embed raw repo code, scanner raw output, or chat history.
- **No git commits.** The user has not authorized commits for this phase; do NOT run `git commit`, `git add`, or any history-affecting command. Leave changes unstaged. (Commit steps from the plan template are intentionally omitted.)
- **Do not modify** `backend/services/scanning/workflow/enhanced.py`, `backend/tests/test_scan_progress.py`, or the frontend - later phases / separate workflow.
- **Preserve these test seams** (name and return type): `TriageService._call_ai(prompt) -> Optional[str]`, `routes.ai_chat._call_ai_chat(message, scan_context, conversation_history) -> str`, `_get_active_model() -> str`, `get_ai_processor()`, `create_ai_processor()`, `build_remediation_prompt(finding_data)`, `enrich_detailed_findings(findings, *, top_n=None, batch_size=5) -> bool`. Any new parameter on these functions must be optional keyword-only with a default that preserves today's behavior byte-for-byte.
- **AI/RAG must never fail a request.** Missing `knowledge.db`, missing embedding provider, corrupt DB, retrieval errors - all degrade gracefully (log + best-effort answer) and must never raise into routes or the scan flow.
- **No SSE streaming, no fix-agent, no triage annotation, no frontend changes** - those are Phases 3/3.5/UX-track scope.
- Run all commands from `E:\Projects\ONYX\backend` unless stated otherwise.

---

## Design Notes (decisions locked for this plan)

1. **`knowledge.db` location:** `data/knowledge.db` resolved relative to the backend working directory (`backend/data/knowledge.db` when run from `backend/`), following the existing `data/vulnerabilities`, `data/baselines` convention (`Path("data/...")` relative to CWD, created on demand). Configurable via `knowledge_db_path`.
2. **Schema versioning + dimension safety:** a `meta` table stores `schema_version`, `dim`, `model`, `built_at`, `doc_count`, `chunk_count` (observability + rebuild diagnostics). Every read method in `KnowledgeStore` swallows sqlite/vec errors and returns `[]`, so a dim mismatch or corrupt vector table silently degrades the vector leg to FTS-only (logged at debug, never raised). Within one build, ingest embeds all cache misses in a single `embed_texts` call at `settings.ai_embed_dimensions`, so a single build cannot mix vector spaces.
3. **Vector insert/query format:** JSON arrays (`'[0.1, 0.2, ...]'`) for both INSERT and `MATCH` - documented sqlite-vec format, no serialize API needed, fine at 2k-50k chunk scale.
4. **Citations format:** inline `[[n]]` markers in the model reply (n = 1-based index of the retrieved block actually shown to the model). Post-processing keeps only ids in range and strips the markers from the visible text. Chosen over a JSON answer schema because it preserves the `_call_ai_chat -> str` seam, works with degraded text fallback, and adds no schema-retry path to the chat hot loop.
5. **Enrichment grounding is FTS-only:** finding titles/CWE-ids are keyword-rich and FTS matches them well; this keeps enrichment at zero embedding calls (free-tier RPM headroom). Chat uses full hybrid (one embed call per user message).
6. **Full corpus = optional operator step.** MITRE publishes the official CWE downloads at `https://cwe.mitre.org/data/downloads.html`. The ingest CLI accepts `--cwe-xml <path>` (uses already-installed `xmltodict`). A committed seed corpus (`cwe_seed.json` with 16 common weaknesses, `owasp.json` with the OWASP Top 10 2021 entries, `snippets.json` with remediation snippets) makes the product work out-of-box and keeps every test offline.
7. **Embedding cache** lives inside `knowledge.db` (`embed_cache` table keyed by `sha256(model + text)`), so re-ingesting after a chunker change re-embeds only new/changed texts.
8. **Deterministic tests - no provider calls:** unit tests inject fake lanes by patching `_gemini_lane`/`_ollama_lane`/`embed_texts`/`embed_query`, and retrieval tests build throwaway stores under `tmp_path` with hand-constructed vectors. Retrieval-quality evals build an `embed=False` knowledge db into a temp dir, so ranking is fully deterministic and every test/eval runs offline.
9. **FTS indexes `title` too:** section chunks carry generic headers (`CWE-89: Remediation`), so the FTS table is `fts5(title, header, text)` - without titles, queries like "SQL injection" or `_lookup_guidance("CWE-89 Use of ...")` would miss the very documents they target (verified while designing Task 9's golden set).

---

## File Structure

**Create:**

| File | Responsibility |
|---|---|
| `backend/services/ai/embeddings.py` | `embed_texts()` / `embed_query()` - free-tier embedding chain (Gemini → Ollama), `EmbeddingError` |
| `backend/services/ai/knowledge_sources.py` | `KnowledgeDoc`/`KnowledgeSection` models + `load_source_file()`/`load_all_sources()` JSON readers |
| `backend/services/ai/knowledge_store.py` | `KnowledgeStore` - schema create/open, chunk upsert, FTS + vector search, meta, embed cache |
| `backend/services/ai/ingest.py` | `chunk_doc()` + `parse_cwe_xml()` + `build()` + `python -m services.ai.ingest` CLI (reset-safe rebuild keeps embed cache, `--no-embed`, `--cwe-xml`) |
| `backend/services/ai/retrieval.py` | `build_fts_query()`, `rrf_fuse()`, `retrieve()` hybrid+RRF, `retrieve_fts_only()` (never embeds) |
| `backend/services/ai/chat_grounding.py` | `format_context()` numbered knowledge blocks + `extract_citations()` `[[n]]` parsing |
| `backend/knowledge/sources/cwe_seed.json` | 16 seed CWE docs (committed) |
| `backend/knowledge/sources/owasp.json` | OWASP Top 10 2021 docs (committed) |
| `backend/knowledge/sources/snippets.json` | remediation snippets per vuln-class × language (committed) |
| `backend/knowledge/__init__.py` | package marker (empty) |
| `backend/knowledge/README.md` | corpus schema + how to fetch/build the full CWE corpus |
| `backend/tests/test_rag_config.py` | Task 1 (settings + sqlite capability) |
| `backend/tests/test_knowledge_sources.py` | Task 2 (loader + seed corpus validation) |
| `backend/tests/test_embeddings.py` | Task 3 (provider chain, batching, failure) |
| `backend/tests/test_knowledge_store.py` | Task 4 (schema, upsert, FTS, vector search, cache) |
| `backend/tests/test_ingest.py` | Task 5 (chunking, rebuild, no-embed mode, CLI) |
| `backend/tests/test_retrieval.py` | Task 6 (hybrid, RRF, filters, degradation) |
| `backend/tests/test_chat_grounding.py` | Task 7 (context formatting, citation parsing) |
| `backend/tests/test_enrichment_guidance.py` | Task 8 (grounded remediation prompts) |
| `backend/evals/test_rag_golden.py` | Task 9 (golden recall@window, rank-1 anchors, CWE filter, hostile-query safety) |

**Modify:** `backend/requirements.txt` (+`sqlite-vec` only), `backend/config.py` (RAG settings), `backend/.env.example` (RAG block), `backend/routes/ai_chat.py` (`_retrieve_knowledge()` helper, optional `knowledge=` kwarg on `_call_ai_chat`, `ChatResponse.citations`), `backend/tests/test_ai_chat.py` (offline-retrieval fixture + citation tests), `backend/services/ai/ai_processor.py` (guidance lookup in `_enrich_batch_with_remediation`), `backend/services/ai/prompts.py` (`build_remediation_prompt(..., guidance=None)`, chat system prompt citation instructions).

**Delete:** nothing.

---

### Task 1: Config + sqlite-vec capability

**Files:**
- Modify: `backend/requirements.txt` (one line), `backend/config.py` (RAG settings block), `backend/.env.example`
- Test: `backend/tests/test_rag_config.py` (create)

**Interfaces:**
- Consumes: existing `Settings` (pydantic-settings, `env=` style used throughout `config.py`)
- Produces (used by every later task):
  - `settings.knowledge_db_path: str = "data/knowledge.db"`
  - `settings.ai_embed_model: str = "gemini-embedding-2"`
  - `settings.ai_embed_local_model: str = "nomic-embed-text"`
  - `settings.ai_embed_dimensions: int = 768`
  - `settings.ai_embed_batch_size: int = 16`
  - `settings.rag_top_k: int = 6`
  - `settings.rag_rrf_k: int = 60`
  - `settings.rag_max_context_chars: int = 6000`
  - capability helper `services.ai.knowledge_store.sqlite_capabilities()` is NOT in this task - this task only proves `sqlite-vec` + FTS5 load in-process.

- [ ] **Step 1: Add the dependency**

In `backend/requirements.txt`, append under the `# AI and Machine Learning` block (after `google-genai>=1.0.0`):

```ini
# AI and Machine Learning
openai>=1.3.7
google-genai>=1.0.0
sqlite-vec>=0.1.0   # Phase 2 RAG: vector search in knowledge.db (spec 2.4)
```

Run: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
Expected: `Successfully installed sqlite-vec-<version>` (only this package is new).

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_rag_config.py`:

```python
"""Phase 2 config + sqlite capability."""
from config import Settings, settings


def test_rag_settings_defaults():
    s = Settings(_env_file=None)
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
```

Note: `Settings(_env_file=None)` requires the required fields (`mongodb_uri`, `secret_key`) to have usable test defaults exactly as `tests/test_config_ai.py` already does - copy that pattern: `Settings(_env_file=None, mongodb_uri="mongodb://localhost:27017", secret_key="x" * 32)` if `Settings` requires them. Match whatever `test_config_ai.py` does; keep this test hermetic.

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_rag_config.py -v`
Expected: FAIL - `ValidationError` (unknown fields off / missing attrs) or `AttributeError: 'Settings' object has no attribute 'knowledge_db_path'`.

- [ ] **Step 4: Add config fields**

In `backend/config.py`, inside `class Settings(BaseSettings)`, immediately after the Phase 1 AI block (after `ai_post_scan_concurrency`), add:

```python
    # --- Phase 2: RAG / knowledge retrieval --------------------------------
    knowledge_db_path: str = Field(default="data/knowledge.db", env="KNOWLEDGE_DB_PATH")
    ai_embed_model: str = Field(default="gemini-embedding-2", env="AI_EMBED_MODEL")
    ai_embed_local_model: str = Field(default="nomic-embed-text", env="AI_EMBED_LOCAL_MODEL")
    ai_embed_dimensions: int = Field(default=768, env="AI_EMBED_DIMENSIONS")
    ai_embed_batch_size: int = Field(default=16, env="AI_EMBED_BATCH_SIZE")
    rag_top_k: int = Field(default=6, env="RAG_TOP_K")
    rag_rrf_k: int = Field(default=60, env="RAG_RRF_K")
    rag_max_context_chars: int = Field(default=6000, env="RAG_MAX_CONTEXT_CHARS")
```

In `backend/.env.example`, append an RAG block (keep the file's existing comment style):

```ini
# --- Phase 2: RAG / knowledge retrieval ---------------------------------
# Single SQLite file holding vectors (sqlite-vec) + full-text index (FTS5).
KNOWLEDGE_DB_PATH=data/knowledge.db
# Embedding provider chain: Gemini free tier, then Ollama. Dimensions must
# match between provider and stored vectors (768 works for both defaults).
AI_EMBED_MODEL=gemini-embedding-2
AI_EMBED_LOCAL_MODEL=nomic-embed-text
AI_EMBED_DIMENSIONS=768
AI_EMBED_BATCH_SIZE=16
# Retrieval: blocks returned per query, RRF fusion constant, context cap.
RAG_TOP_K=6
RAG_RRF_K=60
RAG_MAX_CONTEXT_CHARS=6000
```

- [ ] **Step 5: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_rag_config.py -v`
Expected: 3 passed.

- [ ] **Step 6: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 532 passed (529 + 3).

### Task 2: Knowledge sources - loader + committed seed corpus

**Files:**
- Create: `backend/services/ai/knowledge_sources.py`, `backend/knowledge/__init__.py` (empty), `backend/knowledge/sources/cwe_seed.json`, `backend/knowledge/sources/owasp.json`, `backend/knowledge/sources/snippets.json`, `backend/knowledge/README.md`
- Test: `backend/tests/test_knowledge_sources.py` (create)

**Interfaces:**
- Consumes: Pydantic v2 only.
- Produces (used by Tasks 5 and 9):
  - `knowledge_sources.KnowledgeSection(heading: str, text: str)`
  - `knowledge_sources.KnowledgeDoc(source: str, source_id: str, title: str, text: str, cwe_id: Optional[str] = None, severity: Optional[str] = None, language: Optional[str] = None, vuln_class: Optional[str] = None, sections: List[KnowledgeSection] = [])`
  - `knowledge_sources.load_source_file(path: Path) -> List[KnowledgeDoc]`
  - `knowledge_sources.load_all_sources(directory: Path | None = None) -> List[KnowledgeDoc]` (default `backend/knowledge/sources`, resolved relative to this file: `Path(__file__).resolve().parents[2] / "knowledge" / "sources"`)
  - `knowledge_sources.SOURCES_DIR: Path`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_knowledge_sources.py`:

```python
"""Seed corpus loads and validates."""
from pathlib import Path

from services.ai.knowledge_sources import (
    SOURCES_DIR,
    KnowledgeDoc,
    load_all_sources,
    load_source_file,
)


def test_sources_dir_exists():
    assert SOURCES_DIR.is_dir()
    assert (SOURCES_DIR / "cwe_seed.json").is_file()
    assert (SOURCES_DIR / "owasp.json").is_file()
    assert (SOURCES_DIR / "snippets.json").is_file()


def test_load_all_sources_validates_schema():
    docs = load_all_sources()
    assert all(isinstance(d, KnowledgeDoc) for d in docs)
    assert len(docs) >= 36  # 16 cwe + 10 owasp + 10 snippets minimum


def test_cwe_seed_contains_anchor_entries():
    docs = {d.source_id: d for d in load_source_file(SOURCES_DIR / "cwe_seed.json")}
    assert docs["CWE-89"].cwe_id == "CWE-89"
    assert "SQL Injection" in docs["CWE-89"].title
    assert docs["CWE-89"].severity == "critical"
    assert any(s.heading == "Remediation" for s in docs["CWE-89"].sections)
    assert "CWE-798" in docs
    assert len(docs) >= 16


def test_owasp_has_top10_2021():
    docs = {d.source_id: d for d in load_source_file(SOURCES_DIR / "owasp.json")}
    assert len(docs) == 10
    assert docs["owasp-a01"].title.startswith("A01")
    assert all(d.source == "owasp" for d in docs.values())


def test_snippets_have_language_and_vuln_class():
    docs = load_source_file(SOURCES_DIR / "snippets.json")
    assert len(docs) >= 10
    assert all(d.language for d in docs)
    assert all(d.vuln_class for d in docs)
    assert any(d.language == "python" and d.vuln_class == "sql_injection" for d in docs)


def test_loader_rejects_malformed_doc(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"source": "x", "docs": [{"source_id": "a"}]}', encoding="utf-8")
    try:
        load_source_file(bad)
    except Exception:
        return
    raise AssertionError("malformed doc must not validate")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_knowledge_sources.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'services.ai.knowledge_sources'`.

- [ ] **Step 3: Write `backend/services/ai/knowledge_sources.py`**

```python
"""JSON knowledge sources -> validated KnowledgeDoc records.

Source file schema (all files: {"source": str, "docs": [...]}):
  doc: source_id (str, unique per file), title, text,
       optional cwe_id, severity, language, vuln_class,
       optional sections: [{heading, text}]
"""
import json
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

SOURCES_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "sources"


class KnowledgeSection(BaseModel):
    heading: str
    text: str


class KnowledgeDoc(BaseModel):
    source: str
    source_id: str
    title: str
    text: str
    cwe_id: Optional[str] = None
    severity: Optional[str] = None
    language: Optional[str] = None
    vuln_class: Optional[str] = None
    sections: List[KnowledgeSection] = Field(default_factory=list)

    @field_validator("source", "source_id", "title")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be non-empty")
        return v


def load_source_file(path: Path) -> List[KnowledgeDoc]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    source = raw.get("source")
    if not source:
        raise ValueError(f"{path}: missing top-level 'source'")
    docs = []
    for item in raw.get("docs", []):
        item.setdefault("source", source)
        docs.append(KnowledgeDoc.model_validate(item))
    seen = set()
    for d in docs:
        if d.source_id in seen:
            raise ValueError(f"{path}: duplicate source_id {d.source_id}")
        seen.add(d.source_id)
    return docs


def load_all_sources(directory: Optional[Path] = None) -> List[KnowledgeDoc]:
    directory = directory or SOURCES_DIR
    docs: List[KnowledgeDoc] = []
    for path in sorted(directory.glob("*.json")):
        docs.extend(load_source_file(path))
    logger.info("Loaded %s knowledge docs from %s", len(docs), directory)
    return docs
```

- [ ] **Step 4: Write the seed corpus files**

Create `backend/knowledge/__init__.py` (empty file).

Create `backend/knowledge/sources/cwe_seed.json` - exactly 16 entries with this shape; the three anchor entries are fully written here, the remaining 13 follow the identical schema with accurate, concise CWE summaries (2-4 sentences of `text` each, one `Remediation` section each, correct `severity`):

```json
{
  "source": "cwe",
  "docs": [
    {
      "source_id": "CWE-89",
      "title": "SQL Injection (SQLi)",
      "cwe_id": "CWE-89",
      "severity": "critical",
      "text": "Improper neutralization of special elements used in an SQL command allows attacker-controlled data to alter the query structure (G78/Owasp). Successful exploitation can disclose, modify, or destroy database data and may lead to full application compromise.",
      "sections": [
        {"heading": "Remediation", "text": "Use parameterized queries or prepared statements for all database access; never concatenate user input into SQL. Apply least-privilege database accounts, validate input against strict allow-lists, and use an ORM with safe bindings where practical."},
        {"heading": "Detection", "text": "Look for string-built queries (f-strings, + concatenation, format()) feeding cursor.execute, raw query planners, and error messages that echo SQL syntax back to the client."}
      ]
    },
    {
      "source_id": "CWE-798",
      "title": "Use of Hard-coded Credentials",
      "cwe_id": "CWE-798",
      "severity": "high",
      "text": "A password, API key, or other secret is baked into source code. Anyone with repository access (or anyone who obtains a copy) can authenticate as the trusted component, and rotation requires a code change.",
      "sections": [
        {"heading": "Remediation", "text": "Move secrets to environment variables or a secret manager, rotate any exposed credential immediately, and scan history for prior leaks. Commit pre-receive hooks with detect-secrets/gitleaks prevent regressions."}
      ]
    },
    {
      "source_id": "CWE-79",
      "title": "Cross-site Scripting (XSS)",
      "cwe_id": "CWE-79",
      "severity": "high",
      "text": "Web applications include untrusted data in output pages without proper validation or escaping, allowing attackers to execute scripts in victims' browsers (session hijacking, defacement, credential theft).",
      "sections": [
        {"heading": "Remediation", "text": "Context-escape all dynamic output (HTML, JS, URL, CSS contexts), prefer framework auto-escaping and safe DOM APIs (textContent over innerHTML), sanitize rich HTML with a vetted allow-list sanitizer, and deploy a restrictive Content-Security-Policy."}
      ]
    },
    {
      "source_id": "CWE-78",
      "title": "OS Command Injection",
      "cwe_id": "CWE-78",
      "severity": "critical",
      "text": "User-controlled data reaches an OS shell command, letting attackers execute arbitrary commands with the application's privileges (RCE).",
      "sections": [{"heading": "Remediation", "text": "Avoid shells: use argument-array APIs (subprocess.run([...]) with shell=False), validate input against strict allow-lists, and drop privileges for child processes."}]},
    {
      "source_id": "CWE-22",
      "title": "Path Traversal",
      "cwe_id": "CWE-22",
      "severity": "high",
      "text": "External input is used to construct a path that can escape the intended directory, exposing or overwriting arbitrary files (source disclosure, config theft, code execution via writable paths).",
      "sections": [{"heading": "Remediation", "text": "Resolve the final path with os.path.realpath/Path.resolve and verify it stays under the intended root; prefer id-based access over user paths; block ../ and absolute paths; run with least filesystem privilege."}]},
    {
      "source_id": "CWE-200",
      "title": "Exposure of Sensitive Information",
      "cwe_id": "CWE-200",
      "severity": "medium",
      "text": "The application leaks confidential data (PII, secrets, internal state, stack traces) to actors not authorized to see it, via responses, logs, error pages, or side channels.",
      "sections": [{"heading": "Remediation", "text": "Minimize data returned, redact secrets and PII in responses and logs, disable debug error pages in production, and enforce server-side authorization on every object."}]},
    {
      "source_id": "CWE-319",
      "title": "Cleartext Transmission of Sensitive Information",
      "cwe_id": "CWE-319",
      "severity": "medium",
      "text": "Sensitive data travels in cleartext (HTTP, FTP, unencrypted SMTP), allowing network observers to capture credentials, tokens, and personal data.",
      "sections": [{"heading": "Remediation", "text": "Enforce HTTPS/TLS everywhere with HSTS, disable plaintext fallbacks, and use encrypted protocols (SMTPS/IMAPS) for mail."}]},
    {
      "source_id": "CWE-306",
      "title": "Missing Authentication for Critical Function",
      "cwe_id": "CWE-306",
      "severity": "critical",
      "text": "A sensitive operation (account admin, payment, config change) is reachable without proving identity, letting any attacker invoke it directly.",
      "sections": [{"heading": "Remediation", "text": "Require authentication on every critical route by default (deny-by-default), enforce authorization checks server-side, and add regression tests that unauthenticated requests are rejected with 401/403."}]},
    {
      "source_id": "CWE-639",
      "title": "Authorization Bypass Through User-Controlled Key (IDOR)",
      "cwe_id": "CWE-639",
      "severity": "high",
      "text": "Objects are accessed by directly guessing or manipulating an identifier (id, uuid, account number) without verifying the caller owns or may access that object.",
      "sections": [{"heading": "Remediation", "text": "Enforce object-level authorization on every access (ownership/tenant checks server-side), prefer non-guessable identifiers, and never trust IDs from the client without a permission lookup."}]},
    {
      "source_id": "CWE-502",
      "title": "Deserialization of Untrusted Data",
      "cwe_id": "CWE-502",
      "severity": "critical",
      "text": "Parsing attacker-controlled serialized objects (pickle, yaml.load, Java serialization) can trigger gadget chains that execute arbitrary code or instantiate attacker-chosen types.",
      "sections": [{"heading": "Remediation", "text": "Never deserialize untrusted data with unsafe formats; use JSON for untrusted payloads, safe loaders (yaml.safe_load), and integrity-check signed payloads before parsing."}]},
    {
      "source_id": "CWE-918",
      "title": "Server-Side Request Forgery (SSRF)",
      "cwe_id": "CWE-918",
      "severity": "high",
      "text": "The server fetches a user-supplied URL, letting attackers reach internal services, cloud metadata endpoints (169.254.169.254), or scan the private network from the server's vantage point.",
      "sections": [{"heading": "Remediation", "text": "Allow-list outbound destinations, resolve and validate IPs (block private/link-local ranges), disable redirects, and separate egress networks for user-initiated fetches."}]},
    {
      "source_id": "CWE-770",
      "title": "Allocation of Resources Without Limits",
      "cwe_id": "CWE-770",
      "severity": "medium",
      "text": "Unbounded allocation of files, memory, connections, or compute per request lets an attacker exhaust resources and cause denial of service for all users.",
      "sections": [{"heading": "Remediation", "text": "Apply quotas and rate limits per user/IP, bound request body and collection sizes, and set timeouts on all outbound calls."}]},
    {
      "source_id": "CWE-327",
      "title": "Use of a Broken or Risky Cryptographic Algorithm",
      "cwe_id": "CWE-327",
      "severity": "medium",
      "text": "Use of broken or weak algorithms (MD5, SHA-1 for signatures, DES, ECB mode) undermines confidentiality or integrity guarantees even when crypto is 'used'.",
      "sections": [{"heading": "Remediation", "text": "Use modern algorithms (AES-GCM, SHA-256+, ChaCha20-Poly1305), prefer vetted libraries and authenticated encryption, and never design your own crypto."}]},
    {
      "source_id": "CWE-330",
      "title": "Use of Insufficiently Random Values",
      "cwe_id": "CWE-330",
      "severity": "medium",
      "text": "Predictable random values (math.random for tokens, time-based seeds) allow attackers to guess session tokens, password-reset links, or nonces.",
      "sections": [{"heading": "Remediation", "text": "Use cryptographically secure generators (secrets, os.urandom, crypto/rand) for all security-sensitive values, and never seed PRNGs with time or low-entropy input."}]},
    {
      "source_id": "CWE-611",
      "title": "XML External Entity (XXE) Reference",
      "cwe_id": "CWE-611",
      "severity": "high",
      "text": "XML parsers that resolve external entities let attackers read local files, perform SSRF, or exhaust resources while parsing seemingly benign XML.",
      "sections": [{"heading": "Remediation", "text": "Disable DTDs and external entity resolution in all XML parsers; prefer JSON for untrusted data."}]},
    {
      "source_id": "CWE-1176",
      "title": "Improper Handling of Syntax Errors (input validation)",
      "cwe_id": "CWE-1176",
      "severity": "low",
      "text": "Unhandled malformed input causes crashes or inconsistent state instead of clean rejection, enabling denial of service and masking of real attacks in noisy errors.",
      "sections": [{"heading": "Remediation", "text": "Validate all external input against schemas, reject malformed data with clear 4xx responses, and fail closed without leaking internals."}]}
  ]
}
```

Create `backend/knowledge/sources/owasp.json` - 10 entries (`owasp-a01`..`owasp-a10`), `source: "owasp"`, no `cwe_id`, `severity` omitted; each `text` = 2-3 sentences describing the risk class, one `Remediation` section, one `Example attack` section. Titles: `A01:2021 - Broken Access Control`, `A02:2021 - Cryptographic Failures`, `A03:2021 - Injection`, `A04:2021 - Insecure Design`, `A05:2021 - Security Misconfiguration`, `A06:2021 - Vulnerable and Outdated Components`, `A07:2021 - Identification and Authentication Failures`, `A08:2021 - Software and Data Integrity Failures`, `A09:2021 - Security Logging and Monitoring Failures`, `A10:2021 - Server-Side Request Forgery`. Example entry:

```json
{
  "source": "owasp",
  "docs": [
    {
      "source_id": "owasp-a01",
      "title": "A01:2021 - Broken Access Control",
      "text": "Access control enforces that users may only act on the resources and actions their permissions allow. Failures let attackers view or edit records belonging to others, escalate privileges, or invoke administrative functions. This class topped the 2021 OWASP ranking by prevalence.",
      "sections": [
        {"heading": "Remediation", "text": "Deny by default; implement server-side checks on every request; reuse mapped and deny object-level authorization (IDOR guards); disable directory listing; log access-control failures; rate-limit and cap APIs by role."},
        {"heading": "Example attack", "text": "Changing /api/orders/1042 to /api/orders/1043 to read another customer's order, or adding is_admin=true to a profile update body."}
      ]
    }
  ]
}
```

Write the remaining nine entries in the same shape.

Create `backend/knowledge/sources/snippets.json` - `source: "snippet"`, at least 10 docs covering (vuln_class, language) pairs: (`sql_injection`, python), (`sql_injection`, javascript), (`xss`, python), (`path_traversal`, python), (`hardcoded_secret`, python), (`command_injection`, python), (`ssrf`, python), (`insecure_deserialization`, python), (`crypto_weakness`, python), (`auth_missing`, javascript). Each `source_id` = `snip-<vuln_class>-<language>`; `title` like `"Parameterized SQL queries in Python"`; `text` = short framing sentence; one `Remediation` section containing the concrete code example. Example entry:

```json
{
  "source": "snippet",
  "docs": [
    {
      "source_id": "snip-sql_injection-python",
      "title": "Parameterized SQL queries in Python",
      "language": "python",
      "vuln_class": "sql_injection",
      "cwe_id": "CWE-89",
      "text": "Never build SQL by string concatenation. Use driver-level parameter binding so the driver escapes values, never structure.",
      "sections": [
        {"heading": "Remediation", "text": "# vulnerable: cursor.execute(f\"SELECT * FROM users WHERE email = '{email}'\")\n# safe (DB-API drivers):\ncursor.execute(\"SELECT * FROM users WHERE email = %s\", (email,))\n# safe (sqlite3):\ncursor.execute(\"SELECT * FROM users WHERE email = ?\", (email,))"}
      ]
    }
  ]
}
```

Write the other nine snippets with real, correct code for each language/framework.

Create `backend/knowledge/README.md`:

```markdown
# ONYX knowledge corpus

Feeds `data/knowledge.db` (sqlite-vec vectors + FTS5 index).

## Files (`sources/*.json`)
Schema: {"source": str, "docs": [{source_id, title, text, cwe_id?, severity?,
language?, vuln_class?, sections: [{heading, text}]}]}

## Building the database
    cd backend
    .venv\Scripts\python -m services.ai.ingest            # seed corpus, embeds (needs provider)
    .venv\Scripts\python -m services.ai.ingest --no-embed  # FTS5 only (no provider needed)

## Full CWE corpus (optional, ~1,000 entries)
1. Download the latest CWE XML release from https://cwe.mitre.org/data/downloads.html
2. .venv\Scripts\python -m services.ai.ingest --cwe-xml path\to\cwec_x.y.xml

The DB rebuilds idempotently; embeddings are cached inside the DB file.
```

- [ ] **Step 5: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_knowledge_sources.py -v`
Expected: 6 passed.

- [ ] **Step 6: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 538 passed (532 + 6).

### Task 3: Embeddings - free-tier provider chain

**Files:**
- Create: `backend/services/ai/embeddings.py`
- Test: `backend/tests/test_embeddings.py` (create)

**Interfaces:**
- Consumes: `settings.gemini_api_key`, `settings.ai_local_base_url`, `settings.ai_embed_model`, `settings.ai_embed_local_model`, `settings.ai_embed_dimensions`, `settings.ai_embed_batch_size`, `services.ai.gateway._scrub`
- Produces (used by Tasks 5, 6, 7):
  - `embeddings.EmbeddingError(Exception)` - all lanes failed (message already scrubbed)
  - `embeddings.embed_texts(texts: List[str]) -> List[List[float]]` - batches internally, raises `EmbeddingError` on failure, never returns wrong-dim vectors
  - `embeddings.embed_query(text: str) -> Optional[List[float]]` - None on any failure (never raises)
  - `embeddings.GeminiLane` / `embeddings.OllamaLane` - small classes with `async def embed(self, texts) -> List[List[float]]`, patchable seams in tests

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_embeddings.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_embeddings.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'services.ai.embeddings'`.

- [ ] **Step 3: Write `backend/services/ai/embeddings.py`**

```python
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
                got = await lane.embed(batch)
                if len(got) != len(batch):
                    raise EmbeddingError(f"{type(lane).__name__} returned {len(got)} vectors for {len(batch)} texts")
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
```

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_embeddings.py -v`
Expected: 7 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 545 passed (538 + 7).

### Task 4: Knowledge store - `knowledge.db` schema, FTS, vectors, cache

**Files:**
- Create: `backend/services/ai/knowledge_store.py`
- Test: `backend/tests/test_knowledge_store.py` (create)

**Interfaces:**
- Consumes: `sqlite-vec` (`sqlite_vec.load`), stdlib `sqlite3` (FTS5 verified), `settings.knowledge_db_path`
- Produces (used by Tasks 5, 6, 9):
  - `KnowledgeStore(db_path: Optional[str|Path] = None)` - each method opens its own connection (ms-scale queries; never blocks meaningfully)
  - `.initialize(dim: Optional[int] = None)` - creates `meta`, `chunks`, `chunks_fts` (FTS5), and `chunks_vec` (vec0) only when `dim` is given; idempotent
  - `.reset()` - drops all five tables (rebuild path)
  - `.set_meta(key, value)` / `.get_meta(key) -> Optional[str]`
  - `.add_chunks(rows: List[Dict]) -> List[int]` - each row: `source, source_id, title, text, header` required; optional `cwe_id, severity, language, vuln_class`; optional `_embedding: List[float]` (adds vec0 row); returns chunk_ids
  - `.chunk_count() -> int`, `.has_vectors() -> bool`
  - `.search_fts(match: str, limit: int) -> List[Tuple[int, float]]` - BM25 rank (lower = better); returns `[]` on any error (missing db/table)
  - `.search_vec(vec: List[float], limit: int) -> List[Tuple[int, float]]` - (chunk_id, distance); `[]` on any error
  - `.hydrate(ids: List[int]) -> List[Dict]` - chunk rows keyed by `chunk_id`
  - `.get_cached_embedding(text_hash) -> Optional[List[float]]` / `.put_cached_embedding(text_hash, model, dim, vec)`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_knowledge_store.py`:

```python
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
    store.reset()
    assert store.chunk_count() == 0
    assert store.has_vectors() is False
    assert store.get_meta("dim") is None
    store.initialize(dim=4)  # schema can be recreated after reset
    assert store.chunk_count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_knowledge_store.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'services.ai.knowledge_store'`.

- [ ] **Step 3: Write `backend/services/ai/knowledge_store.py`**

```python
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

import sqlite_vec

from config import settings

logger = logging.getLogger(__name__)

_CHUNK_COLS = (
    "source, source_id, title, text, header, "
    "cwe_id, severity, language, vuln_class"
)
_OPTIONAL = ("cwe_id", "severity", "language", "vuln_class")


class KnowledgeStore:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path or settings.knowledge_db_path)

    # --- connection helpers -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.row_factory = sqlite3.Row
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
                conn.execute(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec "
                    f"USING vec0(embedding float[{int(dim)}])"
                )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS embed_cache ("
                "text_hash TEXT PRIMARY KEY, model TEXT NOT NULL, "
                "dim INTEGER NOT NULL, embedding TEXT NOT NULL)"
            )

    def reset(self) -> None:
        # Corpus is rebuildable; embed_cache is content-addressed and costly to
        # regenerate, so reset preserves it (ingest reuses cache across rebuilds).
        if not self.exists():
            return
        with self._connect() as conn:
            for table in ("chunks_vec", "chunks_fts", "chunks", "meta"):
                conn.execute(f"DROP TABLE IF EXISTS {table}")

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
        except sqlite3.Error:
            return None

    # --- chunks -------------------------------------------------------------

    def add_chunks(self, rows: List[Dict]) -> List[int]:
        chunk_ids: List[int] = []
        with self._connect() as conn:
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
                if embedding is not None:
                    conn.execute(
                        "INSERT INTO chunks_vec(rowid, embedding) VALUES (?, ?)",
                        (chunk_id, json.dumps([float(v) for v in embedding])),
                    )
        return chunk_ids

    def chunk_count(self) -> int:
        try:
            with self._connect() as conn:
                return int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        except sqlite3.Error:
            return 0

    def has_vectors(self) -> bool:
        try:
            with self._connect() as conn:
                return int(conn.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]) > 0
        except sqlite3.Error:
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
        except sqlite3.Error as e:
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
        except sqlite3.Error as e:
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
        except sqlite3.Error:
            return []

    # --- embedding cache ----------------------------------------------------

    def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT embedding FROM embed_cache WHERE text_hash = ?", (text_hash,)
                ).fetchone()
                return json.loads(row["embedding"]) if row else None
        except (sqlite3.Error, ValueError):
            return None

    def put_cached_embedding(self, text_hash: str, model: str, dim: int, vec: List[float]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO embed_cache(text_hash, model, dim, embedding) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(text_hash) DO UPDATE SET "
                "model = excluded.model, dim = excluded.dim, embedding = excluded.embedding",
                (text_hash, model, int(dim), json.dumps([float(v) for v in vec])),
            )
```

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_knowledge_store.py -v`
Expected: 7 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 552 passed (545 + 7).

### Task 5: Ingest CLI - chunk, embed (cache-aware), build knowledge.db

**Files:**
- Create: `backend/services/ai/ingest.py`
- Test: `backend/tests/test_ingest.py` (create)

**Interfaces:**
- Consumes: `KnowledgeDoc` / `load_all_sources` (Task 2), `KnowledgeStore` (Task 4), `embed_texts` / `EmbeddingError` (Task 3), `settings.knowledge_db_path`, `settings.ai_embed_model`, `settings.ai_embed_dimensions`, stdlib `argparse`, `xmltodict` (already a dependency)
- Produces (used by Task 10 + operators):
  - `ingest.chunk_doc(doc: KnowledgeDoc) -> List[Dict]` - one chunk per section when sections exist, else one doc-level chunk; `header = f"{source_id}: {heading}"`
  - `ingest.parse_cwe_xml(path: Path) -> List[KnowledgeDoc]` - tolerant xmltodict parse of the official MITRE CWE XML dump (`source="cwe-full"`); malformed entries are skipped with a warning
  - `ingest.build(db_path=None, *, sources_dir=None, cwe_xml=None, embed=True) -> Dict[str, int]` - async; always resets corpus tables first (embed_cache survives), embeds all cache misses in ONE `embed_texts` call (consistent single-lane vector space), degrades to FTS-only build when embedding fails entirely; sets meta `schema_version/dim/model/built_at/doc_count/chunk_count`; returns `{"docs", "chunks", "embedded", "cache_hits", "vectors_failed"}`
  - CLI: `python -m services.ai.ingest [--db PATH] [--sources DIR] [--cwe-xml PATH] [--no-embed]` - prints JSON stats, exit 0

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_ingest.py`:

```python
"""Ingest pipeline: chunking, cache-aware embedding, XML, CLI."""
import json
from unittest.mock import patch

import services.ai.ingest as ingest
from services.ai.embeddings import EmbeddingError
from services.ai.ingest import build, chunk_doc, parse_cwe_xml
from services.ai.knowledge_sources import KnowledgeDoc, KnowledgeSection
from services.ai.knowledge_store import KnowledgeStore


def _doc(i: int = 0, sections=None) -> KnowledgeDoc:
    return KnowledgeDoc(
        source="cwe",
        source_id=f"CWE-{100 + i}",
        title=f"Example weakness {i}",
        text=f"Body {i} describes a weakness used in injection chains.",
        cwe_id=f"CWE-{100 + i}",
        severity="high",
        sections=sections or [],
    )


def test_chunk_doc_one_chunk_without_sections():
    rows = chunk_doc(_doc(0))
    assert len(rows) == 1
    assert rows[0]["header"] == "CWE-100: Example weakness 0"
    assert rows[0]["source_id"] == "CWE-100"


def test_chunk_doc_one_chunk_per_section():
    doc = _doc(0, sections=[
        KnowledgeSection(heading="Description", text="Intro text."),
        KnowledgeSection(heading="Remediation", text="Fix it properly."),
    ])
    rows = chunk_doc(doc)
    assert [r["header"] for r in rows] == [
        "CWE-100: Description",
        "CWE-100: Remediation",
    ]
    assert all(r["cwe_id"] == "CWE-100" for r in rows)


async def test_build_fts_only(tmp_path):
    stats = await build(db_path=tmp_path / "k.db", embed=False)
    store = KnowledgeStore(tmp_path / "k.db")
    assert stats["chunks"] == store.chunk_count() > 0
    assert store.has_vectors() is False
    assert store.get_meta("schema_version") == "1"
    assert store.get_meta("chunk_count") == str(store.chunk_count())
    assert store.get_meta("built_at")


async def test_build_embeds_with_fakes_and_writes_dim(tmp_path):
    async def fake_embed(texts):
        return [[0.5] * 4 for _ in texts]

    with (
        patch.object(ingest.settings, "ai_embed_dimensions", 4),
        patch.object(ingest, "embed_texts", side_effect=fake_embed),
    ):
        stats = await build(db_path=tmp_path / "k.db")
    store = KnowledgeStore(tmp_path / "k.db")
    assert store.has_vectors() is True
    assert store.get_meta("dim") == "4"
    assert stats["embedded"] == stats["chunks"]


async def test_second_build_hits_cache_without_calling_embed(tmp_path):
    async def fake_embed(texts):
        return [[0.5] * 4 for _ in texts]

    with patch.object(ingest.settings, "ai_embed_dimensions", 4):
        with patch.object(ingest, "embed_texts", side_effect=fake_embed):
            first = await build(db_path=tmp_path / "k.db")
        with patch.object(ingest, "embed_texts", side_effect=AssertionError("must be cached")):
            second = await build(db_path=tmp_path / "k.db")

    assert first["cache_hits"] == 0
    assert second["cache_hits"] == second["chunks"]
    assert second["embedded"] == 0
    assert KnowledgeStore(tmp_path / "k.db").has_vectors() is True


async def test_build_degrades_to_fts_only_when_embedding_fails(tmp_path):
    with patch.object(ingest, "embed_texts", side_effect=EmbeddingError("all lanes down")):
        stats = await build(db_path=tmp_path / "k.db")
    store = KnowledgeStore(tmp_path / "k.db")
    assert stats["vectors_failed"] > 0
    assert store.chunk_count() > 0
    assert store.has_vectors() is False
    assert store.get_meta("dim") is None


def test_parse_cwe_xml_tolerant(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Weakness_Catalog xmlns="http://cwe.mitre.org/cwe-1" VERSION="4.14">
  <Weaknesses>
    <Weakness ID="79" Name="Improper Neutralization of Input During Web Page Generation">
      <Description>A <b>web</b> application does not neutralize</Description>
      <Extended_Description>Attackers can inject scripts.</Extended_Description>
    </Weakness>
    <Weakness ID="89" Name="Improper Neutralization of Special Elements used in an SQL Command">
      <Description>SQL injection</Description>
    </Weakness>
  </Weaknesses>
</Weakness_Catalog>
"""
    path = tmp_path / "cwec.xml"
    path.write_text(xml, encoding="utf-8")
    docs = parse_cwe_xml(path)
    assert {d.source_id for d in docs} == {"CWE-79", "CWE-89"}
    cwe79 = next(d for d in docs if d.source_id == "CWE-79")
    assert cwe79.source == "cwe-full"
    assert cwe79.cwe_id == "CWE-79"
    assert "neutralize" in cwe79.text.lower()


def test_cli_smoke(tmp_path):
    from services.ai.ingest import main

    rc = main(["--db", str(tmp_path / "cli.db"), "--no-embed"])
    assert rc == 0
    assert KnowledgeStore(tmp_path / "cli.db").chunk_count() > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ingest.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'services.ai.ingest'`.

- [ ] **Step 3: Write `backend/services/ai/ingest.py`**

```python
"""Build knowledge.db from the committed seed corpus (+ optional CWE XML).

Usage: python -m services.ai.ingest [--db PATH] [--sources DIR]
                                     [--cwe-xml PATH] [--no-embed]

The corpus is fully rebuilt each run (reset preserves embed_cache, so repeat
runs are cheap). Embedding failures degrade the build to FTS-only.
"""
import argparse
import asyncio
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from config import settings
from services.ai.embeddings import EmbeddingError, embed_texts
from services.ai.knowledge_sources import KnowledgeDoc, load_all_sources
from services.ai.knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1"


def chunk_doc(doc: KnowledgeDoc) -> List[Dict]:
    rows: List[Dict] = []
    base = {
        "source": doc.source,
        "source_id": doc.source_id,
        "title": doc.title,
        "cwe_id": doc.cwe_id,
        "severity": doc.severity,
        "language": doc.language,
        "vuln_class": doc.vuln_class,
    }
    if doc.sections:
        for section in doc.sections:
            rows.append({
                **base,
                "header": f"{doc.source_id}: {section.heading}",
                "text": section.text,
            })
    else:
        rows.append({**base, "header": f"{doc.source_id}: {doc.title}", "text": doc.text})
    return rows


def _flatten(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten(v) for v in value)
    if isinstance(value, dict):
        parts = [_flatten(v) for k, v in value.items() if not k.startswith("@")]
        return " ".join(p for p in parts if p)
    return str(value)


def parse_cwe_xml(path: Path) -> List[KnowledgeDoc]:
    import xmltodict

    data = xmltodict.parse(Path(path).read_bytes())
    root = next((v for v in data.values() if isinstance(v, dict)), None) or {}
    weaknesses_node = root.get("Weaknesses") or {}
    raw = weaknesses_node.get("Weakness") or []
    if isinstance(raw, dict):
        raw = [raw]
    docs: List[KnowledgeDoc] = []
    for w in raw:
        try:
            wid = str(w.get("@ID", "")).strip()
            name = str(w.get("@Name", "")).strip()
            if not wid or not name:
                continue
            text = " ".join(
                p for p in (_flatten(w.get("Description")), _flatten(w.get("Extended_Description"))) if p
            )
            docs.append(KnowledgeDoc(
                source="cwe-full",
                source_id=f"CWE-{wid}",
                title=f"CWE-{wid}: {name}",
                text=text or name,
                cwe_id=f"CWE-{wid}",
            ))
        except Exception as e:  # noqa: BLE001 - skip malformed entries
            logger.warning("Skipping malformed CWE entry: %s", e)
    logger.info("Parsed %s weaknesses from %s", len(docs), path)
    return docs


def _text_hash(model: str, dim: int, text: str) -> str:
    return hashlib.sha256(f"{model}\x00{dim}\x00{text}".encode()).hexdigest()


async def build(
    db_path: Optional[str | Path] = None,
    *,
    sources_dir: Optional[Path] = None,
    cwe_xml: Optional[Path] = None,
    embed: bool = True,
) -> Dict[str, int]:
    docs = load_all_sources(sources_dir)
    if cwe_xml is not None:
        docs.extend(parse_cwe_xml(Path(cwe_xml)))

    rows: List[Dict] = []
    for doc in docs:
        rows.extend(chunk_doc(doc))

    store = KnowledgeStore(db_path)
    store.reset()
    model = settings.ai_embed_model
    dim = settings.ai_embed_dimensions
    store.initialize(dim=dim if embed else None)

    stats = {"docs": len(docs), "chunks": len(rows), "embedded": 0,
             "cache_hits": 0, "vectors_failed": 0}

    if embed and rows:
        miss_texts: List[str] = []
        miss_rows: List[Dict] = []
        for row in rows:
            key = _text_hash(model, dim, row["text"])
            cached = store.get_cached_embedding(key)
            if cached is not None and len(cached) == dim:
                row["_embedding"] = cached
                stats["cache_hits"] += 1
            else:
                miss_texts.append(row["text"])
                miss_rows.append(row)
        if miss_texts:
            try:
                vectors = await embed_texts(miss_texts)
                for row, vec in zip(miss_rows, vectors):
                    row["_embedding"] = vec
                    store.put_cached_embedding(_text_hash(model, dim, row["text"]), model, dim, vec)
                stats["embedded"] = len(vectors)
            except EmbeddingError as e:
                logger.warning("Embedding unavailable; building FTS-only: %s", e)
                stats["vectors_failed"] = len(miss_texts)

    store.add_chunks(rows)
    store.set_meta("schema_version", SCHEMA_VERSION)
    if any("_embedding" in r for r in rows):
        store.set_meta("dim", str(dim))
        store.set_meta("model", model)
    store.set_meta("built_at", datetime.now(timezone.utc).isoformat())
    store.set_meta("doc_count", str(len(docs)))
    store.set_meta("chunk_count", str(len(rows)))
    logger.info(
        "knowledge.db built: %s docs, %s chunks (%s embedded, %s cached, %s failed)",
        stats["docs"], stats["chunks"], stats["embedded"],
        stats["cache_hits"], stats["vectors_failed"],
    )
    return stats


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m services.ai.ingest",
        description="Build data/knowledge.db from the knowledge seed corpus.",
    )
    parser.add_argument("--db", default=None, help="override DB path (default: data/knowledge.db)")
    parser.add_argument("--sources", type=Path, default=None, help="override sources directory")
    parser.add_argument("--cwe-xml", type=Path, default=None,
                        help="official CWE XML dump from https://cwe.mitre.org/data/downloads.html")
    parser.add_argument("--no-embed", action="store_true", help="skip embeddings (FTS-only build)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    stats = asyncio.run(build(
        db_path=args.db, sources_dir=args.sources,
        cwe_xml=args.cwe_xml, embed=not args.no_embed,
    ))
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: when `embed=True` but embedding fails, the vec0 table exists yet stays empty - `has_vectors()` correctly reports False, and retrieval (Task 6) degrades to FTS-only. If `embed=False`, the vec0 table is not created at all; `initialize()` on a later embedded run adds it (fresh build resets first).

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ingest.py -v`
Expected: 8 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 560 passed (552 + 8).

### Task 6: Retrieval - hybrid search with Reciprocal Rank Fusion

**Files:**
- Create: `backend/services/ai/retrieval.py`
- Test: `backend/tests/test_retrieval.py` (create)

**Interfaces:**
- Consumes: `KnowledgeStore` (Task 4), `embed_query` (Task 3), `settings.rag_top_k / rag_rrf_k / rag_max_context_chars`
- Produces (used by Tasks 7, 8, 9):
  - `build_fts_query(text) -> str` - sanitizes to double-quoted AND-joined terms (len >= 3, max 12, deduped); `""` when nothing usable (prevents FTS5 syntax errors from raw user input)
  - `rrf_fuse(rankings: List[List[int]], k: int) -> List[Tuple[int, float]]` - classic RRF `1/(k+rank)` with rank starting at 1, tie-break by chunk_id ascending
  - `async retrieve(query, *, top_k=None, cwe_id=None, store=None) -> List[Dict]` - hybrid (FTS + vector when db has vectors AND `embed_query` succeeds), RRF, hydrate, returns chunks as dicts with `score` + `rank`; `[]` on empty query / missing db / no candidates
  - `retrieve_fts_only(query, *, top_k=None, cwe_id=None, store=None) -> List[Dict]` - sync FTS lane only, never touches embeddings (enrichment + deterministic evals)
  - Both: `cwe_id` filters hydrated chunks strictly (misses the FTS index because `header` carries `CWE-xx:`, so queries like `"CWE-79"` still find candidates)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_retrieval.py`:

```python
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
    from services.ai.knowledge_store import KnowledgeStore as KS

    store = KS(tmp_path / "missing.db")
    with patch.object(ret, "embed_query", new=AsyncMock(return_value=None)):
        assert await retrieve("anything", store=store) == []
    assert retrieve_fts_only("anything", store=store) == []


def test_fts_only_never_calls_embeddings(tmp_path):
    store = _seed_store(tmp_path)
    with patch.object(ret, "embed_query", new=AsyncMock(side_effect=AssertionError("no embeds"))):
        hits = retrieve_fts_only("sql injection special elements", store=store)
    assert hits and hits[0]["source_id"] == "CWE-89"


def test_cwe_filter_is_strict(tmp_path):
    store = _seed_store(tmp_path)
    hits = retrieve_fts_only("improper neutralization", cwe_id="CWE-79", store=store)
    assert hits
    assert all(h["cwe_id"] == "CWE-79" for h in hits)
    assert retrieve_fts_only("improper neutralization", cwe_id="CWE-404", store=store) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_retrieval.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'services.ai.retrieval'`.

- [ ] **Step 3: Write `backend/services/ai/retrieval.py`**

```python
"""Hybrid retrieval: FTS5 BM25 + vec0 kNN fused with Reciprocal Rank Fusion.

FTS queries are sanitized to quoted AND-terms so untrusted chat input can
never trigger FTS5 syntax errors. Vector lane activates only when the knowledge
db has vectors and embed_query() succeeds; otherwise retrieval silently
degrades to FTS-only.
"""
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


def build_fts_query(text: str) -> str:
    terms: List[str] = []
    for match in _TERM_RE.finditer(text or ""):
        term = match.group(0).strip(".-_")
        if len(term) < 3 or term.lower() in {t.lower() for t in terms}:
            continue
        terms.append(term)
        if len(terms) >= _MAX_TERMS:
            break
    return " AND ".join(f'"{t}"' for t in terms)


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
    match = build_fts_query(query)
    if not match:
        return []
    hits = store.search_fts(match, limit=top_k * _CANDIDATE_FACTOR)
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

    match = build_fts_query(query)
    if match:
        fts_hits = store.search_fts(match, limit=top_k * _CANDIDATE_FACTOR)
        rankings.append([cid for cid, _ in fts_hits])

    if store.has_vectors():
        vector = await embed_query(query)
        if vector is not None:
            vec_hits = store.search_vec(vector, limit=top_k * _CANDIDATE_FACTOR)
            rankings.append([cid for cid, _ in vec_hits])
        else:
            logger.debug("Vector lane skipped: query embedding unavailable")

    fused = rrf_fuse(rankings, k=settings.rag_rrf_k)
    return _hydrate_fused(fused, store, top_k, cwe_id)
```

Note: `retrieve()` runs sync sqlite work on the event loop; per spec this is accepted - single-digit-ms FTS + KNN + hydrate calls, no threadpool needed for Phase 2.

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_retrieval.py -v`
Expected: 8 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 568 passed (560 + 8).

### Task 7: Chat grounding - knowledge context, `[[n]]` citations, ChatResponse.citations

**Files:**
- Create: `backend/services/ai/chat_grounding.py`
- Modify: `backend/routes/ai_chat.py` (retrieve -> pass knowledge -> parse citations; `ChatResponse` gains `citations`)
- Modify: `backend/tests/test_ai_chat.py` (autouse offline-retrieval fixture + 3 new tests)
- Test: `backend/tests/test_chat_grounding.py` (create)

**Interfaces:**
- Consumes: `retrieve` (Task 6), `settings.rag_max_context_chars`, existing `_call_ai_chat` / `ChatResponse` / `_build_scan_context`
- Preserved seams: `_call_ai_chat(...)` keeps returning `str`; `knowledge` is a new OPTIONAL keyword arg (default `None`) so `tests/test_chat_gateway.py` and patched call sites stay valid; `_get_active_model()` untouched; `ChatResponse.citations` defaults to `[]` (backward compatible)
- Produces:
  - `chat_grounding.format_context(chunks, max_chars) -> str` - numbered blocks `[n] header (source=..., id=...)\ntext` joined by blank lines, hard-truncated to `max_chars`
  - `chat_grounding.extract_citations(answer, chunks) -> Tuple[str, List[Dict]]` - rewrites every `[[n]]` -> `[n]`; citations list only for valid, in-range `n` in first-appearance order, deduped; each entry `{n, chunk_id, header, source, source_id, cwe_id}`
  - Route-level `_retrieve_knowledge(message) -> List[Dict]` - wraps `retrieve()`, swallows ALL exceptions, returns `[]` (never breaks chat)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_chat_grounding.py`:

```python
"""Pure functions: knowledge context formatting and citation parsing."""
from services.ai.chat_grounding import extract_citations, format_context


def _chunk(i: int, text=None):
    return {
        "chunk_id": i,
        "header": f"CWE-7{i}: Example weakness {i}",
        "source": "cwe",
        "source_id": f"CWE-7{i}",
        "cwe_id": f"CWE-7{i}",
        "text": text or f"Body of weakness {i} with remediation guidance.",
    }


def test_format_context_numbers_blocks():
    ctx = format_context([_chunk(1), _chunk(2)], max_chars=10_000)
    assert ctx.startswith("[1] CWE-71")
    assert "\n\n[2] CWE-72" in ctx
    assert "Body of weakness 2" in ctx


def test_format_context_respects_max_chars():
    chunks = [_chunk(1, text="x" * 500), _chunk(2, text="y" * 500)]
    ctx = format_context(chunks, max_chars=200)
    assert len(ctx) <= 200
    assert ctx.startswith("[1]")


def test_extract_citations_rewrites_and_dedupes():
    answer, citations = extract_citations(
        "Parameterize queries [[1]]. Use CSP [[2]]; repeat [[1]] again.",
        [_chunk(1), _chunk(2)],
    )
    assert "[[1]]" not in answer and "[[2]]" not in answer
    assert "[1]" in answer and "[2]" in answer
    assert [c["n"] for c in citations] == [1, 2]
    assert citations[0]["source_id"] == "CWE-71"
    assert citations[1]["cwe_id"] == "CWE-72"


def test_extract_citations_ignores_out_of_range_markers():
    answer, citations = extract_citations("See [[9]] and [[0]].", [_chunk(1)])
    assert answer == "See [9] and [0]."
    assert citations == []


def test_extract_citations_no_markers_returns_unchanged():
    answer, citations = extract_citations("Plain answer.", [_chunk(1)])
    assert answer == "Plain answer."
    assert citations == []
```

Append to `backend/tests/test_ai_chat.py` at module level (after `class TestAIChatEndpoint`; reuse the file's existing `_setup_client()` / `_patch_access()` helpers and `@pytest.mark.asyncio` style exactly as shown):

```python
@pytest.fixture(autouse=True)
def _offline_retrieval():
    """Chat tests must never touch knowledge.db or call embedding APIs."""
    with patch("routes.ai_chat.retrieve", new=AsyncMock(return_value=[])):
        yield


@pytest.mark.asyncio
async def test_chat_returns_parsed_citations():
    chunks = [
        {"chunk_id": 1, "header": "CWE-79: XSS", "source": "cwe",
         "source_id": "CWE-79", "cwe_id": "CWE-79", "text": "x"},
        {"chunk_id": 2, "header": "CWE-89: SQLi", "source": "cwe",
         "source_id": "CWE-89", "cwe_id": "CWE-89", "text": "y"},
    ]
    client = _setup_client()
    patchers = _patch_access()
    try:
        with (
            patch("routes.ai_chat._retrieve_knowledge", new=AsyncMock(return_value=chunks)),
            patch(
                "routes.ai_chat._call_ai_chat",
                new=AsyncMock(return_value="Prefer parameterized queries [[2]]. Also [[1]]."),
            ),
        ):
            response = client.post(
                "/api/ai/chat",
                json={"scan_id": "scan-001", "message": "How do I fix SQLi and XSS?"},
            )
    finally:
        for patcher in patchers:
            patcher.stop()

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Prefer parameterized queries [2]. Also [1]."
    assert [c["n"] for c in data["citations"]] == [2, 1]
    assert data["citations"][0]["source_id"] == "CWE-89"
    assert data["citations"][1]["cwe_id"] == "CWE-79"


@pytest.mark.asyncio
async def test_retrieve_knowledge_swallows_errors():
    from routes.ai_chat import _retrieve_knowledge

    with patch("routes.ai_chat.retrieve", new=AsyncMock(side_effect=Exception("db gone"))):
        assert await _retrieve_knowledge("how do I fix XSS?") == []


@pytest.mark.asyncio
async def test_chat_with_empty_knowledge_has_empty_citations():
    client = _setup_client()
    patchers = _patch_access()
    try:
        with (
            patch("routes.ai_chat._retrieve_knowledge", new=AsyncMock(return_value=[])),
            patch("routes.ai_chat._call_ai_chat", new=AsyncMock(return_value="No citations here.")),
        ):
            response = client.post(
                "/api/ai/chat",
                json={"scan_id": "scan-001", "message": "hello"},
            )
    finally:
        for patcher in patchers:
            patcher.stop()

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "No citations here."
    assert data["citations"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_chat_grounding.py tests/test_ai_chat.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'services.ai.chat_grounding'` (grounding tests); the two new route tests ERROR in the autouse fixture with `AttributeError: module 'routes.ai_chat' has no attribute 'retrieve'` (import added in Step 3); existing route tests error the same way.

- [ ] **Step 3: Implement**

Create `backend/services/ai/chat_grounding.py`:

```python
"""Grounded-chat helpers: knowledge context blocks and [[n]] citation parsing."""
import re
from typing import Any, Dict, List, Tuple

CITATION_RE = re.compile(r"\[\[(\d+)\]\]")
_MAX_HEADER = 120


def format_context(chunks: List[Dict[str, Any]], max_chars: int) -> str:
    parts: List[str] = []
    total = 0
    for i, chunk in enumerate(chunks, start=1):
        header = str(chunk.get("header") or chunk.get("title") or "")[:_MAX_HEADER]
        block = (
            f"[{i}] {header} (source={chunk.get('source', '?')}, id={chunk.get('source_id', '?')})\n"
            f"{str(chunk.get('text', '')).strip()}"
        )
        separator = 2 if parts else 0
        if total + separator + len(block) > max_chars:
            budget = max_chars - total - separator
            if budget <= 0:
                break
            parts.append(block[:budget])
            total = max_chars
            break
        parts.append(block)
        total += separator + len(block)
    return "\n\n".join(parts)


def extract_citations(
    answer: str, chunks: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:
    citations: List[Dict[str, Any]] = []
    seen: set = set()

    def _collect(match: "re.Match") -> str:
        n = int(match.group(1))
        idx = n - 1
        if 0 <= idx < len(chunks) and n not in seen:
            seen.add(n)
            chunk = chunks[idx]
            citations.append({
                "n": n,
                "chunk_id": chunk.get("chunk_id"),
                "header": chunk.get("header"),
                "source": chunk.get("source"),
                "source_id": chunk.get("source_id"),
                "cwe_id": chunk.get("cwe_id"),
            })
        return f"[{n}]"

    return CITATION_RE.sub(_collect, answer or ""), citations
```

Modify `backend/routes/ai_chat.py`:

1. Add imports: `from services.ai.chat_grounding import extract_citations, format_context` and `from services.ai.retrieval import retrieve`.
2. `ChatResponse` gains: `citations: List[Dict[str, Any]] = Field(default_factory=list)` (import `Field` from pydantic).
3. Add helper (place above `_call_ai_chat`):

```python
async def _retrieve_knowledge(message: str) -> List[Dict[str, Any]]:
    try:
        return await retrieve(message)
    except Exception as e:
        logger.info("Knowledge retrieval unavailable (chat proceeds ungrounded): %s", e)
        return []
```

4. `_call_ai_chat(...)` signature gains `knowledge: Optional[List[Dict[str, Any]]] = None`. After building `full_system_prompt` (line ~120), append:

```python
if knowledge:
    full_system_prompt += (
        "\n\n## Knowledge Base (grounding)\n"
        + format_context(knowledge, settings.rag_max_context_chars)
        + "\n\nWhen a knowledge block supports your answer, cite it inline as [[n]] "
        "using that block's number. Cite only blocks you actually used. "
        "If the knowledge base does not cover the question, answer from the scan "
        "context without inventing citations."
    )
```

5. In route `ai_chat()`: before the existing `try:` call `knowledge = await _retrieve_knowledge(payload.message)`; pass `knowledge=knowledge` into `_call_ai_chat`; change return to:

```python
reply, citations = extract_citations(raw_reply, knowledge)
return ChatResponse(reply=reply, model_used=_get_active_model(), citations=citations)
```

(rename the local `reply` variable to `raw_reply` for the gateway result).

- [ ] **Step 4: Run the touched tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_chat_grounding.py tests/test_ai_chat.py tests/test_chat_gateway.py -v`
Expected: 5 + existing + 3 new pass, gateway suite unchanged.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 576 passed (568 + 8).

### Task 8: Enrichment grounding - FTS-only guidance in remediation prompts

**Files:**
- Modify: `backend/services/ai/prompts.py` (`build_remediation_prompt` gains kw-only `guidance=None`)
- Modify: `backend/services/ai/ai_processor.py` (module-level `_lookup_guidance` + pass into prompt at line ~141)
- Test: `backend/tests/test_enrichment_guidance.py` (create)

**Interfaces:**
- Consumes: `retrieve_fts_only` (Task 6 - **zero embedding calls**; enrichment stays free-tier-safe and offline-capable), existing `build_remediation_prompt(finding)` callers (`ai_processor.py:141`, `evals/test_eval_golden.py:167`, `tests/test_ai_schemas_prompts.py`) - all positional/single-arg calls keep working because `guidance` is keyword-only with default `None`
- Preserved seams: `enrich_detailed_findings(findings, *, top_n, batch_size)` untouched; `_enrich_batch_with_remediation(findings) -> int` signature untouched; with `guidance=None` the prompt output is **byte-identical** to today (existing exact-shape tests stay green)
- Produces:
  - `prompts.build_remediation_prompt(finding, *, guidance: Optional[List[Dict]] = None) -> str`
  - `ai_processor._lookup_guidance(finding_dict) -> List[Dict]` - builds query from `cwe_id + rule_id + title` (whichever present), `top_k=3`, never raises, skips retrieval entirely on empty query

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_enrichment_guidance.py`:

```python
"""Grounded remediation enrichment: prompt section + FTS-only lookup."""
from unittest.mock import patch

import services.ai.ai_processor as proc
from services.ai.prompts import build_remediation_prompt


def _chunk(i: int = 0):
    return {
        "chunk_id": i + 1,
        "header": "CWE-89: SQL injection",
        "source": "cwe",
        "source_id": "CWE-89",
        "cwe_id": "CWE-89",
        "text": "Use parameterized queries or prepared statements instead of string concatenation.",
    }


def test_prompt_omits_guidance_section_when_absent():
    prompt = build_remediation_prompt({"title": "SQLi", "description": "concat"})
    assert "Knowledge grounding" not in prompt
    assert "Prompt version:" in prompt
    assert prompt.index("## Finding") < prompt.index("## Required Output")


def test_prompt_includes_guidance_before_required_output():
    prompt = build_remediation_prompt({"title": "SQLi"}, guidance=[_chunk()])
    assert "## Knowledge grounding" in prompt
    assert "CWE-89: SQL injection" in prompt
    assert "parameterized queries" in prompt
    assert prompt.index("Knowledge grounding") < prompt.index("## Required Output")


def test_prompt_caps_guidance_at_three_chunks():
    chunks = [_chunk(i) for i in range(6)]
    for i, c in enumerate(chunks):
        c["header"] = f"Header {i}"
    prompt = build_remediation_prompt({"title": "x"}, guidance=chunks)
    assert "Header 0" in prompt and "Header 2" in prompt
    assert "Header 3" not in prompt


def test_lookup_guidance_returns_fts_hits():
    with patch.object(proc, "retrieve_fts_only", return_value=[_chunk()]) as m:
        out = proc._lookup_guidance({"cwe_id": "CWE-89", "title": "SQL injection"})
    assert out == [_chunk()]
    assert m.call_args.kwargs.get("top_k") == 3
    assert "CWE-89" in m.call_args.args[0]


def test_lookup_guidance_never_raises():
    with patch.object(proc, "retrieve_fts_only", side_effect=Exception("boom")):
        assert proc._lookup_guidance({"title": "SQLi"}) == []


def test_lookup_guidance_skips_retrieval_on_empty_query():
    with patch.object(proc, "retrieve_fts_only", return_value=[]) as m:
        assert proc._lookup_guidance({}) == []
        assert proc._lookup_guidance({"title": "", "cwe_id": None}) == []
        m.assert_not_called()


async def test_enrich_batch_passes_guidance_into_prompt():
    processor = proc.VulnerabilityAIProcessor()
    finding = {
        "title": "SQL injection in login handler",
        "description": "query built by concatenation",
        "cwe_id": "CWE-89",
    }
    captured = {}

    async def fake_complete(gateway, *, system, user, purpose, schema,
                            temperature, use_cache, **kwargs):
        captured["user"] = user
        return (object(), True)

    with (
        patch.object(proc, "retrieve_fts_only", return_value=[_chunk()]),
        patch.object(proc, "complete_structured", side_effect=fake_complete),
        patch.object(processor, "_apply_advice"),
    ):
        applied = await processor._enrich_batch_with_remediation([finding])
    assert applied == 1
    assert "## Knowledge grounding" in captured["user"]
    assert "Use parameterized queries" in captured["user"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_enrichment_guidance.py -v`
Expected: FAIL - `AttributeError: module 'services.ai.ai_processor' has no attribute '_lookup_guidance'`, plus guidance-section assertions failing (prompt has no section).

- [ ] **Step 3: Implement**

In `backend/services/ai/prompts.py`:

1. Signature: `def build_remediation_prompt(finding: Dict[str, Any], *, guidance: Optional[List[Dict[str, Any]]] = None) -> str:` (ensure `Optional` imported).
2. Add a private helper above it:

```python
_MAX_GUIDANCE_CHUNKS = 3
_MAX_GUIDANCE_CHARS = 400


def _guidance_section(guidance: Optional[List[Dict[str, Any]]]) -> str:
    if not guidance:
        return ""
    lines = [
        "## Knowledge grounding",
        "Reference material for this finding. Use it only where it directly "
        "applies; do not quote it verbatim.",
        "",
    ]
    for chunk in guidance[:_MAX_GUIDANCE_CHUNKS]:
        header = _one_line(chunk.get("header") or chunk.get("title"), 120)
        text = str(chunk.get("text") or "").replace("\n", " ")[:_MAX_GUIDANCE_CHARS]
        lines.append(f"- {header}: {text}")
    lines.append("")
    return "\n".join(lines) + "\n"
```

3. In the returned f-string, insert `{_guidance_section(guidance)}` immediately before `"## Required Output\n"` (so empty guidance renders nothing and the existing byte-shape is preserved).

In `backend/services/ai/ai_processor.py`:

1. Add import: `from services.ai.retrieval import retrieve_fts_only`.
2. Add module-level helper (place next to the other module-level helpers near the bottom, above `get_ai_processor`):

```python
def _lookup_guidance(finding: Dict[str, Any]) -> List[Dict[str, Any]]:
    """FTS-only knowledge lookup for one finding. Never raises, never embeds."""
    query = " ".join(
        str(finding.get(key) or "").strip()
        for key in ("cwe_id", "rule_id", "title")
    ).strip()
    if not query:
        return []
    try:
        return retrieve_fts_only(query, top_k=3)
    except Exception as e:
        logger.debug("Guidance lookup failed (continuing ungrounded): %s", e)
        return []
```

3. In `_enrich_batch_with_remediation`, before the `complete_structured` call add `guidance = _lookup_guidance(data)` and change the call to `user=build_remediation_prompt(data, guidance=guidance),`.

- [ ] **Step 4: Run the new + touched tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_enrichment_guidance.py tests/test_ai_schemas_prompts.py tests/test_enrichment.py tests/test_ai_processor*.py -v`
Expected: 7 new pass; existing prompt-shape and enrichment tests unchanged/green.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 583 passed (576 + 7).

### Task 9: Retrieval evals - golden queries, FTS-only, deterministic

**Files:**
- Test: `backend/evals/test_rag_golden.py` (create)

**Interfaces:**
- Consumes: `build` (Task 5), `retrieve_fts_only` (Task 6), `KnowledgeStore` (Task 4), pytest marker `eval` (already registered in `pytest.ini`; `testpaths = tests` keeps these out of the default run)
- Runtime: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval` - must stay **offline** (module fixture builds a throwaway `knowledge.db` from the committed corpus with `embed=False`; no embedding calls, no dependence on operator-built `data/knowledge.db`)
- Golden queries are written against real corpus vocabulary (verified against seed corpus titles/sections). FTS semantics that shaped them: `build_fts_query` AND-joins all terms of length >= 3 (hyphen splits tokens: "hard-coded" -> `hard` AND `coded`; no stemming: "credential" != "credentials"), and the FTS index covers `title, header, text` (Task 4 amendment).

- [ ] **Step 1: Write the failing tests**

Create `backend/evals/test_rag_golden.py`:

```python
"""Golden retrieval evals - FTS-only, deterministic, offline.

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
```

- [ ] **Step 2: Run the new evals**

Run: `.venv\Scripts\python.exe -m pytest evals/test_rag_golden.py -v -m eval`
Expected: 4 passed. This task is test-only and the production code (Tasks 5/6) already exists, so green is the expected outcome. If a golden query fails, do NOT weaken the query first - inspect `retrieve_fts_only(...)` output and the corpus entry: the query vocabulary must be AND-matchable (every term of length >= 3 present in title/header/text of the target chunk). Fix the query only if it was poorly written; fix `retrieval.py`/`ingest.py` only for a genuine defect.

- [ ] **Step 3: No production code changes**

This task is evaluation-only. If a golden pair exposes a real retrieval defect, fix it in `services/ai/retrieval.py` or `services/ai/ingest.py` (smallest change), re-run Steps 2/4, and note the fix in the task log.

- [ ] **Step 4: Run the eval suite**

Run: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval`
Expected: all evals pass (28 existing Phase 1 evals + 4 new RAG evals = 32).

- [ ] **Step 5: Confirm the default suite is unaffected**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q`
Expected: 583 passed (evals are excluded via `testpaths`).

### Task 10: Full verification, seam audit, independent review

**Files:** none created - verification and audit only.

- [ ] **Step 1: Full default suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q` (from `backend/`)
Expected: **583 passed**, 0 failed. Investigate any failure before proceeding - do not re-run hoping for green.

- [ ] **Step 2: Full eval suite**

Run: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval`
Expected: **32 passed** (28 Phase 1 + 4 Phase 2 RAG).

- [ ] **Step 3: Import smoke**

Run:
```
.venv\Scripts\python.exe -c "import services.ai.embeddings, services.ai.knowledge_store, services.ai.ingest, services.ai.retrieval, services.ai.chat_grounding, services.ai.knowledge_sources, services.ai.prompts, services.ai.ai_processor, routes.ai_chat; print('imports ok')"
```
Expected: `imports ok` (use the venv interpreter with `workdir=backend`; ignore LSP diagnostics - the LSP interpreter differs from `.venv`).

- [ ] **Step 4: Dependency constraint audit**

Run: `git diff backend/requirements.txt`
Expected: exactly one added line - `sqlite-vec>=0.1.0` (or equivalent pin). Any other diff (new libs, version churn) is a violation: revert the extra lines.

- [ ] **Step 5: Seam + scope audit (greps)**

From repo root, verify ALL of the following:

```
git diff --name-only
```
Expected paths ONLY under: `backend/config.py`, `.env.example`, `backend/requirements.txt`, `backend/services/ai/*` (new/modified), `backend/routes/ai_chat.py`, `backend/tests/test_*.py`, `backend/evals/test_rag_golden.py`, `backend/knowledge/**`, `docs/superpowers/plans/2026-10-07-onyx-phase2-rag.md`.
Forbidden (must be absent): `backend/services/scanning/workflow/enhanced.py`, `backend/tests/test_scan_progress.py`, anything under `frontend/`, any git commit (run `git log --oneline -3` - Phase 2 work must NOT appear).

```
grep -n "async def _call_ai_chat" backend/routes/ai_chat.py
```
Expected: signature still returns through `-> str` path (knowledge is optional kw-only addition).

```
grep -n "def enrich_detailed_findings" backend/services/ai/enrichment.py
```
Expected: `findings, *, top_n=None, batch_size=5) -> bool` unchanged.

```
grep -rn "def _call_ai_chat\|def _get_active_model\|def get_ai_processor\|def create_ai_processor" backend/services/ai backend/routes/ai_chat.py
```
Expected: all four still present.

- [ ] **Step 6: Manual CLI smoke (non-test verification)**

Run:
```
.venv\Scripts\python.exe -m services.ai.ingest --db %TEMP%\onyx-knowledge-smoke.db --no-embed
```
Expected: JSON stats printed, exit code 0, `chunk_count > 0`. Delete the temp db afterwards.

- [ ] **Step 7: Independent review (required checkpoint)**

Dispatch the `reviewer` subagent with:
- scope: `git diff` since commit `851cf27` (Phase 1) plus new untracked files under `backend/services/ai`, `backend/knowledge`, `backend/tests`, `backend/evals`, and this plan;
- constraints: no new deps beyond `sqlite-vec`; AI/RAG failures must degrade gracefully (never raise into request paths); preserved seams listed in Global Constraints; citations numbering must match `format_context` ordering; no commits;
- evidence to cite: full suite 583, evals 32, requirements diff single-line.

Resolve all critical/high findings before reporting completion; document accepted-severity findings with rationale.

- [ ] **Step 8: Operator note (documented, not executed by CI)**

Post-plan developer step (optional, needs network for real embeddings): `.venv\Scripts\python.exe -m services.ai.ingest` builds `data/knowledge.db` (add `--cwe-xml path/to/cwec.xml` for the full CWE corpus). Chat grounding and enrichment guidance activate automatically once the db exists; everything works ungrounded without it.
