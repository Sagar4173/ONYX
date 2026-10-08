"""Ingest pipeline: chunking, cache-aware embedding, XML, CLI."""
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


async def test_failed_rebuild_preserves_previous_db(tmp_path):
    db = tmp_path / "k.db"
    await build(db_path=db, embed=False)
    first_count = KnowledgeStore(db).chunk_count()
    assert first_count > 0

    with patch.object(ingest, "embed_texts", side_effect=RuntimeError("power loss")):
        try:
            await build(db_path=db)
        except RuntimeError:
            pass
        else:
            raise AssertionError("unexpected build failure must propagate")
    assert KnowledgeStore(db).chunk_count() == first_count


async def test_build_fresh_db_with_vec0_unavailable_is_fts_only(tmp_path):
    db = tmp_path / "fresh.db"

    async def fake_embed(texts):
        return [[0.5] * 4 for _ in texts]

    with (
        patch.dict(__import__("sys").modules, {"sqlite_vec": None}),
        patch.object(ingest.settings, "ai_embed_dimensions", 4),
        patch.object(ingest, "embed_texts", side_effect=fake_embed),
    ):
        await build(db_path=db)
    store = KnowledgeStore(db)
    assert store.chunk_count() > 0, "vec0 missing must not crash a fresh build"
    assert store.has_vectors() is False
    assert store.get_meta("dim") is None
    assert store.search_fts("parameterized", 5), "FTS must remain usable"


async def test_rebuild_with_vec0_unavailable_preserves_live_db(tmp_path):
    db = tmp_path / "k.db"

    async def fake_embed(texts):
        return [[0.5] * 4 for _ in texts]

    with (
        patch.object(ingest.settings, "ai_embed_dimensions", 4),
        patch.object(ingest, "embed_texts", side_effect=fake_embed),
    ):
        await build(db_path=db)
    assert KnowledgeStore(db).has_vectors() is True

    with (
        patch.dict(__import__("sys").modules, {"sqlite_vec": None}),
        patch.object(ingest.settings, "ai_embed_dimensions", 4),
        patch.object(ingest, "embed_texts", side_effect=fake_embed),
    ):
        await build(db_path=db)
    store = KnowledgeStore(db)
    assert store.chunk_count() > 0, "rebuild without vec0 must not empty the live db"
    assert store.get_meta("schema_version") == "1"
    assert store.search_fts("parameterized", 5)
