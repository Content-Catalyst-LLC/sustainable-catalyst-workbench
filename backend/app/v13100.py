"""Workbench v13.10.0 — Intent-to-Calculation Planning & Explainable Execution.

This layer turns v13.9 natural-language interpretations into explicit,
inspectable execution plans. It does not become a mathematics authority.
Canonical execution still occurs through the existing Calculator workspace.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1390 import interpret_text, natural_language_contract

VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v13100-intent-planning-explainable-execution"])

STATUS_SCHEMA = "sc-workbench-intent-planning-status/1.0"
PLAN_SCHEMA = "sc-workbench-intent-calculation-plan/1.0"
VALIDATION_SCHEMA = "sc-workbench-intent-plan-validation/1.0"
EXPLANATION_SCHEMA = "sc-workbench-explainable-execution/1.0"


class IntentPlanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    mode: Literal["conservative"] = "conservative"


class PlanValidationRequest(BaseModel):
    plan: Dict[str, Any]


class ExplainExecutionRequest(BaseModel):
    plan: Dict[str, Any]
    calculationObject: Dict[str, Any]


def _hash(x: Any) -> str:
    return content_hash(x)


def _steps_for(operation: Optional[str]) -> List[Dict[str, Any]]:
    base = [
        {
            "id": "interpret-intent",
            "kind": "interpretation",
            "label": "Interpret requested mathematical intent",
            "authority": "v13.9 natural-language interpretation",
            "executesMathematics": False,
        },
        {
            "id": "normalize-input",
            "kind": "normalization",
            "label": "Normalize mathematical notation conservatively",
            "authority": "v13.3 notation normalization",
            "executesMathematics": False,
        },
        {
            "id": "validate-request",
            "kind": "validation",
            "label": "Validate operation, variables, assumptions, and ambiguity state",
            "authority": "v13.10 planner",
            "executesMathematics": False,
        },
    ]
    if operation:
        base.append({
            "id": "execute-canonical",
            "kind": "execution",
            "label": f"Execute canonical {operation} calculation",
            "authority": "v11 Unified Calculation Engine through v12.3 Calculator Workspace",
            "executesMathematics": True,
        })
        base.append({
            "id": "explain-result",
            "kind": "explanation",
            "label": "Explain how the canonical result relates to the approved plan",
            "authority": "v13.10 explanation layer",
            "executesMathematics": False,
        })
    return base


def _assumptions(interp: Dict[str, Any]) -> List[Dict[str, Any]]:
    calc = (interp.get("proposedCalculationRequest") or {}).get("calculation") or {}
    operation = interp.get("intent")
    out: List[Dict[str, Any]] = []
    if operation in {"differentiate", "integrate-symbolic", "root", "solve"}:
        variable = calc.get("variable")
        out.append({
            "id": "primary-variable",
            "kind": "variable",
            "value": variable,
            "explicit": "variable-defaulted-to-x" not in (interp.get("ambiguities") or []),
            "description": f"Primary variable is {variable or 'unspecified'}.",
        })
    out.append({
        "id": "verification-required",
        "kind": "execution-policy",
        "value": True,
        "explicit": True,
        "description": "Canonical execution must request verification.",
    })
    out.append({
        "id": "provenance-required",
        "kind": "execution-policy",
        "value": True,
        "explicit": True,
        "description": "Canonical execution must preserve provenance.",
    })
    return out


def _alternatives(interp: Dict[str, Any]) -> List[Dict[str, Any]]:
    req = interp.get("proposedCalculationRequest")
    if not req:
        return []
    operation = interp.get("intent")
    calc = req.get("calculation") or {}
    alternatives: List[Dict[str, Any]] = [{
        "id": "primary",
        "label": f"Use interpreted {operation} request",
        "operation": operation,
        "calculationRequest": copy.deepcopy(req),
        "recommended": True,
        "reason": "Direct match to the recognized intent rule.",
    }]
    # Conservative, mechanically derived alternatives only.
    if operation == "evaluate":
        alt = copy.deepcopy(req)
        alt["calculation"]["operation"] = "exact"
        alt["requestedResultType"] = "exact"
        alternatives.append({
            "id": "exact-alternative",
            "label": "Evaluate exactly instead of numerically",
            "operation": "exact",
            "calculationRequest": alt,
            "recommended": False,
            "reason": "Same expression with exact-result semantics.",
        })
    elif operation == "exact":
        alt = copy.deepcopy(req)
        alt["calculation"]["operation"] = "evaluate"
        alt["requestedResultType"] = "numeric"
        alternatives.append({
            "id": "numeric-alternative",
            "label": "Evaluate numerically instead of exactly",
            "operation": "evaluate",
            "calculationRequest": alt,
            "recommended": False,
            "reason": "Same expression with numeric-result semantics.",
        })
    elif operation == "root":
        alt = copy.deepcopy(req)
        alt["calculation"]["operation"] = "solve"
        alt["requestedResultType"] = "symbolic"
        alt["calculation"].pop("initialGuess", None)
        alternatives.append({
            "id": "symbolic-solve-alternative",
            "label": "Try symbolic solve",
            "operation": "solve",
            "calculationRequest": alt,
            "recommended": False,
            "reason": "Same expression and variable using symbolic equation solving.",
        })
    return alternatives


def _validation_for(interp: Dict[str, Any]) -> Dict[str, Any]:
    req = interp.get("proposedCalculationRequest")
    ambiguities = list(interp.get("ambiguities") or [])
    blockers = [
        x for x in ambiguities
        if x in {
            "unrecognized-natural-language-intent",
            "implicit-multiplication-not-expanded",
            "adjacent-parentheses-multiplication-not-expanded",
        }
    ]
    warnings = [x for x in ambiguities if x not in blockers]
    checks = {
        "intentRecognized": interp.get("intent") is not None,
        "calculationRequestPresent": req is not None,
        "canonicalExecutionRequested": bool(req and req.get("requireVerification") and req.get("requireProvenance")),
        "noBlockingAmbiguity": not blockers,
        "confirmationStillRequired": True,
    }
    executable_after_confirmation = (
        all(v for k, v in checks.items() if k != "confirmationStillRequired")
        and bool(req)
    )
    body = {
        "schema": VALIDATION_SCHEMA,
        "version": VERSION,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "valid": executable_after_confirmation,
        "executableAfterConfirmation": executable_after_confirmation,
        "requiresConfirmation": True,
    }
    body["validationHash"] = _hash(body)
    return body


def build_plan(text: str) -> Dict[str, Any]:
    interp = interpret_text(text)
    validation = _validation_for(interp)
    req = interp.get("proposedCalculationRequest")
    plan = {
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "originalText": text,
        "intent": interp.get("intent"),
        "confidence": interp.get("confidence"),
        "matchedRule": interp.get("matchedRule"),
        "interpretationHash": interp.get("interpretationHash"),
        "normalization": interp.get("normalization"),
        "ambiguities": interp.get("ambiguities") or [],
        "assumptions": _assumptions(interp),
        "alternatives": _alternatives(interp),
        "selectedAlternativeId": "primary" if req else None,
        "selectedCalculationRequest": copy.deepcopy(req),
        "steps": _steps_for(interp.get("intent")),
        "validation": validation,
        "policy": {
            "directPlannerExecution": False,
            "userConfirmationRequired": True,
            "canonicalCalculationEngineRequired": True,
            "plannerMayExplainButNotChangeResult": True,
        },
    }
    plan["planHash"] = _hash({
        "originalText": plan["originalText"],
        "intent": plan["intent"],
        "interpretationHash": plan["interpretationHash"],
        "selectedCalculationRequest": plan["selectedCalculationRequest"],
        "assumptions": plan["assumptions"],
        "steps": plan["steps"],
        "validationHash": validation["validationHash"],
    })
    return plan


def validate_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    selected = plan.get("selectedCalculationRequest")
    blockers: List[str] = []
    warnings: List[str] = list((plan.get("validation") or {}).get("warnings") or [])
    if plan.get("schema") != PLAN_SCHEMA:
        blockers.append("unsupported-plan-schema")
    if not selected:
        blockers.append("missing-selected-calculation-request")
    else:
        calc = selected.get("calculation") or {}
        if not calc.get("operation"):
            blockers.append("missing-operation")
        if not calc.get("expression"):
            blockers.append("missing-expression")
        if not selected.get("requireVerification"):
            blockers.append("verification-must-remain-enabled")
        if not selected.get("requireProvenance"):
            blockers.append("provenance-must-remain-enabled")
    supplied_hash = plan.get("planHash")
    recomputed = _hash({
        "originalText": plan.get("originalText"),
        "intent": plan.get("intent"),
        "interpretationHash": plan.get("interpretationHash"),
        "selectedCalculationRequest": plan.get("selectedCalculationRequest"),
        "assumptions": plan.get("assumptions"),
        "steps": plan.get("steps"),
        "validationHash": (plan.get("validation") or {}).get("validationHash"),
    })
    if supplied_hash and supplied_hash != recomputed:
        blockers.append("plan-hash-mismatch")
    result = {
        "schema": VALIDATION_SCHEMA,
        "version": VERSION,
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "requiresConfirmation": True,
        "canonicalExecutionEndpoint": "/standalone/v1/calculator/execute",
        "planHash": supplied_hash,
        "recomputedPlanHash": recomputed,
    }
    result["validationHash"] = _hash(result)
    return result


def explain_execution(plan: Dict[str, Any], calculation_object: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_plan(plan)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail={"message": "Plan is not valid", "validation": validation})
    selected = plan["selectedCalculationRequest"]
    requested = selected.get("calculation") or {}
    execution_plan = calculation_object.get("executionPlan") or {}
    verification = calculation_object.get("verification") or {}
    provenance = calculation_object.get("provenance") or {}
    exact = calculation_object.get("exactResult")
    approx = calculation_object.get("approximateResult")
    result_summary = exact if exact is not None else approx
    explanation = {
        "schema": EXPLANATION_SCHEMA,
        "version": VERSION,
        "planHash": plan.get("planHash"),
        "calculationObjectHash": calculation_object.get("calculationObjectHash"),
        "intent": plan.get("intent"),
        "requestedOperation": requested.get("operation"),
        "requestedExpression": requested.get("expression"),
        "resultSummary": result_summary,
        "execution": {
            "runtime": execution_plan.get("runtime"),
            "method": execution_plan.get("method"),
            "solver": execution_plan.get("solver"),
            "tolerances": execution_plan.get("tolerances"),
        },
        "verification": {
            "reported": bool(verification),
            "status": verification.get("status"),
            "passed": verification.get("passed"),
        },
        "provenance": {
            "reported": bool(provenance),
            "provenanceHash": provenance.get("provenanceHash"),
        },
        "narrative": [
            f"Workbench interpreted the request as '{plan.get('intent')}'.",
            "The user-approved plan was handed to the canonical Calculator execution endpoint.",
            f"The canonical engine executed operation '{requested.get('operation')}' without the planner modifying the mathematical result.",
            "Verification and provenance are reported from the CalculationObject, not invented by the explanation layer.",
        ],
        "policy": {
            "resultAuthority": "CalculationObject",
            "plannerResultMutation": False,
            "explanationIsDerived": True,
        },
    }
    explanation["explanationHash"] = _hash(explanation)
    return explanation


def planning_contract() -> Dict[str, Any]:
    prior = natural_language_contract()
    features = {
        "v139InterpretationPreserved": all(prior["features"].values()),
        "explicitPlanObject": True,
        "multiStagePlan": True,
        "deterministicAlternatives": True,
        "assumptionDisclosure": True,
        "variableResolutionDisclosure": True,
        "preExecutionValidation": True,
        "blockingAmbiguityDetection": True,
        "planHashAndLineage": True,
        "canonicalExecutionHandoff": True,
        "postExecutionExplanation": True,
        "calculationObjectRemainsResultAuthority": True,
        "plannerCannotMutateResult": True,
        "userConfirmationRequired": True,
        "wordpressRequiredFalse": True,
    }
    body = {
        "schema": "sc-workbench-intent-planning-contract/1.0",
        "version": VERSION,
        "features": features,
        "canonicalExecutionAuthority": "v11 Unified Calculation Engine through v12.3 Calculator Workspace",
        "plannerAuthority": "intent interpretation, plan construction, validation, explanation only",
        "wordpressRequired": False,
    }
    body["contractHash"] = _hash(body)
    return body


def status() -> Dict[str, Any]:
    c = planning_contract()
    checks = {
        "intentPlanningReady": all(c["features"].values()),
        "v139InterpretationPreserved": c["features"]["v139InterpretationPreserved"],
        "canonicalCalculationAuthorityPreserved": c["features"]["calculationObjectRemainsResultAuthority"],
        "plannerCannotMutateResult": c["features"]["plannerCannotMutateResult"],
        "userConfirmationRequired": c["features"]["userConfirmationRequired"],
        "wordpressRequiredFalse": c["wordpressRequired"] is False,
    }
    return {
        "ok": all(checks.values()),
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Intent-to-Calculation Planning & Explainable Execution",
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "intentPlanningReady": all(checks.values()),
        "checks": checks,
        "contractHash": c["contractHash"],
    }


@router.get("/v13100/status")
def status_route():
    return status()


@router.get("/standalone/v1/intent-planning/contract")
def contract_route():
    return {"ok": True, "version": VERSION, "planning": planning_contract()}


@router.post("/standalone/v1/intent-planning/plan")
def plan_route(req: IntentPlanRequest):
    return {"ok": True, "version": VERSION, "plan": build_plan(req.text)}


@router.post("/standalone/v1/intent-planning/validate")
def validate_route(req: PlanValidationRequest):
    return {"ok": True, "version": VERSION, "validation": validate_plan(req.plan)}


@router.post("/standalone/v1/intent-planning/explain")
def explain_route(req: ExplainExecutionRequest):
    return {
        "ok": True,
        "version": VERSION,
        "explanation": explain_execution(req.plan, req.calculationObject),
    }
