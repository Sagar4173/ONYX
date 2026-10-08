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
