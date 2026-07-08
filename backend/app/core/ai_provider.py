from __future__ import annotations
import requests
from .config import settings

SYSTEM_PROMPT = """You are the Sustainable Catalyst Workbench assistant. You are not a general chatbot. Answer only within Sustainable Catalyst topics: governance, sustainability, technology, AI, data systems, natural science, psychology, philosophy, meaning, culture, religious studies, healing traditions, problem solving, mathematical modeling, systems modeling, economics, energy, and research-library learning pathways. Prefer concise, useful answers. Recommend calculators and pathways when helpful. State assumptions and limits. Never claim legal, medical, financial, or clinical authority."""


def configured(provider_key: str | None = None) -> bool:
    return bool(settings.openai_api_key or (settings.allow_wordpress_provider_key and provider_key)) and settings.ai_provider == "openai"


def answer_with_model(question: str, context: dict, provider_key: str | None = None) -> dict:
    api_key = settings.openai_api_key or (provider_key if settings.allow_wordpress_provider_key else "")
    if not api_key or settings.ai_provider != "openai":
        return fallback_answer(question, context)
    context_text = "Recommended tools:\n" + "\n".join(f"- {t['title']}: {t.get('description','')}" for t in context.get("tools", []))
    context_text += "\n\nPathways:\n" + "\n".join(f"- {p['title']}: {p.get('description','')}" for p in context.get("pathways", []))
    payload = {
        "model": settings.openai_model,
        "input": [
            {"role":"system", "content": SYSTEM_PROMPT},
            {"role":"user", "content": f"Question: {question}\n\nUse this Sustainable Catalyst context:\n{context_text}"}
        ],
        "max_output_tokens": settings.max_output_tokens,
        "temperature": settings.temperature,
    }
    try:
        res = requests.post("https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}, json=payload, timeout=45)
        if res.status_code >= 400:
            return {"configured": True, "provider":"openai", "model": settings.openai_model, "answer": f"AI provider returned HTTP {res.status_code}. The Workbench can still recommend tools and pathways."}
        data=res.json()
        text=data.get("output_text")
        if not text:
            parts=[]
            for item in data.get("output",[]):
                for c in item.get("content",[]):
                    if c.get("type") in {"output_text","text"} and c.get("text"):
                        parts.append(c["text"])
            text="\n".join(parts).strip()
        return {"configured": True, "provider":"openai", "model": settings.openai_model, "answer": text or "The model returned an empty answer."}
    except Exception as exc:
        return {"configured": True, "provider":"openai", "model": settings.openai_model, "answer": f"AI request failed: {exc}. The Workbench can still run calculators and show pathways."}


def fallback_answer(question: str, context: dict) -> dict:
    tools = context.get("tools", [])[:4]
    paths = context.get("pathways", [])[:3]
    lines = ["I can help with this inside the Sustainable Catalyst Workbench."]
    if tools:
        lines.append("Recommended tools: " + ", ".join(t["title"] for t in tools) + ".")
    if paths:
        lines.append("Relevant learning pathways: " + ", ".join(p["title"] for p in paths) + ".")
    lines.append("For calculation-heavy work, choose a tool from the calculator list; the Python/R/Julia/Haskell backend handles the analytics and graphs.")
    return {"configured": False, "provider":"fallback", "model": None, "answer":"\n\n".join(lines)}
