from __future__ import annotations

from typing import Any

FIELDS = {
    "transparency": "Can affected people and reviewers understand the system purpose, logic, limits, and use context?",
    "human_oversight": "Is there meaningful human supervision with authority to intervene?",
    "data_quality": "Are data sources documented, appropriate, representative, and periodically reviewed?",
    "contestability": "Can affected people challenge, appeal, or correct outputs?",
    "harm_risk": "How severe could foreseeable harms be if the system fails or is misused?",
}


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    values = {field: float(inputs.get(field, 0.0)) for field in FIELDS}
    # harm_risk is inverted because high harm raises governance concern.
    positive_score = (
        values["transparency"] + values["human_oversight"] + values["data_quality"] + values["contestability"] + (5.0 - values["harm_risk"])
    ) / 5.0

    if positive_score >= 4:
        band = "lower governance concern"
    elif positive_score >= 2.75:
        band = "moderate governance concern"
    else:
        band = "high governance concern"

    warnings = []
    if values["harm_risk"] >= 4 and values["human_oversight"] <= 2:
        warnings.append("High harm risk with weak oversight should trigger escalation before deployment.")
    if values["contestability"] <= 2:
        warnings.append("Low contestability creates accountability and procedural fairness concerns.")
    if values["data_quality"] <= 2:
        warnings.append("Weak data quality can undermine validity even when the interface appears reliable.")

    return {
        "result": {
            "fields": FIELDS,
            "input_scores_0_to_5": values,
            "governance_readiness_score_0_to_5": positive_score,
            "band": band,
        },
        "warnings": warnings,
        "interpretation": "This audit is educational and governance-oriented. It is not a legal compliance determination and should be paired with documentation, stakeholder review, and context-specific standards.",
    }
