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
