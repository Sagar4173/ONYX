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
    ctx, visible = format_context([_chunk(1), _chunk(2)], max_chars=10_000)
    assert ctx.startswith("[1] CWE-71")
    assert "\n\n[2] CWE-72" in ctx
    assert "Body of weakness 2" in ctx
    assert visible == 2


def test_format_context_respects_max_chars():
    chunks = [_chunk(1, text="x" * 500), _chunk(2, text="y" * 500)]
    ctx, visible = format_context(chunks, max_chars=200)
    assert len(ctx) <= 200
    assert ctx.startswith("[1]")
    assert visible >= 1


def test_truncated_blocks_beyond_visible_count_not_citable():
    chunks = [_chunk(1, text="x" * 500), _chunk(2, text="y" * 500), _chunk(3, text="z" * 500)]
    ctx, visible = format_context(chunks, max_chars=200)
    assert ctx and visible < len(chunks)
    answer, citations = extract_citations("See [[3]].", chunks[:visible])
    assert "[[3]]" not in answer
    assert "[3]" not in answer
    assert citations == []


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
    assert "[[9]]" not in answer
    assert "[9]" not in answer and "[0]" not in answer
    assert "See" in answer and "." in answer
    assert citations == []


def test_extract_citations_no_markers_returns_unchanged():
    answer, citations = extract_citations("Plain answer.", [_chunk(1)])
    assert answer == "Plain answer."
    assert citations == []


def test_extract_citations_includes_capped_normalized_text():
    long_text = "word " * 600  # 3000 chars
    answer, citations = extract_citations("Fixed [[1]] now.", [_chunk(1, text=long_text)])
    assert [c["n"] for c in citations] == [1]
    text = citations[0]["text"]
    assert len(text) <= 1500
    assert "  " not in text
    assert text.startswith("word word")


def test_extract_citations_text_empty_when_chunk_has_none():
    chunk = _chunk(1)
    chunk.pop("text")
    _, citations = extract_citations("See [[1]].", [chunk])
    assert citations[0]["text"] == ""
