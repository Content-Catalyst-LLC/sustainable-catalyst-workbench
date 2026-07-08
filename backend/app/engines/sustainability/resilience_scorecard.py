from __future__ import annotations

from typing import Any

DEFAULT_WEIGHTS = {
    "exposure": 0.20,
    "sensitivity": 0.20,
    "adaptive_capacity": 0.25,
    "redundancy": 0.15,
    "recovery_capacity": 0.20,
}


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    weights = inputs.get("weights", DEFAULT_WEIGHTS)
    scores = {k: float(inputs.get(k, 0.0)) for k in DEFAULT_WEIGHTS}
    total_weight = sum(float(v) for v in weights.values()) or 1.0

    # exposure and sensitivity are risk-increasing, so invert for resilience score.
    adjusted = {
        "exposure": 10.0 - scores["exposure"],
        "sensitivity": 10.0 - scores["sensitivity"],
        "adaptive_capacity": scores["adaptive_capacity"],
        "redundancy": scores["redundancy"],
        "recovery_capacity": scores["recovery_capacity"],
    }

    resilience_score = sum(adjusted[k] * float(weights.get(k, 0.0)) for k in DEFAULT_WEIGHTS) / total_weight
    if resilience_score >= 7.5:
        band = "strong"
    elif resilience_score >= 5:
        band = "moderate"
    else:
        band = "fragile"

    warnings = []
    if scores["exposure"] >= 8 or scores["sensitivity"] >= 8:
        warnings.append("High exposure or sensitivity may dominate resilience even when adaptive capacity appears strong.")
    if scores["redundancy"] <= 3:
        warnings.append("Low redundancy can turn localized disruption into system-wide fragility.")

    return {
        "result": {
            "raw_scores": scores,
            "adjusted_scores": adjusted,
            "resilience_score_0_to_10": resilience_score,
            "resilience_band": band,
        },
        "warnings": warnings,
        "interpretation": "This score is a structured diagnostic, not a prediction. It should be paired with scenario analysis and evidence about the actual system boundary.",
    }
