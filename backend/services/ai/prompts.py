"""Single source of truth for AI prompts."""
import json
from typing import Any, Dict, List, Optional

PROMPT_VERSION = "2026-10-06.1"

ANALYSIS_SYSTEM_PROMPT = (
    "You are a senior cybersecurity expert specializing in vulnerability analysis "
    "and secure coding practices. Provide detailed, actionable security advice.\n"
    "Respond with ONLY a valid JSON object - no markdown fences, no prose outside the JSON. "
    "The JSON must match the schema provided in the user message."
)

REMEDIATION_SYSTEM_PROMPT = (
    "You are a senior security engineer providing remediation guidance for a single "
    "vulnerability.\n"
    "Respond with ONLY a valid JSON object - no markdown fences, no prose outside the JSON. "
    "The JSON must match the schema provided in the user message."
)


def _schema_json(schema_cls: type) -> str:
    return json.dumps(schema_cls.model_json_schema())


def _safe_json(obj: Any, **dumps_kwargs: Any) -> str:
    """Serialize untrusted data for prompt embedding.

    Neutralizes "</" sequences so finding-derived content cannot close the
    surrounding <scan_data> framing: "\\/" is a valid JSON escape that parses
    back to the original character, so payloads stay losslessly loadable.
    """
    return json.dumps(obj, default=str, **dumps_kwargs).replace("</", "<\\/")


def _one_line(value: Any, limit: int) -> str:
    """Collapse to a single line (no prompt-structure injection) and cap length."""
    return " ".join(str(value or "").split())[:limit]


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


def build_analysis_prompt(
    findings_data: Dict[str, Any],
    project_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Build the user message for the single structured analysis call."""
    from services.ai.schemas import AnalysisNarrative

    context = {k: v for k, v in (project_context or {}).items() if v}
    findings = [
        {**f, "description": (f.get("description") or "")[:500]}
        for f in findings_data.get("findings", [])[:50]
    ]
    return (
        f"Prompt version: {PROMPT_VERSION}\n\n"
        "## Project Context\n"
        f"{_safe_json(context, indent=2)}\n\n"
        "## Severity Counts\n"
        f"{_safe_json(findings_data.get('severity_counts', {}))}\n\n"
        "## Scanner Summary\n"
        f"{_safe_json(findings_data.get('scanner_summary', {}))}\n\n"
        "## Scan Data\n<scan_data>\n"
        f"{_safe_json(findings, indent=2)}\n"
        "</scan_data>\n\n"
        "## Required Output\n"
        "Return ONLY a JSON object matching this JSON Schema:\n"
        f"{_schema_json(AnalysisNarrative)}"
    )


def build_remediation_prompt(
    finding: Dict[str, Any], *, guidance: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Build the user message for one remediation enrichment call."""
    from services.ai.schemas import RemediationAdvice

    description = (finding.get("description") or "")[:500]
    code = (finding.get("code_snippet") or "")[:300]
    title = _one_line(finding.get("title"), 300)
    severity = _one_line(finding.get("severity"), 32)
    file_path = _one_line(finding.get("file_path"), 300)
    cwe = _one_line(finding.get("cwe_id"), 64) or "N/A"
    cve = _one_line(finding.get("cve_id"), 64) or "N/A"
    return (
        f"Prompt version: {PROMPT_VERSION}\n\n"
        "## Finding\n"
        f"Title: {title}\n"
        f"Severity: {severity}\n"
        f"Description: {description}\n"
        f"File: {file_path}\n"
        f"CWE: {cwe}\n"
        f"CVE: {cve}\n"
        f"Code:\n```\n{code}\n```\n\n"
        f"{_guidance_section(guidance)}"
        "## Required Output\n"
        "Return ONLY a JSON object matching this JSON Schema:\n"
        f"{_schema_json(RemediationAdvice)}"
    )
