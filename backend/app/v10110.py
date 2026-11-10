"""Workbench v10.11.0 — Reproducible Computational Package.

Builds portable, content-addressed computational packages from canonical
Workbench calculation requests and results. Packages preserve runtime identity,
inputs, results, provenance, verification metadata, and replay instructions.
"""
from __future__ import annotations

import platform
from typing import Any, Dict, Literal, Optional

import numpy as np
import scipy
import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    import pint
except Exception:  # pragma: no cover
    pint = None

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v10100 import (
    CalculationRequest,
    execute as execute_calculation,
    plan as plan_calculation,
    PlanRequest,
)
from .v10102 import api_contract
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-reproducible-computational-package-status/1.0"
PACKAGE_SCHEMA = "sc-workbench-reproducible-computational-package/1.0"
MANIFEST_SCHEMA = "sc-workbench-computational-package-manifest/1.0"
REPLAY_SCHEMA = "sc-workbench-computational-package-replay/1.0"
VERIFY_SCHEMA = "sc-workbench-computational-package-verification/1.0"

router = APIRouter(tags=["workbench-v10110-reproducible-computational-package"])


class PackageMetadata(BaseModel):
    title: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=5000)
    author: str = Field(default="", max_length=500)
    projectId: Optional[str] = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=100)


class PackageBuildRequest(BaseModel):
    calculation: CalculationRequest
    metadata: PackageMetadata = Field(default_factory=PackageMetadata)
    includePlan: bool = True
    includeEnvironment: bool = True
    includeReplay: bool = True


class PackageVerifyRequest(BaseModel):
    package: Dict[str, Any]
    mode: Literal["manifest", "replay"] = "replay"


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def environment_manifest() -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "workbenchVersion": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "python": platform.python_version(),
        "engines": {
            "sympy": sp.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pint": getattr(pint, "__version__", None) if pint is not None else None,
        },
        "architecture": {
            "canonicalBackend": "FastAPI",
            "wordpressRequired": False,
            "apiContractVersion": api_contract()["contractVersion"],
        },
    }
    body["environmentHash"] = _hash(
        {k: v for k, v in body.items() if k != "environmentHash"}
    )
    return body


def _plan_for(calculation: CalculationRequest) -> Dict[str, Any]:
    req = PlanRequest(
        operation=calculation.operation,
        expression=calculation.expression,
        objective="Reproduce packaged Workbench calculation",
        requireExactWhenPossible=True,
        requireUnits=calculation.operation == "units",
        requireUncertainty=False,
        preferredRuntime="auto",
    )
    return plan_calculation(req)


def build_package(req: PackageBuildRequest) -> Dict[str, Any]:
    calculation_payload = req.calculation.model_dump(mode="json")
    result = execute_calculation(req.calculation)
    plan = _plan_for(req.calculation) if req.includePlan else None
    environment = environment_manifest() if req.includeEnvironment else None

    manifest: Dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "packageSchema": PACKAGE_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "application": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "calculationInputHash": _hash(calculation_payload),
        "calculationResultHash": result.get("calculationHash"),
        "planHash": plan.get("planHash") if plan else None,
        "environmentHash": environment.get("environmentHash") if environment else None,
    }
    manifest["manifestHash"] = _hash(
        {k: v for k, v in manifest.items() if k != "manifestHash"}
    )

    replay = None
    if req.includeReplay:
        replay = {
            "schema": REPLAY_SCHEMA,
            "operation": "POST",
            "path": "/computational-packages/replay",
            "calculation": calculation_payload,
            "expectedCalculationHash": result.get("calculationHash"),
            "expectedResult": result.get("result"),
            "expectedWorkbenchVersion": VERSION,
        }
        replay["replayHash"] = _hash(
            {k: v for k, v in replay.items() if k != "replayHash"}
        )

    package: Dict[str, Any] = {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "packageType": "reproducible-computation",
        "metadata": req.metadata.model_dump(mode="json"),
        "input": calculation_payload,
        "plan": plan,
        "environment": environment,
        "result": result,
        "manifest": manifest,
        "replay": replay,
        "provenance": {
            "canonicalBackend": "FastAPI",
            "calculationEngine": result.get("engine"),
            "calculationMethod": result.get("method"),
            "runtimeVersion": VERSION,
            "wordpressRequired": False,
            "authoritativeComputationOutsideWordPress": True,
        },
    }
    package["packageHash"] = _hash(
        {k: v for k, v in package.items() if k not in {"ok", "packageHash"}}
    )
    return package


def verify_manifest(package: Dict[str, Any]) -> Dict[str, Any]:
    manifest = package.get("manifest")
    if not isinstance(manifest, dict):
        raise HTTPException(status_code=422, detail="Package manifest missing")

    expected = manifest.get("manifestHash")
    regenerated = _hash(
        {k: v for k, v in manifest.items() if k != "manifestHash"}
    )
    checks = {
        "manifestPresent": True,
        "manifestHashMatches": bool(expected) and expected == regenerated,
        "packageSchemaMatches": package.get("schema") == PACKAGE_SCHEMA,
        "wordpressRequiredFalse": package.get("provenance", {}).get("wordpressRequired") is False,
    }
    return {
        "ok": all(checks.values()),
        "schema": VERIFY_SCHEMA,
        "version": VERSION,
        "verificationMode": "manifest",
        "checks": checks,
        "expectedManifestHash": expected,
        "regeneratedManifestHash": regenerated,
    }


def replay_package(package: Dict[str, Any]) -> Dict[str, Any]:
    replay = package.get("replay")
    if not isinstance(replay, dict):
        raise HTTPException(status_code=422, detail="Package replay metadata missing")

    calculation = replay.get("calculation")
    if not isinstance(calculation, dict):
        raise HTTPException(status_code=422, detail="Replay calculation missing")

    req = CalculationRequest.model_validate(calculation)
    reproduced = execute_calculation(req)
    expected_hash = replay.get("expectedCalculationHash")
    expected_result = replay.get("expectedResult")

    checks = {
        "executionSucceeded": reproduced.get("ok") is True,
        "calculationHashMatches": reproduced.get("calculationHash") == expected_hash,
        "resultMatches": reproduced.get("result") == expected_result,
        "wordpressRequiredFalse": reproduced.get("wordpressRequired") is False,
    }

    body: Dict[str, Any] = {
        "ok": all(checks.values()),
        "schema": REPLAY_SCHEMA,
        "version": VERSION,
        "verificationMode": "replay",
        "checks": checks,
        "expectedCalculationHash": expected_hash,
        "reproducedCalculationHash": reproduced.get("calculationHash"),
        "expectedResult": expected_result,
        "reproducedResult": reproduced.get("result"),
        "reproduced": reproduced,
    }
    body["replayVerificationHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "replayVerificationHash"}}
    )
    return body


def verify_package(req: PackageVerifyRequest) -> Dict[str, Any]:
    if req.mode == "manifest":
        return verify_manifest(req.package)
    manifest_check = verify_manifest(req.package)
    replay_check = replay_package(req.package)
    body: Dict[str, Any] = {
        "ok": manifest_check["ok"] and replay_check["ok"],
        "schema": VERIFY_SCHEMA,
        "version": VERSION,
        "verificationMode": "replay",
        "manifest": manifest_check,
        "replay": replay_check,
    }
    body["verificationHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "verificationHash"}}
    )
    return body


def status() -> Dict[str, Any]:
    environment = environment_manifest()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Reproducible Computational Package",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "packageSchema": PACKAGE_SCHEMA,
        "manifestSchema": MANIFEST_SCHEMA,
        "replaySchema": REPLAY_SCHEMA,
        "capabilities": {
            "contentAddressedPackages": True,
            "deterministicInputHashes": True,
            "calculationResultHashes": True,
            "runtimeEnvironmentManifest": True,
            "executionPlanCapture": True,
            "replayMetadata": True,
            "manifestVerification": True,
            "replayVerification": True,
            "portableJsonPackage": True,
            "wordpressIndependent": True,
        },
        "environmentHash": environment["environmentHash"],
    }


@router.get("/v10110/status")
def status_route():
    return status()


@router.get("/computational-packages/environment")
def computational_package_environment_route():
    return environment_manifest()


@router.post("/computational-packages/build")
def computational_package_build_route(req: PackageBuildRequest):
    return build_package(req)


@router.post("/computational-packages/replay")
def computational_package_replay_route(req: PackageVerifyRequest):
    return replay_package(req.package)


@router.post("/computational-packages/verify")
def computational_package_verify_route(req: PackageVerifyRequest):
    return verify_package(req)
