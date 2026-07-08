from __future__ import annotations

TOPIC_TERMS = {
    "governance", "law", "legal", "international", "institution", "policy", "geopolitics", "organization",
    "sustainability", "sustainable", "climate", "planetary", "resilience", "risk", "energy", "emissions", "ecology",
    "technology", "ai", "artificial intelligence", "data", "algorithm", "embedded", "infrastructure", "monitoring",
    "science", "physics", "biology", "chemistry", "materials", "earth", "astronomy", "environmental",
    "anthropology", "culture", "ritual", "symbolism", "kinship", "modernity", "place",
    "literature", "poetry", "memory", "shakespeare", "dante", "myth", "folklore", "legend",
    "religion", "religious", "sacred", "mysticism", "contemplative", "healing", "medicine", "herbalism",
    "psychology", "cognitive", "social", "developmental", "personality", "behavior", "organizational", "moral",
    "philosophy", "ethics", "metaphysics", "ontology", "causation", "freedom", "justice",
    "thinking", "systems thinking", "mathematical", "computation", "futures", "knowledge architecture",
    "meaning", "aesthetic", "beauty", "music", "design", "story", "narrative",
    "problem", "decision", "strategy", "model", "calculus", "linear algebra", "probability", "statistics", "differential", "simulation", "arduino", "raspberry pi",
    "calculator", "calculate", "graph", "analyze", "analysis", "modeling", "workbench", "research library"
}

OUT_OF_SCOPE_HINTS = {"celebrity", "sports scores", "dating", "shopping", "recipe", "movie gossip", "lottery"}


def is_in_scope(question: str, topic: str | None = None) -> tuple[bool, str]:
    text = f"{question or ''} {topic or ''}".lower()
    if not text.strip():
        return True, "empty question allowed for tool discovery"
    if any(h in text for h in OUT_OF_SCOPE_HINTS) and not any(t in text for t in TOPIC_TERMS):
        return False, "outside Sustainable Catalyst topic map"
    if any(term in text for term in TOPIC_TERMS):
        return True, "matched Sustainable Catalyst topic map"
    # permissive for compact tool: invite bridge framing rather than hard fail
    return False, "no Sustainable Catalyst topic match"


def redirect_message() -> str:
    return (
        "That question appears outside the Sustainable Catalyst knowledge map. "
        "I can help if you connect it to sustainability, governance, systems thinking, science, technology, psychology, philosophy, meaning, problem solving, modeling, analytics, or the Research Library."
    )
