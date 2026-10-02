"""Workbench v10.10.2 — Standalone Runtime Health, Bootstrap & API Contract Stabilization.

Defines the stable standalone client boundary for Sustainable Catalyst Workbench.
The canonical client namespace is /standalone/v1. WordPress remains optional.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from typing import Any, Dict

import numpy as np
import scipy
import sympy as sp
from fastapi import APIRouter

try:
    import pint
except Exception:  # pragma: no cover
    pint = None

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-standalone-stabilization-status/1.0"
HEALTH_SCHEMA = "sc-workbench-standalone-runtime-health/1.0"
BOOTSTRAP_SCHEMA = "sc-workbench-standalone-bootstrap/1.0"
API_SCHEMA = "sc-workbench-standalone-api-contract/1.0"
COMPAT_SCHEMA = "sc-workbench-standalone-compatibility-policy/1.0"

router = APIRouter(tags=["workbench-v10102-standalone-contract-stabilization"])


def _stable_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def runtime_health() -> Dict[str, Any]:
    engines = {
        "python": platform.python_version(),
        "sympy": sp.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pint": getattr(pint, "__version__", None) if pint is not None else None,
    }
    checks = {
        "api": True,
        "symbolic": True,
        "numeric": True,
        "units": pint is not None,
        "wordpressRequired": False,
    }
    body: Dict[str, Any] = {
        "ok": all(v for k, v in checks.items() if k != "wordpressRequired"),
        "schema": HEALTH_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "readiness": "ready" if all(v for k, v in checks.items() if k != "wordpressRequired") else "degraded",
        "canonicalClientNamespace": "/standalone/v1",
        "wordpressRequired": False,
        "authoritativeRuntime": "FastAPI",
        "checks": checks,
        "engines": engines,
    }
    body["healthHash"] = _stable_hash({k: v for k, v in body.items() if k not in {"ok", "healthHash"}})
    return body


def api_contract() -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "ok": True,
        "schema": API_SCHEMA,
        "version": VERSION,
        "contractVersion": "1.0",
        "product": PRODUCT_KEY,
        "canonicalBackend": "FastAPI",
        "canonicalClientNamespace": "/standalone/v1",
        "wordpressRequired": False,
        "transport": {
            "protocol": "https",
            "format": "application/json",
            "requestIdentityHeader": "X-Request-ID",
            "runtimeVersionHeader": "X-SC-Workbench-Version",
            "wordpressNonceRequired": False,
        },
        "stableRoutes": {
            "health": {"method": "GET", "path": "/standalone/v1/health"},
            "bootstrap": {"method": "GET", "path": "/standalone/v1/bootstrap"},
            "apiContract": {"method": "GET", "path": "/standalone/v1/api-contract"},
            "compatibility": {"method": "GET", "path": "/standalone/v1/compatibility"},
            "capabilities": {"method": "GET", "path": "/numerical/capabilities"},
            "plan": {"method": "POST", "path": "/numerical/plan"},
            "compute": {"method": "POST", "path": "/numerical/compute"},
        },
        "responseRules": {
            "successIncludesOk": True,
            "releaseIdentityUsesVersion": True,
            "calculationResultsRemainBackendOwned": True,
            "stableRoutesAreClientAgnostic": True,
            "breakingChangesRequireNewContractVersion": True,
        },
        "clientRules": {
            "mayCallBackendDirectly": True,
            "mayRunOutsideWordPress": True,
            "mustNotRequireWpRestNonce": True,
            "mustNotExecuteAuthoritativeMath": True,
        },
    }
    body["contractHash"] = _stable_hash({k: v for k, v in body.items() if k not in {"ok", "contractHash"}})
    return body


def compatibility_policy() -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "ok": True,
        "schema": COMPAT_SCHEMA,
        "version": VERSION,
        "contractVersion": "1.0",
        "canonicalNamespace": "/standalone/v1",
        "wordpressRequired": False,
        "legacyAliases": {
            "/standalone/bootstrap": {
                "status": "supported-legacy-alias",
                "replacement": "/standalone/v1/bootstrap",
                "removalScheduled": False,
            }
        },
        "policy": {
            "additiveFieldsAllowedWithinContractVersion": True,
            "existingStableRouteSemanticsMustRemainCompatible": True,
            "breakingRouteChangesRequireNewNamespace": True,
            "breakingSchemaChangesRequireNewContractVersion": True,
            "wordpressAdaptersMayLagWithoutBlockingBackend": True,
        },
    }
    body["compatibilityHash"] = _stable_hash({k: v for k, v in body.items() if k not in {"ok", "compatibilityHash"}})
    return body


def bootstrap() -> Dict[str, Any]:
    contract = api_contract()
    health = runtime_health()
    compat = compatibility_policy()
    body: Dict[str, Any] = {
        "ok": health["ok"],
        "schema": BOOTSTRAP_SCHEMA,
        "version": VERSION,
        "contractVersion": "1.0",
        "application": PRODUCT_NAME,
        "product": PRODUCT_KEY,
        "architecture": "backend-first-standalone-capable",
        "canonicalBackend": "FastAPI",
        "canonicalClientNamespace": "/standalone/v1",
        "wordpressRequired": False,
        "wordpressRole": "optional-adapter-and-embed-host",
        "runtime": {
            "kind": RUNTIME_KIND,
            "readiness": health["readiness"],
            "health": "/standalone/v1/health",
        },
        "api": contract["stableRoutes"],
        "compatibility": {
            "policy": "/standalone/v1/compatibility",
            "legacyBootstrap": "/standalone/bootstrap",
            "legacyBootstrapSupported": True,
        },
        "migration": {
            "standaloneFrontendCanLaunchWithoutWordPress": True,
            "calculationContractsAreClientAgnostic": True,
            "runtimeStateOwnedByBackend": True,
            "wordpressSpecificStateCanonical": False,
        },
        "contractHash": contract["contractHash"],
        "healthHash": health["healthHash"],
        "compatibilityHash": compat["compatibilityHash"],
    }
    body["bootstrapHash"] = _stable_hash({k: v for k, v in body.items() if k not in {"ok", "bootstrapHash"}})
    return body


def status() -> Dict[str, Any]:
    health = runtime_health()
    contract = api_contract()
    return {
        "ok": health["ok"],
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Standalone Runtime Health, Bootstrap & API Contract Stabilization",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "backendFirst": True,
        "standaloneReady": health["readiness"] == "ready",
        "wordpressRequired": False,
        "canonicalClientNamespace": "/standalone/v1",
        "contractVersion": contract["contractVersion"],
        "contractHash": contract["contractHash"],
        "healthHash": health["healthHash"],
    }


@router.get("/v10102/status")
def status_route():
    return status()


@router.get("/standalone/v1/health")
def standalone_health_route():
    return runtime_health()


@router.get("/standalone/v1/bootstrap")
def standalone_bootstrap_route():
    return bootstrap()


@router.get("/standalone/v1/api-contract")
def standalone_api_contract_route():
    return api_contract()


@router.get("/standalone/v1/compatibility")
def standalone_compatibility_route():
    return compatibility_policy()
