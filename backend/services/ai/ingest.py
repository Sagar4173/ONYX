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
    model = settings.ai_embed_model
    dim = settings.ai_embed_dimensions

    stats = {"docs": len(docs), "chunks": len(rows), "embedded": 0,
             "cache_hits": 0, "vectors_failed": 0}

    # Phase A: resolve embeddings FIRST (network-bound, slow) while the live
    # db keeps serving its previous corpus; only Phase B mutates the schema.
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

    # Phase B: fast local rebuild (reset -> schema -> rows -> meta).
    store.reset()
    store.initialize(dim=dim if embed else None)
    store.add_chunks(rows)
    store.set_meta("schema_version", SCHEMA_VERSION)
    if store.has_vectors():
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
