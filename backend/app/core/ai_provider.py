from __future__ import annotations
from typing import Any
import requests
from .config import get_settings
from .scope_gate import classify_scope, out_of_scope_message
from .retrieval import retrieve_context

SYSTEM_PROMPT = """You are Sustainable Catalyst Workbench, a site-scoped research and analytics assistant. Answer only within the Sustainable Catalyst knowledge map: science, sustainability, engineering, architecture, psychology, economics, energy, governance, meaning, mathematical modeling, systems modeling, decision science, and related research pathways. Be useful, structured, honest about limits, and recommend appropriate calculators when relevant. Do not provide final professional certification, clinical diagnosis, legal advice, financial advice, or safety-critical engineering decisions."""

SUPPORTED_PROVIDERS = {"disabled", "gemini", "deepseek", "openai"}


def _clean_provider(provider: str | None) -> str:
    p = (provider or "").strip().lower()
    return p if p in SUPPORTED_PROVIDERS else ""


def _provider_choice(provider_override: str | None = None) -> str:
    s = get_settings()
    override = _clean_provider(provider_override)
    configured = _clean_provider(s.ai_provider) or "disabled"
    return override or configured


def _provider_key(provider: str, provider_keys: dict[str, str] | None = None) -> str:
    s = get_settings()
    provider_keys = provider_keys or {}
    forwarded_generic = provider_keys.get("provider") or ""
    if provider == "gemini":
        return s.gemini_api_key or provider_keys.get("gemini", "") or (forwarded_generic if s.allow_wordpress_provider_key else "")
    if provider == "deepseek":
        return s.deepseek_api_key or provider_keys.get("deepseek", "") or (forwarded_generic if s.allow_wordpress_provider_key else "")
    if provider == "openai":
        return s.openai_api_key or provider_keys.get("openai", "") or (forwarded_generic if s.allow_wordpress_provider_key else "")
    return ""


def _model_for_provider(provider: str) -> str | None:
    s = get_settings()
    if provider == "gemini":
        return s.gemini_model
    if provider == "deepseek":
        return s.deepseek_model
    if provider == "openai":
        return s.openai_model
    return None


def provider_status(provider_override: str | None = None, provider_keys: dict[str, str] | None = None) -> dict:
    s = get_settings()
    provider = _provider_choice(provider_override)
    return {
        "provider": provider,
        "configured_provider": s.ai_provider,
        "supported_providers": ["disabled", "gemini", "deepseek", "openai"],
        "model": _model_for_provider(provider),
        "models": {
            "gemini": s.gemini_model,
            "deepseek": s.deepseek_model,
            "openai": s.openai_model,
        },
        "env_key_set": bool(_provider_key(provider, {})),
        "forwarded_key_present": bool(_provider_key(provider, provider_keys or {}) and not _provider_key(provider, {})),
        "wordpress_key_allowed": s.allow_wordpress_provider_key,
        "scope_gate": s.scope_gate,
    }


def _context_prompt(question: str, topic: str, mode: str, context: dict[str, Any]) -> str:
    tool_lines = "\n".join([f"- {t['title']} ({t['domain']}): {t['description']}" for t in context['tools']])
    pathway_lines = "\n".join([f"- {p['title']}: {p['summary']}" for p in context['pathways']])
    return (
        f"Question: {question}\n"
        f"Topic: {topic}\n"
        f"Mode: {mode}\n"
        f"Relevant Workbench tools:\n{tool_lines}\n"
        f"Relevant pathways:\n{pathway_lines}\n"
        "Give a concise, useful answer and recommend the best next calculator/model when appropriate. "
        "For law, health, engineering, environmental compliance, or safety-critical topics, explicitly frame the answer as educational/analytical support only."
    )


def _registry_answer(context: dict[str, Any], provider: str) -> str:
    tools = ", ".join(t['title'] for t in context['tools'][:4]) or "the Workbench model registry"
    if provider == "disabled":
        provider_hint = "AI is currently disabled."
    else:
        provider_hint = f"The selected AI provider is {provider}, but no usable provider key is configured."
    return (
        "This is in scope for Sustainable Catalyst. "
        f"Based on the Workbench registry, the most relevant tools are: {tools}. "
        f"{provider_hint} Configure Gemini, DeepSeek, or OpenAI in the FastAPI backend environment, or forward a provider key from WordPress over HTTPS."
    )


def _call_openai(user_content: str, key: str) -> tuple[bool, str]:
    s = get_settings()
    resp = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": s.openai_model,
            "instructions": SYSTEM_PROMPT,
            "input": user_content,
            "temperature": s.temperature,
            "max_output_tokens": s.max_output_tokens,
        },
        timeout=45,
    )
    if resp.status_code >= 400:
        return False, f"OpenAI provider error: {resp.status_code} {resp.text[:300]}"
    data = resp.json()
    text = data.get("output_text")
    if not text:
        chunks = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text"):
                    chunks.append(c.get("text", ""))
        text = "\n".join(chunks).strip()
    return True, text or "OpenAI returned no text."


def _call_gemini(user_content: str, key: str) -> tuple[bool, str]:
    s = get_settings()
    url = f"{s.gemini_base_url.rstrip('/')}/models/{s.gemini_model}:generateContent"
    resp = requests.post(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "generationConfig": {
                "temperature": s.temperature,
                "maxOutputTokens": s.max_output_tokens,
            },
        },
        timeout=45,
    )
    if resp.status_code >= 400:
        return False, f"Gemini provider error: {resp.status_code} {resp.text[:300]}"
    data = resp.json()
    chunks = []
    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if isinstance(part, dict) and part.get("text"):
                chunks.append(part["text"])
    return True, "\n".join(chunks).strip() or "Gemini returned no text."


def _call_deepseek(user_content: str, key: str) -> tuple[bool, str]:
    s = get_settings()
    url = f"{s.deepseek_base_url.rstrip('/')}/chat/completions"
    body: dict[str, Any] = {
        "model": s.deepseek_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": s.temperature,
        "max_tokens": s.max_output_tokens,
        "stream": False,
    }
    thinking = (s.deepseek_thinking or "disabled").strip().lower()
    if thinking in {"enabled", "disabled"}:
        body["thinking"] = {"type": thinking}
    if s.deepseek_reasoning_effort:
        body["reasoning_effort"] = s.deepseek_reasoning_effort
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=body,
        timeout=45,
    )
    if resp.status_code >= 400:
        return False, f"DeepSeek provider error: {resp.status_code} {resp.text[:300]}"
    data = resp.json()
    choices = data.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        return True, (message.get("content") or "").strip() or "DeepSeek returned no text."
    return True, "DeepSeek returned no choices."


def answer_question(
    question: str,
    topic: str,
    mode: str = "guided",
    scope_gate_enabled: bool = True,
    provider_keys: dict[str, str] | None = None,
    provider_override: str | None = None,
) -> dict:
    s = get_settings()
    provider = _provider_choice(provider_override)
    scope = classify_scope(question, topic)
    context = retrieve_context(question, topic)
    if scope_gate_enabled and s.scope_gate and not scope.get("in_scope"):
        return {"ok": True, "answer": out_of_scope_message(), "scope": scope, "recommended_tools": context["tools"], "provider": "scope_gate", "model": None}

    key = _provider_key(provider, provider_keys)
    if provider == "disabled" or not key:
        return {
            "ok": True,
            "answer": _registry_answer(context, provider),
            "scope": scope,
            "recommended_tools": context["tools"],
            "pathways": context["pathways"],
            "provider": "registry" if provider == "disabled" else provider,
            "model": _model_for_provider(provider),
        }

    user_content = _context_prompt(question, topic, mode, context)
    try:
        if provider == "gemini":
            ok, text = _call_gemini(user_content, key)
        elif provider == "deepseek":
            ok, text = _call_deepseek(user_content, key)
        elif provider == "openai":
            ok, text = _call_openai(user_content, key)
        else:
            ok, text = False, f"Unsupported AI provider: {provider}. Supported providers: disabled, gemini, deepseek, openai."
        return {
            "ok": ok,
            "answer": text,
            "scope": scope,
            "recommended_tools": context["tools"],
            "pathways": context["pathways"],
            "provider": provider,
            "model": _model_for_provider(provider),
        }
    except Exception as exc:
        return {"ok": False, "answer": f"AI request failed: {exc}", "scope": scope, "recommended_tools": context["tools"], "provider": provider, "model": _model_for_provider(provider)}
