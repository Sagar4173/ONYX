# ONYX Phase 1 — AI Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ONYX's three duplicate AI processors and scattered inline provider calls with a single free-tier LLM gateway (Gemini → Groq → OpenRouter → Ollama failover), one structured analysis call per scan, revived auto-fix enrichment, AI decoupled from scan completion, and a deterministic eval harness.

**Architecture:** A new `LLMGateway` owns all provider I/O: ordered failover chain, sliding-window rate limits, circuit breaker, daily quota ledger, response cache, and invocation traces. One unified `VulnerabilityAIProcessor` computes deterministic fields (risk/security scores, threat categories, fix time, roadmap) in code and makes a single JSON-structured gateway call for the narrative. Triage and chat route through the same gateway; post-scan AI runs as a background task after the scan reaches 100%.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2 (structured outputs), `openai` (OpenAI-compatible clients for Groq/OpenRouter/Ollama), `google-genai` (Gemini), Motor/Beanie (quota/cache/trace persistence), pytest + pytest-asyncio (`asyncio_mode=auto`).

## Global Constraints

- **Test command** (from `E:\Projects\ONYX\backend`): `.venv\Scripts\python.exe -m pytest tests/ -v` — every task must leave this suite green.
- **Zero new dependencies.** Only packages already in `backend/requirements.txt` may be used (`openai`, `google-genai`, `httpx`, `pydantic`, `pymongo`). `git diff backend/requirements.txt` must stay empty.
- **$0 AI budget.** Free-tier providers only: Gemini free tier (primary), Groq free tier, OpenRouter `:free` models, Ollama local (dev). Defaults: `gemini-2.5-flash`, `openai/gpt-oss-120b`, `google/gemma-4-27b-it:free`, `gpt-4o-mini` (legacy OpenAI). Provider chain default: `gemini,groq,openrouter,ollama`.
- **No git commits.** The user has not authorized commits; do NOT run `git commit`, `git add`, or any history-affecting command. Leave changes unstaged. (Commit steps from the plan template are intentionally omitted.)
- **Do not modify** `backend/services/scanning/workflow/enhanced.py`, `backend/tests/test_scan_progress.py`, or the frontend — they are a separate workflow path / later phase.
- **Preserve these test seams** (name and signature): `TriageService._call_ai(prompt) -> Optional[str]`, `routes.ai_chat._call_ai_chat(message, scan_context, conversation_history) -> str`, `get_ai_processor()`, `AIProcessorError`, `create_ai_processor()`.
- **AI processing must never fail a scan.** All AI failures degrade gracefully (log + fallback), except `create_ai_processor()` when no provider is configured (existing contract).
- Run all commands from `E:\Projects\ONYX\backend` unless stated otherwise.

## File Structure

**Create:**

| File | Responsibility |
|---|---|
| `backend/services/ai/schemas.py` | Structured-output Pydantic models (`AnalysisNarrative`, `RemediationAdvice`) + `parse_json_model` |
| `backend/services/ai/prompts.py` | `PROMPT_VERSION`, system prompts, prompt builders (single source of truth) |
| `backend/services/ai/stores.py` | `QuotaLedger` (daily budget) + `ResponseCache` (prompt-hash cache), Mongo-backed with memory fallback |
| `backend/services/ai/trace.py` | `InvocationTracer` — every gateway call logged to `ai_invocations` + in-memory ring |
| `backend/services/ai/gateway.py` | `LLMGateway`: provider specs, adapters, failover, rate limit, circuit breaker, `complete`/`complete_messages`/`complete_structured`, `get_gateway()`/`reset_gateway()` |
| `backend/services/ai/factory.py` | `create_ai_processor()` (moved from `gemini_ai_processor.py`) |
| `backend/services/ai/enrichment.py` | `select_findings_for_enrichment()` + `enrich_detailed_findings()` — severity-stratified top-N remediation enrichment |
| `backend/services/ai/post_scan.py` | `schedule_post_scan_ai()` / `run_post_scan_ai()` — background AI after scan completes |
| `backend/tests/test_config_ai.py` | Task 1 config tests |
| `backend/tests/test_ai_schemas_prompts.py` | Task 2 schema/prompt tests |
| `backend/tests/test_ai_stores.py` | Task 3 quota/cache/trace tests |
| `backend/tests/test_gateway.py` | Task 4 gateway tests |
| `backend/tests/test_ai_processor.py` | Task 5 unified processor tests (replaces `test_ollama_processor.py`) |
| `backend/tests/test_ai_factory.py` | Task 6 factory/import tests |
| `backend/tests/test_triage_gateway.py` | Task 7 triage-via-gateway tests |
| `backend/tests/test_chat_gateway.py` | Task 8 chat-via-gateway tests |
| `backend/tests/test_enrichment.py` | Task 9 enrichment tests |
| `backend/tests/test_post_scan.py` | Task 10 background AI tests |
| `backend/evals/__init__.py`, `backend/evals/conftest.py`, `backend/evals/cases.py`, `backend/evals/test_eval_golden.py` | Task 11 deterministic eval harness (24 golden cases) |

**Modify:** `backend/config.py` (AI settings + validation), `backend/.env.example` (provider chain + governance), `backend/services/ai/ai_processor.py` (unified processor), `backend/services/ai/__init__.py` (drop star imports), `backend/services/triage/triage_service.py` (`_call_ai` via gateway), `backend/routes/ai_chat.py` (`_call_ai_chat`/`_get_active_model` via gateway), `backend/routes/webhook/scan_operations.py` (remove inline AI; add enrichment; schedule background), `backend/pytest.ini` (add `eval` marker).

**Delete:** `backend/services/ai/gemini_ai_processor.py`, `backend/services/ai/ollama_ai_processor.py`, `backend/tests/test_ollama_processor.py`.

---

### Task 1: Config — provider chain, Groq/OpenRouter, governance knobs

**Files:**
- Modify: `backend/config.py:57-75` (AI settings), `backend/config.py:197-227` (`validate_ai_config` + `ai_available`), `backend/config.py:244-270` (`validate_settings_on_startup` AI section)
- Modify: `backend/.env.example:60-73`
- Test: `backend/tests/test_config_ai.py` (create)

**Interfaces:**
- Consumes: nothing (first task)
- Produces (used by Tasks 2, 4, 9, 10):
  - `Settings.provider_chain() -> list[str]` — ordered provider names for current mode (`auto` → parsed chain; explicit → single)
  - `Settings.configured_provider_chain() -> list[str]` — chain filtered to providers with credentials (ollama always counts; `auto` mode appends configured legacy `openai` last)
  - `Settings._provider_configured(name: str) -> bool`
  - New fields: `ai_provider_chain`, `groq_api_key`, `groq_model`, `openrouter_api_key`, `openrouter_model`, `ai_rate_limit_rpm`, `ai_rate_limit_rpd`, `ai_cache_ttl_days`, `ai_enrich_top_n`, `ai_post_scan_concurrency`
  - Changed defaults: `openai_model` → `"gpt-4o-mini"`, `gemini_model` → `"gemini-2.5-flash"`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_config_ai.py`:

```python
"""Tests for AI provider chain configuration and validation."""
from config import Settings


def _settings(**overrides):
    base = dict(
        _env_file=None,
        ai_provider="auto",
        ai_provider_chain="gemini,groq,openrouter,ollama",
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        gemini_api_key=None,
        gemini_model="gemini-2.5-flash",
        groq_api_key=None,
        groq_model="openai/gpt-oss-120b",
        openrouter_api_key=None,
        openrouter_model="google/gemma-4-27b-it:free",
        ai_local_base_url="http://localhost:11434/v1",
        ai_local_model="qwen2.5-coder:7b",
        ai_rate_limit_rpm=15,
        ai_rate_limit_rpd=500,
        ai_cache_ttl_days=7,
        ai_enrich_top_n=10,
        ai_post_scan_concurrency=2,
    )
    base.update(overrides)
    return Settings(**base)


def test_provider_chain_defaults():
    s = _settings()
    assert s.provider_chain() == ["gemini", "groq", "openrouter", "ollama"]


def test_provider_chain_explicit_single():
    s = _settings(ai_provider="groq")
    assert s.provider_chain() == ["groq"]


def test_configured_chain_filters_missing_keys():
    s = _settings(gemini_api_key="x" * 20)
    assert s.configured_provider_chain() == ["gemini", "ollama"]


def test_configured_chain_appends_legacy_openai_when_unchained():
    s = _settings(openai_api_key="sk-legacy" + "x" * 15)
    assert s.configured_provider_chain() == ["ollama", "openai"]


def test_validate_auto_reports_configured_chain():
    s = _settings(groq_api_key="g" * 20)
    ok, msg = s.validate_ai_config()
    assert ok is True
    assert "groq" in msg
    assert "ollama" in msg


def test_validate_explicit_openai_missing_key():
    s = _settings(ai_provider="openai", openai_api_key=None)
    ok, msg = s.validate_ai_config()
    assert ok is False
    assert "OPENAI_API_KEY" in msg


def test_validate_unknown_provider():
    s = _settings(ai_provider="azure")
    ok, msg = s.validate_ai_config()
    assert ok is False
    assert "Unknown AI provider" in msg


def test_model_defaults_are_current():
    s = _settings()
    assert s.gemini_model == "gemini-2.5-flash"
    assert s.openai_model == "gpt-4o-mini"
    assert s.groq_model == "openai/gpt-oss-120b"
    assert s.openrouter_model == "google/gemma-4-27b-it:free"


def test_governance_defaults():
    s = _settings()
    assert s.ai_rate_limit_rpm == 15
    assert s.ai_rate_limit_rpd == 500
    assert s.ai_cache_ttl_days == 7
    assert s.ai_enrich_top_n == 10
    assert s.ai_post_scan_concurrency == 2


def test_ai_available_single_explicit_provider():
    s = _settings(ai_provider="gemini", gemini_api_key="k" * 20)
    assert s.ai_available is True
    s2 = _settings(ai_provider="gemini", gemini_api_key=None)
    assert s2.ai_available is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config_ai.py -v`
Expected: FAIL — `TypeError`/`ValidationError` for unexpected `ai_provider_chain`, `groq_api_key` etc.

- [ ] **Step 3: Replace the AI settings block in `config.py`**

Replace lines 57-75 (from `# AI Configuration` through `ai_local_timeout`) with:

```python
    # AI Configuration
    # Supported providers: auto (follows ai_provider_chain), ollama, openai, gemini, groq, openrouter
    ai_provider: str = Field(default="auto", env="AI_PROVIDER")
    # Failover chain used when ai_provider=auto (left -> right)
    ai_provider_chain: str = Field(default="gemini,groq,openrouter,ollama", env="AI_PROVIDER_CHAIN")

    # OpenAI (legacy fallback)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")

    # Google Gemini (primary free-tier provider)
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    gemini_max_tokens: int = Field(default=2000, env="GEMINI_MAX_TOKENS")

    # Groq (free-tier fallback, OpenAI-compatible API)
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", env="GROQ_MODEL")

    # OpenRouter (free-tier fallback, OpenAI-compatible API)
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="google/gemma-4-27b-it:free", env="OPENROUTER_MODEL")

    # Ollama (self-hosted local LLM, dev only)
    ai_local_base_url: str = Field(default="http://ollama:11434/v1", env="AI_LOCAL_BASE_URL")
    ai_local_model: str = Field(default="qwen2.5-coder:7b", env="AI_LOCAL_MODEL")
    ai_local_timeout: int = Field(default=120, env="AI_LOCAL_TIMEOUT")

    # AI gateway governance (budget protection)
    ai_rate_limit_rpm: int = Field(default=15, env="AI_RATE_LIMIT_RPM")      # per provider, per minute
    ai_rate_limit_rpd: int = Field(default=500, env="AI_RATE_LIMIT_RPD")     # per provider, per day
    ai_cache_ttl_days: int = Field(default=7, env="AI_CACHE_TTL_DAYS")
    ai_enrich_top_n: int = Field(default=10, env="AI_ENRICH_TOP_N")          # findings enriched per scan
    ai_post_scan_concurrency: int = Field(default=2, env="AI_POST_SCAN_CONCURRENCY")
```

- [ ] **Step 4: Add chain helpers and rewrite validation in `config.py`**

Replace the `validate_ai_config` method (starts at old line 197) and `ai_available` property (old lines 221-227) with:

```python
    def provider_chain(self) -> list[str]:
        """Ordered provider names for the configured AI provider mode."""
        if self.ai_provider.lower() != "auto":
            return [self.ai_provider.lower()]
        return [p.strip().lower() for p in self.ai_provider_chain.split(",") if p.strip()]

    def _provider_configured(self, name: str) -> bool:
        """Whether a provider has credentials (ollama needs none)."""
        if name == "ollama":
            return True
        keys = {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "groq": self.groq_api_key,
            "openrouter": self.openrouter_api_key,
        }
        key = keys.get(name)
        return bool(key) and len(key) > 10

    def configured_provider_chain(self) -> list[str]:
        """Chain entries that are actually usable right now."""
        chain = [name for name in self.provider_chain() if self._provider_configured(name)]
        if self.ai_provider.lower() != "auto":
            return chain
        # Legacy installs may only have OPENAI_API_KEY set; keep it as a last resort.
        if self._provider_configured("openai") and "openai" not in chain:
            chain.append("openai")
        return chain

    def validate_ai_config(self) -> tuple[bool, str]:
        """
        Validate that the selected AI provider has a valid API key configured.
        Returns (is_valid, message) tuple.
        """
        provider = self.ai_provider.lower()
        if provider == "auto":
            chain = self.configured_provider_chain()
            if not chain:
                return False, "No AI providers configured for AI_PROVIDER_CHAIN"
            return True, "Auto AI chain: " + " -> ".join(chain)
        if provider == "ollama":
            return True, "Ollama local AI configured"
        if provider not in ("openai", "gemini", "groq", "openrouter"):
            return False, (
                f"Unknown AI provider: {provider}. "
                "Use 'auto', 'ollama', 'openai', 'gemini', 'groq', or 'openrouter'"
            )
        api_key = getattr(self, f"{provider}_api_key")
        if api_key and len(api_key) > 10:
            return True, f"{provider.capitalize()} configuration valid"
        return False, f"{provider.upper()}_API_KEY is required when ai_provider={provider}"

    @property
    def ai_available(self) -> bool:
        """Check if AI functionality is properly configured"""
        is_valid, _ = self.validate_ai_config()
        return is_valid
```

- [ ] **Step 5: Rewrite the AI section of `validate_settings_on_startup`**

In `validate_settings_on_startup`, replace everything from `# Validate AI configuration` through the line `logger.warning("⚠️ No AI provider configured - AI features disabled")` (old lines 251-270) with:

```python
    # Validate AI configuration
    is_valid, message = settings.validate_ai_config()
    if not is_valid:
        logger.warning(f"⚠️ AI Configuration Issue: {message}")
        logger.warning("⚠️ AI-powered features (remediation, analysis) will be unavailable.")
    else:
        logger.info(f"✅ AI Configuration: {message}")

    configured = settings.configured_provider_chain()
    if "ollama" in configured:
        logger.info(
            f"✅ Ollama local AI configured at {settings.ai_local_base_url} (model: {settings.ai_local_model})"
        )
    cloud = [p for p in configured if p != "ollama"]
    if len(cloud) >= 2:
        logger.info(f"ℹ️ Cloud AI providers available: {', '.join(cloud)}")
    elif len(cloud) == 1:
        logger.info(f"ℹ️ One cloud AI provider available: {cloud[0]}")
    elif not configured:
        logger.warning("⚠️ No AI provider configured - AI features disabled")
```

Note: the function must still `return is_valid` at the end (that line is below the replaced region — do not remove it).

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config_ai.py -v`
Expected: 10 passed.

- [ ] **Step 7: Update `backend/.env.example`**

Replace lines 60-73 (the `# Provider:` comment through `GEMINI_MAX_TOKENS=2000`) with:

```
# Provider: auto (default, follows AI_PROVIDER_CHAIN), or a single provider:
#   ollama | openai | gemini | groq | openrouter
AI_PROVIDER=auto
# Failover chain used when AI_PROVIDER=auto (left -> right)
AI_PROVIDER_CHAIN=gemini,groq,openrouter,ollama
# Google Gemini (primary free tier)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_TOKENS=2000
# Groq (free tier fallback, OpenAI-compatible)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=openai/gpt-oss-120b
# OpenRouter (free tier fallback, OpenAI-compatible)
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=google/gemma-4-27b-it:free
# OpenAI (optional legacy fallback)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
# Ollama (local dev, zero-cost; keep last in chain)
AI_LOCAL_BASE_URL=http://ollama:11434/v1
AI_LOCAL_MODEL=qwen2.5-coder:7b
AI_LOCAL_TIMEOUT=120
# AI gateway governance (budget protection)
AI_RATE_LIMIT_RPM=15
AI_RATE_LIMIT_RPD=500
AI_CACHE_TTL_DAYS=7
AI_ENRICH_TOP_N=10
AI_POST_SCAN_CONCURRENCY=2
```

- [ ] **Step 8: Run the full suite to catch regressions**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all previously passing tests still pass (config import-time validation only logs warnings).

---

### Task 2: Structured schemas and prompt builders

**Files:**
- Create: `backend/services/ai/schemas.py`
- Create: `backend/services/ai/prompts.py`
- Test: `backend/tests/test_ai_schemas_prompts.py` (create)

**Interfaces:**
- Consumes: nothing from earlier tasks (pure additions)
- Produces (used by Tasks 4, 5, 11):
  - `schemas.AnalysisNarrative` — fields: `executive_summary: str`, `risk_assessment: str`, `priority_findings: list[str]`, `recommendations: list[str]`, `secure_code_examples: dict[str, str]`, `compliance_impact: dict[str, Any]`, `attack_vectors: list[str]`
  - `schemas.RemediationAdvice` — fields: `remediation: str`, `fix_effort: Literal["low","medium","high"]`, `secure_code: Optional[str]`
  - `schemas.parse_json_model(text: Optional[str], schema: type[T]) -> Optional[T]` (T bound to BaseModel)
  - `prompts.PROMPT_VERSION: str` (value `"2026-10-06.1"`)
  - `prompts.ANALYSIS_SYSTEM_PROMPT: str`, `prompts.REMEDIATION_SYSTEM_PROMPT: str`
  - `prompts.build_analysis_prompt(findings_data: dict, project_context: Optional[dict] = None) -> str`
  - `prompts.build_remediation_prompt(finding: dict) -> str`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_ai_schemas_prompts.py`:

```python
"""Tests for structured output schemas and prompt builders."""
import json

from services.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    PROMPT_VERSION,
    REMEDIATION_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_remediation_prompt,
)
from services.ai.schemas import AnalysisNarrative, RemediationAdvice, parse_json_model

VALID_NARRATIVE = {
    "executive_summary": "Summary text",
    "risk_assessment": "Assessment text",
    "priority_findings": ["SQL Injection"],
    "recommendations": ["Use parameterized queries"],
    "secure_code_examples": {"sql": "cursor.execute('...', (id,))"},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated SQLi scanners"],
}


def test_analysis_narrative_validates():
    model = AnalysisNarrative.model_validate(VALID_NARRATIVE)
    assert model.executive_summary == "Summary text"
    assert model.priority_findings == ["SQL Injection"]


def test_analysis_narrative_requires_core_fields():
    import pydantic
    import pytest

    with pytest.raises(pydantic.ValidationError):
        AnalysisNarrative.model_validate({"executive_summary": "only this"})


def test_remediation_advice_validates_and_defaults_effort():
    model = RemediationAdvice.model_validate({"remediation": "Fix it"})
    assert model.fix_effort == "medium"
    assert model.secure_code is None
    model2 = RemediationAdvice.model_validate(
        {"remediation": "Fix it", "fix_effort": "high", "secure_code": "x = 1"}
    )
    assert model2.fix_effort == "high"


def test_parse_json_model_plain():
    parsed = parse_json_model(json.dumps(VALID_NARRATIVE), AnalysisNarrative)
    assert parsed is not None
    assert parsed.risk_assessment == "Assessment text"


def test_parse_json_model_fenced():
    text = "```json\n" + json.dumps(VALID_NARRATIVE) + "\n```"
    parsed = parse_json_model(text, AnalysisNarrative)
    assert parsed is not None


def test_parse_json_model_embedded_in_prose():
    text = "Here you go: " + json.dumps(VALID_NARRATIVE) + " done."
    parsed = parse_json_model(text, AnalysisNarrative)
    assert parsed is not None


def test_parse_json_model_garbage_returns_none():
    assert parse_json_model("not json at all", AnalysisNarrative) is None
    assert parse_json_model("", AnalysisNarrative) is None
    assert parse_json_model(None, AnalysisNarrative) is None
    assert parse_json_model('{"wrong": "shape"}', AnalysisNarrative) is None


def test_build_analysis_prompt_contains_required_sections():
    findings_data = {
        "total_findings": 2,
        "findings": [
            {
                "scanner": "bandit",
                "rule_id": "B201",
                "title": "SQL Injection",
                "description": "User input concatenated into query",
                "severity": "critical",
                "file_path": "app.py",
                "cwe_id": "CWE-89",
                "cve_id": None,
                "owasp_category": "A03",
            },
            {
                "scanner": "semgrep",
                "rule_id": "py.sqli",
                "title": "Command Injection",
                "description": "D" * 1000,
                "severity": "high",
                "file_path": "cli.py",
                "cwe_id": None,
                "cve_id": None,
                "owasp_category": None,
            },
        ],
        "severity_counts": {"critical": 1, "high": 1, "medium": 0, "low": 0, "info": 0},
        "scanner_summary": {"bandit": {"status": "completed", "findings_count": 1, "duration": 1.0}},
    }
    prompt = build_analysis_prompt(findings_data, {"project_name": "demo"})

    assert PROMPT_VERSION in prompt
    assert "demo" in prompt
    assert "<scan_data>" in prompt
    assert "</scan_data>" in prompt
    assert "SQL Injection" in prompt
    assert "critical" in prompt
    assert "AnalysisNarrative" in prompt  # schema title embedded
    # Descriptions are truncated to 500 chars
    assert "D" * 500 in prompt
    assert "D" * 1000 not in prompt
    assert ANALYSIS_SYSTEM_PROMPT


def test_build_analysis_prompt_caps_findings_at_50():
    findings = [
        {
            "scanner": "bandit",
            "rule_id": f"r{i}",
            "title": f"Finding {i}",
            "description": "d",
            "severity": "low",
            "file_path": "f.py",
            "cwe_id": None,
            "cve_id": None,
            "owasp_category": None,
        }
        for i in range(60)
    ]
    findings_data = {
        "total_findings": 60,
        "findings": findings[:50],  # _prepare_findings_data already caps at 50
        "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 60, "info": 0},
        "scanner_summary": {},
    }
    prompt = build_analysis_prompt(findings_data, None)
    assert prompt.count('"title"') <= 50


def test_build_remediation_prompt_contains_finding_and_schema():
    prompt = build_remediation_prompt(
        {
            "title": "SQL Injection",
            "severity": "critical",
            "description": "Concatenated query",
            "file_path": "app.py",
            "cwe_id": "CWE-89",
            "code_snippet": "cursor.execute(f'SELECT {q}')",
        }
    )
    assert "SQL Injection" in prompt
    assert "CWE-89" in prompt
    assert "RemediationAdvice" in prompt
    assert PROMPT_VERSION in prompt
    assert REMEDIATION_SYSTEM_PROMPT
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_schemas_prompts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.ai.schemas'`

- [ ] **Step 3: Write `backend/services/ai/schemas.py`**

```python
"""Pydantic schemas for structured LLM outputs."""
import json
import re
from typing import Any, Dict, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field, ValidationError

T = TypeVar("T", bound=BaseModel)


class AnalysisNarrative(BaseModel):
    """LLM-authored narrative portion of an AI analysis.

    Deterministic fields (risk_score, security_score, threat_categories,
    estimated_fix_time, remediation_roadmap) are computed in code and
    deliberately absent here — they are never re-asked to a model.
    """

    executive_summary: str = Field(..., min_length=1)
    risk_assessment: str = Field(..., min_length=1)
    priority_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    secure_code_examples: Dict[str, str] = Field(default_factory=dict)
    compliance_impact: Dict[str, Any] = Field(default_factory=dict)
    attack_vectors: List[str] = Field(default_factory=list)


class RemediationAdvice(BaseModel):
    """LLM-authored remediation for a single finding."""

    remediation: str = Field(..., min_length=1)
    fix_effort: Literal["low", "medium", "high"] = "medium"
    secure_code: Optional[str] = None


def parse_json_model(text: Optional[str], schema: type[T]) -> Optional[T]:
    """Parse `text` into `schema`, tolerating fences and surrounding prose.

    Returns None when no candidate parses and validates.
    """
    if not text:
        return None
    stripped = text.strip()
    candidates = [stripped]
    if stripped.startswith("```"):
        inner = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        inner = re.sub(r"\s*```$", "", inner)
        candidates.append(inner)
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            return schema.model_validate_json(candidate)
        except (ValidationError, ValueError, AttributeError):
            continue
    return None
```

- [ ] **Step 4: Write `backend/services/ai/prompts.py`**

```python
"""Single source of truth for AI prompts."""
import json
from typing import Any, Dict, Optional

PROMPT_VERSION = "2026-10-06.1"

ANALYSIS_SYSTEM_PROMPT = (
    "You are a senior cybersecurity expert specializing in vulnerability analysis "
    "and secure coding practices. Provide detailed, actionable security advice.\n"
    "Respond with ONLY a valid JSON object — no markdown fences, no prose outside the JSON. "
    "The JSON must match the schema provided in the user message."
)

REMEDIATION_SYSTEM_PROMPT = (
    "You are a senior security engineer providing remediation guidance for a single "
    "vulnerability.\n"
    "Respond with ONLY a valid JSON object — no markdown fences, no prose outside the JSON. "
    "The JSON must match the schema provided in the user message."
)


def _schema_json(schema_cls: type) -> str:
    return json.dumps(schema_cls.model_json_schema())


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
        f"{json.dumps(context, indent=2, default=str)}\n\n"
        "## Severity Counts\n"
        f"{json.dumps(findings_data.get('severity_counts', {}))}\n\n"
        "## Scanner Summary\n"
        f"{json.dumps(findings_data.get('scanner_summary', {}), default=str)}\n\n"
        "## Scan Data\n<scan_data>\n"
        f"{json.dumps(findings, indent=2, default=str)}\n"
        "</scan_data>\n\n"
        "## Required Output\n"
        "Return ONLY a JSON object matching this JSON Schema:\n"
        f"{_schema_json(AnalysisNarrative)}"
    )


def build_remediation_prompt(finding: Dict[str, Any]) -> str:
    """Build the user message for one remediation enrichment call."""
    from services.ai.schemas import RemediationAdvice

    description = (finding.get("description") or "")[:500]
    code = (finding.get("code_snippet") or "")[:300]
    return (
        f"Prompt version: {PROMPT_VERSION}\n\n"
        "## Finding\n"
        f"Title: {finding.get('title', '')}\n"
        f"Severity: {finding.get('severity', '')}\n"
        f"Description: {description}\n"
        f"File: {finding.get('file_path', '')}\n"
        f"CWE: {finding.get('cwe_id') or 'N/A'}\n"
        f"CVE: {finding.get('cve_id') or 'N/A'}\n"
        f"Code:\n```\n{code}\n```\n\n"
        "## Required Output\n"
        "Return ONLY a JSON object matching this JSON Schema:\n"
        f"{_schema_json(RemediationAdvice)}"
    )
```

Note: imports of `AnalysisNarrative`/`RemediationAdvice` are function-local to avoid any import cycle with `schemas` (schemas does not import prompts, so a top-level import would also be safe — either is acceptable).

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_schemas_prompts.py -v`
Expected: 10 passed.

- [ ] **Step 6: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green.

---

### Task 3: Quota ledger, response cache, invocation tracer

**Files:**
- Create: `backend/services/ai/stores.py`
- Create: `backend/services/ai/trace.py`
- Test: `backend/tests/test_ai_stores.py` (create)

**Interfaces:**
- Consumes: `config.settings.ai_rate_limit_rpd`, `config.settings.ai_cache_ttl_days` (Task 1)
- Produces (used by Task 4):
  - `stores.QuotaLedger(db: Optional[Any] = None)`
    - `async try_consume(provider: str) -> bool` — increments today's counter, False when over `ai_rate_limit_rpd`
    - `remaining(provider: str) -> int`
  - `stores.ResponseCache(db: Optional[Any] = None)`
    - `staticmethod make_key(*, purpose: str, messages: list[dict], temperature: float, schema_name: str, chain: str) -> str` → sha256 hex
    - `async get(key: str) -> Optional[dict]` / `async set(key: str, value: dict) -> None`
  - `trace.InvocationTracer(db: Optional[Any] = None, maxlen: int = 500)`
    - `async record(**entry) -> None` — appends to ring; best-effort insert into `ai_invocations`
    - `recent() -> list[dict]`
  - When `db is None`, stores resolve `database.db_manager.db` lazily at call time; if that is also None (tests, DB down) they degrade to pure in-memory behavior. All Mongo errors are swallowed (logging only) — stores must never raise.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_ai_stores.py`:

```python
"""Tests for quota ledger, response cache, and invocation tracer."""
import pytest

from config import settings
from services.ai.stores import QuotaLedger, ResponseCache
from services.ai.trace import InvocationTracer


class FakeCollection:
    """Minimal async Mongo collection double."""

    def __init__(self, doc=None, raise_on_call=False):
        self.doc = doc
        self.raise_on_call = raise_on_call
        self.calls = []

    async def find_one_and_update(self, filter, update, upsert=False, return_document=None):
        self.calls.append(("find_one_and_update", filter, update))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        count = (self.doc or {}).get("count", 0) + update["$inc"]["count"]
        self.doc = {"_id": filter["_id"], "count": count}
        return dict(self.doc)

    async def update_one(self, filter, update, upsert=False):
        self.calls.append(("update_one", filter, update))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        self.doc = {"_id": filter["_id"], **update["$set"]}
        return MagicMockResult()

    async def find_one(self, filter):
        self.calls.append(("find_one", filter))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        return dict(self.doc) if self.doc else None

    async def insert_one(self, doc):
        self.calls.append(("insert_one", doc))
        if self.raise_on_call:
            raise RuntimeError("mongo down")
        return object()


class MagicMockResult:
    pass


class FakeDB:
    def __init__(self, **collections):
        for name, coll in collections.items():
            setattr(self, name, coll)


class TestQuotaLedger:
    async def test_memory_mode_exhausts_at_limit(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 2)
        ledger = QuotaLedger(db=None)
        ledger._db_disabled = True  # force memory path even if a real DB is connected
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("gemini") is False
        assert ledger.remaining("gemini") == 0

    async def test_memory_mode_isolates_providers_and_days(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 1)
        ledger = QuotaLedger(db=None)
        ledger._db_disabled = True
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("groq") is True  # different provider
        assert await ledger.try_consume("groq") is False

    async def test_mongo_mode_uses_counter(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 5)
        coll = FakeCollection()
        ledger = QuotaLedger(db=FakeDB(ai_quota_ledgers=coll))
        assert await ledger.try_consume("gemini") is True
        assert await ledger.try_consume("gemini") is True
        assert coll.doc["count"] == 2
        assert ledger.remaining("gemini") == 3

    async def test_mongo_failure_falls_back_to_memory(self, monkeypatch):
        monkeypatch.setattr(settings, "ai_rate_limit_rpd", 5)
        coll = FakeCollection(raise_on_call=True)
        ledger = QuotaLedger(db=FakeDB(ai_quota_ledgers=coll))
        assert await ledger.try_consume("gemini") is True
        assert ledger.remaining("gemini") == 4


class TestResponseCache:
    async def test_roundtrip_in_memory(self):
        cache = ResponseCache(db=None)
        cache._db_disabled = True
        key = ResponseCache.make_key(
            purpose="analysis", messages=[{"role": "user", "content": "hi"}],
            temperature=0.3, schema_name="AnalysisNarrative", chain="gemini",
        )
        await cache.set(key, {"text": "value", "provider": "gemini"})
        hit = await cache.get(key)
        assert hit == {"text": "value", "provider": "gemini"}

    async def test_key_changes_with_content(self):
        a = ResponseCache.make_key(
            purpose="analysis", messages=[{"role": "user", "content": "hi"}],
            temperature=0.3, schema_name="", chain="gemini",
        )
        b = ResponseCache.make_key(
            purpose="analysis", messages=[{"role": "user", "content": "ho"}],
            temperature=0.3, schema_name="", chain="gemini",
        )
        assert a != b
        assert len(a) == 64

    async def test_ttl_zero_expires_immediately(self):
        cache = ResponseCache(db=None)
        cache._db_disabled = True
        key = ResponseCache.make_key(
            purpose="p", messages=[], temperature=0.0, schema_name="", chain="c",
        )
        await cache.set(key, {"text": "v"}, ttl_days=0)
        assert await cache.get(key) is None

    async def test_mongo_set_and_get(self):
        coll = FakeCollection()
        cache = ResponseCache(db=FakeDB(ai_response_cache=coll))
        key = ResponseCache.make_key(
            purpose="p", messages=[], temperature=0.0, schema_name="", chain="c",
        )
        await cache.set(key, {"text": "v", "provider": "groq"})
        assert coll.doc["value"] == {"text": "v", "provider": "groq"}
        # Memory already holds it; clear to force DB path
        cache._mem.clear()
        hit = await cache.get(key)
        assert hit == {"text": "v", "provider": "groq"}

    async def test_mongo_failure_degrades_to_memory(self):
        coll = FakeCollection(raise_on_call=True)
        cache = ResponseCache(db=FakeDB(ai_response_cache=coll))
        key = "k" * 64
        await cache.set(key, {"text": "v"})  # must not raise
        cache._db_disabled = True
        assert await cache.get(key) == {"text": "v"}


class TestInvocationTracer:
    async def test_record_appends_to_ring(self):
        tracer = InvocationTracer(db=None, maxlen=3)
        tracer._db_disabled = True
        for i in range(4):
            await tracer.record(purpose="analysis", provider="gemini", ok=True, i=i)
        recent = tracer.recent()
        assert len(recent) == 3
        assert recent[0]["i"] == 1  # oldest evicted

    async def test_record_persists_best_effort(self):
        coll = FakeCollection()
        tracer = InvocationTracer(db=FakeDB(ai_invocations=coll))
        await tracer.record(purpose="chat", provider="groq", ok=True)
        assert len(coll.calls) == 1
        assert coll.calls[0][1]["purpose"] == "chat"

    async def test_record_swallows_db_errors(self):
        coll = FakeCollection(raise_on_call=True)
        tracer = InvocationTracer(db=FakeDB(ai_invocations=coll))
        await tracer.record(purpose="chat", provider="groq", ok=False)  # must not raise
        assert len(tracer.recent()) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_stores.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.ai.stores'`

- [ ] **Step 3: Write `backend/services/ai/stores.py`**

```python
"""Budget and cache stores for the LLM gateway.

Mongo-backed when a DB connection is available, in-memory otherwise.
All persistence failures degrade silently — these stores never raise.
"""
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from config import settings

logger = logging.getLogger(__name__)

class _LazyStore:
    def __init__(self, db: Optional[Any] = None):
        self._db = db
        self._mem: dict = {}
        # Tests set this to force memory-only mode while a real DB may be connected.
        self._db_disabled: bool = False

    def _resolve_db(self) -> Optional[Any]:
        if self._db_disabled:
            return None
        if self._db is not None:
            return self._db
        try:
            from database import db_manager

            return db_manager.db
        except Exception:
            return None


class QuotaLedger(_LazyStore):
    """Daily per-provider request budget ($inc upserts in ai_quota_ledgers)."""

    def _key(self, provider: str) -> str:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{provider}:{day}"

    async def try_consume(self, provider: str) -> bool:
        key = self._key(provider)
        limit = settings.ai_rate_limit_rpd
        if self._mem.get(key, 0) >= limit:
            return False
        db = self._resolve_db()
        if db is not None:
            try:
                from pymongo import ReturnDocument

                doc = await db.ai_quota_ledgers.find_one_and_update(
                    {"_id": key},
                    {"$inc": {"count": 1}, "$set": {"provider": provider}},
                    upsert=True,
                    return_document=ReturnDocument.AFTER,
                )
                count = int((doc or {}).get("count", 1))
                self._mem[key] = count
                return count <= limit
            except Exception as e:
                logger.debug("QuotaLedger mongo unavailable (%s); using memory", e)
        self._mem[key] = self._mem.get(key, 0) + 1
        return self._mem[key] <= limit

    def remaining(self, provider: str) -> int:
        return max(0, settings.ai_rate_limit_rpd - self._mem.get(self._key(provider), 0))


class ResponseCache(_LazyStore):
    """SHA-256(prompt+settings) response cache with TTL (ai_response_cache)."""

    @staticmethod
    def make_key(
        *,
        purpose: str,
        messages: list,
        temperature: float,
        schema_name: str,
        chain: str,
    ) -> str:
        payload = json.dumps(
            {
                "p": purpose,
                "m": messages,
                "t": temperature,
                "s": schema_name,
                "c": chain,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    async def get(self, key: str) -> Optional[dict]:
        now = time.time()
        mem = self._mem.get(key)
        if mem is not None:
            if mem["expires_at"] > now:
                return mem["value"]
            self._mem.pop(key, None)
        db = self._resolve_db()
        if db is not None:
            try:
                doc = await db.ai_response_cache.find_one(
                    {"_id": key, "expires_at": {"$gt": datetime.fromtimestamp(now, tz=timezone.utc)}}
                )
                if doc and doc.get("value") is not None:
                    expires = doc["expires_at"]
                    self._mem[key] = {
                        "value": doc["value"],
                        "expires_at": expires.timestamp() if hasattr(expires, "timestamp") else now + 60,
                    }
                    return doc["value"]
            except Exception as e:
                logger.debug("ResponseCache mongo unavailable (%s)", e)
        return None

    async def set(self, key: str, value: dict, ttl_days: Optional[int] = None) -> None:
        ttl = settings.ai_cache_ttl_days if ttl_days is None else ttl_days
        expires = time.time() + max(0, ttl) * 86400
        self._mem[key] = {"value": value, "expires_at": expires}
        db = self._resolve_db()
        if db is not None:
            try:
                await db.ai_response_cache.update_one(
                    {"_id": key},
                    {
                        "$set": {
                            "value": value,
                            "expires_at": datetime.fromtimestamp(expires, tz=timezone.utc),
                        }
                    },
                    upsert=True,
                )
            except Exception as e:
                logger.debug("ResponseCache mongo write failed (%s)", e)
```

- [ ] **Step 4: Write `backend/services/ai/trace.py`**

```python
"""Invocation tracing for every LLM gateway call."""
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InvocationTracer:
    """Records gateway invocations to an in-memory ring and ai_invocations."""

    def __init__(self, db: Optional[Any] = None, maxlen: int = 500):
        self._db = db
        self._ring: deque = deque(maxlen=maxlen)
        self._db_disabled = False

    def _resolve_db(self) -> Optional[Any]:
        if self._db_disabled or self._db is not None:
            return None if self._db_disabled else self._db
        try:
            from database import db_manager

            return db_manager.db
        except Exception:
            return None

    async def record(self, **entry) -> None:
        entry["ts"] = datetime.now(timezone.utc).isoformat()
        self._ring.append(entry)
        db = self._resolve_db()
        if db is not None:
            try:
                await db.ai_invocations.insert_one(dict(entry))
            except Exception as e:
                logger.debug("InvocationTracer insert failed (%s)", e)

    def recent(self) -> list:
        return list(self._ring)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_stores.py -v`
Expected: 12 passed.

- [ ] **Step 6: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green.

---

### Task 4: LLM Gateway — adapters, failover, rate limits, circuit breaker, cache

**Files:**
- Create: `backend/services/ai/gateway.py`
- Test: `backend/tests/test_gateway.py` (create)

**Interfaces:**
- Consumes: `Settings.provider_chain()` / `configured_provider_chain()` (Task 1), `QuotaLedger` / `ResponseCache` (Task 3), `InvocationTracer` (Task 3), `schemas.parse_json_model` (Task 2)
- Produces (used by Tasks 5, 7, 8):
  - `gateway.GatewayResult(text: str, provider: str, model: str, usage: dict, latency_ms: int, cached: bool = False)`
  - `gateway.GatewayError(Exception)`
  - `gateway.ProviderSpec(name: str, model: str, api_key: Optional[str], base_url: Optional[str])` (frozen dataclass)
  - `gateway.LLMGateway(adapters=None, quota=None, cache=None, tracer=None)`
    - `async complete(*, system: str, user: str, purpose: str, max_tokens: Optional[int] = None, temperature: float = 0.3, json_schema: Optional[type] = None, use_cache: bool = False) -> GatewayResult`
    - `async complete_messages(*, messages: list[dict], purpose: str, max_tokens: Optional[int] = None, temperature: float = 0.3, json_schema: Optional[type] = None, use_cache: bool = False) -> GatewayResult`
  - `gateway.complete_structured(gateway, *, system, user, purpose, schema, temperature=0.3, retries=1, use_cache=False) -> tuple[Optional[TModel], GatewayResult]` — raises `GatewayError` when every provider fails; returns `(None, result)` when text came back but never parsed
  - `gateway.get_gateway() -> LLMGateway` (singleton), `gateway.reset_gateway() -> None`
  - Adapter contract: `async adapter(spec: ProviderSpec, messages: list[dict], max_tokens: int, temperature: float, json_mode: bool) -> tuple[str, dict]`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_gateway.py`:

```python
"""Tests for the LLM gateway: failover, rate limits, circuit breaker, cache, structured output."""
import json

import pytest

from config import settings
from services.ai.gateway import (
    GatewayError,
    LLMGateway,
    complete_structured,
    get_gateway,
    reset_gateway,
)
from services.ai.schemas import AnalysisNarrative
from services.ai.stores import QuotaLedger, ResponseCache
from services.ai.trace import InvocationTracer

VALID_NARRATIVE = {
    "executive_summary": "Summary text",
    "risk_assessment": "Assessment text",
    "priority_findings": ["SQL Injection"],
    "recommendations": ["Use parameterized queries"],
    "secure_code_examples": {},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated scanners"],
}


@pytest.fixture
def gw_settings(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini,groq")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "groq_api_key", "k" * 20)
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "ai_rate_limit_rpm", 15)
    monkeypatch.setattr(settings, "ai_rate_limit_rpd", 500)
    return settings


def _gateway(adapters, quota=None, cache=None, tracer=None):
    if quota is None:
        quota = QuotaLedger(db=None)
        quota._db_disabled = True
    if cache is None:
        cache = ResponseCache(db=None)
        cache._db_disabled = True
    if tracer is None:
        tracer = InvocationTracer(db=None)
        tracer._db_disabled = True
    return LLMGateway(adapters=adapters, quota=quota, cache=cache, tracer=tracer)


async def test_failover_to_second_provider(gw_settings):
    calls = []

    async def fail_gemini(spec, messages, max_tokens, temperature, json_mode):
        calls.append(spec.name)
        raise RuntimeError("gemini down")

    async def ok_groq(spec, messages, max_tokens, temperature, json_mode):
        calls.append(spec.name)
        return '{"ok": true}', {"prompt_tokens": 1, "completion_tokens": 1}

    gw = _gateway({"gemini": fail_gemini, "groq": ok_groq})
    result = await gw.complete(system="sys", user="usr", purpose="analysis")
    assert result.provider == "groq"
    assert result.text == '{"ok": true}'
    assert calls == ["gemini", "groq"]


async def test_all_providers_fail_raises_with_details(gw_settings):
    async def boom(spec, messages, max_tokens, temperature, json_mode):
        raise RuntimeError(f"{spec.name} exploded")

    gw = _gateway({"gemini": boom, "groq": boom})
    with pytest.raises(GatewayError) as excinfo:
        await gw.complete(system="s", user="u", purpose="analysis")
    msg = str(excinfo.value)
    assert "gemini" in msg and "groq" in msg


async def test_no_configured_provider_raises(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "groq_api_key", None)
    gw = _gateway({})
    with pytest.raises(GatewayError, match="No AI provider configured"):
        await gw.complete(system="s", user="u", purpose="analysis")


async def test_rate_limit_blocks_second_call(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    monkeypatch.setattr(settings, "ai_rate_limit_rpm", 1)

    async def ok(spec, messages, max_tokens, temperature, json_mode):
        return "ok", {}

    gw = _gateway({"gemini": ok})
    first = await gw.complete(system="s", user="u", purpose="chat")
    assert first.text == "ok"
    with pytest.raises(GatewayError, match="rate limit"):
        await gw.complete(system="s", user="u", purpose="chat")


async def test_circuit_opens_after_three_failures(gw_settings, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    calls = 0

    async def always_fail(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        calls += 1
        raise RuntimeError("nope")

    gw = _gateway({"gemini": always_fail})
    for _ in range(3):
        with pytest.raises(GatewayError):
            await gw.complete(system="s", user="u", purpose="analysis")
    assert calls == 3
    with pytest.raises(GatewayError, match="circuit"):
        await gw.complete(system="s", user="u", purpose="analysis")
    assert calls == 3  # circuit open: adapter not invoked again


async def test_cache_hit_skips_adapter(gw_settings):
    calls = 0

    async def counting(spec, messages, max_tokens, temperature, json_mode):
        nonlocal calls
        calls += 1
        return '{"a": 1}', {}

    gw = _gateway({"gemini": counting})
    r1 = await gw.complete(system="s", user="u", purpose="remediation", use_cache=True)
    r2 = await gw.complete(system="s", user="u", purpose="remediation", use_cache=True)
    assert r1.cached is False
    assert r2.cached is True
    assert r2.text == r1.text
    assert calls == 1


async def test_quota_exhausted_blocks_provider(gw_settings):
    class DenyQuota:
        async def try_consume(self, provider):
            return False

        def remaining(self, provider):
            return 0

    async def ok(spec, messages, max_tokens, temperature, json_mode):
        return "ok", {}

    gw = _gateway({"gemini": ok}, quota=DenyQuota())
    with pytest.raises(GatewayError, match="quota"):
        await gw.complete(system="s", user="u", purpose="analysis")


async def test_json_schema_enables_json_mode(gw_settings):
    seen = {}

    async def capture(spec, messages, max_tokens, temperature, json_mode):
        seen["json_mode"] = json_mode
        return '{"a": 1}', {}

    gw = _gateway({"gemini": capture})
    await gw.complete(system="s", user="u", purpose="analysis")
    assert seen["json_mode"] is False
    await gw.complete(system="s", user="u", purpose="analysis", json_schema=AnalysisNarrative)
    assert seen["json_mode"] is True


async def test_complete_messages_passes_messages_verbatim(gw_settings):
    captured = {}

    async def capture(spec, messages, max_tokens, temperature, json_mode):
        captured["messages"] = messages
        return "ok", {}

    gw = _gateway({"gemini": capture})
    msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "u1"}]
    await gw.complete_messages(messages=msgs, purpose="chat")
    assert captured["messages"] == msgs


async def test_complete_structured_parses_valid_json(gw_settings):
    async def returns_narrative(spec, messages, max_tokens, temperature, json_mode):
        return json.dumps(VALID_NARRATIVE), {}

    gw = _gateway({"gemini": returns_narrative})
    parsed, result = await complete_structured(
        gw, system="s", user="u", purpose="analysis", schema=AnalysisNarrative
    )
    assert parsed is not None
    assert parsed.executive_summary == "Summary text"
    assert result.provider == "gemini"


async def test_complete_structured_retries_invalid_json_once(gw_settings):
    texts = iter(["definitely not json", json.dumps(VALID_NARRATIVE)])

    async def two_responses(spec, messages, max_tokens, temperature, json_mode):
        return next(texts), {}

    gw = _gateway({"gemini": two_responses})
    parsed, _ = await complete_structured(
        gw, system="s", user="u", purpose="analysis", schema=AnalysisNarrative
    )
    assert parsed is not None


async def test_complete_structured_gives_up_returns_none(gw_settings):
    async def always_bad(spec, messages, max_tokens, temperature, json_mode):
        return "garbage", {}

    gw = _gateway({"gemini": always_bad})
    parsed, result = await complete_structured(
        gw, system="s", user="u", purpose="analysis", schema=AnalysisNarrative, retries=1
    )
    assert parsed is None
    assert result.text == "garbage"


def test_get_gateway_singleton():
    reset_gateway()
    a = get_gateway()
    b = get_gateway()
    assert a is b
    reset_gateway()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_gateway.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.ai.gateway'`

- [ ] **Step 3: Write `backend/services/ai/gateway.py`**

```python
"""LLM gateway: one entry point for all AI provider calls.

Provider order comes from Settings (auto -> configured chain, or a single
explicit provider). Every call is rate-limited, quota-checked, circuit-broken,
cached (opt-in) and traced. Failures fail over to the next provider.
"""
import json
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from pydantic import BaseModel

from config import settings
from services.ai.schemas import parse_json_model
from services.ai.stores import QuotaLedger, ResponseCache
from services.ai.trace import InvocationTracer

logger = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

AdapterFn = Callable[..., Awaitable[tuple[str, dict]]]


class GatewayError(Exception):
    """All eligible providers failed, or none are configured."""


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class GatewayResult:
    text: str
    provider: str
    model: str
    usage: dict
    latency_ms: int
    cached: bool = False


def spec_for(name: str, s=None) -> ProviderSpec:
    s = s or settings
    if name == "gemini":
        return ProviderSpec("gemini", s.gemini_model, s.gemini_api_key, None)
    if name == "groq":
        return ProviderSpec("groq", s.groq_model, s.groq_api_key, GROQ_BASE_URL)
    if name == "openrouter":
        return ProviderSpec("openrouter", s.openrouter_model, s.openrouter_api_key, OPENROUTER_BASE_URL)
    if name == "openai":
        return ProviderSpec("openai", s.openai_model, s.openai_api_key, None)
    if name == "ollama":
        return ProviderSpec("ollama", s.ai_local_model, "ollama", s.ai_local_base_url)
    raise GatewayError(f"Unknown AI provider: {name}")


async def _call_openai_compat(
    spec: ProviderSpec,
    messages: list,
    max_tokens: int,
    temperature: float,
    json_mode: bool,
) -> tuple[str, dict]:
    """OpenAI-compatible adapter (OpenAI, Groq, OpenRouter, Ollama /v1)."""
    from openai import AsyncOpenAI, BadRequestError

    client = AsyncOpenAI(api_key=spec.api_key, base_url=spec.base_url, max_retries=0, timeout=60.0)
    kwargs: Dict[str, Any] = {
        "model": spec.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = await client.chat.completions.create(**kwargs)
    except BadRequestError:
        if not json_mode:
            raise
        # Some gateways do not support response_format; retry without it.
        kwargs.pop("response_format", None)
        resp = await client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    usage = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "prompt_tokens": resp.usage.prompt_tokens or 0,
            "completion_tokens": resp.usage.completion_tokens or 0,
        }
    return text, usage


async def _call_gemini(
    spec: ProviderSpec,
    messages: list,
    max_tokens: int,
    temperature: float,
    json_mode: bool,
) -> tuple[str, dict]:
    """Google Gemini adapter via google-genai."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=spec.api_key)
    system = next((m.get("content", "") for m in messages if m.get("role") == "system"), None)
    parts = [
        f"{m.get('role', 'user')}: {m.get('content', '')}"
        for m in messages
        if m.get("role") != "system"
    ]
    cfg_kwargs: Dict[str, Any] = {
        "system_instruction": system,
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        cfg_kwargs["response_mime_type"] = "application/json"
    resp = await client.aio.models.generate_content(
        model=spec.model,
        contents="\n".join(parts),
        config=types.GenerateContentConfig(**cfg_kwargs),
    )
    text = resp.text or ""
    usage = {}
    um = getattr(resp, "usage_metadata", None)
    if um is not None:
        usage = {
            "prompt_tokens": getattr(um, "prompt_token_count", 0) or 0,
            "completion_tokens": getattr(um, "candidate_token_count", 0) or 0,
        }
    return text, usage


_DEFAULT_ADAPTERS: Dict[str, AdapterFn] = {
    "gemini": _call_gemini,
    "groq": _call_openai_compat,
    "openrouter": _call_openai_compat,
    "openai": _call_openai_compat,
    "ollama": _call_openai_compat,
}


class LLMGateway:
    def __init__(self, adapters=None, quota=None, cache=None, tracer=None):
        self._adapters = dict(_DEFAULT_ADAPTERS) if adapters is None else dict(adapters)
        self._quota = quota if quota is not None else QuotaLedger()
        self._cache = cache if cache is not None else ResponseCache()
        self._tracer = tracer if tracer is not None else InvocationTracer()
        self._hits: Dict[str, deque] = {}
        self._failures: Dict[str, int] = {}
        self._open_until: Dict[str, float] = {}

    async def complete(
        self,
        *,
        system: str,
        user: str,
        purpose: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        json_schema: Optional[type] = None,
        use_cache: bool = False,
    ) -> GatewayResult:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return await self.complete_messages(
            messages=messages,
            purpose=purpose,
            max_tokens=max_tokens,
            temperature=temperature,
            json_schema=json_schema,
            use_cache=use_cache,
        )

    async def complete_messages(
        self,
        *,
        messages: list,
        purpose: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        json_schema: Optional[type] = None,
        use_cache: bool = False,
    ) -> GatewayResult:
        max_tokens = max_tokens or settings.openai_max_tokens
        schema_name = json_schema.__name__ if json_schema else ""
        cache_key = ResponseCache.make_key(
            purpose=purpose,
            messages=messages,
            temperature=temperature,
            schema_name=schema_name,
            chain=settings.ai_provider_chain,
        )
        if use_cache:
            hit = await self._cache.get(cache_key)
            if hit is not None:
                return GatewayResult(
                    text=hit["text"],
                    provider=hit.get("provider", "cache"),
                    model=hit.get("model", ""),
                    usage=hit.get("usage", {}),
                    latency_ms=hit.get("latency_ms", 0),
                    cached=True,
                )

        specs = [spec_for(name, settings) for name in settings.configured_provider_chain()]
        if not specs:
            raise GatewayError(
                "No AI provider configured (set GEMINI_API_KEY, GROQ_API_KEY, "
                "OPENROUTER_API_KEY, OPENAI_API_KEY, or AI_PROVIDER=ollama)"
            )

        errors = []
        for spec in specs:
            now = time.monotonic()
            if self._circuit_open(spec.name, now):
                errors.append(f"{spec.name}: circuit open (cooling down)")
                continue
            if not self._rate_ok(spec.name, now):
                errors.append(f"{spec.name}: rate limit exceeded ({settings.ai_rate_limit_rpm}/min)")
                continue
            if not await self._quota.try_consume(spec.name):
                errors.append(f"{spec.name}: daily quota exhausted ({settings.ai_rate_limit_rpd}/day)")
                continue
            adapter = self._adapters.get(spec.name)
            if adapter is None:
                errors.append(f"{spec.name}: no adapter registered")
                continue
            start = time.perf_counter()
            try:
                text, usage = await adapter(spec, messages, max_tokens, temperature, json_schema is not None)
            except Exception as e:
                latency = int((time.perf_counter() - start) * 1000)
                self._note_failure(spec.name)
                errors.append(f"{spec.name}: {e}")
                await self._tracer.record(
                    purpose=purpose, provider=spec.name, model=spec.model,
                    ok=False, latency_ms=latency, error=str(e)[:500],
                )
                logger.warning("AI provider %s failed: %s", spec.name, e)
                continue
            self._note_success(spec.name)
            latency = int((time.perf_counter() - start) * 1000)
            await self._tracer.record(
                purpose=purpose, provider=spec.name, model=spec.model,
                ok=True, latency_ms=latency, usage=usage,
            )
            if use_cache:
                await self._cache.set(
                    cache_key,
                    {"text": text, "provider": spec.name, "model": spec.model,
                     "usage": usage, "latency_ms": latency},
                )
            return GatewayResult(
                text=text, provider=spec.name, model=spec.model,
                usage=usage, latency_ms=latency,
            )
        raise GatewayError("All AI providers failed: " + "; ".join(errors))

    # --- protection primitives -------------------------------------------

    def _rate_ok(self, provider: str, now: float) -> bool:
        window = self._hits.setdefault(provider, deque())
        while window and now - window[0] > 60.0:
            window.popleft()
        if len(window) >= settings.ai_rate_limit_rpm:
            return False
        window.append(now)
        return True

    def _circuit_open(self, provider: str, now: float) -> bool:
        return now < self._open_until.get(provider, 0.0)

    def _note_failure(self, provider: str) -> None:
        self._failures[provider] = self._failures.get(provider, 0) + 1
        if self._failures[provider] >= 3:
            self._open_until[provider] = time.monotonic() + 60.0
            logger.warning("AI circuit opened for %s for 60s", provider)

    def _note_success(self, provider: str) -> None:
        self._failures[provider] = 0
        self._open_until[provider] = 0.0


async def complete_structured(
    gateway: LLMGateway,
    *,
    system: str,
    user: str,
    purpose: str,
    schema: type[TModel],
    temperature: float = 0.3,
    retries: int = 1,
    use_cache: bool = False,
) -> tuple[Optional[TModel], GatewayResult]:
    """Gateway call that must return JSON validating as `schema`.

    One retry with a schema reminder is attempted on parse failure.
    Raises GatewayError if no provider could be reached at all.
    Returns (None, last_result) if text arrived but never parsed.
    """
    prompt = user
    result: Optional[GatewayResult] = None
    for attempt in range(retries + 1):
        result = await gateway.complete(
            system=system,
            user=prompt,
            purpose=purpose,
            temperature=temperature,
            json_schema=schema,
            use_cache=use_cache and attempt == 0,
        )
        parsed = parse_json_model(result.text, schema)
        if parsed is not None:
            return parsed, result
        prompt = (
            user
            + "\n\nIMPORTANT: Respond with ONLY a valid JSON object matching this JSON Schema:\n"
            + json.dumps(schema.model_json_schema())
        )
    return None, result


_gateway: Optional[LLMGateway] = None


def get_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway


def reset_gateway() -> None:
    global _gateway
    _gateway = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_gateway.py -v`
Expected: 13 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green.

---

### Task 5: Unified processor — one structured call, deterministic fields in code

**Files:**
- Rewrite: `backend/services/ai/ai_processor.py` (full replacement)
- Test: `backend/tests/test_ai_processor.py` (create)

**Interfaces:**
- Consumes: `gateway.complete_structured` + `GatewayError`/`GatewayResult`/`LLMGateway` (Task 4), `AnalysisNarrative`/`RemediationAdvice`/`parse_json_model` (Task 2 — via complete_structured), prompt builders (Task 2)
- Produces (used by Tasks 6, 7, 9, 10, 11):
  - `ai_processor.AIProcessorError(Exception)` (unchanged)
  - `ai_processor.VulnerabilityAIProcessor(gateway: Optional[LLMGateway] = None)`
    - `async analyze_scan_results(scan_results: List[ScanResult], project_context: Optional[dict] = None) -> AIAnalysis`
    - `async enrich_findings_with_remediation(findings: List[Any], batch_size: int = 5) -> List[Any]`
    - kept helpers: `_prepare_findings_data`, `_create_clean_analysis`, `_calculate_risk_score`, `_calculate_security_score`, `_categorize_threats`, `_estimate_fix_time`, `_generate_remediation_roadmap`
  - `ai_processor.get_ai_processor() -> VulnerabilityAIProcessor` (still lazily imports `create_ai_processor` from `gemini_ai_processor` — Task 6 repoints it to `factory.py`)
  - `model_used` format: `"{provider}/{model}"` (e.g. `gemini/gemini-2.5-flash`), `"unavailable"` when the gateway was unreachable, `"none/clean-scan"` for clean scans

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_ai_processor.py`:

```python
"""Tests for the unified vulnerability AI processor."""
import json

import pytest

from models.base import ScannerType, ScanStatus, SeverityLevel
from models.report import AIAnalysis, ScanResult, VulnerabilityFinding
from services.ai.gateway import GatewayError, GatewayResult
from services.ai.schemas import AnalysisNarrative


class FakeGateway:
    """Deterministic gateway double: returns fixed text or raises."""

    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="fake-1",
            usage={"prompt_tokens": 1, "completion_tokens": 1}, latency_ms=1,
        )


def _finding(title="SQL Injection", severity="critical", **kwargs):
    return VulnerabilityFinding(
        id=kwargs.pop("id", "f-1"),
        scanner=ScannerType.BANDIT,
        rule_id="rule-1",
        title=title,
        description=kwargs.pop("description", "SQL injection in login"),
        severity=SeverityLevel(severity),
        file_path=kwargs.pop("file_path", "app/login.py"),
        **kwargs,
    )


def _scan_result(findings, scanner=ScannerType.BANDIT):
    return ScanResult(
        scanner=scanner, status=ScanStatus.COMPLETED,
        findings=findings, duration_seconds=1.0,
    )


VALID_NARRATIVE = {
    "executive_summary": "Two issues need attention.",
    "risk_assessment": "High risk overall.",
    "priority_findings": ["SQL Injection"],
    "recommendations": ["Parameterize queries"],
    "secure_code_examples": {"sql": "cursor.execute('...', (id,))"},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated scanners"],
}


class TestAnalyzeScanResults:
    async def test_clean_scan_short_circuits_without_gateway_call(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(error=AssertionError("gateway must not be called"))
        proc = VulnerabilityAIProcessor(gateway=gw)
        result = await proc.analyze_scan_results([])
        assert isinstance(result, AIAnalysis)
        assert result.risk_score == 5
        assert result.risk_level == "LOW"
        assert result.security_score == 98
        assert result.model_used == "none/clean-scan"
        assert gw.calls == []

    async def test_assembles_narrative_and_deterministic_fields(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(text=json.dumps(VALID_NARRATIVE))
        proc = VulnerabilityAIProcessor(gateway=gw)
        findings = [
            _finding(title="SQL Injection", severity="critical"),
            _finding(title="Weak password hash", severity="high"),
        ]
        result = await proc.analyze_scan_results(
            [_scan_result(findings)], {"project_name": "demo"}
        )
        assert result.model_used == "fake/fake-1"
        assert result.executive_summary == "Two issues need attention."
        assert result.priority_findings == ["SQL Injection"]
        assert result.recommendations == ["Parameterize queries"]
        # Deterministic fields computed in code:
        assert result.risk_score == 65          # 40*1 + 25*1
        assert result.risk_level == "CRITICAL"
        assert result.security_score == 68      # 100 - 20 - 12
        assert result.threat_categories == {"Injection": 1, "Cryptographic Issues": 1}
        assert [p["phase"] for p in result.remediation_roadmap] == [1, 2]
        assert "days" in result.estimated_fix_time  # 12h
        # Single gateway call, structured:
        assert len(gw.calls) == 1
        assert gw.calls[0]["purpose"] == "analysis"
        assert gw.calls[0]["json_schema"] is AnalysisNarrative
        assert gw.calls[0]["use_cache"] is False

    async def test_gateway_error_yields_degraded_analysis(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(error=GatewayError("All AI providers failed: gemini: boom"))
        proc = VulnerabilityAIProcessor(gateway=gw)
        result = await proc.analyze_scan_results([_scan_result([_finding(severity="critical")])])
        assert result.model_used == "unavailable"
        assert result.risk_score == 40
        assert result.risk_level == "CRITICAL"
        assert result.security_score == 80
        assert result.executive_summary  # deterministic fallback text
        assert result.raw_response is None

    async def test_unparseable_narrative_falls_back_but_keeps_raw(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(text="definitely not json")
        proc = VulnerabilityAIProcessor(gateway=gw)
        result = await proc.analyze_scan_results([_scan_result([_finding(severity="high")])])
        assert result.model_used == "fake/fake-1"
        assert result.raw_response == "definitely not json"
        assert result.risk_score == 25
        assert result.executive_summary  # fallback narrative, not empty
        # one retry with schema reminder = 2 calls
        assert len(gw.calls) == 2


class TestEnrichment:
    async def test_sets_fields_on_model_finding(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        advice = {
            "remediation": "Use parameterized queries",
            "fix_effort": "high",
            "secure_code": "cursor.execute('SELECT * FROM t WHERE id = ?', (id,))",
        }
        gw = FakeGateway(text=json.dumps(advice))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = _finding()
        result = await proc.enrich_findings_with_remediation([finding])
        assert result == [finding]
        assert finding.remediation == "Use parameterized queries"
        assert finding.fix_effort == "high"
        assert finding.remediation_code is not None
        assert gw.calls[0]["purpose"] == "remediation"
        assert gw.calls[0]["use_cache"] is True
        assert gw.calls[0]["json_schema"].__name__ == "RemediationAdvice"

    async def test_sets_fields_on_dict_finding(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        advice = {"remediation": "Escape output", "fix_effort": "low", "secure_code": None}
        gw = FakeGateway(text=json.dumps(advice))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = {"title": "XSS", "description": "reflected", "remediation": None}
        await proc.enrich_findings_with_remediation([finding])
        assert finding["remediation"] == "Escape output"
        assert finding["fix_effort"] == "low"
        assert finding["remediation_code"] is None

    async def test_skips_findings_without_title_or_description(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(text=json.dumps({"remediation": "x"}))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = _finding(title="", description="")
        await proc.enrich_findings_with_remediation([finding])
        assert gw.calls == []

    async def test_gateway_error_returns_findings_unchanged(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        gw = FakeGateway(error=GatewayError("All AI providers failed"))
        proc = VulnerabilityAIProcessor(gateway=gw)
        finding = _finding()
        result = await proc.enrich_findings_with_remediation([finding])
        assert result == [finding]
        assert finding.remediation is None
        assert finding.remediation_code is None


class TestHelpers:
    @pytest.fixture
    def proc(self):
        from services.ai.ai_processor import VulnerabilityAIProcessor

        return VulnerabilityAIProcessor(gateway=FakeGateway())

    def test_prepare_findings_data(self, proc):
        data = proc._prepare_findings_data(
            [_scan_result([_finding(severity="high")])]
        )
        assert data["total_findings"] == 1
        assert data["severity_counts"]["high"] == 1
        assert data["scanner_summary"]["bandit"]["findings_count"] == 1

    def test_prepare_findings_data_empty(self, proc):
        data = proc._prepare_findings_data([])
        assert data["total_findings"] == 0
        assert data["severity_counts"]["critical"] == 0

    def test_calculate_risk_score(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 0, "low": 0, "info": 0},
        }
        score, level = proc._calculate_risk_score(data)
        assert score == 90
        assert level == "CRITICAL"

    def test_calculate_security_score(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1},
        }
        assert proc._calculate_security_score(data) == 60

    def test_categorize_threats(self, proc):
        data = {"findings": [
            {"title": "SQL Injection vulnerability", "description": "SQL injection in login"}
        ]}
        assert proc._categorize_threats(data).get("Injection") == 1

    def test_estimate_fix_time(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1},
        }
        assert "hours" in proc._estimate_fix_time(data)

    def test_remediation_roadmap(self, proc):
        data = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 3, "low": 0, "info": 0},
        }
        roadmap = proc._generate_remediation_roadmap(data)
        assert [r["priority"] for r in roadmap] == ["CRITICAL", "HIGH", "MEDIUM"]

    def test_create_clean_analysis(self, proc):
        analysis = proc._create_clean_analysis()
        assert isinstance(analysis, AIAnalysis)
        assert analysis.risk_score == 5
        assert analysis.security_score == 98
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_processor.py -v`
Expected: FAIL — import errors (`VulnerabilityAIProcessor.__init__` signature / missing `_generate_remediation_roadmap`) and assertion failures against the old fan-out implementation.

- [ ] **Step 3: Replace `backend/services/ai/ai_processor.py` entirely**

```python
"""Unified AI processing service.

Deterministic fields (risk/security scores, threat categories, fix time,
roadmap) are computed in code. The narrative fields come from a single
JSON-structured LLM call through the gateway — one call per scan instead
of the old 7-8 prompt fan-out.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import settings
from models.report import AIAnalysis, ScanResult
from services.ai.gateway import (
    GatewayError,
    LLMGateway,
    complete_structured,
    get_gateway,
)
from services.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    REMEDIATION_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_remediation_prompt,
)
from services.ai.schemas import AnalysisNarrative, RemediationAdvice

logger = logging.getLogger(__name__)


class AIProcessorError(Exception):
    """Custom exception for AI processing errors"""
    pass


class VulnerabilityAIProcessor:
    """AI processor for vulnerability analysis and recommendations"""

    def __init__(self, gateway: Optional[LLMGateway] = None):
        self._gateway = gateway

    @property
    def gateway(self) -> LLMGateway:
        return self._gateway if self._gateway is not None else get_gateway()

    async def analyze_scan_results(
        self,
        scan_results: List[ScanResult],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> AIAnalysis:
        """Analyze vulnerability scan results: deterministic math + 1 structured LLM call."""
        try:
            logger.info("Starting AI analysis of vulnerability findings")
            findings_data = self._prepare_findings_data(scan_results)
            if not findings_data["total_findings"]:
                return self._create_clean_analysis()

            # Deterministic fields — never re-asked to a model.
            risk_score, risk_level = self._calculate_risk_score(findings_data)
            security_score = self._calculate_security_score(findings_data)
            threat_categories = self._categorize_threats(findings_data)
            estimated_fix_time = self._estimate_fix_time(findings_data)
            roadmap = self._generate_remediation_roadmap(findings_data)

            model_used = "unavailable"
            raw_response = None
            narrative: Optional[AnalysisNarrative] = None
            try:
                narrative, result = await complete_structured(
                    self.gateway,
                    system=ANALYSIS_SYSTEM_PROMPT,
                    user=build_analysis_prompt(findings_data, project_context),
                    purpose="analysis",
                    schema=AnalysisNarrative,
                    temperature=0.3,
                )
                model_used = f"{result.provider}/{result.model}"
                raw_response = result.text
            except GatewayError as e:
                logger.warning("AI narrative unavailable, using deterministic fallback: %s", e)

            if narrative is None:
                narrative = self._fallback_narrative(findings_data)

            ai_analysis = AIAnalysis(
                model_used=model_used,
                generated_at=datetime.now(timezone.utc),
                executive_summary=narrative.executive_summary,
                risk_assessment=narrative.risk_assessment,
                risk_score=risk_score,
                risk_level=risk_level,
                priority_findings=narrative.priority_findings,
                recommendations=narrative.recommendations,
                secure_code_examples=narrative.secure_code_examples,
                compliance_impact=narrative.compliance_impact,
                estimated_fix_time=estimated_fix_time,
                attack_vectors=narrative.attack_vectors,
                threat_categories=threat_categories,
                remediation_roadmap=roadmap,
                security_score=security_score,
                raw_response=raw_response,
            )
            logger.info("AI analysis completed successfully (%s)", model_used)
            return ai_analysis
        except Exception as e:
            logger.error("AI analysis failed: %s", e)
            raise AIProcessorError(f"Failed to analyze vulnerabilities: {e}")

    async def enrich_findings_with_remediation(
        self,
        findings: List[Any],
        batch_size: int = 5,
    ) -> List[Any]:
        """Enrich findings with AI remediation guidance (sequential batches)."""
        try:
            logger.info("Enriching %s findings with AI remediation guidance", len(findings))
            for i in range(0, len(findings), batch_size):
                await self._enrich_batch_with_remediation(findings[i : i + batch_size])
            return findings
        except Exception as e:
            logger.error("Error enriching findings with remediation: %s", e)
            return findings

    async def _enrich_batch_with_remediation(self, findings: List[Any]) -> None:
        for finding in findings:
            try:
                data = self._finding_as_dict(finding)
                if not data.get("title") and not data.get("description"):
                    continue
                advice, _ = await complete_structured(
                    self.gateway,
                    system=REMEDIATION_SYSTEM_PROMPT,
                    user=build_remediation_prompt(data),
                    purpose="remediation",
                    schema=RemediationAdvice,
                    temperature=0.2,
                    use_cache=True,
                )
                if advice is None:
                    logger.warning(
                        "No parseable remediation for finding %r", data.get("title", "")[:80]
                    )
                    continue
                self._apply_advice(finding, advice)
            except Exception as e:
                logger.warning("Failed to generate remediation for finding: %s", e)
                continue

    # --- finding helpers --------------------------------------------------

    @staticmethod
    def _finding_as_dict(finding: Any) -> Dict[str, Any]:
        if isinstance(finding, dict):
            return finding
        severity = getattr(finding, "severity", "") or ""
        if hasattr(severity, "value"):
            severity = severity.value
        return {
            "title": getattr(finding, "title", "") or "",
            "description": getattr(finding, "description", "") or "",
            "severity": severity,
            "file_path": getattr(finding, "file_path", "") or "",
            "code_snippet": getattr(finding, "code_snippet", "") or "",
            "cwe_id": getattr(finding, "cwe_id", "") or "",
            "cve_id": getattr(finding, "cve_id", "") or "",
        }

    @staticmethod
    def _apply_advice(finding: Any, advice: RemediationAdvice) -> None:
        remediation = advice.remediation or None
        fix_effort = advice.fix_effort if advice.fix_effort in ("low", "medium", "high") else "medium"
        secure_code = advice.secure_code or None
        if isinstance(finding, dict):
            finding["remediation"] = remediation
            finding["fix_effort"] = fix_effort
            finding["remediation_code"] = secure_code
            return
        if hasattr(finding, "remediation"):
            finding.remediation = remediation
            finding.fix_effort = fix_effort
            finding.remediation_code = secure_code

    # --- deterministic analysis ------------------------------------------

    @staticmethod
    def _fallback_narrative(findings_data: Dict[str, Any]) -> AnalysisNarrative:
        """Degraded narrative when the LLM was unreachable or unparseable."""
        counts = findings_data["severity_counts"]
        total = findings_data["total_findings"]
        crit, high = counts.get("critical", 0), counts.get("high", 0)
        priority = [
            f.get("title", "")
            for f in findings_data.get("findings", [])
            if (f.get("severity") or "").lower() in ("critical", "high")
        ][:5]
        return AnalysisNarrative(
            executive_summary=(
                f"Automated scan identified {total} finding(s) "
                f"({crit} critical, {high} high). AI narrative generation was unavailable; "
                "the deterministic risk metrics below are computed directly from scanner results."
            ),
            risk_assessment=(
                f"{crit + high} critical/high finding(s) require prioritized remediation. "
                "Follow the remediation roadmap for a phased fix plan."
            ),
            priority_findings=priority,
            recommendations=[
                "Remediate critical and high-severity findings first",
                "Add automated security tests to the CI/CD pipeline",
                "Keep dependencies updated to patched versions",
            ],
            secure_code_examples={},
            compliance_impact={},
            attack_vectors=[],
        )

    def _prepare_findings_data(self, scan_results: List[ScanResult]) -> Dict[str, Any]:
        """Prepare findings data for AI analysis"""
        all_findings = []
        scanner_summary = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for scan_result in scan_results:
            scanner_summary[scan_result.scanner.value] = {
                "status": scan_result.status.value,
                "findings_count": len(scan_result.findings),
                "duration": scan_result.duration_seconds,
            }

            for finding in scan_result.findings:
                all_findings.append({
                    "scanner": finding.scanner.value,
                    "rule_id": finding.rule_id,
                    "title": finding.title,
                    "description": finding.description,
                    "severity": finding.severity.value,
                    "file_path": finding.file_path,
                    "cwe_id": finding.cwe_id,
                    "cve_id": finding.cve_id,
                    "owasp_category": finding.owasp_category,
                })
                severity_counts[finding.severity.value] += 1

        return {
            "total_findings": len(all_findings),
            "findings": all_findings[:50],  # Limit for API call
            "severity_counts": severity_counts,
            "scanner_summary": scanner_summary,
        }

    def _create_clean_analysis(self) -> AIAnalysis:
        """Create analysis for clean scan (no vulnerabilities)"""
        return AIAnalysis(
            model_used="none/clean-scan",
            generated_at=datetime.now(timezone.utc),
            executive_summary="🎉 Excellent security posture! No security vulnerabilities were detected in this comprehensive scan. The codebase demonstrates strong adherence to security best practices and secure coding standards.",
            risk_assessment="LOW - No immediate security risks identified. The application shows a mature security stance with no critical, high, or medium vulnerabilities detected. Continue following secure coding practices and regular security assessments.",
            risk_score=5,
            risk_level="LOW",
            security_score=98,
            priority_findings=[],
            recommendations=[
                "✅ Maintain current security practices and coding standards",
                "🔄 Continue regular automated security scans in CI/CD pipeline",
                "📦 Keep all dependencies updated to latest secure versions",
                "👥 Implement security-focused peer code reviews",
                "📚 Provide ongoing security training for development team",
            ],
            secure_code_examples={},
            compliance_impact={
                "overall_impact": "Positive",
                "analysis": "Clean scan results strongly support compliance requirements across all major frameworks",
                "frameworks_affected": "SOC 2, ISO 27001, NIST, PCI-DSS, GDPR, HIPAA",
                "required_actions": "No immediate actions required. Continue current security practices.",
            },
            estimated_fix_time="0 hours - No issues to fix",
            attack_vectors=[],
            threat_categories={},
            remediation_roadmap=[],
        )

    def _calculate_risk_score(self, findings_data: Dict[str, Any]) -> tuple:
        """Calculate numerical risk score and level based on findings"""
        severity_counts = findings_data["severity_counts"]

        # Weighted scoring: Critical=40, High=25, Medium=10, Low=3, Info=1
        score = (
            severity_counts["critical"] * 40
            + severity_counts["high"] * 25
            + severity_counts["medium"] * 10
            + severity_counts["low"] * 3
            + severity_counts["info"] * 1
        )
        risk_score = min(100, score)

        if severity_counts["critical"] > 0 or risk_score >= 70:
            risk_level = "CRITICAL"
        elif severity_counts["high"] > 0 or risk_score >= 40:
            risk_level = "HIGH"
        elif severity_counts["medium"] > 0 or risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return risk_score, risk_level

    def _calculate_security_score(self, findings_data: Dict[str, Any]) -> int:
        """Calculate overall security score (inverse of risk)"""
        severity_counts = findings_data["severity_counts"]

        score = 100
        score -= severity_counts["critical"] * 20
        score -= severity_counts["high"] * 12
        score -= severity_counts["medium"] * 5
        score -= severity_counts["low"] * 2
        score -= severity_counts["info"] * 0.5

        return max(0, int(score))

    def _categorize_threats(self, findings_data: Dict[str, Any]) -> Dict[str, int]:
        """Categorize findings into threat categories"""
        categories = {
            "Injection": 0,
            "Authentication": 0,
            "Sensitive Data": 0,
            "Access Control": 0,
            "Security Misconfiguration": 0,
            "Cryptographic Issues": 0,
            "Input Validation": 0,
            "Other": 0,
        }

        for finding in findings_data.get("findings", []):
            title = finding.get("title", "").lower()
            desc = finding.get("description", "").lower()
            if any(k in title + desc for k in ["sql", "injection", "sqli", "command injection", "ldap", "xpath"]):
                categories["Injection"] += 1
            elif any(k in title + desc for k in ["auth", "password", "credential", "session", "token", "login"]):
                categories["Authentication"] += 1
            elif any(k in title + desc for k in ["secret", "key", "api_key", "private", "sensitive", "exposure"]):
                categories["Sensitive Data"] += 1
            elif any(k in title + desc for k in ["access", "permission", "privilege", "authorization", "idor"]):
                categories["Access Control"] += 1
            elif any(k in title + desc for k in ["config", "setting", "debug", "verbose", "default"]):
                categories["Security Misconfiguration"] += 1
            elif any(k in title + desc for k in ["crypto", "encrypt", "hash", "ssl", "tls", "certificate"]):
                categories["Cryptographic Issues"] += 1
            elif any(k in title + desc for k in ["input", "validation", "sanitiz", "xss", "cross-site"]):
                categories["Input Validation"] += 1
            else:
                categories["Other"] += 1

        return {k: v for k, v in categories.items() if v > 0}

    def _estimate_fix_time(self, findings_data: Dict[str, Any]) -> str:
        """Estimate time required to fix identified issues"""
        severity_counts = findings_data["severity_counts"]

        critical_hours = severity_counts["critical"] * 8
        high_hours = severity_counts["high"] * 4
        medium_hours = severity_counts["medium"] * 2
        low_hours = severity_counts["low"] * 1

        total_hours = critical_hours + high_hours + medium_hours + low_hours

        if total_hours == 0:
            return "0 hours - No issues to fix"
        elif total_hours < 8:
            return f"{total_hours} hours"
        elif total_hours < 40:
            days = total_hours / 8
            return f"{days:.1f} days ({total_hours} hours)"
        else:
            weeks = total_hours / 40
            return f"{weeks:.1f} weeks ({total_hours} hours)"

    def _generate_remediation_roadmap(self, findings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Phased remediation roadmap (deterministic, ported from ollama processor)."""
        severity_counts = findings_data["severity_counts"]
        roadmap = []

        if severity_counts.get("critical", 0) > 0:
            roadmap.append({
                "phase": 1,
                "title": "Emergency Response",
                "timeline": "Within 24 hours",
                "priority": "CRITICAL",
                "tasks": [
                    f"Address {severity_counts['critical']} critical vulnerabilities immediately",
                    "Implement emergency patches or workarounds",
                    "Enable enhanced monitoring for exploitation attempts",
                    "Notify security team and stakeholders",
                ],
                "status": "pending",
            })

        if severity_counts.get("high", 0) > 0:
            roadmap.append({
                "phase": 2,
                "title": "High Priority Fixes",
                "timeline": "Within 1 week",
                "priority": "HIGH",
                "tasks": [
                    f"Remediate {severity_counts['high']} high-severity findings",
                    "Update vulnerable dependencies",
                    "Implement security controls and hardening",
                    "Conduct security code review",
                ],
                "status": "pending",
            })

        if severity_counts.get("medium", 0) > 0:
            roadmap.append({
                "phase": 3,
                "title": "Security Hardening",
                "timeline": "Within 2 weeks",
                "priority": "MEDIUM",
                "tasks": [
                    f"Address {severity_counts['medium']} medium-severity issues",
                    "Implement additional security best practices",
                    "Enhance input validation and sanitization",
                    "Review and update security configurations",
                ],
                "status": "pending",
            })

        if severity_counts.get("low", 0) > 0 or severity_counts.get("info", 0) > 0:
            roadmap.append({
                "phase": 4,
                "title": "Security Posture Improvement",
                "timeline": "Within 1 month",
                "priority": "LOW",
                "tasks": [
                    f"Address {severity_counts.get('low', 0)} low-severity findings",
                    "Implement security best practices",
                    "Update documentation and security policies",
                    "Conduct security awareness training",
                ],
                "status": "pending",
            })

        return roadmap


# Global AI processor instance - lazy initialization
_ai_processor = None


def get_ai_processor() -> VulnerabilityAIProcessor:
    """Get or create the global AI processor instance"""
    global _ai_processor
    if _ai_processor is None:
        try:
            # Factory selects the provider chain (repointed to factory.py in Task 6)
            from .gemini_ai_processor import create_ai_processor

            _ai_processor = create_ai_processor()
            logger.info("AI processor initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize AI processor: {e}")
            raise AIProcessorError(f"AI processor initialization failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing AI processor: {e}")
            raise AIProcessorError(f"AI processor initialization failed: {e}")
    return _ai_processor


# Create function to get the processor when needed
def ai_processor():
    return get_ai_processor()
```

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_processor.py -v`
Expected: 16 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green (`test_ollama_processor.py` still tests the old Ollama class, which is untouched until Task 6).

---

### Task 6: Factory module, package cleanup, delete duplicate processors

**Files:**
- Create: `backend/services/ai/factory.py`
- Modify: `backend/services/ai/__init__.py` (remove star imports of gemini/ollama)
- Modify: `backend/services/ai/ai_processor.py:708` (repoint `get_ai_processor` to factory)
- Delete: `backend/services/ai/gemini_ai_processor.py`, `backend/services/ai/ollama_ai_processor.py`, `backend/tests/test_ollama_processor.py`
- Test: `backend/tests/test_ai_factory.py` (create)

**Interfaces:**
- Consumes: `VulnerabilityAIProcessor` (Task 5), `Settings.configured_provider_chain()` (Task 1)
- Produces:
  - `factory.create_ai_processor()` — same name/contract as the old gemini factory: returns a processor, raises `ValueError` when no provider in the chain has credentials
  - `services.ai` package exports exactly `get_ai_processor` and `AIProcessorError` (plus existing `ml_anomaly_detection_engine` star import)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_ai_factory.py`:

```python
"""Tests for the AI processor factory and package exports."""
import pytest

from config import settings


def test_create_returns_unified_processor(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini,groq")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "groq_api_key", "k" * 20)
    monkeypatch.setattr(settings, "openai_api_key", None)

    from services.ai.factory import create_ai_processor
    from services.ai.ai_processor import VulnerabilityAIProcessor

    processor = create_ai_processor()
    assert isinstance(processor, VulnerabilityAIProcessor)


def test_create_raises_when_explicit_provider_lacks_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)

    from services.ai.factory import create_ai_processor

    with pytest.raises(ValueError, match="No AI provider available"):
        create_ai_processor()


def test_create_raises_when_chain_unusable(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)

    from services.ai.factory import create_ai_processor

    with pytest.raises(ValueError, match="No AI provider available"):
        create_ai_processor()


def test_package_exports():
    from services.ai import AIProcessorError, get_ai_processor

    assert callable(get_ai_processor)
    assert issubclass(AIProcessorError, Exception)


def test_get_ai_processor_uses_factory(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "openai_api_key", None)

    import services.ai.ai_processor as mod

    monkeypatch.setattr(mod, "_ai_processor", None)
    from services.ai.ai_processor import get_ai_processor

    processor = get_ai_processor()
    from services.ai.ai_processor import VulnerabilityAIProcessor

    assert isinstance(processor, VulnerabilityAIProcessor)
```

Note: `test_get_ai_processor_uses_factory` only passes after `get_ai_processor` is repointed to `factory.py`; `get_ai_processor` caches in module global `_ai_processor`, which the test resets via `monkeypatch.setattr(mod, "_ai_processor", None)`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_factory.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.ai.factory'`

- [ ] **Step 3: Write `backend/services/ai/factory.py`**

```python
"""Factory for the unified AI processor."""
import logging

from config import settings

logger = logging.getLogger(__name__)


def create_ai_processor():
    """Create the unified AI processor.

    Provider selection: uses Settings.configured_provider_chain() — for
    ai_provider=auto that is the configured subset of ai_provider_chain
    (legacy OPENAI_API_KEY appended last); for an explicit provider, just it.

    Raises ValueError when no provider in the chain has credentials.
    """
    configured = settings.configured_provider_chain()
    if not configured:
        raise ValueError(
            "No AI provider available. Configure at least one of:\n"
            "  - GEMINI_API_KEY (primary, free tier)\n"
            "  - GROQ_API_KEY / OPENROUTER_API_KEY (free-tier fallbacks)\n"
            "  - OPENAI_API_KEY (legacy fallback)\n"
            "  - AI_PROVIDER=ollama with a running Ollama server"
        )
    logger.info("Creating unified AI processor (chain: %s)", " -> ".join(configured))
    from .ai_processor import VulnerabilityAIProcessor

    return VulnerabilityAIProcessor()
```

- [ ] **Step 4: Repoint `get_ai_processor` in `backend/services/ai/ai_processor.py`**

Replace inside `get_ai_processor`:

```python
            # Factory selects the provider chain (repointed to factory.py in Task 6)
            from .gemini_ai_processor import create_ai_processor

            _ai_processor = create_ai_processor()
```

with:

```python
            from .factory import create_ai_processor

            _ai_processor = create_ai_processor()
```

- [ ] **Step 5: Update `backend/services/ai/__init__.py`**

Replace the whole file with:

```python
"""
AI & Machine Learning Services
"""
from .ai_processor import AIProcessorError, get_ai_processor
from .ml_anomaly_detection_engine import *

__all__ = [
    "get_ai_processor",
    "AIProcessorError",
]
```

- [ ] **Step 6: Delete the duplicate processors and their test**

Run (PowerShell, from `E:\Projects\ONYX`):

```powershell
Remove-Item -LiteralPath backend\services\ai\gemini_ai_processor.py
Remove-Item -LiteralPath backend\services\ai\ollama_ai_processor.py
Remove-Item -LiteralPath backend\tests\test_ollama_processor.py
```

- [ ] **Step 7: Verify no stale references remain**

Run (from `E:\Projects\ONYX`):

```powershell
Get-ChildItem -Recurse -Path backend -Include *.py | Select-String -Pattern "gemini_ai_processor|ollama_ai_processor"
```
Expected: no output.

- [ ] **Step 8: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ai_factory.py -v`
Expected: 5 passed.

- [ ] **Step 9: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green — `test_ollama_processor.py` is gone, everything else passes (the 5 factory tests replace its coverage of `create_ai_processor`).

---

### Task 7: Triage via gateway

**Files:**
- Modify: `backend/services/triage/triage_service.py` (imports + `__init__` + `_call_ai`)
- Test: `backend/tests/test_triage_gateway.py` (create)

**Interfaces:**
- Consumes: `LLMGateway.complete`, `GatewayError`, `get_gateway()` (Task 4)
- Produces (preserved seam): `TriageService._call_ai(prompt: str) -> Optional[str]` — returns `None` on any AI failure so `triage_scan` degrades exactly as today (existing tests patch this seam with `AsyncMock(return_value=None)`)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_triage_gateway.py`:

```python
"""Triage AI calls go through the LLM gateway."""
from unittest.mock import patch

import pytest

from services.ai.gateway import GatewayError, GatewayResult
from services.triage.triage_service import TriageService


class FakeGateway:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="fake-1",
            usage={}, latency_ms=1,
        )


async def test_call_ai_returns_gateway_text():
    gw = FakeGateway(text="Executive summary text")
    with patch("services.triage.triage_service.get_gateway", return_value=gw):
        out = await TriageService()._call_ai("rate this scan")
    assert out == "Executive summary text"
    assert gw.calls[0]["purpose"] == "triage"
    assert gw.calls[0]["temperature"] == 0.3
    assert "cybersecurity expert" in gw.calls[0]["system"]
    assert gw.calls[0]["user"] == "rate this scan"


async def test_call_ai_gateway_error_returns_none():
    gw = FakeGateway(error=GatewayError("All AI providers failed"))
    with patch("services.triage.triage_service.get_gateway", return_value=gw):
        assert await TriageService()._call_ai("p") is None


async def test_call_ai_unexpected_error_returns_none():
    gw = FakeGateway(error=RuntimeError("boom"))
    with patch("services.triage.triage_service.get_gateway", return_value=gw):
        assert await TriageService()._call_ai("p") is None


def test_legacy_httpx_client_removed():
    service = TriageService()
    assert not hasattr(TriageService, "_ensure_ai_client")
    assert not hasattr(service, "_ai_http_client")
    assert not hasattr(service, "_ai_client_initialized")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_triage_gateway.py -v`
Expected: FAIL — `AttributeError: module 'services.triage.triage_service' has no attribute 'get_gateway'` (import missing) and `test_legacy_httpx_client_removed` fails (`_ensure_ai_client` still exists).

- [ ] **Step 3: Rewrite the AI call path in `backend/services/triage/triage_service.py`**

1. Remove `import httpx` (line 7) — no other usage remains.
2. Add module-level import next to the other service imports:

```python
from services.ai.gateway import GatewayError, get_gateway
```

3. Replace `TriageService.__init__` (lines 61-64) — drop the legacy client fields:

```python
    def __init__(self):
        pass
```

4. Delete `async def _ensure_ai_client` (lines 66-76) entirely.
5. Replace `async def _call_ai` (lines 294-320) with:

```python
    async def _call_ai(self, prompt: str) -> Optional[str]:
        try:
            result = await get_gateway().complete(
                system=(
                    "You are a senior cybersecurity expert specializing in "
                    "vulneracy triage and business risk analysis."
                ),
                user=prompt,
                purpose="triage",
                max_tokens=settings.openai_max_tokens,
                temperature=0.3,
            )
            return result.text
        except GatewayError as e:
            logger.warning(f"AI call failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"AI call failed: {e}")
            return None
```

Keep `from config import settings` — `settings.openai_max_tokens` is still used (only `settings.openai_api_key`/`settings.openai_model` usages disappear, all of which were inside the deleted code).

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_triage_gateway.py -v`
Expected: 4 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green — `test_triage_service.py` still patches `_call_ai` at the seam.

---

### Task 8: AI chat via gateway

**Files:**
- Modify: `backend/routes/ai_chat.py` (`_call_ai_chat` + `_get_active_model` + imports)
- Test: `backend/tests/test_chat_gateway.py` (create)

**Interfaces:**
- Consumes: `LLMGateway.complete_messages`, `GatewayError`, `get_gateway()` (Task 4), `Settings.configured_provider_chain()` (Task 1)
- Produces (preserved seams):
  - `_call_ai_chat(message, scan_context, conversation_history) -> str` — still raises `HTTPException` (503 on gateway exhaustion, everything else propagates to the route's 502 handler)
  - `_get_active_model() -> str` — still `"provider/model"` shape

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_chat_gateway.py`:

```python
"""AI chat calls go through the LLM gateway."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from config import settings
from routes.ai_chat import _call_ai_chat, _get_active_model
from services.ai.gateway import GatewayError, GatewayResult


class FakeGateway:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete_messages(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="fake-1",
            usage={}, latency_ms=1,
        )


async def test_builds_messages_and_calls_gateway():
    gw = FakeGateway(text="Use parameterized queries.")
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        out = await _call_ai_chat(
            message="how do I fix SQLi?",
            scan_context={"project_name": "demo", "total_findings": 3},
            conversation_history=history,
        )
    assert out == "Use parameterized queries."
    call = gw.calls[0]
    assert call["purpose"] == "chat"
    assert call["max_tokens"] == 1500
    assert call["temperature"] == 0.3
    msgs = call["messages"]
    assert msgs[0]["role"] == "system"
    assert "ONYX Security AI" in msgs[0]["content"]
    assert "## Current Scan Context" in msgs[0]["content"]
    assert '"total_findings": 3' in msgs[0]["content"]
    assert msgs[1] == {"role": "user", "content": "hi"}
    assert msgs[2] == {"role": "assistant", "content": "hello"}
    assert msgs[-1] == {"role": "user", "content": "how do I fix SQLi?"}


async def test_history_capped_at_10_and_roles_sanitized():
    gw = FakeGateway(text="ok")
    history = [{"role": "system", "content": f"m{i}"} for i in range(15)]
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        await _call_ai_chat(message="q", scan_context={}, conversation_history=history)
    msgs = gw.calls[0]["messages"]
    # 1 system + 10 capped history + 1 user
    assert len(msgs) == 12
    assert all(m["role"] == "user" for m in msgs[1:-1])
    assert msgs[-1] == {"role": "user", "content": "q"}


async def test_gateway_error_raises_503_with_generic_detail():
    gw = FakeGateway(error=GatewayError("All AI providers failed: gemini: 401 INVALID_API_KEY sk-secret"))
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        with pytest.raises(HTTPException) as exc:
            await _call_ai_chat(message="q", scan_context={})
    assert exc.value.status_code == 503
    assert "temporarily unavailable" in exc.value.detail
    assert "sk-secret" not in exc.value.detail
    assert "gemini" not in exc.value.detail


async def test_no_history_still_calls_user_message():
    gw = FakeGateway(text="reply")
    with patch("routes.ai_chat.get_gateway", return_value=gw):
        out = await _call_ai_chat(message="only question", scan_context={"a": 1})
    assert out == "reply"
    assert len(gw.calls[0]["messages"]) == 2


def test_get_active_model_first_configured(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "ai_provider_chain", "gemini,groq")
    monkeypatch.setattr(settings, "gemini_api_key", "g" * 20)
    monkeypatch.setattr(settings, "groq_api_key", "k" * 20)
    monkeypatch.setattr(settings, "openai_api_key", None)
    assert _get_active_model() == "gemini/gemini-2.5-flash"


def test_get_active_model_unavailable_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)
    assert _get_active_model() == "unavailable"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_chat_gateway.py -v`
Expected: FAIL — `AttributeError: module 'routes.ai_chat' has no attribute 'get_gateway'` (import missing) and `_get_active_model` assertions fail (old logic).

- [ ] **Step 3: Rewrite the AI path in `backend/routes/ai_chat.py`**

1. Add module-level import next to `from config import settings`:

```python
from services.ai.gateway import GatewayError, get_gateway
```

2. Replace `async def _call_ai_chat` (lines ~99-206) entirely — note the new implementation caps history and uses one message list (fixes the Gemini per-turn replay bug where history was sent twice):

```python
async def _call_ai_chat(
    message: str,
    scan_context: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    system_prompt = """You are ONYX Security AI, a senior application security engineer assistant.
You analyze security scan results and answer questions about vulnerabilities, risks, and fixes.

Guidelines:
- Be concise and technical. Focus on actionable security advice.
- When asked about specific findings, reference the actual scan data provided.
- Explain vulnerability impact in business terms (data breach risk, compliance violation, etc.).
- Provide specific code-level remediation guidance when relevant.
- If the question is outside security scanning scope, politely redirect to security topics.
- Format code snippets with appropriate language tags.
- Use plain text - no markdown formatting symbols like asterisks or backticks in your thinking, but you may use natural formatting.

The user's scan results and AI analysis context are provided below. Use them to answer questions accurately."""

    context_str = json.dumps(scan_context, indent=2, default=str)
    full_system_prompt = f"{system_prompt}\n\n## Current Scan Context\n```json\n{context_str}\n```"

    messages: List[Dict[str, str]] = [{"role": "system", "content": full_system_prompt}]
    for msg in (conversation_history or [])[-10:]:
        role = msg["role"] if msg["role"] in ALLOWED_CHAT_ROLES else "user"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        result = await get_gateway().complete_messages(
            messages=messages,
            purpose="chat",
            max_tokens=1500,
            temperature=0.3,
        )
    except GatewayError as e:
        logger.error(f"AI chat gateway exhausted: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI chat is temporarily unavailable. Please try again shortly.",
        )
    return result.text
```

This deletes the whole ollama/gemini/openai cascade including `from openai import AsyncOpenAI`, `from google import genai` branches. `get_safe_error_detail` remains used only by the route's generic `except` handler (line ~240) — keep that import.

3. Replace `def _get_active_model` (lines ~209-215) with:

```python
def _get_active_model() -> str:
    chain = settings.configured_provider_chain()
    if not chain:
        return "unavailable"
    provider = chain[0]
    models = {
        "gemini": settings.gemini_model,
        "groq": settings.groq_model,
        "openrouter": settings.openrouter_model,
        "openai": settings.openai_model,
        "ollama": settings.ai_local_model,
    }
    return f"{provider}/{models.get(provider, 'unknown')}"
```

4. Leave `_build_scan_context`, the route handler, `ChatRequest`/`ChatResponse`, and rate limiting untouched. The route already converts any non-`HTTPException` to 502, which `test_chat_ai_service_error` asserts.

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_chat_gateway.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green — `test_ai_chat.py` patches `_call_ai_chat` at the seam; `_get_active_model` in those tests runs against fixture settings where keys are unset → returns `"unavailable"` for `model_used` (assertions there check reply content, not model string — verified: `test_chat_success` asserts `reply`, not `model_used`).

---

### Task 9: Remediation enrichment module + scan-flow wiring

**Files:**
- Create: `backend/services/ai/enrichment.py`
- Modify: `backend/routes/webhook/scan_operations.py` (import + enrichment block before `final_update` + conditional re-persist)
- Test: `backend/tests/test_enrichment.py` (create)

**Interfaces:**
- Consumes: `VulnerabilityAIProcessor.enrich_findings_with_remediation` + `get_ai_processor` (Task 5/6), `settings.ai_enrich_top_n` (Task 1)
- Produces:
  - `enrichment.select_findings_for_enrichment(findings: list[dict], top_n: Optional[int] = None) -> list[dict]` — severity-stratified top-N (critical/high always first, capped at `settings.ai_enrich_top_n`, default 10)
  - `enrichment.enrich_detailed_findings(findings: list[dict], *, top_n=None, batch_size=5) -> bool` — enriches the selected subset **in place**, returns `True` only if enrichment ran; never raises

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_enrichment.py`:

```python
"""Severity-stratified top-N remediation enrichment."""
from unittest.mock import AsyncMock, MagicMock, patch

import services.ai.enrichment as enrichment_mod
from services.ai.enrichment import enrich_detailed_findings, select_findings_for_enrichment


def _finding(sev, i):
    return {"id": f"f-{i}", "title": f"t{i}", "description": "d", "severity": sev}


def test_select_orders_by_severity_and_caps_at_top_n():
    findings = (
        [_finding("info", i) for i in range(4)]
        + [_finding("low", 10 + i) for i in range(1)]
        + [_finding("medium", 20 + i) for i in range(3)]
        + [_finding("high", 30 + i) for i in range(2)]
        + [_finding("critical", 40 + i) for i in range(2)]
    )  # 12 total
    selected = select_findings_for_enrichment(findings, top_n=10)
    assert len(selected) == 10
    severities = [f["severity"] for f in selected]
    # all critical + high first, then medium, low, info last
    assert severities[:4] == ["critical", "critical", "high", "high"]
    assert severities[4:7] == ["medium", "medium", "medium"]
    assert severities[7:] == ["low", "info", "info"]


def test_select_zero_top_n_returns_empty():
    assert select_findings_for_enrichment([_finding("critical", 1)], top_n=0) == []


def test_select_empty_findings_returns_empty():
    assert select_findings_for_enrichment([], top_n=10) == []


async def test_enrich_runs_processor_on_selected_subset_only():
    findings = [_finding("critical", 1)] + [_finding("low", i) for i in range(2, 15)]
    fake_processor = MagicMock()
    fake_processor.enrich_findings_with_remediation = AsyncMock(return_value=None)

    with patch.object(enrichment_mod, "get_ai_processor", return_value=fake_processor):
        ran = await enrich_detailed_findings(findings, top_n=3, batch_size=2)

    assert ran is True
    passed = fake_processor.enrich_findings_with_remediation.call_args.args[0]
    assert len(passed) == 3
    assert passed[0]["severity"] == "critical"
    kwargs = fake_processor.enrich_findings_with_remediation.call_args.kwargs
    assert kwargs["batch_size"] == 2


async def test_enrich_processor_unavailable_returns_false_and_leaves_findings():
    from services.ai.ai_processor import AIProcessorError

    findings = [_finding("critical", 1)]
    with patch.object(
        enrichment_mod, "get_ai_processor", side_effect=AIProcessorError("no provider")
    ):
        assert await enrich_detailed_findings(findings) is False
    assert findings == [_finding("critical", 1)]


async def test_enrich_processor_crash_returns_false():
    findings = [_finding("critical", 1)]
    fake_processor = MagicMock()
    fake_processor.enrich_findings_with_remediation = AsyncMock(side_effect=RuntimeError("boom"))
    with patch.object(enrichment_mod, "get_ai_processor", return_value=fake_processor):
        assert await enrich_detailed_findings(findings) is False


async def test_enrich_no_findings_skips_processor():
    with patch.object(enrichment_mod, "get_ai_processor") as m:
        assert await enrich_detailed_findings([]) is False
    m.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_enrichment.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.ai.enrichment'`

- [ ] **Step 3: Write `backend/services/ai/enrichment.py`**

```python
"""Severity-stratified top-N remediation enrichment for scan findings.

Token budgeting: critical/high findings are always selected first, then
medium, low, info — capped at settings.ai_enrich_top_n (default 10).
Failures never propagate: enrichment is best-effort enrichment only.
"""
import logging
from typing import Any, Dict, List, Optional

from config import settings
from services.ai.ai_processor import get_ai_processor

logger = logging.getLogger(__name__)

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def select_findings_for_enrichment(
    findings: List[Dict[str, Any]],
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Pick the highest-value findings to enrich (stable order within severity)."""
    if top_n is None:
        top_n = settings.ai_enrich_top_n
    if top_n <= 0 or not findings:
        return []
    ranked = sorted(
        findings,
        key=lambda f: _SEVERITY_RANK.get(str(f.get("severity", "")).lower(), 5),
    )
    return ranked[:top_n]


async def enrich_detailed_findings(
    findings: List[Dict[str, Any]],
    *,
    top_n: Optional[int] = None,
    batch_size: int = 5,
) -> bool:
    """Enrich the selected subset in place. Returns True if enrichment ran."""
    selected = select_findings_for_enrichment(findings, top_n)
    if not selected:
        return False
    try:
        processor = get_ai_processor()
        await processor.enrich_findings_with_remediation(selected, batch_size=batch_size)
        return True
    except Exception as e:
        logger.warning("AI remediation enrichment skipped: %s", e)
        return False
```

- [ ] **Step 4: Wire into `backend/routes/webhook/scan_operations.py`**

1. Add import next to the other `services.*` imports (top of file):

```python
from services.ai.enrichment import enrich_detailed_findings
```

2. After the CVE-correlation `except` block (`logger.warning(f"CVE correlation failed ...")`) and **before** `final_update = {`, insert:

```python
        enrichment_applied = False
        if detailed_findings:
            enrichment_applied = await enrich_detailed_findings(detailed_findings)
            if enrichment_applied:
                logger.info(f"AI remediation enrichment applied for scan {scan_id}")
```

(`enrich_detailed_findings` never raises; enrichment mutates the selected dicts in place.)

3. Inside `final_update` construction, after the existing `if cve_enrichments:` block, add:

```python
        if enrichment_applied:
            final_update["metadata.findings"] = detailed_findings
```

The 85%-progress update persists `metadata.findings` unenriched; this re-persists only when enrichment actually ran.

- [ ] **Step 5: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_enrichment.py -v`
Expected: 7 passed.

- [ ] **Step 6: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green.

---

### Task 10: Background post-scan AI + decouple AI from the scan request

**Files:**
- Create: `backend/services/ai/post_scan.py`
- Modify: `backend/routes/webhook/scan_operations.py` (delete inline AI block, enqueue background task)
- Test: `backend/tests/test_post_scan.py` (create)

**Interfaces:**
- Consumes: `VulnerabilityAIProcessor.analyze_scan_results` (Task 5), `settings.ai_post_scan_concurrency` (Task 1, default 2), beanie chained `await ScanReport.find_one(cond).update({...})` pattern used throughout `scan_operations.py`
- Produces (spec: "AI enqueued after scan 100%, concurrency 1-2 per provider"):
  - `post_scan.schedule_post_scan_ai(scan_id: str) -> None` — fire-and-forget (`asyncio.create_task`, strong ref kept until done)
  - `post_scan.run_post_scan_ai(scan_id: str) -> None` — semaphore-bounded; writes `ai_analysis` + `metadata.ai_status` = `running` → `complete`/`failed`
  - `post_scan.reset_post_scan_state() -> None` — test hook (clears semaphore + task refs)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_post_scan.py`:

```python
"""Background post-scan AI analysis."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import services.ai.post_scan as post_scan_mod
from services.ai.post_scan import (
    reset_post_scan_state,
    run_post_scan_ai,
    schedule_post_scan_ai,
)


class FakeQuery:
    """Mimics beanie: await query gives the record; query.update({...}) chains."""

    def __init__(self, record=None):
        self.record = record
        self.updates = []

    def __await__(self):
        async def _get():
            return self.record
        return _get().__await__()

    def update(self, doc):
        async def _do():
            self.updates.append(doc)
            return 1
        return _do()


def _report():
    return SimpleNamespace(
        scan_id="scan-001",
        project_name="demo",
        scan_results=[MagicMock()],
        git_metadata=None,
    )


def _fake_analysis():
    from models.report import AIAnalysis
    from datetime import datetime, timezone

    return AIAnalysis(
        model_used="gemini/gemini-2.5-flash",
        generated_at=datetime.now(timezone.utc),
        executive_summary="s", risk_assessment="r",
        risk_score=40, risk_level="CRITICAL", security_score=80,
        priority_findings=[], recommendations=[],
        secure_code_examples={}, compliance_impact={},
        estimated_fix_time="8 hours", attack_vectors=[],
        threat_categories={}, remediation_roadmap=[],
    )


async def test_success_writes_analysis_and_status_complete():
    reset_post_scan_state()
    query = FakeQuery(record=_report())
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(return_value=_fake_analysis())

    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")

    fake_processor.analyze_scan_results.assert_awaited_once()
    # ai_analysis write + two status writes (running, complete)
    assert len(query.updates) == 3
    assert "ai_analysis" in query.updates[1]["$set"]
    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", None, "complete"]


async def test_processor_failure_sets_status_failed():
    reset_post_scan_state()
    query = FakeQuery(record=_report())
    fake_processor = MagicMock()
    fake_processor.analyze_scan_results = AsyncMock(side_effect=RuntimeError("provider down"))

    with (
        patch.object(post_scan_mod.ScanReport, "find_one", return_value=query),
        patch.object(post_scan_mod, "get_ai_processor", return_value=fake_processor),
    ):
        await run_post_scan_ai("scan-001")

    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", "failed"]
    assert "provider down" in query.updates[-1]["$set"]["metadata.ai_error"]


async def test_missing_report_sets_status_failed():
    reset_post_scan_state()
    query = FakeQuery(record=None)
    with patch.object(post_scan_mod.ScanReport, "find_one", return_value=query):
        await run_post_scan_ai("scan-001")
    statuses = [u["$set"].get("metadata.ai_status") for u in query.updates]
    assert statuses == ["running", "failed"]


async def test_schedule_creates_task_and_cleans_up():
    reset_post_scan_state()
    mock_run = AsyncMock()
    with patch.object(post_scan_mod, "run_post_scan_ai", mock_run):
        schedule_post_scan_ai("scan-001")
        await asyncio.sleep(0.05)
    mock_run.assert_awaited_once_with("scan-001")
    assert len(post_scan_mod._tasks) == 0


async def test_reset_clears_semaphore():
    reset_post_scan_state()
    first = post_scan_mod._get_semaphore()
    reset_post_scan_state()
    assert post_scan_mod._semaphore is None
    assert post_scan_mod._get_semaphore() is not first  # fresh instance
```

Note: `patch.object(post_scan_mod, "run_post_scan_ai", mock_run)` works because `schedule_post_scan_ai` looks up the module global at call time.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_post_scan.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.ai.post_scan'`

- [ ] **Step 3: Write `backend/services/ai/post_scan.py`**

```python
"""Background post-scan AI analysis.

Enqueued after the scan hits 100% so AI latency never blocks scan
completion (spec: "AI blocks scan at progress 90" -> "AI enqueued after
scan 100%, concurrency 1-2 per provider").
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from config import settings
from models.report import ScanReport
from services.ai.ai_processor import get_ai_processor

logger = logging.getLogger(__name__)

_semaphore: Optional[asyncio.Semaphore] = None
_tasks: Set[asyncio.Task] = set()


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(max(1, settings.ai_post_scan_concurrency))
    return _semaphore


async def _set_ai_status(scan_id: str, status: str, error: Optional[str] = None) -> None:
    update: Dict[str, object] = {
        "metadata.ai_status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if error:
        update["metadata.ai_error"] = error[:200]
    try:
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({"$set": update})
    except Exception as e:
        logger.warning("Failed to set ai_status=%s for %s: %s", status, scan_id, e)


async def run_post_scan_ai(scan_id: str) -> None:
    """Analyze scan results in the background; status: running -> complete/failed."""
    async with _get_semaphore():
        await _set_ai_status(scan_id, "running")
        try:
            report = await ScanReport.find_one(ScanReport.scan_id == scan_id)
            if report is None or not report.scan_results:
                logger.warning("Post-scan AI skipped: no report/results for %s", scan_id)
                await _set_ai_status(scan_id, "failed", "report unavailable")
                return

            processor = get_ai_processor()
            project_context = {
                "project_name": report.project_name,
                "repository_url": str(report.git_metadata.repository_url)
                if report.git_metadata else "",
                "branch": report.git_metadata.branch if report.git_metadata else "main",
            }
            ai_analysis = await processor.analyze_scan_results(
                report.scan_results, project_context
            )
            await ScanReport.find_one(ScanReport.scan_id == scan_id).update(
                {
                    "$set": {
                        "ai_analysis": ai_analysis.model_dump(),
                        "updated_at": datetime.now(timezone.utc),
                    }
                }
            )
            await _set_ai_status(scan_id, "complete")
            logger.info(
                "Post-scan AI analysis completed for scan %s (%s)",
                scan_id,
                ai_analysis.model_used,
            )
        except Exception as e:
            logger.error("Post-scan AI analysis failed for scan %s: %s", scan_id, e)
            await _set_ai_status(scan_id, "failed", str(e))


def schedule_post_scan_ai(scan_id: str) -> None:
    """Fire-and-forget enqueue; safe to call from request handlers."""
    task = asyncio.create_task(run_post_scan_ai(scan_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


def reset_post_scan_state() -> None:
    """Test hook: forget the semaphore and pending task refs."""
    global _semaphore
    _semaphore = None
    _tasks.clear()
```

- [ ] **Step 4: Run the new tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_post_scan.py -v`
Expected: 5 passed.

- [ ] **Step 5: Decouple AI from `backend/routes/webhook/scan_operations.py`**

1. Add import next to the Task 9 import:

```python
from services.ai.post_scan import schedule_post_scan_ai
```

2. **Delete the entire inline AI block**: from `ai_analysis_result = None` through the matching `except Exception as ai_error:` block (ends at `logger.exception("Full AI analysis error:")`). That removes the progress-90 "AI analyzing..." update and the whole `get_ai_processor()` fan-out — the compliance block below stays untouched.

3. In `final_update` construction, delete the two lines:

```python
        if ai_analysis_result:
            final_update["ai_analysis"] = ai_analysis_result.model_dump()
```

and add to the same dict literal (keeping the Task 9 `metadata.findings` line):

```python
            "metadata.ai_status": "queued",
```

4. Immediately after:

```python
        await ScanReport.find_one(ScanReport.scan_id == scan_id).update({"$set": final_update})
```

insert:

```python
        schedule_post_scan_ai(scan_id)
```

- [ ] **Step 6: Verify the removal left no stale references**

Run (from `E:\Projects\ONYX`):

```powershell
Get-ChildItem backend\routes\webhook\scan_operations.py | Select-String -Pattern "ai_analysis_result|AI analyzing|get_ai_processor"
```
Expected: no output.

- [ ] **Step 7: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green — `test_scan_progress.py` uses `__new__` (never constructs the real workflow) and does not assert the progress-90 AI update; `test_scan_webhook*` tests do not assert inline AI fields (Task 12 re-verifies with a grep of `ai_analysis` assertions in tests).

---

### Task 11: Deterministic eval harness — 24 golden cases

**Files:**
- Create: `backend/evals/__init__.py`, `backend/evals/conftest.py`, `backend/evals/cases.py`, `backend/evals/test_eval_golden.py`
- Modify: `backend/pytest.ini` (add `eval` marker)

**Interfaces:**
- Consumes: `VulnerabilityAIProcessor` + `FakeGateway` pattern (Task 5), prompt builders + `PROMPT_VERSION` (Task 2)
- Produces:
  - `evals.cases.CASES` — 24 parametrized cases; each: `{"name", "counts": {"critical","high","medium","low","info"}, "expected": {...}}`
  - Run command: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval` (28 tests) — **not** collected by the default `pytest tests/` run (`testpaths = tests`)
- **All expected values below were computed with the exact Task 5 formulas and verified against Python's float-format semantics** (e.g. `14/8 → "1.8 days"`, `15/8 → "1.9 days"`).

- [ ] **Step 1: Write the eval files**

Create `backend/evals/__init__.py` (empty) and `backend/evals/conftest.py`:

```python
"""Make the backend package importable when running `pytest evals/`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
```

Create `backend/evals/cases.py`:

```python
"""Golden eval cases: hand-verified expected deterministic AI outputs.

Expected values computed with the exact formulas in
services.ai.ai_processor (risk/security scores, fix-time formatting,
roadmap phases, threat-categorization keyword rules).
Finding titles are chosen per severity so threat categories are
deterministic; descriptions are keyword-neutral on purpose.
"""
from typing import Any, Dict, List

SEVERITY_TITLES = {
    "critical": "SQL Injection in login query",          # -> Injection
    "high": "Weak password hashing algorithm used",      # -> Authentication
    "medium": "Insecure default configuration setting",  # -> Security Misconfiguration
    "low": "Unused import in helper module",             # -> Other
    "info": "Missing HTTP security header",              # -> Other
}
NEUTRAL_DESCRIPTION = "Detected by automated scanner."
SEVERITIES = ("critical", "high", "medium", "low", "info")


def _e(risk_score, risk_level, security_score, estimated_fix_time, roadmap_phases, threat_categories):
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "security_score": security_score,
        "estimated_fix_time": estimated_fix_time,
        "roadmap_phases": roadmap_phases,
        "threat_categories": threat_categories,
    }


CASES: List[Dict[str, Any]] = [
    # name, severity counts, expected deterministic outputs
    {"name": "clean", "counts": {}, "expected": _e(5, "LOW", 98, "0 hours - No issues to fix", [], {})},
    {"name": "crit-1", "counts": {"critical": 1}, "expected": _e(40, "CRITICAL", 80, "1.0 days (8 hours)", [1], {"Injection": 1})},
    {"name": "crit-3", "counts": {"critical": 3}, "expected": _e(100, "CRITICAL", 40, "3.0 days (24 hours)", [1], {"Injection": 3})},
    {"name": "high-1", "counts": {"high": 1}, "expected": _e(25, "HIGH", 88, "4 hours", [2], {"Authentication": 1})},
    {"name": "high-4", "counts": {"high": 4}, "expected": _e(100, "CRITICAL", 52, "2.0 days (16 hours)", [2], {"Authentication": 4})},
    {"name": "medium-1", "counts": {"medium": 1}, "expected": _e(10, "MEDIUM", 95, "2 hours", [3], {"Security Misconfiguration": 1})},
    {"name": "medium-6", "counts": {"medium": 6}, "expected": _e(60, "HIGH", 70, "1.5 days (12 hours)", [3], {"Security Misconfiguration": 6})},
    {"name": "medium-7", "counts": {"medium": 7}, "expected": _e(70, "CRITICAL", 65, "1.8 days (14 hours)", [3], {"Security Misconfiguration": 7})},
    {"name": "medium-10", "counts": {"medium": 10}, "expected": _e(100, "CRITICAL", 50, "2.5 days (20 hours)", [3], {"Security Misconfiguration": 10})},
    {"name": "low-5", "counts": {"low": 5}, "expected": _e(15, "LOW", 90, "5 hours", [4], {"Other": 5})},
    {"name": "low-12", "counts": {"low": 12}, "expected": _e(36, "MEDIUM", 76, "1.5 days (12 hours)", [4], {"Other": 12})},
    {"name": "info-20", "counts": {"info": 20}, "expected": _e(20, "MEDIUM", 90, "0 hours - No issues to fix", [4], {"Other": 20})},
    {"name": "crit-high", "counts": {"critical": 1, "high": 1}, "expected": _e(65, "CRITICAL", 68, "1.5 days (12 hours)", [1, 2], {"Injection": 1, "Authentication": 1})},
    {"name": "crit-high-med-low-info", "counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1}, "expected": _e(79, "CRITICAL", 60, "1.9 days (15 hours)", [1, 2, 3, 4], {"Injection": 1, "Authentication": 1, "Security Misconfiguration": 1, "Other": 2})},
    {"name": "mixed-4", "counts": {"critical": 2, "high": 1, "medium": 1}, "expected": _e(100, "CRITICAL", 43, "2.8 days (22 hours)", [1, 2, 3], {"Injection": 2, "Authentication": 1, "Security Misconfiguration": 1})},
    {"name": "low-flood-100", "counts": {"low": 100}, "expected": _e(100, "CRITICAL", 0, "2.5 weeks (100 hours)", [4], {"Other": 100})},
    {"name": "info-flood-60", "counts": {"info": 60}, "expected": _e(60, "HIGH", 70, "0 hours - No issues to fix", [4], {"Other": 60})},
    {"name": "crit-2-high-1", "counts": {"critical": 2, "high": 1}, "expected": _e(100, "CRITICAL", 48, "2.5 days (20 hours)", [1, 2], {"Injection": 2, "Authentication": 1})},
    {"name": "high-2-medium-3", "counts": {"high": 2, "medium": 3}, "expected": _e(80, "CRITICAL", 61, "1.8 days (14 hours)", [2, 3], {"Authentication": 2, "Security Misconfiguration": 3})},
    {"name": "medium-2-low-4-info-2", "counts": {"medium": 2, "low": 4, "info": 2}, "expected": _e(34, "MEDIUM", 81, "1.0 days (8 hours)", [3, 4], {"Security Misconfiguration": 2, "Other": 6})},
    {"name": "low-8-info-5", "counts": {"low": 8, "info": 5}, "expected": _e(29, "MEDIUM", 81, "1.0 days (8 hours)", [4], {"Other": 13})},
    {"name": "crit-1-low-1", "counts": {"critical": 1, "low": 1}, "expected": _e(43, "CRITICAL", 78, "1.1 days (9 hours)", [1, 4], {"Injection": 1, "Other": 1})},
    {"name": "mixed-7", "counts": {"critical": 1, "medium": 1, "info": 1}, "expected": _e(51, "CRITICAL", 74, "1.2 days (10 hours)", [1, 3, 4], {"Injection": 1, "Security Misconfiguration": 1, "Other": 1})},
    {"name": "high-1-low-1", "counts": {"high": 1, "low": 1}, "expected": _e(28, "HIGH", 86, "5 hours", [2, 4], {"Authentication": 1, "Other": 1})},
]
```

Create `backend/evals/test_eval_golden.py`:

```python
"""Golden eval: deterministic AI outputs for 24 hand-computed cases.

Run: .venv\\Scripts\\python.exe -m pytest evals/ -v -m eval
No network: every case drives the unified processor with FakeGateway.
"""
import json

import pytest

from evals.cases import CASES, NEUTRAL_DESCRIPTION, SEVERITIES, SEVERITY_TITLES
from models.base import ScannerType, ScanStatus, SeverityLevel
from models.report import ScanResult, VulnerabilityFinding
from services.ai.gateway import GatewayError, GatewayResult
from services.ai.prompts import (
    PROMPT_VERSION,
    build_analysis_prompt,
    build_remediation_prompt,
)
from services.ai.schemas import AnalysisNarrative

NARRATIVE = {
    "executive_summary": "Golden eval summary.",
    "risk_assessment": "Golden eval assessment.",
    "priority_findings": ["SQL Injection in login query"],
    "recommendations": ["Apply parameterized queries"],
    "secure_code_examples": {"python": "cursor.execute('SELECT 1 WHERE id = ?', (id,))"},
    "compliance_impact": {"overall_impact": "Negative"},
    "attack_vectors": ["Automated scanners"],
}


class FakeGateway:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    async def complete(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return GatewayResult(
            text=self.text, provider="fake", model="golden",
            usage={}, latency_ms=1,
        )


def _finding(sev: str, i: int) -> VulnerabilityFinding:
    return VulnerabilityFinding(
        id=f"{sev}-{i}",
        scanner=ScannerType.BANDIT,
        rule_id=f"rule-{sev}",
        title=SEVERITY_TITLES[sev],
        description=NEUTRAL_DESCRIPTION,
        severity=SeverityLevel(sev),
        file_path=f"src/{sev}/file_{i}.py",
    )


def _scan_result(counts: dict) -> ScanResult:
    findings = [
        _finding(sev, i)
        for sev in SEVERITIES
        for i in range(counts.get(sev, 0))
    ]
    return ScanResult(
        scanner=ScannerType.BANDIT,
        status=ScanStatus.COMPLETED,
        findings=findings,
        duration_seconds=1.0,
    )


@pytest.mark.eval
@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
async def test_golden_case(case):
    from services.ai.ai_processor import VulnerabilityAIProcessor

    gw = FakeGateway(text=json.dumps(NARRATIVE))
    proc = VulnerabilityAIProcessor(gateway=gw)
    scan_results = [_scan_result(case["counts"])] if case["counts"] else []

    analysis = await proc.analyze_scan_results(scan_results)
    exp = case["expected"]

    assert analysis.risk_score == exp["risk_score"]
    assert analysis.risk_level == exp["risk_level"]
    assert analysis.security_score == exp["security_score"]
    assert analysis.estimated_fix_time == exp["estimated_fix_time"]
    assert [p["phase"] for p in analysis.remediation_roadmap] == exp["roadmap_phases"]
    assert analysis.threat_categories == exp["threat_categories"]

    if not case["counts"]:
        assert analysis.model_used == "none/clean-scan"
        assert "No security vulnerabilities were detected" in analysis.executive_summary
        assert gw.calls == []
    else:
        assert analysis.model_used == "fake/golden"
        assert analysis.executive_summary == "Golden eval summary."
        assert analysis.priority_findings == ["SQL Injection in login query"]
        assert analysis.recommendations == ["Apply parameterized queries"]
        assert analysis.raw_response == json.dumps(NARRATIVE)
        assert len(gw.calls) == 1
        assert gw.calls[0]["purpose"] == "analysis"
        assert gw.calls[0]["json_schema"] is AnalysisNarrative
        assert gw.calls[0]["use_cache"] is False


@pytest.mark.eval
async def test_gateway_error_degrades_to_deterministic_analysis():
    from services.ai.ai_processor import VulnerabilityAIProcessor

    gw = FakeGateway(error=GatewayError("All AI providers failed: gemini: 401"))
    proc = VulnerabilityAIProcessor(gateway=gw)
    analysis = await proc.analyze_scan_results([_scan_result({"critical": 1})])

    assert analysis.model_used == "unavailable"
    assert analysis.risk_score == 40
    assert analysis.risk_level == "CRITICAL"
    assert analysis.security_score == 80
    assert analysis.executive_summary
    assert "Automated scan identified" in analysis.executive_summary
    assert analysis.raw_response is None


@pytest.mark.eval
def test_analysis_prompt_shape():
    prompt = build_analysis_prompt(
        {
            "total_findings": 1,
            "findings": [{"title": "SQL Injection in login query", "description": "SQLi", "severity": "critical"}],
            "severity_counts": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
            "scanner_summary": {"bandit": {"status": "completed", "findings_count": 1, "duration": 1.0}},
        },
        {"project_name": "demo"},
    )
    assert f"Prompt version: {PROMPT_VERSION}" in prompt
    assert "<scan_data>" in prompt and "</scan_data>" in prompt
    assert '"SQL Injection in login query"' in prompt
    assert '"executive_summary"' in prompt  # schema embedded
    assert "demo" in prompt


@pytest.mark.eval
def test_analysis_prompt_truncates_descriptions_and_caps_findings():
    long_desc = "D" * 600
    findings = [
        {"title": f"f{i}", "description": long_desc, "severity": "high"}
        for i in range(55)
    ]
    prompt = build_analysis_prompt(
        {
            "total_findings": 55,
            "findings": findings,
            "severity_counts": {"critical": 0, "high": 55, "medium": 0, "low": 0, "info": 0},
            "scanner_summary": {},
        }
    )
    assert '"f49"' in prompt          # last of the capped 50
    assert '"f50"' not in prompt      # findings[:50] cap
    assert "D" * 500 in prompt        # description[:500]
    assert "D" * 501 not in prompt


@pytest.mark.eval
def test_remediation_prompt_includes_identifiers_and_schema():
    prompt = build_remediation_prompt(
        {
            "title": "SQL Injection",
            "severity": "critical",
            "description": "SQLi in query",
            "file_path": "app/login.py",
            "code_snippet": "cursor.execute(f\"SELECT {q}\")",
            "cwe_id": "CWE-89",
            "cve_id": "CVE-2024-1234",
        }
    )
    assert f"Prompt version: {PROMPT_VERSION}" in prompt
    assert "CWE-89" in prompt
    assert "CVE-2024-1234" in prompt
    assert "app/login.py" in prompt
    assert "cursor.execute" in prompt
    assert '"remediation"' in prompt and '"fix_effort"' in prompt
```

- [ ] **Step 2: Register the marker in `backend/pytest.ini`**

Add under the existing `markers =` block:

```ini
    eval: mark golden eval case
```

- [ ] **Step 3: Run the evals**

Run: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval`
Expected: 28 passed (24 golden + 1 gateway-error + 3 prompt gates).

- [ ] **Step 4: Confirm the default suite ignores evals**

Run: `.venv\Scripts\python.exe -m pytest tests/ -q --collect-only | findstr /i eval`
Expected: no output.

---

### Task 12: Full verification

**Files:** none (verification only; fix any failures found in prior tasks)

- [ ] **Step 1: Full unit suite**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v`
Expected: all green (existing suite + ~90 new tests across Tasks 1-10).

- [ ] **Step 2: Eval harness**

Run: `.venv\Scripts\python.exe -m pytest evals/ -v -m eval`
Expected: 28 passed.

- [ ] **Step 3: Stale-reference greps** (from `E:\Projects\ONYX`)

```powershell
Get-ChildItem -Recurse -Path backend -Include *.py | Select-String -Pattern "gemini_ai_processor|ollama_ai_processor" | Where-Object { $_.Path -notlike "*__pycache__*" }
Get-ChildItem backend\services\triage\triage_service.py | Select-String -Pattern "httpx"
Get-ChildItem backend\routes\ai_chat.py | Select-String -Pattern "genai|AsyncOpenAI"
Get-ChildItem backend\routes\webhook\scan_operations.py | Select-String -Pattern "ai_analysis_result|AI analyzing|get_ai_processor"
```
Expected: no output from any of the four.

- [ ] **Step 4: Import smoke test**

Run (from `E:\Projects\ONYX\backend`):

```powershell
.venv\Scripts\python.exe -c "import services.ai, services.ai.factory, services.ai.enrichment, services.ai.post_scan, routes.ai_chat, services.triage.triage_service, routes.webhook.scan_operations; print('imports ok')"
```
Expected: `imports ok`.

- [ ] **Step 5: Dependency freeze check**

Run (from `E:\Projects\ONYX`):
```powershell
git diff --stat backend/requirements.txt
```
Expected: empty output.

- [ ] **Step 6: Report uncommitted changes — do NOT commit**

Run (from `E:\Projects\ONYX`): `git status --porcelain`
Expected: a list of the created/modified/deleted files from this plan. Leave all changes unstaged/uncommitted — committing requires explicit user authorization (Global Constraint). Surface this list to the user in the completion report.

