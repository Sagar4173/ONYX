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
