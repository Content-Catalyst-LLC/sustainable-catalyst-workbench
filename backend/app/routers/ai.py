from __future__ import annotations
from fastapi import APIRouter, Header
from app.schemas.requests import AskRequest
from app.core.scope_gate import is_in_scope, redirect_message
from app.core.retrieval import retrieve
from app.core.ai_provider import answer_with_model, configured
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/status")
def status(x_sc_provider_key: str | None = Header(default=None)):
    return {"ok": True, "provider": settings.ai_provider, "model": settings.openai_model if settings.ai_provider == "openai" else None, "configured": configured(x_sc_provider_key), "wordpress_provider_key_allowed": settings.allow_wordpress_provider_key}

@router.post("/ask-library")
def ask(req: AskRequest, x_sc_provider_key: str | None = Header(default=None)):
    allowed, reason = is_in_scope(req.question, req.topic)
    if req.scope_gate_enabled and not allowed:
        return {"ok": True, "scoped": False, "reason": reason, "answer": redirect_message(), "recommended_tools": [], "pathways": [], "ai": {"configured": configured(x_sc_provider_key), "provider": settings.ai_provider}}
    context = retrieve(req.question, req.topic)
    ai = answer_with_model(req.question, context, x_sc_provider_key)
    return {"ok": True, "scoped": True, "reason": reason, "answer": ai["answer"], "recommended_tools": context.get("tools", []), "pathways": context.get("pathways", []), "ai": ai}
