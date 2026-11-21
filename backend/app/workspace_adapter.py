"""Governed Workspace execution adapter (SC-SIM-01 G7).

Workspace owns orchestration, permissions, ExecutionRuns and receipts; Workbench keeps its calculations.
This adapter lets the Workspace job fabric call two existing Workbench calculations through one
authenticated endpoint, so their results get a Workspace runtime receipt and can be exported to Research:

- ``workspace.workbench.uncertainty-propagation`` -> v11150.execute_uncertainty (first-order propagation,
  seeded Monte Carlo, convergence study)
- ``workspace.workbench.dynamical-simulation`` -> v750.run_simulation (scalar dynamics, linear state space,
  ODE IVP)

No algorithm is reimplemented here. Calculations called any other way (browser engines, direct routes)
remain exploratory: they have no Workspace receipt and cannot be cited as verified evidence.
"""
from __future__ import annotations

import hmac
import os
import platform
import re
from typing import Any, Callable, Dict

import numpy as np
import scipy
import sympy as sp
from fastapi import APIRouter, Header, HTTPException
from pydantic import ValidationError

from .release import APP_VERSION
from .v750 import SimulationRequest, run_simulation
from .v11150 import UncertaintyRequest, execute_uncertainty

ENVELOPE_SCHEMA = "sc-workspace-polyglot-execution-envelope/1.0"
RESULT_SCHEMA = "sc-workbench-workspace-adapter-result/1.0"
RUNTIME = "workbench-calculation-engine"
TOKEN_ENV = "SC_WORKBENCH_WORKSPACE_ADAPTER_TOKEN"
MAX_EXPRESSION_CHARS = 4000
# The Workspace symbolic grammar: no attribute access, indexing, strings or statements reach sympify.
EXPRESSION_RE = re.compile(r"[A-Za-z0-9_+\-*/^()., \t]+")
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ALLOWED_NAMES = {"sin", "cos", "tan", "exp", "log", "sqrt", "Abs", "abs", "pi", "E"}

router = APIRouter(tags=["workbench-workspace-execution-adapter"])


def _uncertainty(payload: Dict[str, Any]) -> Dict[str, Any]:
    expression = str(payload.get("expression") or "")
    if len(expression) > MAX_EXPRESSION_CHARS or "__" in expression or not EXPRESSION_RE.fullmatch(expression):
        raise HTTPException(status_code=422, detail="expression is outside the governed symbolic grammar")
    declared = {str(v) for v in payload.get("variables") or []} | {
        str(x.get("name")) for x in payload.get("inputs") or [] if isinstance(x, dict)}
    unknown = sorted(set(IDENTIFIER_RE.findall(expression)) - declared - ALLOWED_NAMES)
    if unknown:
        raise HTTPException(status_code=422, detail=f"undeclared identifiers in expression: {', '.join(unknown[:8])}")
    body = execute_uncertainty(UncertaintyRequest.model_validate(payload))
    if body["operation"] in {"monte-carlo", "monte-carlo-convergence"}:
        # Seeded draws: echo the seed where Workspace looks for it, so a same-seed replay is never a reproduction.
        body = {**body, "seed": body["result"].get("seed")}
    return body


def _dynamics(payload: Dict[str, Any]) -> Dict[str, Any]:
    request = SimulationRequest.model_validate(payload)
    if request.simulationKind == "digital-twin":
        raise HTTPException(status_code=422, detail="digital-twin calibration is not a governed adapter operation")
    return run_simulation(request)


OPERATIONS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "workspace.workbench.uncertainty-propagation": _uncertainty,
    "workspace.workbench.dynamical-simulation": _dynamics,
}


def numerical_libraries() -> Dict[str, Any]:
    deps: Dict[str, Any] = {}
    try:
        deps = np.show_config(mode="dicts").get("Build Dependencies") or {}
    except Exception:  # pragma: no cover - older NumPy
        deps = {}
    out: Dict[str, Any] = {"source": "build-configuration", "runtime": f"workbench {APP_VERSION}",
                           "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                           "sympy": sp.__version__, "precision": "ieee754-binary64"}
    for key in ("blas", "lapack"):
        dep = deps.get(key) if isinstance(deps.get(key), dict) else {}
        out[key] = {"name": str(dep.get("name") or "unrecorded"), "version": str(dep.get("version") or "unrecorded")}
    return out


def _authorize(authorization: str | None) -> None:
    token = os.getenv(TOKEN_ENV, "").strip()
    if not token:
        raise HTTPException(status_code=503, detail="Workspace execution adapter is not configured")
    if not authorization or not hmac.compare_digest(authorization.strip().encode(), f"Bearer {token}".encode()):
        raise HTTPException(status_code=401, detail="Workspace execution adapter authentication failed")


@router.get("/v1/workspace/adapter")
def adapter_status() -> Dict[str, Any]:
    return {"schema": "sc-workbench-workspace-adapter-status/1.0", "runtime": RUNTIME, "version": APP_VERSION,
            "operations": sorted(OPERATIONS), "configured": bool(os.getenv(TOKEN_ENV, "").strip()),
            "arbitraryCodeExecution": False, "receiptAuthority": "workspace"}


@router.post("/v1/workspace/execute")
def execute(envelope: Dict[str, Any], authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    _authorize(authorization)
    if envelope.get("schema") != ENVELOPE_SCHEMA or envelope.get("language") != "workbench":
        raise HTTPException(status_code=400, detail="Unsupported Workspace execution envelope")
    if envelope.get("arbitraryCodeExecution") is not False:
        raise HTTPException(status_code=400, detail="Arbitrary-code execution must remain disabled")
    operation = str(envelope.get("operation") or "")
    handler = OPERATIONS.get(operation)
    if handler is None:
        raise HTTPException(status_code=400, detail="Workbench operation is not a governed adapter operation")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be an object")
    try:
        result = handler(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=[{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()[:16]]) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)[:400]) from exc
    return {"ok": True, "schema": RESULT_SCHEMA, "runtime": RUNTIME, "operation": operation,
            "requestFingerprint": envelope.get("requestFingerprint"), "numericalLibraries": numerical_libraries(),
            "boundedOperationsOnly": True, "arbitraryCodeExecution": False, "result": result}
