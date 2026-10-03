"""Workbench v11.18.0 — Multi-Runtime Calculation Certification.

Certifies numerical equivalence across the canonical Python reference runtime
and the structured Julia scientific runtime. Runtime identity, tolerances,
fallback state, normalized results, divergences, and certification hashes are
preserved for reproducible inspection.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
import math

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v1150 import JuliaExecutionRequest, execute_julia, runtime_identity as julia_runtime_identity
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-multi-runtime-certification-status/1.0"
CERT_SCHEMA = "sc-workbench-multi-runtime-calculation-certificate/1.0"

router = APIRouter(tags=["workbench-v11180-multi-runtime-calculation-certification"])


class MultiRuntimeCertificationRequest(BaseModel):
    operation: Literal["vector-dot", "matrix-multiply", "linear-solve", "statistics"]
    vectorA: List[float] = Field(default_factory=list, max_length=100000)
    vectorB: List[float] = Field(default_factory=list, max_length=100000)
    matrixA: List[List[float]] = Field(default_factory=list, max_length=5000)
    matrixB: List[List[float]] = Field(default_factory=list, max_length=5000)
    absoluteTolerance: float = Field(default=1e-10, ge=0)
    relativeTolerance: float = Field(default=1e-10, ge=0)
    requireNativeJulia: bool = False


class MultiRuntimeCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    certification: MultiRuntimeCertificationRequest


def _hash(payload: Any) -> str:
    return content_hash(payload)


def _python_runtime_identity() -> Dict[str, Any]:
    body = {
        "runtime": "python",
        "engine": "numpy",
        "numpyVersion": np.__version__,
    }
    body["runtimeIdentityHash"] = _hash(body)
    return body


def _python_reference(req: MultiRuntimeCertificationRequest) -> Any:
    op = req.operation
    if op == "vector-dot":
        if len(req.vectorA) != len(req.vectorB):
            raise ValueError("vector-dot requires equal vector lengths")
        return float(np.dot(np.asarray(req.vectorA, dtype=float), np.asarray(req.vectorB, dtype=float)))
    if op == "matrix-multiply":
        return (
            np.asarray(req.matrixA, dtype=float) @ np.asarray(req.matrixB, dtype=float)
        ).tolist()
    if op == "linear-solve":
        return np.linalg.solve(
            np.asarray(req.matrixA, dtype=float),
            np.asarray(req.vectorA, dtype=float),
        ).tolist()
    if op == "statistics":
        if not req.vectorA:
            raise ValueError("statistics requires vectorA")
        arr = np.asarray(req.vectorA, dtype=float)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
            "minimum": float(np.min(arr)),
            "maximum": float(np.max(arr)),
        }
    raise ValueError(f"unsupported operation: {op}")


def _flatten(value: Any, prefix: str = "result") -> Dict[str, float]:
    if isinstance(value, dict):
        out: Dict[str, float] = {}
        for key in sorted(value):
            out.update(_flatten(value[key], f"{prefix}.{key}"))
        return out
    if isinstance(value, (list, tuple)):
        out: Dict[str, float] = {}
        for i, item in enumerate(value):
            out.update(_flatten(item, f"{prefix}[{i}]"))
        return out
    if isinstance(value, (int, float, np.integer, np.floating)):
        return {prefix: float(value)}
    raise ValueError(f"non-numeric certification result at {prefix}: {type(value).__name__}")


def _compare(expected: Any, observed: Any, abs_tol: float, rel_tol: float) -> Dict[str, Any]:
    a = _flatten(expected)
    b = _flatten(observed)
    fields = sorted(set(a) | set(b))
    comparisons = []
    for field in fields:
        if field not in a or field not in b:
            comparisons.append({
                "field": field,
                "match": False,
                "reason": "missing-field",
                "expected": a.get(field),
                "observed": b.get(field),
            })
            continue
        x, y = a[field], b[field]
        abs_error = abs(x-y)
        scale = max(abs(x), abs(y))
        allowed = abs_tol + rel_tol * scale
        comparisons.append({
            "field": field,
            "expected": x,
            "observed": y,
            "absoluteError": abs_error,
            "allowedError": allowed,
            "match": bool(abs_error <= allowed),
        })
    return {
        "match": all(row["match"] for row in comparisons),
        "comparisons": comparisons,
        "divergences": [row for row in comparisons if not row["match"]],
        "maxAbsoluteError": max(
            (row.get("absoluteError", math.inf) for row in comparisons if "absoluteError" in row),
            default=0.0,
        ),
    }


def certify(req: MultiRuntimeCertificationRequest) -> Dict[str, Any]:
    python_result = _python_reference(req)
    python_identity = _python_runtime_identity()

    julia_req = JuliaExecutionRequest(
        operation=req.operation,
        vectorA=req.vectorA,
        vectorB=req.vectorB,
        matrixA=req.matrixA,
        matrixB=req.matrixB,
        allowPythonFallback=not req.requireNativeJulia,
    )
    julia_exec = execute_julia(julia_req)
    julia_result = julia_exec["result"]
    comparison = _compare(
        python_result,
        julia_result,
        req.absoluteTolerance,
        req.relativeTolerance,
    )

    native_julia = julia_exec["selectedRuntime"] == "julia" and not julia_exec["fallback"]
    contract_compatible = comparison["match"]
    cross_runtime_certified = contract_compatible and native_julia

    if cross_runtime_certified:
        certification_status = "certified"
    elif contract_compatible and julia_exec["fallback"]:
        certification_status = "compatible-fallback-observed"
    else:
        certification_status = "divergent"

    certificate = {
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "operation": req.operation,
        "certificationStatus": certification_status,
        "crossRuntimeCertified": cross_runtime_certified,
        "contractCompatible": contract_compatible,
        "nativeJuliaExecuted": native_julia,
        "fallbackUsed": bool(julia_exec["fallback"]),
        "tolerances": {
            "absolute": req.absoluteTolerance,
            "relative": req.relativeTolerance,
        },
        "runtimes": {
            "python": {
                "identity": python_identity,
                "result": python_result,
                "resultHash": _hash(python_result),
            },
            "julia": {
                "identity": julia_exec["runtimeIdentity"],
                "selectedRuntime": julia_exec["selectedRuntime"],
                "engine": julia_exec["engine"],
                "fallback": julia_exec["fallback"],
                "fallbackReason": julia_exec.get("fallbackReason"),
                "result": julia_result,
                "resultHash": _hash(julia_result),
                "executionHash": julia_exec["executionHash"],
            },
        },
        "comparison": comparison,
    }
    certificate["certificateHash"] = _hash(certificate)

    return {
        "ok": True,
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "certificate": certificate,
        "wordpressRequired": False,
    }


def calculation_object_extension(
    calculation_req: UnifiedCalculationRequest,
    certification_req: MultiRuntimeCertificationRequest,
):
    obj = build_calculation_object(calculation_req)
    certified = certify(certification_req)
    cert = certified["certificate"]

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["multiRuntimeCertification"] = cert

    obj["verification"] = dict(obj.get("verification") or {})
    obj["verification"]["multiRuntimeCertification"] = {
        "certificationStatus": cert["certificationStatus"],
        "crossRuntimeCertified": cert["crossRuntimeCertified"],
        "contractCompatible": cert["contractCompatible"],
        "nativeJuliaExecuted": cert["nativeJuliaExecuted"],
        "fallbackUsed": cert["fallbackUsed"],
        "divergenceCount": len(cert["comparison"]["divergences"]),
    }

    obj["executionPlan"] = dict(obj.get("executionPlan") or {})
    obj["executionPlan"]["multiRuntimeCertification"] = {
        "referenceRuntime": "python",
        "candidateRuntime": "julia",
        "operation": certification_req.operation,
        "absoluteTolerance": certification_req.absoluteTolerance,
        "relativeTolerance": certification_req.relativeTolerance,
        "requireNativeJulia": certification_req.requireNativeJulia,
    }

    obj["provenance"] = dict(obj.get("provenance") or {})
    obj["provenance"]["multiRuntimeCertificationHash"] = cert["certificateHash"]
    obj["provenance"]["pythonRuntimeIdentityHash"] = cert["runtimes"]["python"]["identity"]["runtimeIdentityHash"]
    obj["provenance"]["juliaRuntimeIdentityHash"] = cert["runtimes"]["julia"]["identity"]["runtimeIdentityHash"]

    obj["reproducibility"] = dict(obj.get("reproducibility") or {})
    obj["reproducibility"]["multiRuntimeCertification"] = {
        "certificateHash": cert["certificateHash"],
        "crossRuntimeCertified": cert["crossRuntimeCertified"],
        "contractCompatible": cert["contractCompatible"],
    }

    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    julia = julia_runtime_identity()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Multi-Runtime Calculation Certification",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "python-julia-cross-runtime-certifier",
        "wordpressRequired": False,
        "runtimeReadiness": {
            "python": True,
            "juliaInstalled": julia["installed"],
            "juliaRunnerPresent": julia["runnerPresent"],
            "juliaRuntimeIdentityHash": julia["runtimeIdentityHash"],
        },
        "capabilities": {
            "pythonReferenceExecution": True,
            "nativeJuliaCandidateExecution": True,
            "vectorDotCertification": True,
            "matrixMultiplyCertification": True,
            "linearSolveCertification": True,
            "statisticsCertification": True,
            "absoluteRelativeTolerance": True,
            "normalizedCrossRuntimeComparison": True,
            "runtimeIdentityCapture": True,
            "fallbackDetection": True,
            "structuredDivergenceReporting": True,
            "certificationHash": True,
            "calculationObjectCertification": True,
        },
    }


@router.get("/v11180/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/runtime-certification")
def certification_route(req: MultiRuntimeCertificationRequest):
    return certify(req)


@router.post("/calculation-engine/v1/runtime-certification/calculation-object")
def certification_calculation_object_route(req: MultiRuntimeCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.certification)
