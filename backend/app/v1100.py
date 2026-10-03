"""Workbench v11.0.0 — Unified Calculation Engine & Calculation Object Foundation.

Defines the canonical CalculationObject used by the v11 calculator program.
All calculator capabilities normalize into this object before/after execution.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v10100 import CalculationRequest, PlanRequest, execute as execute_legacy, plan as plan_legacy
from .v510 import content_hash

VERSION = APP_VERSION

STATUS_SCHEMA = "sc-workbench-unified-calculation-engine-status/1.0"
OBJECT_SCHEMA = "sc-workbench-calculation-object/1.0"
REQUEST_SCHEMA = "sc-workbench-unified-calculation-request/1.0"
PLAN_SCHEMA = "sc-workbench-unified-calculation-execution-plan/1.0"
RESULT_SCHEMA = "sc-workbench-unified-calculation-result/1.0"

router = APIRouter(tags=["workbench-v1100-unified-calculation-engine"])


class AssumptionSpec(BaseModel):
    symbol: str = Field(max_length=200)
    assumption: str = Field(max_length=500)
    value: Optional[Any] = None


class QuantitySpec(BaseModel):
    expression: Optional[str] = Field(default=None, max_length=2000)
    targetUnit: Optional[str] = Field(default=None, max_length=300)


class UnifiedCalculationRequest(BaseModel):
    calculation: CalculationRequest
    assumptions: List[AssumptionSpec] = Field(default_factory=list, max_length=200)
    quantities: List[QuantitySpec] = Field(default_factory=list, max_length=100)
    domain: Optional[str] = Field(default=None, max_length=500)
    objective: str = Field(default="", max_length=5000)
    requestedResultType: Literal[
        "auto", "exact", "numeric", "symbolic", "quantity", "matrix", "timeseries"
    ] = "auto"
    preferredRuntime: Literal["auto", "python", "julia", "haskell", "native"] = "auto"
    requireVerification: bool = True
    requireProvenance: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def normalize_request(req: UnifiedCalculationRequest) -> Dict[str, Any]:
    calc = req.calculation.model_dump(mode="json")
    normalized = {
        "schema": REQUEST_SCHEMA,
        "version": VERSION,
        "operation": calc["operation"],
        "expression": calc.get("expression"),
        "variable": calc.get("variable"),
        "variables": calc.get("variables") or [],
        "values": calc.get("values") or {},
        "domain": calc.get("domain"),
        "initialGuess": calc.get("initialGuess"),
        "bracket": calc.get("bracket"),
        "matrix": calc.get("matrix"),
        "vector": calc.get("vector"),
        "matrixOperation": calc.get("matrixOperation"),
        "initialState": calc.get("initialState"),
        "timeSpan": calc.get("timeSpan"),
        "unitExpression": calc.get("unitExpression"),
        "targetUnit": calc.get("targetUnit"),
        "precision": calc.get("precision"),
        "randomSeed": calc.get("randomSeed"),
        "notes": calc.get("notes"),
        "assumptions": [x.model_dump(mode="json") for x in req.assumptions],
        "quantities": [x.model_dump(mode="json") for x in req.quantities],
        "declaredDomain": req.domain,
        "objective": req.objective,
        "requestedResultType": req.requestedResultType,
        "preferredRuntime": req.preferredRuntime,
        "requireVerification": req.requireVerification,
        "requireProvenance": req.requireProvenance,
        "metadata": req.metadata,
    }
    normalized["inputHash"] = _hash(normalized)
    return normalized


def build_execution_plan(req: UnifiedCalculationRequest) -> Dict[str, Any]:
    op = req.calculation.operation

    if req.preferredRuntime == "julia":
        selected = "julia"
        runtime_note = "Julia scientific runtime active from Workbench v11.5.0."
    elif req.preferredRuntime == "haskell":
        selected = "python"
        runtime_note = "Haskell requested but verification runtime is not active in v11.0.0."
    elif req.preferredRuntime == "native":
        selected = "python"
        runtime_note = "Native runtime requested but no native calculation adapter is active in v11.0.0."
    else:
        selected = "python"
        runtime_note = "Canonical Python runtime selected."

    if op in {"exact", "simplify", "solve", "differentiate", "integrate-symbolic"}:
        engine = "sympy"
        method_family = "symbolic"
    elif op == "matrix":
        engine = "numpy"
        method_family = "linear-algebra"
    elif op == "units":
        engine = "pint"
        method_family = "units"
    else:
        engine = "scipy"
        method_family = "numerical"

    legacy_plan = plan_legacy(PlanRequest(
        operation=op,
        expression=req.calculation.expression,
        objective=req.objective,
        requireExactWhenPossible=req.requestedResultType in {"auto", "exact", "symbolic"},
        requireUnits=op == "units" or bool(req.quantities),
        requireUncertainty=False,
        preferredRuntime="auto",
    ))

    plan = {
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "planner": "unified-calculation-planner/1.0",
        "selectedRuntime": selected,
        "selectedEngine": engine,
        "methodFamily": method_family,
        "runtimeNote": runtime_note,
        "preferredRuntime": req.preferredRuntime,
        "fallbackPolicy": ["python"],
        "automaticExecution": True,
        "legacyPlanner": legacy_plan,
        "futureRuntimeSlots": {
            "julia": {
                "enabled": True,
                "intendedFor": ["linear-algebra", "statistics", "ode", "sde", "dae", "optimization", "simulation", "scientific-ml"],
            },
            "haskell": {
                "enabled": False,
                "intendedFor": ["typed-ir-validation", "transformation-verification", "dimension-contracts"],
            },
            "native": {
                "enabled": False,
                "intendedFor": ["performance-kernels"],
            },
        },
    }
    plan["executionPlanHash"] = _hash(
        {k: v for k, v in plan.items() if k != "executionPlanHash"}
    )
    return plan


def build_calculation_object(req: UnifiedCalculationRequest) -> Dict[str, Any]:
    normalized = normalize_request(req)
    plan = build_execution_plan(req)
    legacy_result = execute_legacy(req.calculation)

    result = {
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "engine": legacy_result.get("engine"),
        "method": legacy_result.get("method"),
        "operation": legacy_result.get("operation"),
        "value": legacy_result.get("result"),
        "precision": legacy_result.get("precision"),
        "diagnostics": legacy_result.get("diagnostics"),
        "legacyCalculationHash": legacy_result.get("calculationHash"),
        "wordpressRequired": False,
    }
    result["resultHash"] = _hash(
        {k: v for k, v in result.items() if k != "resultHash"}
    )

    verification = {
        "requested": req.requireVerification,
        "status": "verified-by-canonical-runtime" if req.requireVerification else "not-requested",
        "checks": {
            "executionSucceeded": legacy_result.get("ok") is True,
            "resultPresent": "result" in legacy_result,
            "runtimeMatchesPlan": plan["selectedRuntime"] == "python",
            "wordpressNotRequired": legacy_result.get("wordpressRequired") is False,
        },
    }
    verification["verificationHash"] = _hash(verification)

    provenance = {
        "requested": req.requireProvenance,
        "canonicalBackend": "FastAPI",
        "runtime": RUNTIME_KIND,
        "workbenchVersion": VERSION,
        "engine": result["engine"],
        "method": result["method"],
        "inputHash": normalized["inputHash"],
        "executionPlanHash": plan["executionPlanHash"],
        "resultHash": result["resultHash"],
        "legacyCalculationHash": result["legacyCalculationHash"],
        "wordpressRequired": False,
    }
    provenance["provenanceHash"] = _hash(provenance)

    obj = {
        "ok": True,
        "schema": OBJECT_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "application": PRODUCT_NAME,
        "objectType": "calculation",
        "input": normalized,
        "assumptions": normalized["assumptions"],
        "domain": {
            "declared": normalized["declaredDomain"],
            "operationDomain": normalized["domain"],
        },
        "units": {
            "quantities": normalized["quantities"],
            "unitExpression": normalized["unitExpression"],
            "targetUnit": normalized["targetUnit"],
        },
        "precision": normalized["precision"],
        "executionPlan": plan,
        "result": result,
        "verification": verification,
        "visualizations": [],
        "provenance": provenance,
        "reproducibility": {
            "deterministicInputHash": normalized["inputHash"],
            "executionPlanHash": plan["executionPlanHash"],
            "resultHash": result["resultHash"],
            "provenanceHash": provenance["provenanceHash"],
        },
        "wordpressRequired": False,
    }
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def object_schema_contract() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": OBJECT_SCHEMA,
        "version": VERSION,
        "objectType": "calculation",
        "requiredSections": [
            "input",
            "assumptions",
            "domain",
            "units",
            "precision",
            "executionPlan",
            "result",
            "verification",
            "visualizations",
            "provenance",
            "reproducibility",
        ],
        "extensionPolicy": {
            "additiveFieldsAllowed": True,
            "runtimeSpecificDetailsBelongInExecutionPlan": True,
            "domainSpecificDetailsBelongInExtensions": True,
            "calculationObjectHashMustCoverCanonicalContent": True,
            "wordpressRequired": False,
        },
        "futureRuntimeModel": {
            "python": "active-canonical",
            "julia": "active-scientific",
            "haskell": "reserved-verification",
            "native": "reserved",
        },
    }
    body["schemaContractHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "schemaContractHash"}}
    )
    return body


def status() -> Dict[str, Any]:
    contract = object_schema_contract()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Unified Calculation Engine & Calculation Object Foundation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "canonicalCalculationObject": OBJECT_SCHEMA,
        "canonicalPlanner": "unified-calculation-planner/1.0",
        "activeRuntimes": ["python", "julia"],
        "reservedRuntimes": ["haskell", "native"],
        "capabilities": {
            "normalizedCalculationInput": True,
            "assumptionCapture": True,
            "domainCapture": True,
            "unitCapture": True,
            "precisionCapture": True,
            "executionPlanning": True,
            "verificationEnvelope": True,
            "provenanceEnvelope": True,
            "reproducibilityHashes": True,
            "futureRuntimeSlots": True,
            "standaloneFirst": True,
        },
        "schemaContractHash": contract["schemaContractHash"],
    }


@router.get("/v1100/status")
def status_route():
    return status()


@router.get("/calculation-engine/v1/schema")
def calculation_object_schema_route():
    return object_schema_contract()


@router.post("/calculation-engine/v1/normalize")
def calculation_normalize_route(req: UnifiedCalculationRequest):
    return {
        "ok": True,
        "schema": REQUEST_SCHEMA,
        "version": VERSION,
        "normalized": normalize_request(req),
    }


@router.post("/calculation-engine/v1/plan")
def calculation_plan_route(req: UnifiedCalculationRequest):
    return {
        "ok": True,
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "executionPlan": build_execution_plan(req),
    }


@router.post("/calculation-engine/v1/compute")
def calculation_compute_route(req: UnifiedCalculationRequest):
    return build_calculation_object(req)
