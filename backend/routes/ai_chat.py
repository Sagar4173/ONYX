"""
AI Security Chat Assistant - Interactive vulnerability Q&A
Allows users to ask natural language questions about their scan results
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from config import settings
from routes.dependencies import get_current_user
from routes.reports.report_dependencies import get_accessible_scan_report
from utils.error_handling import get_safe_error_detail
from utils.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Security Chat"])

ALLOWED_CHAT_ROLES = ("user", "assistant")


class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ALLOWED_CHAT_ROLES:
            raise ValueError("role must be 'user' or 'assistant'")
        return v


class ChatRequest(BaseModel):
    scan_id: str
    message: str
    conversation_history: Optional[List[ChatMessage]] = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank")
        return v


class ChatResponse(BaseModel):
    reply: str
    model_used: str


async def _build_scan_context(scan_id: str, user) -> Optional[Dict[str, Any]]:
    report = await get_accessible_scan_report(scan_id, str(user.id))
    if not report:
        return None

    findings_summary = []
    if report.scan_results:
        for result in report.scan_results:
            scanner_name = getattr(result, "scanner", "unknown")
            findings = getattr(result, "findings", []) or []
            for f in findings:
                findings_summary.append({
                    "scanner": scanner_name,
                    "severity": getattr(f, "severity", "unknown"),
                    "title": getattr(f, "title", ""),
                    "description": getattr(f, "description", ""),
                    "file_path": getattr(f, "file_path", ""),
                    "remediation": getattr(f, "remediation", ""),
                    "cwe_id": getattr(f, "cwe_id", ""),
                })

    ai_analysis = None
    if report.ai_analysis:
        ai_analysis = {
            "executive_summary": report.ai_analysis.executive_summary,
            "risk_assessment": report.ai_analysis.risk_assessment,
            "risk_score": report.ai_analysis.risk_score,
            "security_score": report.ai_analysis.security_score,
            "recommendations": report.ai_analysis.recommendations,
            "estimated_fix_time": report.ai_analysis.estimated_fix_time,
        }

    return {
        "project_name": report.project_name,
        "status": report.status,
        "total_findings": report.total_findings or 0,
        "findings_by_severity": report.findings_by_severity or {},
        "findings": findings_summary[:50],
        "ai_analysis": ai_analysis,
        "created_at": str(report.created_at) if report.created_at else None,
    }


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

    messages = [{"role": "system", "content": full_system_prompt}]

    if conversation_history:
        for msg in conversation_history:
            role = msg["role"] if msg["role"] in ALLOWED_CHAT_ROLES else "user"
            messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    provider = settings.ai_provider.lower() if settings.ai_provider else "auto"

    if provider in ("auto", "ollama"):
        try:
            from openai import AsyncOpenAI as OllamaClient

            client = OllamaClient(
                base_url=settings.ai_local_base_url,
                api_key="ollama",
                max_retries=0,
            )
            response = await client.chat.completions.create(
                model=settings.ai_local_model,
                messages=messages,
                max_tokens=1500,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Ollama chat failed ({e}), trying fallback")
            if provider == "ollama":
                raise HTTPException(
                    status_code=502,
                    detail=f"Ollama AI chat error: {get_safe_error_detail(e)}",
                )

    if provider in ("auto", "gemini") and settings.gemini_api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.gemini_api_key)
            chat = client.aio.chats.create(
                model=settings.gemini_model or "gemini-1.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=full_system_prompt[:32000],
                ),
            )
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        await chat.send_message(msg["content"])
            response = await chat.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            if provider == "gemini" and not settings.openai_api_key:
                raise

    if settings.openai_api_key:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model or "gpt-4",
                messages=messages,
                max_tokens=1500,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"AI chat service error: {get_safe_error_detail(e)}",
            )

    raise HTTPException(
        status_code=503,
        detail="No AI provider available. Configure Ollama, OPENAI_API_KEY, or GEMINI_API_KEY.",
    )


def _get_active_model() -> str:
    provider = settings.ai_provider.lower() if settings.ai_provider else "auto"
    if provider in ("auto", "ollama"):
        return f"ollama/{settings.ai_local_model}"
    if provider == "gemini":
        return settings.gemini_model or "gemini-1.5-flash"
    return settings.openai_model or "gpt-4"


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def ai_chat(
    request: Request,
    payload: ChatRequest,
    user=Depends(get_current_user),
):
    scan_context = await _build_scan_context(payload.scan_id, user)
    if not scan_context:
        raise HTTPException(
            status_code=404,
            detail="Scan report not found or access denied",
        )

    hist = None
    if payload.conversation_history:
        hist = [{"role": m.role, "content": m.content} for m in payload.conversation_history]

    try:
        reply = await _call_ai_chat(
            message=payload.message,
            scan_context=scan_context,
            conversation_history=hist,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"AI chat service error: {get_safe_error_detail(e)}",
        )

    return ChatResponse(reply=reply, model_used=_get_active_model())
