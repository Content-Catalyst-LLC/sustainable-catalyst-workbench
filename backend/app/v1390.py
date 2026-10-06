"""Workbench v13.9.0 — Natural-Language Computation Foundation.

Natural language is an input/planning layer only. It never becomes a second
mathematics authority and it never executes directly. Parsed intent is converted
into an explicit proposed UnifiedCalculationRequest that the user can inspect
and apply to the canonical Calculator workspace.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1330 import normalize_notation
from .v1380 import unified_contract

VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v1390-natural-language-computation-foundation"])

STATUS_SCHEMA = "sc-workbench-natural-language-computation-status/1.0"
INTERPRETATION_SCHEMA = "sc-workbench-natural-language-interpretation/1.0"


class NaturalLanguageInterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    mode: Literal["conservative"] = "conservative"


def _hash(x: Any) -> str:
    return content_hash(x)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _requested_result_type(operation: str) -> str:
    if operation in {"evaluate", "root"}:
        return "numeric"
    if operation == "exact":
        return "exact"
    return "symbolic"


def _plan(operation: str, expression: str, variable: Optional[str], *,
          confidence: float, matched_rule: str,
          initial_guess: Optional[float] = None) -> Dict[str, Any]:
    normalization = normalize_notation(expression)
    calculation: Dict[str, Any] = {
        "operation": operation,
        "expression": normalization["normalizedExpression"],
    }
    if operation in {"solve", "differentiate", "integrate-symbolic", "root"}:
        calculation["variable"] = variable or "x"
    if operation == "root" and initial_guess is not None:
        calculation["initialGuess"] = initial_guess

    ambiguities: List[str] = list(normalization.get("ambiguities") or [])
    if operation in {"differentiate", "integrate-symbolic", "root"} and not variable:
        ambiguities.append("variable-defaulted-to-x")
    if operation == "solve" and "=" not in expression:
        ambiguities.append("solve-expression-has-no-explicit-equality")

    request = {
        "calculation": calculation,
        "requestedResultType": _requested_result_type(operation),
        "requireVerification": True,
        "requireProvenance": True,
    }
    return {
        "intent": operation,
        "confidence": confidence,
        "matchedRule": matched_rule,
        "originalExpression": expression,
        "normalization": normalization,
        "proposedCalculationRequest": request,
        "ambiguities": ambiguities,
        "requiresConfirmation": True,
        "executionAllowed": False,
    }


def interpret_text(text: str) -> Dict[str, Any]:
    original = text
    q = _clean(text)
    low = q.lower()
    result: Dict[str, Any]

    m = re.match(
        r"^(?:differentiate|derive|find the derivative of)\s+(.+?)(?:\s+(?:with respect to|wrt)\s+([A-Za-z][A-Za-z0-9_]*))?$",
        q, re.I,
    )
    if m:
        result = _plan("differentiate", m.group(1), m.group(2), confidence=0.98, matched_rule="differentiate")
    else:
        m = re.match(
            r"^(?:integrate|find the integral of)\s+(.+?)(?:\s+(?:with respect to|wrt)\s+([A-Za-z][A-Za-z0-9_]*))?$",
            q, re.I,
        )
        if m:
            result = _plan("integrate-symbolic", m.group(1), m.group(2), confidence=0.98, matched_rule="integrate-symbolic")
        else:
            m = re.match(
                r"^solve\s+(.+?)(?:\s+for\s+([A-Za-z][A-Za-z0-9_]*))?$",
                q, re.I,
            )
            if m:
                result = _plan("solve", m.group(1), m.group(2), confidence=0.98, matched_rule="solve")
            else:
                m = re.match(
                    r"^(?:simplify|simplify the expression)\s+(.+)$",
                    q, re.I,
                )
                if m:
                    result = _plan("simplify", m.group(1), None, confidence=0.99, matched_rule="simplify")
                else:
                    m = re.match(
                        r"^(?:find the exact value of|exact value of|evaluate exactly)\s+(.+)$",
                        q, re.I,
                    )
                    if m:
                        result = _plan("exact", m.group(1), None, confidence=0.97, matched_rule="exact")
                    else:
                        m = re.match(
                            r"^(?:find (?:a |the )?root of)\s+(.+?)(?:\s+for\s+([A-Za-z][A-Za-z0-9_]*))?(?:\s+near\s+(-?\d+(?:\.\d+)?))?$",
                            q, re.I,
                        )
                        if m:
                            guess = float(m.group(3)) if m.group(3) is not None else None
                            result = _plan("root", m.group(1), m.group(2), confidence=0.94, matched_rule="root", initial_guess=guess)
                        else:
                            m = re.match(
                                r"^(?:calculate|compute|evaluate|what is)\s+(.+?)[?]?$",
                                q, re.I,
                            )
                            if m:
                                result = _plan("evaluate", m.group(1), None, confidence=0.95, matched_rule="evaluate")
                            else:
                                result = {
                                    "intent": None,
                                    "confidence": 0.0,
                                    "matchedRule": None,
                                    "originalExpression": None,
                                    "normalization": None,
                                    "proposedCalculationRequest": None,
                                    "ambiguities": ["unrecognized-natural-language-intent"],
                                    "requiresConfirmation": True,
                                    "executionAllowed": False,
                                }

    body = {
        "schema": INTERPRETATION_SCHEMA,
        "version": VERSION,
        "mode": "conservative",
        "originalText": original,
        **result,
        "principles": {
            "naturalLanguageIsDerivedInput": True,
            "canonicalCalculationEngineUnchanged": True,
            "noDirectNaturalLanguageExecution": True,
            "userConfirmationRequired": True,
            "originalLanguagePreserved": True,
            "ambiguityIsSurfacedNotGuessed": True,
        },
    }
    body["interpretationHash"] = _hash({
        "originalText": body["originalText"],
        "intent": body["intent"],
        "proposedCalculationRequest": body["proposedCalculationRequest"],
        "ambiguities": body["ambiguities"],
        "matchedRule": body["matchedRule"],
    })
    return body


def natural_language_contract() -> Dict[str, Any]:
    previous = unified_contract()
    features = {
        "conservativeIntentRecognition": True,
        "evaluateIntent": True,
        "exactIntent": True,
        "simplifyIntent": True,
        "solveIntent": True,
        "differentiateIntent": True,
        "integrateIntent": True,
        "rootIntent": True,
        "notationNormalizationReuse": True,
        "explicitProposedCalculationRequest": True,
        "confidenceAndMatchedRule": True,
        "ambiguitySurfacing": True,
        "confirmationRequired": True,
        "directExecutionDisabled": True,
        "canonicalCalculationAuthorityPreserved": True,
        "unifiedWorkspacePreserved": all(previous["features"].values()),
        "wordpressRequiredFalse": True,
    }
    body = {
        "schema": "sc-workbench-natural-language-computation-contract/1.0",
        "version": VERSION,
        "features": features,
        "canonicalExecutionAuthority": "v11 Unified Calculation Engine through v12.3 Calculator Workspace",
        "naturalLanguageRole": "derived input and proposed request only",
        "executionPolicy": "inspect-and-apply; no direct NL execution in v13.9",
        "wordpressRequired": False,
    }
    body["contractHash"] = _hash(body)
    return body


def status() -> Dict[str, Any]:
    c = natural_language_contract()
    checks = {
        "naturalLanguageFoundationReady": all(c["features"].values()),
        "canonicalCalculationAuthorityPreserved": c["features"]["canonicalCalculationAuthorityPreserved"],
        "directExecutionDisabled": c["features"]["directExecutionDisabled"],
        "unifiedWorkspacePreserved": c["features"]["unifiedWorkspacePreserved"],
        "wordpressRequiredFalse": c["wordpressRequired"] is False,
    }
    return {
        "ok": all(checks.values()),
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Natural-Language Computation Foundation",
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "naturalLanguageFoundationReady": all(checks.values()),
        "checks": checks,
        "contractHash": c["contractHash"],
    }


@router.get("/v1390/status")
def status_route():
    return status()


@router.get("/standalone/v1/natural-language/contract")
def contract_route():
    return {"ok": True, "version": VERSION, "naturalLanguage": natural_language_contract()}


@router.post("/standalone/v1/natural-language/interpret")
def interpret_route(req: NaturalLanguageInterpretRequest):
    return {
        "ok": True,
        "version": VERSION,
        "interpretation": interpret_text(req.text),
    }
