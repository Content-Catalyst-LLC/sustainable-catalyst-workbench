from __future__ import annotations

from typing import Any

CATEGORIES = [
    "core_theme",
    "symbols_or_motifs",
    "institutional_context",
    "narrative_structure",
    "ethical_tensions",
    "comparative_links",
    "limits_of_interpretation",
]


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    subject = inputs.get("subject", "Unspecified subject")
    notes = inputs.get("notes", {})
    matrix = []
    for category in CATEGORIES:
        matrix.append({
            "category": category,
            "user_notes": notes.get(category, ""),
            "prompt": _prompt_for(category),
        })

    return {
        "result": {"subject": subject, "matrix": matrix},
        "warnings": ["Interpretive tools structure inquiry; they do not produce final or objective meanings."],
        "interpretation": "Use this matrix to make interpretive assumptions visible across meaning, myth, religion, literature, philosophy, anthropology, and cultural memory.",
    }


def _prompt_for(category: str) -> str:
    prompts = {
        "core_theme": "What central human question, tension, or pattern is being explored?",
        "symbols_or_motifs": "Which symbols, images, metaphors, rituals, or recurring motifs carry meaning?",
        "institutional_context": "What social, religious, political, artistic, or cultural setting shapes interpretation?",
        "narrative_structure": "How does sequence, conflict, transformation, return, loss, or revelation organize the material?",
        "ethical_tensions": "What moral, existential, or communal tensions are present?",
        "comparative_links": "What related traditions, texts, myths, theories, or frameworks are useful comparisons?",
        "limits_of_interpretation": "What should not be overclaimed based on the available evidence?",
    }
    return prompts[category]
