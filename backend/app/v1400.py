"""Workbench v14.0.0 — Computational Workflow & Multi-Step Calculation Composer.

Defines a first-class workflow object for chaining canonical calculations.
Workflow orchestration never becomes a second mathematics authority: every step
is an explicit UnifiedCalculationRequest and execution is delegated to the
existing v11 calculation engine through the standalone calculator service.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v13120 import status as v13_certification_status

VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v1400-computational-workflow-composer"])
STATUS_SCHEMA = "sc-workbench-computational-workflow-status/1.0"
WORKFLOW_SCHEMA = "sc-workbench-computational-workflow/1.0"
VALIDATION_SCHEMA = "sc-workbench-computational-workflow-validation/1.0"
EXECUTION_SCHEMA = "sc-workbench-computational-workflow-execution/1.0"

_REF_RE = re.compile(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\.result\}")


class WorkflowStep(BaseModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    title: str = Field(default="Calculation step", min_length=1, max_length=240)
    calculationRequest: UnifiedCalculationRequest
    dependsOn: List[str] = Field(default_factory=list, max_length=100)
    description: str = Field(default="", max_length=1000)


class WorkflowDefinitionRequest(BaseModel):
    title: str = Field(default="Computational Workflow", min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    steps: List[WorkflowStep] = Field(min_length=1, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecuteRequest(BaseModel):
    workflow: Dict[str, Any]


def _hash(x: Any) -> str:
    return content_hash(x)


def _dependencies(step: Dict[str, Any]) -> Set[str]:
    deps = set(step.get("dependsOn") or [])
    expression = ((step.get("calculationRequest") or {}).get("calculation") or {}).get("expression") or ""
    deps.update(_REF_RE.findall(expression))
    return deps


def _topological_order(steps: List[Dict[str, Any]]) -> List[str]:
    ids = [s["id"] for s in steps]
    incoming = {s["id"]: set(_dependencies(s)) for s in steps}
    order: List[str] = []
    ready = sorted([sid for sid in ids if not incoming[sid]])
    while ready:
        sid = ready.pop(0)
        order.append(sid)
        for other in ids:
            if sid in incoming[other]:
                incoming[other].remove(sid)
                if not incoming[other] and other not in order and other not in ready:
                    ready.append(other)
                    ready.sort()
    if len(order) != len(ids):
        return []
    return order


def validate_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    blockers: List[str] = []
    warnings: List[str] = []
    steps = list(workflow.get("steps") or [])
    ids = [s.get("id") for s in steps]
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    if not steps:
        blockers.append("workflow-has-no-steps")
    if duplicates:
        blockers.append("duplicate-step-ids:" + ",".join(duplicates))
    known = set(ids)
    for step in steps:
        sid = step.get("id")
        req = step.get("calculationRequest") or {}
        calc = req.get("calculation") or {}
        if not calc.get("operation"):
            blockers.append(f"{sid}:missing-operation")
        if not calc.get("expression"):
            blockers.append(f"{sid}:missing-expression")
        if req.get("requireVerification") is not True:
            blockers.append(f"{sid}:verification-required")
        if req.get("requireProvenance") is not True:
            blockers.append(f"{sid}:provenance-required")
        for dep in sorted(_dependencies(step)):
            if dep not in known:
                blockers.append(f"{sid}:unknown-dependency:{dep}")
            if dep == sid:
                blockers.append(f"{sid}:self-dependency")
    order = _topological_order(steps) if steps and not duplicates else []
    if steps and not order:
        blockers.append("workflow-cycle-detected")
    if len(steps) == 1:
        warnings.append("single-step-workflow")
    body = {
        "schema": VALIDATION_SCHEMA,
        "version": VERSION,
        "valid": not blockers,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "topologicalOrder": order,
        "stepCount": len(steps),
        "canonicalExecutionOnly": True,
    }
    body["validationHash"] = _hash(body)
    return body


def compose_workflow(req: WorkflowDefinitionRequest) -> Dict[str, Any]:
    steps = [s.model_dump() for s in req.steps]
    workflow = {
        "schema": WORKFLOW_SCHEMA,
        "version": VERSION,
        "title": req.title,
        "description": req.description,
        "steps": steps,
        "metadata": req.metadata,
        "policy": {
            "workflowExecutesMathDirectly": False,
            "canonicalCalculationEngineRequired": True,
            "verificationRequiredPerStep": True,
            "provenanceRequiredPerStep": True,
            "deterministicDependencyResolution": True,
        },
    }
    workflow["validation"] = validate_workflow(workflow)
    workflow["workflowHash"] = _hash({
        "title": workflow["title"],
        "description": workflow["description"],
        "steps": workflow["steps"],
        "metadata": workflow["metadata"],
        "policy": workflow["policy"],
    })
    return workflow


def _result_literal(obj: Dict[str, Any]) -> str:
    # Return a scalar suitable for ${stepId.result} substitution.
    #
    # Canonical CalculationObject stores the legacy engine payload at
    # calculationObject.result.value. For evaluate/numeric operations that
    # payload is itself structured, e.g. {"value": "5.0", "float": 5.0}.
    # Workflow substitution must extract the scalar rather than stringify the
    # entire result envelope.
    result = obj.get("result")

    if isinstance(result, dict):
        payload = result.get("value")

        if isinstance(payload, dict):
            # Prefer an actual numeric scalar when the canonical runtime
            # provides one; otherwise accept scalar textual representations.
            for key in ("float", "value", "decimal", "exact", "root", "fun"):
                value = payload.get(key)
                if isinstance(value, (int, float, str)) and not isinstance(value, bool):
                    return str(value)

        if isinstance(payload, (int, float, str)) and not isinstance(payload, bool):
            return str(payload)

    # Compatibility with older/alternate flat calculation envelopes.
    for key in ("exactResult", "approximateResult"):
        value = obj.get(key)
        if isinstance(value, (int, float, str)) and not isinstance(value, bool):
            return str(value)

    if isinstance(result, (int, float, str)) and not isinstance(result, bool):
        return str(result)

    raise HTTPException(
        status_code=422,
        detail=(
            "Workflow step result is not a substitutable scalar. "
            "Use ${stepId.result} only with scalar-producing calculation steps."
        ),
    )


def execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_workflow(workflow)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail={"message": "Workflow validation failed", "validation": validation})
    by_id = {s["id"]: s for s in workflow["steps"]}
    results: Dict[str, Dict[str, Any]] = {}
    execution_steps: List[Dict[str, Any]] = []
    for sid in validation["topologicalOrder"]:
        step = by_id[sid]
        request = dict(step["calculationRequest"])
        calculation = dict(request["calculation"])
        expression = calculation["expression"]
        substitutions = []
        for dep in sorted(_dependencies(step)):
            literal = _result_literal(results[dep])
            token = "${" + dep + ".result}"
            if token in expression:
                expression = expression.replace(token, f"({literal})")
                substitutions.append({"token": token, "stepId": dep, "value": literal})
        calculation["expression"] = expression
        request["calculation"] = calculation
        canonical = build_calculation_object(UnifiedCalculationRequest.model_validate(request))
        results[sid] = canonical
        execution_steps.append({
            "stepId": sid,
            "title": step.get("title"),
            "dependsOn": sorted(_dependencies(step)),
            "resolvedExpression": expression,
            "substitutions": substitutions,
            "calculationObject": canonical,
            "calculationObjectHash": canonical.get("calculationObjectHash"),
        })
    execution = {
        "schema": EXECUTION_SCHEMA,
        "version": VERSION,
        "workflowHash": workflow.get("workflowHash"),
        "validationHash": validation["validationHash"],
        "topologicalOrder": validation["topologicalOrder"],
        "steps": execution_steps,
        "stepCount": len(execution_steps),
        "policy": {
            "canonicalCalculationObjectAuthority": True,
            "workflowOrchestratorMutatesResults": False,
            "perStepVerificationRequired": True,
            "perStepProvenanceRequired": True,
        },
    }
    execution["executionHash"] = _hash({
        "workflowHash": execution["workflowHash"],
        "topologicalOrder": execution["topologicalOrder"],
        "steps": [
            {"stepId": x["stepId"], "calculationObjectHash": x["calculationObjectHash"], "resolvedExpression": x["resolvedExpression"]}
            for x in execution_steps
        ],
    })
    return execution


def workflow_contract() -> Dict[str, Any]:
    v13 = v13_certification_status()
    features = {
        "v13ProductionCertificationPreserved": bool(v13.get("standaloneFunctionalProductionCertified")),
        "firstClassWorkflowObject": True,
        "multiStepComposition": True,
        "explicitStepDependencies": True,
        "resultReferenceSubstitution": True,
        "cycleDetection": True,
        "unknownDependencyDetection": True,
        "deterministicTopologicalOrdering": True,
        "workflowHash": True,
        "validationHash": True,
        "executionHash": True,
        "canonicalCalculationObjectsPerStep": True,
        "perStepVerification": True,
        "perStepProvenance": True,
        "workflowIsNotMathAuthority": True,
        "wordpressRequiredFalse": True,
    }
    body = {
        "schema": "sc-workbench-computational-workflow-contract/1.0",
        "version": VERSION,
        "features": features,
        "referenceSyntax": "${stepId.result}",
        "canonicalExecutionAuthority": "v11 Unified Calculation Engine through v12.3 Calculator Workspace",
        "wordpressRequired": False,
    }
    body["contractHash"] = _hash(body)
    return body


def status() -> Dict[str, Any]:
    c = workflow_contract()
    checks = {
        "computationalWorkflowComposerReady": all(c["features"].values()),
        "v13ProductionCertificationPreserved": c["features"]["v13ProductionCertificationPreserved"],
        "canonicalCalculationAuthorityPreserved": c["features"]["canonicalCalculationObjectsPerStep"],
        "workflowIsNotMathAuthority": c["features"]["workflowIsNotMathAuthority"],
        "wordpressRequiredFalse": c["wordpressRequired"] is False,
    }
    return {
        "ok": all(checks.values()),
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Computational Workflow & Multi-Step Calculation Composer",
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "computationalWorkflowComposerReady": all(checks.values()),
        "checks": checks,
        "contractHash": c["contractHash"],
    }


@router.get("/v1400/status")
def status_route():
    return status()


@router.get("/standalone/v1/workflows/contract")
def contract_route():
    return {"ok": True, "version": VERSION, "workflow": workflow_contract()}


@router.post("/standalone/v1/workflows/compose")
def compose_route(req: WorkflowDefinitionRequest):
    return {"ok": True, "version": VERSION, "workflow": compose_workflow(req)}


@router.post("/standalone/v1/workflows/validate")
def validate_route(workflow: Dict[str, Any]):
    return {"ok": True, "version": VERSION, "validation": validate_workflow(workflow)}


@router.post("/standalone/v1/workflows/execute")
def execute_route(req: WorkflowExecuteRequest):
    return {"ok": True, "version": VERSION, "execution": execute_workflow(req.workflow)}
