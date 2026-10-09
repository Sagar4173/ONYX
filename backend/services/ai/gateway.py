"""LLM gateway: one entry point for all AI provider calls.

Provider order comes from Settings (auto -> configured chain, or a single
explicit provider). Every call is rate-limited, quota-checked, circuit-broken,
cached (opt-in) and traced. Failures fail over to the next provider.

NOTE: rate-window and circuit-breaker state is process-local. With
WORKERS > 1 the effective per-minute budget multiplies across workers;
AI governance (RPM) assumes a single-worker deployment. The daily quota
ledger is Mongo-backed and therefore shared.
"""
import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional, TypeVar

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

_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}|AIza[A-Za-z0-9_\-]{10,}|Bearer\s+[A-Za-z0-9._\-]+|ghp_[A-Za-z0-9]{10,})"
)


def _scrub(text: Any, limit: int = 300) -> str:
    """Redact credential-looking substrings and bound the length of provider errors."""
    return _SECRET_RE.sub("[REDACTED]", str(text))[:limit]


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


@dataclass
class StreamEvent:
    delta: str = ""
    done: bool = False
    provider: str = ""
    model: str = ""
    usage: dict = field(default_factory=dict)
    error: Optional[str] = None


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

    timeout = float(settings.ai_local_timeout) if spec.name == "ollama" else 60.0
    client = AsyncOpenAI(api_key=spec.api_key, base_url=spec.base_url, max_retries=0, timeout=timeout)
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


async def _stream_openai_compat(spec, messages, max_tokens, temperature):
    """OpenAI-compatible streaming adapter (Groq, OpenRouter, OpenAI, Ollama)."""
    from openai import AsyncOpenAI

    timeout = float(settings.ai_local_timeout) if spec.name == "ollama" else 60.0
    client = AsyncOpenAI(api_key=spec.api_key, base_url=spec.base_url, max_retries=0, timeout=timeout)
    stream = await client.chat.completions.create(
        model=spec.model, messages=messages, max_tokens=max_tokens,
        temperature=temperature, stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_gemini(spec, messages, max_tokens, temperature):
    """Gemini streaming adapter via google-genai (already a dependency)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=spec.api_key)
    system = next((m.get("content", "") for m in messages if m.get("role") == "system"), None)
    parts = [
        f"{m.get('role', 'user')}: {m.get('content', '')}"
        for m in messages
        if m.get("role") != "system"
    ]
    stream = await client.aio.models.generate_content_stream(
        model=spec.model,
        contents="\n".join(parts),
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    async for resp in stream:
        if resp.text:
            yield resp.text


_DEFAULT_STREAM_ADAPTERS = {
    "gemini": _stream_gemini,
    "groq": _stream_openai_compat,
    "openrouter": _stream_openai_compat,
    "openai": _stream_openai_compat,
    "ollama": _stream_openai_compat,
}


class LLMGateway:
    def __init__(self, adapters=None, stream_adapters=None, quota=None, cache=None, tracer=None):
        self._adapters = dict(_DEFAULT_ADAPTERS) if adapters is None else dict(adapters)
        self._stream_adapters = dict(_DEFAULT_STREAM_ADAPTERS) if stream_adapters is None else dict(stream_adapters)
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

    def cache_key(
        self,
        *,
        messages: list,
        purpose: str,
        temperature: float,
        schema_name: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        models = "|".join(
            f"{name}={model}"
            for name, model in (
                ("gemini", settings.gemini_model),
                ("groq", settings.groq_model),
                ("openrouter", settings.openrouter_model),
                ("openai", settings.openai_model),
                ("ollama", settings.ai_local_model),
            )
        )
        return ResponseCache.make_key(
            purpose=purpose,
            messages=messages,
            temperature=temperature,
            schema_name=schema_name,
            chain=settings.ai_provider_chain,
            models=models,
            max_tokens=max_tokens or settings.openai_max_tokens,
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
        cache_key = self.cache_key(
            messages=messages,
            purpose=purpose,
            temperature=temperature,
            schema_name=schema_name,
            max_tokens=max_tokens,
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
                errors.append(f"{spec.name}: {_scrub(e)}")
                await self._tracer.record(
                    purpose=purpose, provider=spec.name, model=spec.model,
                    ok=False, latency_ms=latency, error=_scrub(e, 500),
                )
                logger.warning("AI provider %s failed: %s", spec.name, _scrub(e))
                continue
            self._note_success(spec.name)
            latency = int((time.perf_counter() - start) * 1000)
            await self._tracer.record(
                purpose=purpose, provider=spec.name, model=spec.model,
                ok=True, latency_ms=latency, usage=usage,
            )
            if use_cache and json_schema is None:
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

    async def stream_messages(
        self,
        *,
        messages: list,
        purpose: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a chat completion with the same lane protections as complete_messages.

        Yields StreamEvent deltas; exactly one terminal event (done=... or error=...).
        Raises GatewayError only if no lane produced a first delta.
        """
        max_tokens = max_tokens or settings.openai_max_tokens
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
            adapter = self._stream_adapters.get(spec.name)
            if adapter is None:
                errors.append(f"{spec.name}: no streaming adapter registered")
                continue
            start = time.perf_counter()
            started = False
            try:
                async for delta in adapter(spec, messages, max_tokens, temperature):
                    started = True
                    yield StreamEvent(delta=delta, provider=spec.name, model=spec.model)
            except Exception as e:
                latency = int((time.perf_counter() - start) * 1000)
                self._note_failure(spec.name)
                scrubbed = _scrub(e)
                await self._tracer.record(
                    purpose=purpose, provider=spec.name, model=spec.model,
                    ok=False, latency_ms=latency, error=_scrub(e, 500),
                )
                logger.warning("AI stream provider %s failed: %s", spec.name, scrubbed)
                if started:
                    yield StreamEvent(error=scrubbed, provider=spec.name, model=spec.model)
                    yield StreamEvent(done=True, provider=spec.name, model=spec.model)
                    return
                errors.append(f"{spec.name}: {scrubbed}")
                continue
            latency = int((time.perf_counter() - start) * 1000)
            self._note_success(spec.name)
            await self._tracer.record(
                purpose=purpose, provider=spec.name, model=spec.model,
                ok=True, latency_ms=latency,
            )
            yield StreamEvent(done=True, provider=spec.name, model=spec.model)
            return
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
        until = self._open_until.get(provider, 0.0)
        if until and now >= until:
            # Cooldown expired: half-open. Reset the counter so the next
            # probe gets a fresh failure budget.
            self._failures[provider] = 0
            self._open_until[provider] = 0.0
            return False
        return now < until

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
            # Cache only validated structured output, under the original
            # (attempt-0) key so identical future calls hit directly.
            cache = getattr(gateway, "_cache", None)
            if use_cache and not result.cached and cache is not None:
                key = gateway.cache_key(
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    purpose=purpose,
                    temperature=temperature,
                    schema_name=schema.__name__,
                )
                await cache.set(
                    key,
                    {
                        "text": result.text,
                        "provider": result.provider,
                        "model": result.model,
                        "usage": result.usage,
                        "latency_ms": result.latency_ms,
                    },
                )
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
