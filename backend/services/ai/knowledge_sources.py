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
