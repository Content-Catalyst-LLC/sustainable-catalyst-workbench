"""Workbench v10.12.0 — Production Certification & v10 Consolidation.

Closes the Workbench v10 line by certifying the backend-first standalone
architecture, dual-mode access, hybrid calculation runtime, and reproducible
computational packages as one production-ready contract surface.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v10100 import CalculationRequest, capabilities as numerical_capabilities
from .v10102 import api_contract, runtime_health
from .v10103 import client_config
from .v10104 import certification_report as dual_mode_certification
from .v10110 import (
    PackageBuildRequest,
    PackageVerifyRequest,
    build_package,
    environment_manifest,
    status as package_status,
    verify_package,
)
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-v10-production-certification-status/1.0"
CERT_SCHEMA = "sc-workbench-v10-production-certification/1.0"
RELEASE_SCHEMA = "sc-workbench-v10-release-consolidation/1.0"
CONTRACT_SCHEMA = "sc-workbench-v10-contract-consolidation/1.0"
PROBE_SCHEMA = "sc-workbench-v10-production-probe/1.0"

router = APIRouter(tags=["workbench-v10120-production-certification-v10-consolidation"])


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def release_consolidation() -> Dict[str, Any]:
    releases: List[Dict[str, Any]] = [
        {"version": "10.0.0", "capability": "Scientific AI Engineering Runtime Foundation"},
        {"version": "10.1.0", "capability": "Model & Dataset Registry"},
        {"version": "10.2.0", "capability": "Training & Fine-Tuning Experiment Runtime"},
        {"version": "10.3.0", "capability": "AI Evaluation & Benchmark Workspace"},
        {"version": "10.4.0", "capability": "Hyperparameter Optimization & Search Engine"},
        {"version": "10.5.0", "capability": "Feature Engineering & Representation Workspace"},
        {"version": "10.6.0", "capability": "Explainability Workspace"},
        {"version": "10.7.0", "capability": "Uncertainty & Calibration Workspace"},
        {"version": "10.8.0", "capability": "Scientific ML Workspace"},
        {"version": "10.9.0", "capability": "Agent / Computational Graph Workspace"},
        {"version": "10.10.0", "capability": "Hybrid Numerical Runtime & Standalone Application Foundation"},
        {"version": "10.10.1", "capability": "WordPress Dependency Inventory & Routing Isolation"},
        {"version": "10.10.2", "capability": "Standalone Runtime Health, Bootstrap & API Contract Stabilization"},
        {"version": "10.10.3", "capability": "Standalone Client/API Adapter Foundation"},
        {"version": "10.10.4", "capability": "Dual-Mode WordPress + Standalone Certification"},
        {"version": "10.11.0", "capability": "Reproducible Computational Package"},
        {"version": "10.12.0", "capability": "Production Certification & v10 Consolidation"},
    ]
    body: Dict[str, Any] = {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "series": "10.x",
        "releaseCount": len(releases),
        "releases": releases,
        "consolidation": {
            "canonicalBackend": "FastAPI",
            "standaloneCapable": True,
            "wordpressRequired": False,
            "reproduciblePackages": True,
            "productionCertificationRelease": VERSION,
        },
    }
    body["releaseManifestHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "releaseManifestHash"}}
    )
    return body


def contract_consolidation() -> Dict[str, Any]:
    api = api_contract()
    client = client_config()
    numeric = numerical_capabilities()
    environment = environment_manifest()
    body: Dict[str, Any] = {
        "ok": True,
        "schema": CONTRACT_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "canonicalBackend": "FastAPI",
        "wordpressRequired": False,
        "contracts": {
            "standaloneApi": {
                "contractVersion": api["contractVersion"],
                "contractHash": api["contractHash"],
                "namespace": api["canonicalClientNamespace"],
            },
            "standaloneClient": {
                "contractVersion": client["contractVersion"],
                "configHash": client["configHash"],
                "namespace": client["clientNamespace"],
            },
            "numericalRuntime": {
                "schema": numeric["schema"],
                "backendFirst": numeric["backendFirst"],
                "wordpressRequired": numeric["wordpressRequired"],
            },
            "reproduciblePackage": {
                "packageSchema": package_status()["packageSchema"],
                "manifestSchema": package_status()["manifestSchema"],
                "environmentHash": environment["environmentHash"],
            },
        },
        "rules": {
            "authoritativeComputationBackendOnly": True,
            "standaloneClientDirectBackendAccess": True,
            "wordpressPresentationProxyOnly": True,
            "breakingStandaloneChangesRequireVersionedContract": True,
            "packagesPreserveReplayAndProvenance": True,
        },
    }
    body["contractConsolidationHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "contractConsolidationHash"}}
    )
    return body


def production_probe() -> Dict[str, Any]:
    calc = CalculationRequest(operation="exact", expression="2 + 2")
    package = build_package(PackageBuildRequest(calculation=calc))
    verification = verify_package(PackageVerifyRequest(package=package, mode="replay"))
    dual = dual_mode_certification()
    health = runtime_health()

    checks = {
        "runtimeHealthReady": health["ok"] is True and health["readiness"] == "ready",
        "dualModeCertificationPass": dual["ok"] is True and dual["certification"] == "pass",
        "standaloneCanonical": dual["modes"]["standalone"]["canonical"] is True,
        "wordpressOptional": dual["wordpressRequired"] is False,
        "packageBuildSucceeded": package["ok"] is True,
        "packageResultStable": package["result"]["result"].get("exact") == "4",
        "packageReplayVerificationPass": verification["ok"] is True,
        "packageHashPresent": bool(package.get("packageHash")),
        "manifestHashPresent": bool(package.get("manifest", {}).get("manifestHash")),
    }
    body: Dict[str, Any] = {
        "ok": all(checks.values()),
        "schema": PROBE_SCHEMA,
        "version": VERSION,
        "checks": checks,
        "sample": {
            "input": "2 + 2",
            "exactResult": package["result"]["result"].get("exact"),
            "calculationHash": package["result"].get("calculationHash"),
            "packageHash": package.get("packageHash"),
            "manifestHash": package.get("manifest", {}).get("manifestHash"),
        },
    }
    body["probeHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "probeHash"}}
    )
    return body


def production_certification() -> Dict[str, Any]:
    releases = release_consolidation()
    contracts = contract_consolidation()
    probe = production_probe()
    package = package_status()
    dual = dual_mode_certification()

    checks = {
        "releaseManifestComplete": releases["releaseCount"] >= 17,
        "contractsConsolidated": contracts["ok"] is True,
        "productionProbePassed": probe["ok"] is True,
        "dualModeCertified": dual["certification"] == "pass",
        "reproduciblePackageReady": package["ok"] is True,
        "wordpressRequiredFalse": package["wordpressRequired"] is False,
        "standaloneReady": runtime_health()["readiness"] == "ready",
    }

    body: Dict[str, Any] = {
        "ok": all(checks.values()),
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "release": "Production Certification & v10 Consolidation",
        "product": PRODUCT_KEY,
        "application": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "certification": "pass" if all(checks.values()) else "fail",
        "series": "10.x",
        "wordpressRequired": False,
        "checks": checks,
        "hashes": {
            "releaseManifest": releases["releaseManifestHash"],
            "contracts": contracts["contractConsolidationHash"],
            "probe": probe["probeHash"],
            "dualMode": dual["certificationHash"],
        },
        "certifiedArchitecture": {
            "canonicalBackend": "FastAPI",
            "standaloneApplicationReady": True,
            "wordpressAdapterOptional": True,
            "hybridNumericalRuntimeReady": True,
            "reproducibleComputationalPackagesReady": True,
            "clientContractsVersioned": True,
            "v10SeriesConsolidated": True,
        },
        "nextMajorProgram": "v11 Universal Calculation Engine",
    }
    body["certificationHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "certificationHash"}}
    )
    return body


def status() -> Dict[str, Any]:
    cert = production_certification()
    return {
        "ok": cert["ok"],
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Production Certification & v10 Consolidation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "certification": cert["certification"],
        "wordpressRequired": False,
        "v10Consolidated": cert["certifiedArchitecture"]["v10SeriesConsolidated"],
        "standaloneApplicationReady": cert["certifiedArchitecture"]["standaloneApplicationReady"],
        "reproducibleComputationalPackagesReady": cert["certifiedArchitecture"]["reproducibleComputationalPackagesReady"],
        "nextMajorProgram": cert["nextMajorProgram"],
        "certificationHash": cert["certificationHash"],
    }


@router.get("/v10120/status")
def status_route():
    return status()


@router.get("/certification/v10")
def production_certification_route():
    return production_certification()


@router.get("/certification/v10/releases")
def release_consolidation_route():
    return release_consolidation()


@router.get("/certification/v10/contracts")
def contract_consolidation_route():
    return contract_consolidation()


@router.get("/certification/v10/probe")
def production_probe_route():
    return production_probe()
