"""Grounded-chat helpers: knowledge context blocks and [[n]] citation parsing."""
import re
from typing import Any, Dict, List, Tuple

CITATION_RE = re.compile(r"\[\[(\d+)\]\]")
_MAX_HEADER = 120


def format_context(
    chunks: List[Dict[str, Any]], max_chars: int
) -> Tuple[str, int]:
    """Render numbered knowledge blocks; returns (text, visible_block_count).

    visible_block_count is how many blocks (fully or partially) appear in the
    text - callers must bound citation resolution to chunks[:visible] so a
    hallucinated [[n]] can never resolve to a block the model never saw.
    """
    parts: List[str] = []
    total = 0
    for i, chunk in enumerate(chunks, start=1):
        header = " ".join(
            str(chunk.get("header") or chunk.get("title") or "").split()
        )[:_MAX_HEADER]
        text = " ".join(str(chunk.get("text") or "").split())
        block = (
            f"[{i}] {header} (source={chunk.get('source', '?')}, id={chunk.get('source_id', '?')})\n"
            f"{text}"
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
    return "\n\n".join(parts), len(parts)


def extract_citations(
    answer: str, chunks: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:
    citations: List[Dict[str, Any]] = []
    seen: set = set()

    def _collect(match: "re.Match") -> str:
        n = int(match.group(1))
        idx = n - 1
        if 0 <= idx < len(chunks):
            if n not in seen:
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
        return ""  # out-of-range marker: drop, never show a dangling [n]

    return CITATION_RE.sub(_collect, answer or ""), citations
