"""Workbench v10.11 — Reproducible Computational Packages.

Packages preserve calculation inputs, authoritative results,
environment identity, and deterministic integrity hashes.
"""

from __future__ import annotations

from typing import Any, Dict, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v10100 import CalculationRequest, execute


VERSION = APP_VERSION
PACKAGE_SCHEMA = "sc-workbench-computational-package/1.0"
MANIFEST_SCHEMA = "sc-workbench-computational-manifest/1.0"
ENVIRONMENT_SCHEMA = "sc-workbench-computational-environment/1.0"
STATUS_SCHEMA = "sc-workbench-reproducible-package-status/1.0"

router = APIRouter(
    tags=["workbench-v10110-reproducible-computational-packages"]
)


class PackageBuildRequest(BaseModel):
    calculation: CalculationRequest


class PackageVerifyRequest(BaseModel):
    package: Dict[str, Any]
    mode: Literal["integrity", "replay"] = "replay"


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _without_hash(
    value: Dict[str, Any], field: str
) -> Dict[str, Any]:
    return {k: v for k, v in value.items() if k != field}


def environment_manifest() -> Dict[str, Any]:
    payload = {
        "schema": ENVIRONMENT_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "calculationBackend": "FastAPI",
        "numericalEngine": "v10100",
        "wordpressRequired": False,
    }
    payload["environmentHash"] = _hash(payload)
    return payload


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "packageSchema": PACKAGE_SCHEMA,
        "manifestSchema": MANIFEST_SCHEMA,
        "wordpressRequired": False,
        "replaySupported": True,
    }


def build_package(req: PackageBuildRequest) -> Dict[str, Any]:
    calculation = req.calculation.model_dump(mode="json")
    result = execute(req.calculation)

    environment = environment_manifest()

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "version": VERSION,
        "environment": environment,
        "calculationHash": result["calculationHash"],
    }
    manifest["manifestHash"] = _hash(manifest)

    package = {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "calculation": calculation,
        "result": result,
        "manifest": manifest,
    }
    package["packageHash"] = _hash(package)

    return package


def verify_package(req: PackageVerifyRequest) -> Dict[str, Any]:
    package = req.package
    checks: Dict[str, bool] = {}

    checks["packageSchemaValid"] = (
        package.get("schema") == PACKAGE_SCHEMA
    )

    checks["packageHashValid"] = (
        isinstance(package.get("packageHash"), str)
        and package["packageHash"]
        == _hash(_without_hash(package, "packageHash"))
    )

    manifest = package.get("manifest")
    checks["manifestPresent"] = isinstance(manifest, dict)

    if isinstance(manifest, dict):
        checks["manifestSchemaValid"] = (
            manifest.get("schema") == MANIFEST_SCHEMA
        )
        checks["manifestHashValid"] = (
            isinstance(manifest.get("manifestHash"), str)
            and manifest["manifestHash"]
            == _hash(_without_hash(manifest, "manifestHash"))
        )
        checks["environmentValid"] = (
            manifest.get("environment") == environment_manifest()
        )
        checks["calculationHashLinked"] = (
            manifest.get("calculationHash")
            == package.get("result", {}).get("calculationHash")
        )
    else:
        checks.update({
            "manifestSchemaValid": False,
            "manifestHashValid": False,
            "environmentValid": False,
            "calculationHashLinked": False,
        })

    checks["replayMatches"] = False

    if req.mode == "replay" and all(
        value for key, value in checks.items()
        if key != "replayMatches"
    ):
        try:
            calculation = CalculationRequest.model_validate(
                package["calculation"]
            )
            replay = execute(calculation)
            checks["replayMatches"] = (
                replay == package.get("result")
            )
        except Exception:
            checks["replayMatches"] = False

    if req.mode == "integrity":
        checks.pop("replayMatches")

    return {
        "ok": all(checks.values()),
        "schema": "sc-workbench-package-verification/1.0",
        "version": VERSION,
        "mode": req.mode,
        "checks": checks,
        "packageHash": package.get("packageHash"),
    }


@router.get("/v10110/status")
def status_route():
    return status()


@router.get("/v10110/environment")
def environment_route():
    return environment_manifest()


@router.post("/v10110/packages/build")
def build_route(req: PackageBuildRequest):
    return build_package(req)


@router.post("/v10110/packages/verify")
def verify_route(req: PackageVerifyRequest):
    return verify_package(req)
