from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    domain: str
    keywords: tuple[str, ...]


TOPICS: tuple[Topic, ...] = (
    Topic("global-governance", "Global Governance", "Global Governance", ("governance", "international law", "institutions", "geopolitics", "legal traditions", "international organizations")),
    Topic("international-law", "International Law", "Global Governance", ("treaty", "customary international law", "human rights", "jurisdiction", "international court", "compliance")),
    Topic("legal-traditions", "Legal Traditions", "Global Governance", ("roman law", "civil law", "common law", "islamic law", "customary law", "legal pluralism")),
    Topic("sustainable-systems", "Sustainable Systems", "Sustainable Systems", ("sustainability", "sustainable development", "planetary boundaries", "resilience", "stewardship", "economic systems")),
    Topic("risk-resilience", "Risk & Resilience", "Sustainable Systems", ("risk", "resilience", "vulnerability", "adaptation", "scenario", "shock", "exposure")),
    Topic("technology-systems-intelligence", "Technology & Systems Intelligence", "Technology & Systems Intelligence", ("ai", "artificial intelligence", "data systems", "edge systems", "embedded systems", "infrastructure", "energy systems", "environmental monitoring")),
    Topic("artificial-intelligence-systems", "Artificial Intelligence Systems", "Technology & Systems Intelligence", ("ai governance", "algorithm", "model card", "dataset", "automation", "human in the loop")),
    Topic("natural-science", "Natural Science", "Natural Science", ("physics", "biology", "chemistry", "materials science", "earth science", "astronomy", "environmental science")),
    Topic("cultural-anthropology", "Cultural Anthropology", "Cultural Anthropology", ("culture", "ritual", "kinship", "reciprocity", "norms", "modernity", "ecological knowledge")),
    Topic("literature-cultural-memory", "Literature & Cultural Memory", "Literature & Cultural Memory", ("literature", "poetry", "memory", "drama", "tragedy", "cultural memory", "imagination")),
    Topic("mythology", "Mythology", "Mythology", ("myth", "folklore", "legend", "epic", "sacred narrative", "motif")),
    Topic("religious-studies", "Religious Studies", "Religious Studies", ("religion", "sacred", "mysticism", "comparative religion", "tradition", "theology", "ritual")),
    Topic("healing-traditions", "Healing Traditions", "Healing Traditions", ("medicine", "healing", "herbalism", "ayurveda", "chinese medicine", "food as medicine", "shamanism")),
    Topic("psychology", "Psychology", "Psychology", ("cognitive psychology", "social psychology", "developmental psychology", "personality", "positive psychology", "behavioral science", "moral psychology")),
    Topic("behavioral-science", "Behavioral Science & Psychology", "Psychology", ("behavior change", "habit", "motivation", "reinforcement", "nudge", "choice architecture", "behavioral public policy")),
    Topic("philosophy", "Philosophy", "Philosophy", ("ethics", "moral philosophy", "political philosophy", "metaphysics", "ontology", "causation", "consciousness")),
    Topic("thinking", "Thinking", "Thinking", ("knowledge architecture", "design thinking", "mathematical thinking", "systems thinking", "algorithms", "resilience thinking", "futures thinking")),
    Topic("meaning", "Meaning", "Meaning", ("beauty", "aesthetics", "music", "symbolism", "story", "myth", "meaning", "art", "interpretation")),
    Topic("problem-solving", "Problem Solving", "Problem Solving", ("strategic ideation", "content frameworks", "storytelling", "decision science", "mathematical modeling", "systems modeling")),
    Topic("mathematical-modeling", "Mathematical Modeling", "Problem Solving", ("calculus", "linear algebra", "probability", "statistics", "scientific computing", "differential equations", "optimization")),
    Topic("systems-modeling", "Systems Modeling", "Problem Solving", ("systems model", "feedback", "stocks and flows", "network", "simulation", "interdependence")),
    Topic("applied-builds", "Applied Builds", "Problem Solving", ("arduino", "raspberry pi", "sensor", "environmental monitoring", "prototype", "embedded")),
)


def all_topics() -> list[dict]:
    return [topic.__dict__ for topic in TOPICS]


def match_topics(text: str, limit: int = 5) -> list[dict]:
    lower = (text or "").lower()
    scored: list[tuple[int, Topic]] = []
    for topic in TOPICS:
        score = 0
        if topic.title.lower() in lower or topic.id.replace("-", " ") in lower:
            score += 5
        for keyword in topic.keywords:
            if keyword.lower() in lower:
                score += 2
        # Partial token matches for broad queries.
        tokens = set(lower.replace("&", " ").replace("/", " ").split())
        for token in topic.title.lower().replace("&", " ").split():
            if token in tokens and len(token) > 3:
                score += 1
        if score > 0:
            scored.append((score, topic))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [topic.__dict__ | {"score": score} for score, topic in scored[:limit]]


def in_scope(text: str) -> bool:
    return len(match_topics(text, limit=1)) > 0
