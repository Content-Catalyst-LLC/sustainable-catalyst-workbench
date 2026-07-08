from __future__ import annotations
from fastapi import APIRouter, Header
from app.core.ai_provider import answer_question, provider_status
from app.schemas.requests import AskRequest

router = APIRouter(prefix='/ai', tags=['ai'])

@router.get('/status')
def status():
    return {"ok": True, **provider_status()}

@router.post('/ask')
def ask(req: AskRequest, x_sc_openai_key: str | None = Header(default=None)):
    return answer_question(req.question, req.topic, req.mode, req.scope_gate_enabled, provider_key=x_sc_openai_key)
