from __future__ import annotations
from fastapi import APIRouter, Header
from app.core.ai_provider import answer_question, provider_status
from app.schemas.requests import AskRequest

router = APIRouter(prefix='/ai', tags=['ai'])

def _provider_keys(
    x_sc_provider_key: str | None = None,
    x_sc_openai_key: str | None = None,
    x_sc_gemini_key: str | None = None,
    x_sc_deepseek_key: str | None = None,
) -> dict[str, str]:
    return {
        'provider': x_sc_provider_key or '',
        'openai': x_sc_openai_key or '',
        'gemini': x_sc_gemini_key or '',
        'deepseek': x_sc_deepseek_key or '',
    }

@router.get('/status')
def status(
    x_sc_ai_provider: str | None = Header(default=None),
    x_sc_provider_key: str | None = Header(default=None),
    x_sc_openai_key: str | None = Header(default=None),
    x_sc_gemini_key: str | None = Header(default=None),
    x_sc_deepseek_key: str | None = Header(default=None),
):
    return {"ok": True, **provider_status(x_sc_ai_provider, _provider_keys(x_sc_provider_key, x_sc_openai_key, x_sc_gemini_key, x_sc_deepseek_key))}

@router.post('/ask')
def ask(
    req: AskRequest,
    x_sc_ai_provider: str | None = Header(default=None),
    x_sc_provider_key: str | None = Header(default=None),
    x_sc_openai_key: str | None = Header(default=None),
    x_sc_gemini_key: str | None = Header(default=None),
    x_sc_deepseek_key: str | None = Header(default=None),
):
    return answer_question(
        req.question,
        req.topic,
        req.mode,
        req.scope_gate_enabled,
        provider_keys=_provider_keys(x_sc_provider_key, x_sc_openai_key, x_sc_gemini_key, x_sc_deepseek_key),
        provider_override=x_sc_ai_provider,
    )
