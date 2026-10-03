"""Workbench v11.17.0 — Calculation Provenance, Replay & Reproducibility.

Adds canonical replay envelopes, environment/runtime manifests, deterministic
replay, structured divergence reporting, and reproducibility certification to
the unified v11 CalculationObject architecture.
"""
from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-calculation-provenance-replay-status/1.0"
REPLAY_SCHEMA = "sc-workbench-calculation-replay-envelope/1.0"
CERT_SCHEMA = "sc-workbench-reproducibility-certificate/1.0"

router = APIRouter(tags=["workbench-v11170-calculation-provenance-replay-reproducibility"])


class CaptureReplayRequest(BaseModel):
    calculationRequest: UnifiedCalculationRequest
    calculationObject: Optional[Dict[str, Any]] = None
    label: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=5000)


class ReplayEnvelope(BaseModel):
    schema: str = REPLAY_SCHEMA
    version: str
    request: Dict[str, Any]
    requestHash: str
    sourceCalculationObjectHash: str
    sourceInputHash: Optional[str] = None
    sourceExecutionPlanHash: Optional[str] = None
    sourceResultHash: Optional[str] = None
    sourceProvenanceHash: Optional[str] = None
    runtimeManifest: Dict[str, Any]
    runtimeManifestHash: str
    label: str = ""
    notes: str = ""
    envelopeHash: str


class ReplayRequest(BaseModel):
    envelope: ReplayEnvelope
    comparisonMode: Literal["strict", "result-only", "input-plan-result"] = "strict"


class CompareObjectsRequest(BaseModel):
    expected: Dict[str, Any]
    observed: Dict[str, Any]
    comparisonMode: Literal["strict", "result-only", "input-plan-result"] = "strict"


def _hash(payload: Any) -> str:
    return content_hash(payload)


def _package_version(name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def runtime_manifest() -> Dict[str, Any]:
    packages = {
        name: _package_version(name)
        for name in [
            "fastapi", "pydantic", "numpy", "scipy", "sympy",
            "pint", "mpmath", "uvicorn"
        ]
    }
    body = {
        "schema": "sc-workbench-runtime-manifest/1.0",
        "workbenchVersion": VERSION,
        "product": PRODUCT_KEY,
        "application": PRODUCT_NAME,
        "runtimeKind": RUNTIME_KIND,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executableFamily": "python",
        },
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "pythonByteOrder": sys.byteorder,
        },
        "packages": packages,
    }
    body["manifestHash"] = _hash(body)
    return body


def _section_hashes(obj: Dict[str, Any]) -> Dict[str, Optional[str]]:
    provenance = obj.get("provenance") or {}
    reproducibility = obj.get("reproducibility") or {}
    input_obj = obj.get("input")
    execution_plan = obj.get("executionPlan")
    result = obj.get("result")
    prov_hash = provenance.get("provenanceHash")
    return {
        "calculationObjectHash": obj.get("calculationObjectHash"),
        "inputHash": (
            (input_obj or {}).get("inputHash")
            or provenance.get("inputHash")
            or reproducibility.get("deterministicInputHash")
            or (_hash(input_obj) if input_obj is not None else None)
        ),
        "executionPlanHash": (
            (execution_plan or {}).get("executionPlanHash")
            or provenance.get("executionPlanHash")
            or reproducibility.get("executionPlanHash")
            or (_hash(execution_plan) if execution_plan is not None else None)
        ),
        "resultHash": (
            (result or {}).get("resultHash")
            or provenance.get("resultHash")
            or reproducibility.get("resultHash")
            or (_hash(result) if result is not None else None)
        ),
        "provenanceHash": (
            prov_hash
            or reproducibility.get("provenanceHash")
            or (_hash(provenance) if provenance else None)
        ),
    }


def capture_replay(req: CaptureReplayRequest) -> Dict[str, Any]:
    obj = req.calculationObject or build_calculation_object(req.calculationRequest)
    hashes = _section_hashes(obj)
    request_payload = req.calculationRequest.model_dump(mode="json")
    manifest = runtime_manifest()

    envelope = {
        "schema": REPLAY_SCHEMA,
        "version": VERSION,
        "request": request_payload,
        "requestHash": _hash(request_payload),
        "sourceCalculationObjectHash": hashes["calculationObjectHash"] or _hash(obj),
        "sourceInputHash": hashes["inputHash"],
        "sourceExecutionPlanHash": hashes["executionPlanHash"],
        "sourceResultHash": hashes["resultHash"],
        "sourceProvenanceHash": hashes["provenanceHash"],
        "runtimeManifest": manifest,
        "runtimeManifestHash": manifest["manifestHash"],
        "label": req.label,
        "notes": req.notes,
    }
    envelope["envelopeHash"] = _hash(envelope)

    return {
        "ok": True,
        "schema": REPLAY_SCHEMA,
        "version": VERSION,
        "envelope": envelope,
        "source": {
            "calculationObjectHash": envelope["sourceCalculationObjectHash"],
            "inputHash": envelope["sourceInputHash"],
            "executionPlanHash": envelope["sourceExecutionPlanHash"],
            "resultHash": envelope["sourceResultHash"],
            "provenanceHash": envelope["sourceProvenanceHash"],
        },
        "wordpressRequired": False,
    }


def _diff_hashes(expected: Dict[str, Optional[str]], observed: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    rows = []
    for key in [
        "calculationObjectHash", "inputHash", "executionPlanHash", "resultHash", "provenanceHash"
    ]:
        a, b = expected.get(key), observed.get(key)
        rows.append({
            "field": key,
            "expected": a,
            "observed": b,
            "match": a == b,
        })
    return rows


def compare_objects(req: CompareObjectsRequest) -> Dict[str, Any]:
    expected = _section_hashes(req.expected)
    observed = _section_hashes(req.observed)
    rows = _diff_hashes(expected, observed)

    if req.comparisonMode == "result-only":
        relevant = {"resultHash"}
    elif req.comparisonMode == "input-plan-result":
        relevant = {"inputHash", "executionPlanHash", "resultHash"}
    else:
        relevant = {
            "calculationObjectHash", "inputHash", "executionPlanHash",
            "resultHash", "provenanceHash"
        }

    selected = [r for r in rows if r["field"] in relevant]
    reproducible = all(r["match"] for r in selected)

    body = {
        "ok": True,
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "comparisonMode": req.comparisonMode,
        "reproducible": reproducible,
        "matches": rows,
        "divergences": [r for r in selected if not r["match"]],
    }
    body["certificateHash"] = _hash(body)
    return body


def replay(req: ReplayRequest) -> Dict[str, Any]:
    env = req.envelope
    expected_envelope_payload = env.model_dump(mode="json")
    supplied_envelope_hash = expected_envelope_payload.pop("envelopeHash")
    calculated_envelope_hash = _hash(expected_envelope_payload)

    envelope_integrity = supplied_envelope_hash == calculated_envelope_hash
    request_hash_ok = env.requestHash == _hash(env.request)

    parsed_request = UnifiedCalculationRequest.model_validate(env.request)
    observed = build_calculation_object(parsed_request)
    observed_hashes = _section_hashes(observed)

    expected_hashes = {
        "calculationObjectHash": env.sourceCalculationObjectHash,
        "inputHash": env.sourceInputHash,
        "executionPlanHash": env.sourceExecutionPlanHash,
        "resultHash": env.sourceResultHash,
        "provenanceHash": env.sourceProvenanceHash,
    }
    rows = _diff_hashes(expected_hashes, observed_hashes)

    if req.comparisonMode == "result-only":
        relevant = {"resultHash"}
    elif req.comparisonMode == "input-plan-result":
        relevant = {"inputHash", "executionPlanHash", "resultHash"}
    else:
        relevant = {
            "calculationObjectHash", "inputHash", "executionPlanHash",
            "resultHash", "provenanceHash"
        }

    selected = [r for r in rows if r["field"] in relevant]
    reproducible = envelope_integrity and request_hash_ok and all(r["match"] for r in selected)

    current_manifest = runtime_manifest()
    manifest_match = current_manifest["manifestHash"] == env.runtimeManifestHash

    certificate = {
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "comparisonMode": req.comparisonMode,
        "reproducible": reproducible,
        "envelopeIntegrity": envelope_integrity,
        "requestIntegrity": request_hash_ok,
        "runtimeManifestMatch": manifest_match,
        "sourceRuntimeManifestHash": env.runtimeManifestHash,
        "replayRuntimeManifestHash": current_manifest["manifestHash"],
        "matches": rows,
        "divergences": [r for r in selected if not r["match"]],
    }
    certificate["certificateHash"] = _hash(certificate)

    return {
        "ok": True,
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "replayedCalculationObject": observed,
        "certificate": certificate,
        "wordpressRequired": False,
    }


def attach_reproducibility(
    calculation_request: UnifiedCalculationRequest,
    calculation_object: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obj = calculation_object or build_calculation_object(calculation_request)
    capture = capture_replay(CaptureReplayRequest(
        calculationRequest=calculation_request,
        calculationObject=obj,
    ))
    envelope = capture["envelope"]

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["replay"] = envelope
    obj["reproducibility"] = dict(obj.get("reproducibility") or {})
    obj["reproducibility"].update({
        "schema": CERT_SCHEMA,
        "replayEnvelopeHash": envelope["envelopeHash"],
        "runtimeManifestHash": envelope["runtimeManifestHash"],
        "requestHash": envelope["requestHash"],
        "replaySupported": True,
        "certificationMode": "deterministic-hash-replay",
    })
    obj["provenance"] = dict(obj.get("provenance") or {})
    obj["provenance"]["replayEnvelopeHash"] = envelope["envelopeHash"]
    obj["provenance"]["runtimeManifestHash"] = envelope["runtimeManifestHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


class AttachReproducibilityRequest(BaseModel):
    calculationRequest: UnifiedCalculationRequest
    calculationObject: Optional[Dict[str, Any]] = None


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Calculation Provenance, Replay & Reproducibility",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "canonical-hash-replay-certifier",
        "wordpressRequired": False,
        "capabilities": {
            "canonicalReplayEnvelope": True,
            "requestHashing": True,
            "inputHashVerification": True,
            "executionPlanHashVerification": True,
            "resultHashVerification": True,
            "provenanceHashVerification": True,
            "calculationObjectHashVerification": True,
            "runtimeEnvironmentManifest": True,
            "deterministicReplay": True,
            "structuredDivergenceReporting": True,
            "reproducibilityCertification": True,
            "calculationObjectReproducibilityExtension": True,
        },
    }


@router.get("/v11170/status")
def status_route():
    return status()


@router.get("/calculation-engine/v1/reproducibility/runtime-manifest")
def runtime_manifest_route():
    return {"ok": True, "version": VERSION, "runtimeManifest": runtime_manifest()}


@router.post("/calculation-engine/v1/reproducibility/capture")
def capture_route(req: CaptureReplayRequest):
    return capture_replay(req)


@router.post("/calculation-engine/v1/reproducibility/replay")
def replay_route(req: ReplayRequest):
    return replay(req)


@router.post("/calculation-engine/v1/reproducibility/compare")
def compare_route(req: CompareObjectsRequest):
    return compare_objects(req)


@router.post("/calculation-engine/v1/reproducibility/calculation-object")
def calculation_object_route(req: AttachReproducibilityRequest):
    return attach_reproducibility(req.calculationRequest, req.calculationObject)
