"""Workbench v10.10.3 — Standalone Client/API Adapter Foundation.

Provides a stable, client-facing adapter over the canonical Workbench runtime.
The adapter is backend-owned, framework-neutral, and WordPress-independent.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v10100 import (
    CalculationRequest,
    PlanRequest,
    capabilities as numerical_capabilities,
    execute as execute_calculation,
    plan as plan_calculation,
)
from .v10102 import api_contract as standalone_api_contract
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-standalone-client-adapter-status/1.0"
ADAPTER_SCHEMA = "sc-workbench-standalone-client-adapter/1.0"
CONFIG_SCHEMA = "sc-workbench-standalone-client-config/1.0"
ENVELOPE_SCHEMA = "sc-workbench-standalone-client-response/1.0"

router = APIRouter(tags=["workbench-v10103-standalone-client-api-adapter"])


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def client_config() -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "ok": True,
        "schema": CONFIG_SCHEMA,
        "version": VERSION,
        "contractVersion": "1.0",
        "application": PRODUCT_NAME,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "canonicalNamespace": "/standalone/v1",
        "clientNamespace": "/standalone/v1/client",
        "wordpressRequired": False,
        "transport": {
            "format": "application/json",
            "credentialsRequiredForPublicCalculationSurface": False,
            "wordpressNonceRequired": False,
            "requestIdentityHeader": "X-Request-ID",
            "runtimeVersionHeader": "X-SC-Workbench-Version",
        },
        "routes": {
            "config": {"method": "GET", "path": "/standalone/v1/client/config"},
            "capabilities": {"method": "GET", "path": "/standalone/v1/client/capabilities"},
            "plan": {"method": "POST", "path": "/standalone/v1/client/plan"},
            "compute": {"method": "POST", "path": "/standalone/v1/client/compute"},
            "runtimeHealth": {"method": "GET", "path": "/standalone/v1/health"},
            "bootstrap": {"method": "GET", "path": "/standalone/v1/bootstrap"},
            "apiContract": {"method": "GET", "path": "/standalone/v1/api-contract"},
            "compatibility": {"method": "GET", "path": "/standalone/v1/compatibility"},
        },
        "clientRules": {
            "backendIsAuthoritative": True,
            "clientMayRunOutsideWordPress": True,
            "clientMustNotExecuteAuthoritativeMath": True,
            "clientMustTreatServerVersionAsRuntimeIdentity": True,
            "clientShouldSendRequestIdWhenAvailable": True,
            "clientMustNotDependOnWpRestNonce": True,
        },
    }
    body["configHash"] = _hash({k: v for k, v in body.items() if k not in {"ok", "configHash"}})
    return body


def adapter_contract() -> Dict[str, Any]:
    contract = standalone_api_contract()
    body: Dict[str, Any] = {
        "ok": True,
        "schema": ADAPTER_SCHEMA,
        "version": VERSION,
        "contractVersion": "1.0",
        "product": PRODUCT_KEY,
        "adapter": "standalone-web-api",
        "canonicalBackend": "FastAPI",
        "wordpressRequired": False,
        "clientNamespace": "/standalone/v1/client",
        "upstreamContractVersion": contract["contractVersion"],
        "upstreamContractHash": contract["contractHash"],
        "mapping": {
            "capabilities": {
                "adapter": "/standalone/v1/client/capabilities",
                "canonical": "/numerical/capabilities",
            },
            "plan": {
                "adapter": "/standalone/v1/client/plan",
                "canonical": "/numerical/plan",
            },
            "compute": {
                "adapter": "/standalone/v1/client/compute",
                "canonical": "/numerical/compute",
            },
        },
        "guarantees": {
            "sameValidationModelsAsCanonicalRuntime": True,
            "sameCalculationExecutionFunction": True,
            "samePlanExecutionFunction": True,
            "adapterDoesNotDuplicateMathEngine": True,
            "adapterDoesNotOwnCanonicalState": True,
            "wordPressIndependent": True,
        },
    }
    body["adapterHash"] = _hash({k: v for k, v in body.items() if k not in {"ok", "adapterHash"}})
    return body


def _adapt(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = dict(payload)
    body["clientAdapter"] = {
        "schema": ENVELOPE_SCHEMA,
        "version": VERSION,
        "contractVersion": "1.0",
        "kind": kind,
        "namespace": "/standalone/v1/client",
        "wordpressRequired": False,
        "authoritativeRuntime": "FastAPI",
    }
    return body


def status() -> Dict[str, Any]:
    cfg = client_config()
    adapter = adapter_contract()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Standalone Client/API Adapter Foundation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "backendFirst": True,
        "standaloneClientReady": True,
        "wordpressRequired": False,
        "clientNamespace": "/standalone/v1/client",
        "clientContractVersion": "1.0",
        "configHash": cfg["configHash"],
        "adapterHash": adapter["adapterHash"],
    }


@router.get("/v10103/status")
def status_route():
    return status()


@router.get("/standalone/v1/client/config")
def client_config_route():
    return client_config()


@router.get("/standalone/v1/client/adapter")
def client_adapter_contract_route():
    return adapter_contract()


@router.get("/standalone/v1/client/capabilities")
def client_capabilities_route():
    return _adapt("capabilities", numerical_capabilities())


@router.post("/standalone/v1/client/plan")
def client_plan_route(req: PlanRequest):
    return _adapt("plan", plan_calculation(req))


@router.post("/standalone/v1/client/compute")
def client_compute_route(req: CalculationRequest):
    return _adapt("compute", execute_calculation(req))
