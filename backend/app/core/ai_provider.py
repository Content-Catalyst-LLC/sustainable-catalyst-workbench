from __future__ import annotations
import requests
from .config import get_settings
from .scope_gate import classify_scope, out_of_scope_message
from .retrieval import retrieve_context

SYSTEM_PROMPT = """You are Sustainable Catalyst Workbench, a site-scoped research and analytics assistant. Answer only within the Sustainable Catalyst knowledge map: science, sustainability, engineering, architecture, psychology, economics, energy, governance, meaning, mathematical modeling, systems modeling, decision science, and related research pathways. Be useful, structured, honest about limits, and recommend appropriate calculators when relevant. Do not provide final professional certification, clinical diagnosis, legal advice, financial advice, or safety-critical engineering decisions."""


def provider_status() -> dict:
    s = get_settings()
    return {"provider": s.ai_provider, "model": s.openai_model, "env_key_set": bool(s.openai_api_key), "wordpress_key_allowed": s.allow_wordpress_provider_key, "scope_gate": s.scope_gate}


def answer_question(question: str, topic: str, mode: str = 'guided', scope_gate_enabled: bool = True, provider_key: str | None = None) -> dict:
    s = get_settings()
    scope = classify_scope(question, topic)
    context = retrieve_context(question, topic)
    if scope_gate_enabled and s.scope_gate and not scope.get('in_scope'):
        return {"ok": True, "answer": out_of_scope_message(), "scope": scope, "recommended_tools": context['tools'], "provider": "scope_gate", "model": None}
    key = s.openai_api_key or (provider_key if s.allow_wordpress_provider_key else None)
    if s.ai_provider.lower() != 'openai' or not key:
        answer = "This is in scope for Sustainable Catalyst. Based on the Workbench registry, the most relevant tools are: " + ", ".join(t['title'] for t in context['tools'][:4]) + ". Enable an OpenAI key to generate a fuller assistant answer."
        return {"ok": True, "answer": answer, "scope": scope, "recommended_tools": context['tools'], "pathways": context['pathways'], "provider": "registry", "model": None}
    tool_lines = "\n".join([f"- {t['title']} ({t['domain']}): {t['description']}" for t in context['tools']])
    pathway_lines = "\n".join([f"- {p['title']}: {p['summary']}" for p in context['pathways']])
    user_content = f"Question: {question}\nTopic: {topic}\nMode: {mode}\nRelevant Workbench tools:\n{tool_lines}\nRelevant pathways:\n{pathway_lines}\nGive a concise, useful answer and recommend the best next calculator/model when appropriate."
    try:
        resp = requests.post(
            'https://api.openai.com/v1/responses',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={
                'model': s.openai_model,
                'instructions': SYSTEM_PROMPT,
                'input': user_content,
                'temperature': s.temperature,
                'max_output_tokens': s.max_output_tokens,
            },
            timeout=45,
        )
        if resp.status_code >= 400:
            return {"ok": False, "answer": f"AI provider error: {resp.status_code} {resp.text[:300]}", "scope": scope, "recommended_tools": context['tools'], "provider": "openai", "model": s.openai_model}
        data = resp.json()
        text = data.get('output_text')
        if not text:
            chunks = []
            for item in data.get('output', []):
                for c in item.get('content', []):
                    if c.get('type') in ('output_text', 'text'):
                        chunks.append(c.get('text', ''))
            text = "\n".join(chunks).strip() or "AI returned no text."
        return {"ok": True, "answer": text, "scope": scope, "recommended_tools": context['tools'], "pathways": context['pathways'], "provider": "openai", "model": s.openai_model}
    except Exception as exc:
        return {"ok": False, "answer": f"AI request failed: {exc}", "scope": scope, "recommended_tools": context['tools'], "provider": "openai", "model": s.openai_model}
