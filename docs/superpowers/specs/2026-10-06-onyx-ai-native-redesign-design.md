# ONYX AI-Native Redesign — Design Spec

**Date:** 2026-10-06
**Status:** Approved (section-by-section) by product owner
**Approach:** A then B — "The free remediation loop" first, "AI app security scanner" as Phase 5
**Budget constraint:** $0 AI spend (free-tier LLM APIs), AWS free tier / third-party deployer account

---

## 1. Product Strategy

### 1.1 Problem (for users)

1. **Too much noise, no time** — findings outstrip humans; AI triage is named "white space" in market research.
2. **Fixing is the hard part** — tools find bugs, nobody fixes them; industry data: ~6 new vulns introduced per 1 remediated.
3. **Affordable tools don't do AI** — free OSS scanners (Semgrep OSS, Trivy, Gitleaks) output raw JSON: no explanations, no fixes.
4. **AI tools aren't affordable** — Snyk/Semgrep/GitHub AI features are metered or enterprise-gated ($25–350+/mo, credit systems).
5. **Code sovereignty** — teams don't want source code shipped to a SaaS vendor.

### 1.2 Positioning (replaces vague "Security Intelligence Platform")

> **ONYX = the free, self-hosted AI security platform with a complete remediation loop:** unified multi-scanner results → AI triage & dedupe → grounded chat with citations → **verified auto-fix PRs** → compliance reports. Bring your own model (free APIs or local Ollama) — code never leaves your server, $0 forever. Plus (Phase 5): scanning for AI apps themselves (OWASP LLM/MCP Top 10).

### 1.3 How we solve it

| Pain | Mechanism |
|---|---|
| Noise | Cross-scanner dedupe (deterministic: `rule_id + normalized path + snippet hash`) + AI triage weighted by severity/EPSS |
| "Find but never fix" | Fix-agent generates patch → deterministic re-scan verifies → PR behind human approval |
| No AI in free tools | Provider gateway: Gemini/Groq free tiers + Ollama, failover built-in |
| Cost | No seats, no credits, no usage metering |
| Data sovereignty | Self-hosted; RAG retrieves guidance, never sends repo code to LLMs |

### 1.4 Why users choose us

- **vs Snyk/Semgrep/GHAS:** same AI loop, $0, no seat caps, self-hosted, BYO model.
- **vs raw OSS scanners:** they give JSON — we give answers and fixes.
- **vs young OSS clones (Hecate, HenKaiPan):** they stop at summaries — we close the loop with *verified* auto-fix.

### 1.5 Market need (current + future)

- AI-generated code floods repos with vulns (~44% of AI-code tasks introduce an OWASP Top-10 vuln; AI code has 2× security violations) → affordable scanning demand rises.
- Known-vuln exploitation = 31% of breaches → remediation speed matters.
- **Agentic AppSec** is a named 2026 category; **LLM/MCP app security** is emerging whitespace (OWASP MCP Top 10, NSA guidance).
- Verdict: **core idea stays; positioning sharpens.** Distribution via open-source GitHub presence.

### 1.6 Honest risks

- "Free + self-hosted + AI" window is open only months — young OSS clones are circling. Win on completeness (verified fix loop), UX, shipping speed.
- Free-tier price war: cannot out-spend incumbents; moat = self-hosting + BYO-model + no metering.

---

## 2. Technical Architecture (AI Foundation)

### 2.1 Core decision

**One thin LLM Gateway + one unified processor. No LangChain/LiteLLM/guardrails frameworks** — raw SDKs + Pydantic, matching the existing FastAPI stack.

```
App layer:    scan analysis · enrichment · triage · chat (SSE) · fix-agent
Prompt layer: versioned templates (single source) + token-budgeted context builder
Gateway:      adapters → failover chain → rate limiter → structured output → cache → trace
Providers:    Gemini free (primary) → Groq free → OpenRouter :free → Ollama (dev only)
Eval layer:   golden dataset + deterministic gates + LLM-as-judge (offline)
```

### 2.2 Replacements (repo-scoped)

| Today | After |
|---|---|
| 3 duplicate processors × 7-8 prompt fan-out (`ai_processor.py`, `gemini_ai_processor.py`, `ollama_ai_processor.py`) | 1 processor, 1 structured call; deterministic fields (risk_score, security_score, roadmap, fix-time) stay in code and are never re-asked → ~7× fewer calls, 15-30k → 3-5k tokens/scan |
| `triage_service.py` raw OpenAI-only httpx, silent `None` | Routed through gateway |
| `enrich_findings_with_remediation()` never called in prod | Wired into scan flow (top-N critical/high, batched) → revives auto-fix PR (`auto_fix_service.py:34` guard passes) |
| `gpt-4`, `gemini-1.5-flash`, `qwen2.5-coder:7b` defaults | `gemini-flash` free primary + Groq failover; all model IDs env-configured with startup deprecation probe |
| Chat stuffs ≤50 raw findings into system prompt | Gateway today; retrieval-based context in Phase 2 |
| `json.loads` + string-splitting parsing | Provider-native JSON schema (Gemini `response_schema`, OpenAI-compatible `json_schema`) + Pydantic + 1 validation retry + degraded text fallback |
| Gemini chat replays history turn-per-call (`ai_chat.py:168-172`) | Single message array per request, history capped to last N turns, SSE streaming |
| AI blocks scan at progress 90 (`scan_operations.py:413-454`) | AI enqueued after scan 100%, concurrency 1-2 per provider |

### 2.3 Survival features ($0 budget)

- **Failover + circuit breakers** — free catalogs churn monthly (e.g., Groq removed llama free models Aug 2026).
- **Quota ledger in MongoDB** — `$inc` upserts for RPM/RPD/TPM per provider; survives restarts; honors `Retry-After`; jittered backoff.
- **Semantic cache** — key `sha256(findings_hash + prompt_version + model)`, Mongo TTL ~30d. Re-scans/retries are free.
- **Traces** — `ai_invocations` collection (trace_id, provider, model, prompt_version, tokens, latency, cache_hit, schema_valid, error class, quota remaining) + existing Prometheus instrumentation. Optional: Langfuse Cloud Hobby (free) later; never self-hosted (ClickHouse stack won't fit 1 GB).
- **Prompt management** — single module with `PROMPT_VERSION` recorded on every AIAnalysis/trace.
- **Token budgeting** — severity-stratified top-K findings (critical/high always, sample rest), char-based estimation with hard cap, batched enrichment (5-10 findings per call).

### 2.4 New dependencies

Add: `scikit-learn` (Phase 4, already imported but missing), `sqlite-vec` (Phase 2).
Never add: LangChain, LangGraph, LiteLLM, Chroma, guardrails frameworks, CrewAI.

---

## 3. RAG Design

### 3.1 Corpus decisions

| Corpus | Decision | Why |
|---|---|---|
| CWE entries (~1,000) + OWASP/secure-coding guidance + remediation snippets per vuln-class × language | Embed (Phase 2) | Grounded chat citations + fix-agent feed |
| Past findings + human triage decisions (FP/accepted/resolved) | Optional, post-Phase 3 (pending label availability) | Similar-finding context for triage |
| Raw repo code | Never | Repo is cloned locally during scan; sovereignty USP forbids sending it out |
| Scanner raw output, chat history | Never | Mongo queries suffice |

### 3.2 Stack

- **Store:** `knowledge.db` = sqlite-vec (vectors) + FTS5 (BM25) in one SQLite file. Corpus 2k–50k chunks → brute-force KNN single-digit ms, ~10-30 MB RAM.
- **Rejected:** Chroma (HNSW ~610 MB @ 100k vectors — OOM on t3.micro), Atlas `$vectorSearch` (not on free M0), pgvector (no Postgres), hosted vector DBs (cost), dedicated rerankers (RAM/quota).
- **Embeddings:** `gemini-embedding-2` (free) primary → Ollama `nomic-embed-text` fallback → ONNX `bge-small-en-v1.5` int8 (~30 MB) offline.
- **Chunking:** section-aware, 300-600 tokens, self-describing context header prepended (`CWE-89: SQL Injection — …`).
- **Retrieval:** hybrid (vector + FTS5) → Reciprocal Rank Fusion (~30 lines) + metadata filters (`cwe_id`, severity). Optional LLM rerank top-10→3-5 only if evals show a gap.
- **Upgrade path:** LanceDB past ~500k chunks.

### 3.3 Integration points

1. **Chat** — retrieval context replaces 50-finding dump; answers carry citations that resolve to real records.
2. **Remediation enrichment** — fixes grounded in retrieved guidance.
3. **Triage annotation** — similar past findings (Phase 3.5).

### 3.4 RAG evals

- recall@5 / MRR on `rule_id → cwe_id` pairs (ground truth exists in repo data).
- Groundedness gate: every citation must resolve — deterministic, zero tokens.

---

## 4. Agentic AI + Safety

### 4.1 Philosophy

**Deterministic pipeline + exactly one bounded agent loop (fix-agent).** Scan/dedupe/triage stay plain asyncio. Dedupe stays deterministic (no embedding-dedupe).

### 4.2 Fix-agent

```
propose remediation → apply patch → VALIDATE → retry ≤2 → open PR
```

- **Framework:** **Pydantic AI** (chosen — MIT, typed tools, Pydantic v2 fit with FastAPI). Fallback: raw provider function-calling (~50-line loop) only if the dependency is rejected at review. Skip LangGraph/CrewAI/multi-agent either way.
- **Tools (least-privilege):** `read_file(path, start, end)`, `search_repo(pattern)`, `get_cwe(cwe_id)`, `get_epss(cve_id)` / `lookup_osv(...)` (reuse existing services), `propose_patch(...)`. **No shell tool. No network tools.**

### 4.3 Safety rails

1. **Never auto-merge** — branch protection (review + status checks); ONYX token scoped to `contents:write, pull_requests:write` only; branch prefix `onyx-auto-fix/`.
2. **Deterministic gates before PR** — file exists, line range valid, syntax/compile check of patched file, diff-size cap, changed-files allowlist (finding's file only), gitleaks/detect-secrets over the diff.
3. **Verification = re-scan the PR branch** — claim "verified fix" only when scanners confirm. Agents never grade their own work.
4. **Human approval default ON** — `AUTO_FIX_REQUIRES_APPROVAL=true`; dry-run mode prints diff.
5. **Loop caps** — ≤3 LLM turns, ≤1 repair retry, budgeted tokens per fix; every tool call traced.
6. **Prompt-injection boundary** — file contents, commit messages, finding text are attacker-controlled: appear only as delimited data; model output never becomes a tool argument without schema validation + allowlist checks; model cannot widen file scope (escalation requires human approval); inbound chat/finding text screened by `meta-llama/llama-prompt-guard-2-86m` (Groq free: 30 RPM / 14.4k RPD).

### 4.4 Phase 4 bonus agent

Read-only **"investigate finding"** agent (repo exploration + EPSS/OSV intel → blast-radius explanation). No write tools.

### 4.5 Chat UX

SSE streaming (chat only; batch analysis stays non-streaming).

---

## 5. Roadmap & Metrics

### 5.1 Phases

| Phase | Scope | Effort | Ships |
|---|---|---|---|
| **1. Foundation** | LLM Gateway (adapters, failover, quota ledger, cache, traces) · unify 3 processors → 1 structured call · fix triage bypass · revive auto-fix enrichment · model defaults · decouple AI from scan · eval harness (20-30 golden cases) | ~2-3 wk | Reliability + working auto-fix PRs |
| **2. RAG** | `knowledge.db` · embed CWE/OWASP/remediation · hybrid+RRF · grounded chat with citations · retrieval evals | ~2-4 wk | Cited answers, lower token cost |
| **3. Agentic** | Fix-agent with validation gates + re-scan verification · approval flag · SSE streaming · prompt-guard-2 screening | ~3-5 wk | Verified auto-fix loop (the USP) |
| **4. ML + Investigate** | Harden IsolationForest (only with accumulated labels; else deterministic FP heuristics first) · read-only investigate agent | ~1-2 wk | Smarter triage |
| **5. AI App Security** | OWASP LLM Top 10 rules + MCP manifest audit + prompt-injection checks as a new scanner type reusing the AI explanation/report pipeline | ~2-3 wk | "We scan your AI apps too" |
| **UX Track (parallel, starts Phase 1)** | **Deliverable: new "AI Surfaces UX" spec** (foundations = existing July specs + `styles/` design system, not a rewrite). Covers: fix-PR review flow (diff view + approve/dry-run + "verified by re-scan" trust badge) · triage workflow UI (accept/FP/dismiss labels feeding ML) · cited-answer chat UI (live citation chips → CWE panel) · streaming SSE response choreography · AI states nobody designed (long-analysis loading, free-tier 429/quota UX, provider-fallback notice, schema-retry) · dashboard/scoring polish · accessibility pass | spans Phases 1-4 | "Best experience" — the product surface users actually judge |

#### UX quality bar (non-negotiable)

Every AI surface must feel **signature and top-tier, never generic/static**. Concrete standards:

- **Signature moments (ONYX-identifiable):** "verified fix" badge that *animates the re-scan result* (not a static checkmark) · risk-score that recomputes visibly when triage labels are applied · citation chips that stream in live as the answer generates and open a CWE side-panel without leaving the page
- **Motion language:** the established glass/gradient identity extended to AI surfaces — streaming text reveal, staggered finding entrances, diff-highlight sweep on verified patches (all respecting `prefers-reduced-motion`)
- **Interactive, not read-only:** triage = keyboard-fast workflow (severity keys, bulk actions, undo toast), chat = inline citation navigation, fix review = side-by-side diff with one-click approve/dry-run
- **State completeness:** every AI surface ships loading (skeleton/streaming), empty, error, quota-exceeded, and degraded-provider states — designed, not defaulted
- **Reference bar:** judged against Linear, Vercel Dashboard, Cursor — if a screen looks like a plain CRUD table, it fails review
- **Verification:** visual QA against the bar per surface before phase sign-off; Storybook stories for new components

**Effort caveat:** estimates assume **2 engineers** with repo context. Solo (1 engineer) → roughly double. All model IDs and free-tier quotas in §5.3 are **unverified assumptions** — confirm in AI Studio/Groq/OpenRouter consoles before Phase 1 begins.

### 5.2 Evaluation strategy

1. **Deterministic gates (no tokens):** Pydantic schema validity, required fields non-empty, AI "risk level" matches computed `risk_score`, priority findings exist in input, no secret-looking strings in output, citations resolve.
2. **Golden dataset:** 20-30 cases at launch (from test fixtures + real scan snapshots), stratified: clean / critical-heavy / 100+-finding noisy / plain-English question / injection attempt in finding text / truncation path.
3. **LLM-as-judge:** rubric (correctness, completeness, groundedness, actionability), pass ≥0.7 with per-dimension minimums, judge = different model family than generator.
4. **Regression/CI:** `pytest -m eval` nightly (capped, cached judge responses), baseline per `(model, prompt_version)`, block merges on regression.
5. **Production sampling:** 5-10% outputs scored; alert schema-failure >2%, 429 rate, cache-hit rate, p95 latency, tokens/scan.

### 5.3 Model choices (Oct 2026 — verify quotas in consoles)

| Role | Model | Lane |
|---|---|---|
| Primary | current Gemini flash free (pin stable fallback) | AI Studio free |
| Failover | `openai/gpt-oss-120b` or `qwen3` 27B class | Groq free (30 RPM / 1K RPD / 8K TPM) |
| Tertiary | one stable `:free` variant | OpenRouter (20 RPM / 50 RPD at $0) |
| Local | current 7-8B coder via Ollama | dev machine only — won't run on 1 GB instance |
| Embeddings | `gemini-embedding-2` | AI Studio free |
| Injection classifier | `llama-prompt-guard-2-86m` | Groq free |
| Judge | different family than generator | Groq/Gemini free |
| ~~gpt-4 default~~ | removed | paid — contradicts $0 |

### 5.4 Success metrics

- **Technical:** scan AI completes within free-tier daily quota; auto-fix PR passes re-scan verification ≥90%; chat citations resolvable 100%; schema-failure <2%.
- **Product:** one-line pitch lands ("free self-hosted platform that finds AND fixes"); public GitHub README positioned as open-source GHAS/Snyk alternative.
- **Cost:** $0 AI spend; hosting on free tier only.

### 5.5 Global risks & mitigations

- **Privacy/ToS:** Gemini free-tier content may be used for model improvement → redact detected secrets before any LLM call, truncate snippets, route snippet-bearing payloads to Groq/Ollama where possible, never send full repo code. Confirm ToS before Phase 1 ships snippet-bearing calls.
- **Free-tier churn:** env-configured model IDs, mandatory failover, startup deprecation probe, local backstop.
- **1 GB RAM ceiling:** forbids Chroma, self-hosted Langfuse, local 7B models — architecture designed around it.
- **Auto-fix correctness:** syntax/test gates + diff caps + human approval + branch protection; never claim auto-fix works without end-to-end build check.
- **Distribution:** OSS GitHub presence is the growth channel; sustainability (maintainer continuity) is itself a trust signal.
- **Deployment governance (open risk):** production currently runs on a **third-party AWS account** (deployed by a collaborator). If that relationship or account lapses, the product dies. Action before launch: migrate to an account ONYX controls, or formalize ownership in writing (access, billing, DNS for `onyx.ajuna.website`).
- **Single-instance architecture:** current design assumes one self-hosted instance per user (Docker Compose). Horizontal scale, orgs, and multi-tenancy are v2+ concerns.

---

## 6. Out of Scope (explicitly skipped)

LangChain/LangGraph/LlamaIndex · multi-agent swarms · hosted vector DBs · pgvector · self-hosted Langfuse · guardrails frameworks · fine-tuning · GPU rerankers · MCP servers for internal tools · codebase-wide RAG over raw repos · "autonomous SOC" · graph-RAG · new enterprise compliance suites (existing compliance reports stay as-is until demand is proven).

## 7. Out of Scope for v1 (deferred, not rejected)

Product-infrastructure items implied by "real product" but deliberately deferred until the AI loop ships and demand is proven:

- **Multi-tenancy / SaaS platform** — v1 = single self-hosted instance per user (Docker Compose). No orgs, teams, or hosted sign-up flow.
- **Billing / paid tiers** — no Stripe, no metering UI. Free forever as the USP; revisit monetization only with proven usage.
- **Per-user rate limiting & quotas** — v1 relies on instance-level rate limiting (existing 30/min chat limit) since there is one user per instance.
- **Horizontal scaling / Kubernetes** — single-instance only.
- **Formal SLA/support commitments** — OSS-community support model.

These require the deployment-governance risk (§5.5) to be resolved first.
