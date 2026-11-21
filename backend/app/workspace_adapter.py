"""Governed Workspace execution adapter (SC-SIM-01 G7).

Workspace owns orchestration, permissions, ExecutionRuns and receipts; Workbench keeps its calculations.
This adapter lets the Workspace job fabric call two existing Workbench calculations through one
authenticated endpoint, so their results get a Workspace runtime receipt and can be exported to Research:

- ``workspace.workbench.uncertainty-propagation`` -> v11150.execute_uncertainty (first-order propagation,
  seeded Monte Carlo, convergence study)
  or, when Workspace binds a dataset revision (``rows``), the same calculation once per row (SC-OUTPUT-02: a figure
  and table of one propagated quantity across the rows)
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
    if "rows" in payload:
        return _uncertainty_rows(payload)
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


ROWS_SCHEMA = "sc-workbench-uncertainty-rows-result/1.0"
MAX_ROWS = 200
ROW_OPERATIONS = {"first-order-independent", "monte-carlo"}


def _row_number(row: Dict[str, Any], field: str, index: int) -> float:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise HTTPException(status_code=422, detail=f"row {index}: field '{field}' must be a finite number")
    return float(value)


def _uncertainty_rows(payload: Dict[str, Any]) -> Dict[str, Any]:
    """SC-OUTPUT-02: the existing propagation, once per row of a dataset revision Workspace has re-hashed and bound.

    Each input is either a dataset field (``field``, with an optional ``sdField``) or a declared constant (``mean``,
    ``standardDeviation``). Every row is one ``execute_uncertainty`` call; nothing is computed here except reading the
    rows and reporting each call's own nominal value, standard deviation and interval.
    """
    rows = payload.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS or not all(isinstance(r, dict) for r in rows):
        raise HTTPException(status_code=422, detail=f"rows must be 1..{MAX_ROWS} records (bind a dataset revision)")
    operation = str(payload.get("operation") or "first-order-independent")
    if operation not in ROW_OPERATIONS:
        raise HTTPException(status_code=422, detail=f"operation must be one of {sorted(ROW_OPERATIONS)}")
    x_field = str(payload.get("xField") or "")
    inputs = payload.get("inputs")
    if not IDENTIFIER_RE.fullmatch(x_field) or not isinstance(inputs, list) or not 1 <= len(inputs) <= 20:
        raise HTTPException(status_code=422, detail="xField and 1..20 inputs are required")
    names = []
    for spec in inputs:
        if not isinstance(spec, dict) or not IDENTIFIER_RE.fullmatch(str(spec.get("name") or "")):
            raise HTTPException(status_code=422, detail="each input needs an identifier name")
        if ("field" in spec) == ("mean" in spec):
            raise HTTPException(status_code=422, detail=f"input {spec['name']}: give either a dataset field or a constant mean")
        names.append(spec["name"])
    if len(set(names)) != len(names):
        raise HTTPException(status_code=422, detail="input names must be unique")
    level = float(payload.get("confidenceLevel") or 0.95)
    if operation == "monte-carlo" and level != 0.95:
        raise HTTPException(status_code=422, detail="row intervals are the 2.5%-97.5% quantiles; confidenceLevel must be 0.95")
    out, hashes = [], []
    for i, row in enumerate(rows):
        resolved = []
        for spec in inputs:
            if "field" in spec:
                mean = _row_number(row, str(spec["field"]), i)
                sd = _row_number(row, str(spec["sdField"]), i) if spec.get("sdField") else 0.0
            else:
                mean, sd = float(spec["mean"]), float(spec.get("standardDeviation") or 0.0)
            resolved.append({"name": spec["name"], "mean": mean, "standardDeviation": sd})
        call = {"operation": operation, "expression": payload.get("expression"), "variables": names,
                "confidenceLevel": level}
        if operation == "first-order-independent":
            call.update(means=[r["mean"] for r in resolved], standardDeviations=[r["standardDeviation"] for r in resolved])
        else:
            call.update(inputs=resolved, samples=int(payload.get("samples") or 10000), seed=payload.get("seed"))
        body = _uncertainty(call)  # the scalar path: grammar check, then execute_uncertainty
        res = body["result"]
        if operation == "first-order-independent":
            value, sd = res["nominalValue"], res["outputStandardDeviation"]
            lower, upper = value - sd, value + sd
        else:
            summary = res["output"]
            value, sd = summary["mean"], summary["standardDeviation"]
            lower, upper = summary["quantiles"]["0.025"], summary["quantiles"]["0.975"]
        out.append({x_field: _row_number(row, x_field, i), "value": value, "standardUncertainty": sd,
                    "lower": lower, "upper": upper})
        hashes.append(body["resultHash"])
    interval = ("± one standard uncertainty (first-order Taylor propagation, independent inputs)"
                if operation == "first-order-independent" else "2.5%–97.5% quantiles of the seeded Monte Carlo draws")
    return {"schema": ROWS_SCHEMA, "operation": operation, "method": body["method"], "engine": body["engine"],
            "expression": payload.get("expression"), "inputs": inputs, "xField": x_field, "interval": interval,
            "rows": out, "rowResultHashes": hashes,
            **({"seed": payload.get("seed")} if operation == "monte-carlo" else {})}


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
