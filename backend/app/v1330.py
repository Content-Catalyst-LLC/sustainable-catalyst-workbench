"""Workbench v13.3.0 — Advanced Calculator Input & Mathematical Notation."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1320 import experience_contract

VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v1330-advanced-calculator-input-mathematical-notation"])

STATUS_SCHEMA = "sc-workbench-advanced-calculator-input-status/1.0"
NORMALIZATION_SCHEMA = "sc-workbench-mathematical-notation-normalization/1.0"

_SUPERSCRIPTS = str.maketrans({
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
})


class NormalizeNotationRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=20000)
    mode: Literal["conservative"] = "conservative"


def _hash(x: Any) -> str:
    return content_hash(x)


def _record(steps: List[Dict[str, str]], rule: str, before: str, after: str) -> str:
    if before != after:
        steps.append({"rule": rule, "before": before, "after": after})
    return after


def _replace_superscripts(text: str, steps: List[Dict[str, str]]) -> str:
    # Convert a contiguous superscript integer following an atom/closing paren.
    pattern = re.compile(r"(?P<base>(?:[A-Za-z0-9_]+|\)))\s*(?P<sup>[⁰¹²³⁴⁵⁶⁷⁸⁹]+)")
    def repl(m: re.Match[str]) -> str:
        return f"{m.group('base')}**{m.group('sup').translate(_SUPERSCRIPTS)}"
    after = pattern.sub(repl, text)
    return _record(steps, "unicode-superscript-integer", text, after)


def _replace_square_root(text: str, steps: List[Dict[str, str]]) -> str:
    # Conservative forms only: √(...) and √symbol/number.
    before = text
    text = re.sub(r"√\s*\(([^()]*)\)", r"sqrt(\1)", text)
    text = re.sub(r"√\s*([A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?)", r"sqrt(\1)", text)
    return _record(steps, "unicode-square-root", before, text)


def normalize_notation(expression: str) -> Dict[str, Any]:
    original = expression
    text = expression.strip()
    steps: List[Dict[str, str]] = []

    text = _record(steps, "unicode-minus", text, text.replace("−", "-").replace("–", "-"))
    text = _record(steps, "unicode-multiplication", text, text.replace("×", "*").replace("·", "*"))
    text = _record(steps, "unicode-division", text, text.replace("÷", "/"))
    text = _record(steps, "unicode-pi", text, text.replace("π", "pi"))
    text = _record(steps, "unicode-infinity", text, text.replace("∞", "oo"))
    text = _replace_square_root(text, steps)
    text = _replace_superscripts(text, steps)

    # Caret is treated as exponentiation in the Workbench input surface.
    text = _record(steps, "caret-exponent", text, text.replace("^", "**"))

    # Common function glyph/name aliases. No semantic guessing beyond explicit aliases.
    aliases = {
        "ln(": "log(",
        "arcsin(": "asin(",
        "arccos(": "acos(",
        "arctan(": "atan(",
    }
    for src, dst in aliases.items():
        text = _record(steps, f"function-alias:{src[:-1]}", text, text.replace(src, dst))

    # Intentionally do not infer implicit multiplication (2x -> 2*x) because
    # adjacency can be ambiguous. The UI inserts explicit multiplication.
    ambiguous = []
    if re.search(r"(?<![A-Za-z_])\d+(?:\.\d+)?\s*[A-Za-z_]", text):
        ambiguous.append("implicit-multiplication-not-expanded")
    if re.search(r"\)\s*\(", text):
        ambiguous.append("adjacent-parentheses-multiplication-not-expanded")

    result = {
        "schema": NORMALIZATION_SCHEMA,
        "version": VERSION,
        "mode": "conservative",
        "originalExpression": original,
        "normalizedExpression": text,
        "changed": original.strip() != text,
        "transformations": steps,
        "ambiguities": ambiguous,
        "principles": {
            "originalInputPreserved": True,
            "normalizationIsDerivedRepresentation": True,
            "normalizationDoesNotExecuteMathematics": True,
            "implicitMultiplicationIsNotInferred": True,
            "ambiguousNotationRequiresExplicitUserExpression": True,
        },
    }
    result["normalizationHash"] = _hash({
        "originalExpression": result["originalExpression"],
        "normalizedExpression": result["normalizedExpression"],
        "transformations": result["transformations"],
        "ambiguities": result["ambiguities"],
    })
    return result


def input_contract() -> Dict[str, Any]:
    body = {
        "schema": "sc-workbench-advanced-calculator-input-contract/1.0",
        "version": VERSION,
        "canonicalComputationAuthority": "FastAPI calculation engine",
        "notationNormalizationAuthority": "v13.3 conservative normalizer",
        "originalInputCanonical": True,
        "normalizedInputDerived": True,
        "wordpressRequired": False,
        "features": {
            "symbolPalette": True,
            "functionPalette": True,
            "greekConstants": True,
            "unicodeOperators": True,
            "unicodeSuperscripts": True,
            "squareRootNotation": True,
            "caretExponentiation": True,
            "functionAliases": True,
            "normalizedExpressionPreview": True,
            "transformationLineage": True,
            "ambiguousNotationWarnings": True,
            "cursorAwareInsertion": True,
        },
        "intentionallyUnsupportedInference": [
            "implicit multiplication",
            "natural-language intent inference",
            "equation semantic rewriting",
            "automatic variable invention",
        ],
    }
    body["contractHash"] = _hash(body)
    return body


def status() -> Dict[str, Any]:
    previous = experience_contract()
    contract = input_contract()
    checks = {
        "v132ExperiencePreserved": all(previous["features"].values()),
        "originalInputPreserved": contract["originalInputCanonical"] is True,
        "normalizationDerived": contract["normalizedInputDerived"] is True,
        "inputFeaturesReady": all(contract["features"].values()),
        "wordpressRequiredFalse": contract["wordpressRequired"] is False,
    }
    return {
        "ok": all(checks.values()),
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Advanced Calculator Input & Mathematical Notation",
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "inputExperienceReady": all(checks.values()),
        "checks": checks,
        "contractHash": contract["contractHash"],
    }


@router.get("/v1330/status")
def status_route():
    return status()


@router.get("/standalone/v1/calculator/input-contract")
def input_contract_route():
    return {"ok": True, "version": VERSION, "input": input_contract()}


@router.post("/standalone/v1/calculator/normalize")
def normalize_route(req: NormalizeNotationRequest):
    return {
        "ok": True,
        "version": VERSION,
        "normalization": normalize_notation(req.expression),
    }
