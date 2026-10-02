"""Workbench v10.10.1 — WordPress Dependency Inventory & Routing Isolation."""
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter
from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash

VERSION = APP_VERSION
SCHEMA = "sc-workbench-decoupling-inventory/1.0"
ROUTING_SCHEMA = "sc-workbench-routing-isolation-policy/1.0"
ADAPTER_SCHEMA = "sc-workbench-optional-adapter-contract/1.0"

router = APIRouter(tags=["workbench-v10101-decoupling-routing-isolation"])

def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)

def dependency_inventory() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "canonicalApplication": "FastAPI",
        "wordpressRequired": False,
        "backendRequired": True,
        "dependencyGroups": {
            "canonicalBackend": [
                {"name": "fastapi", "role": "HTTP application and API routing", "required": True},
                {"name": "pydantic", "role": "runtime contracts and validation", "required": True},
                {"name": "sympy", "role": "symbolic and exact mathematics", "required": True},
                {"name": "numpy", "role": "array and linear algebra runtime", "required": True},
                {"name": "scipy", "role": "numerical methods runtime", "required": True},
                {"name": "pint", "role": "unit-aware calculation runtime", "required": True},
            ],
            "optionalAdapters": [
                {
                    "name": "wordpress",
                    "role": "optional presentation, shortcode, and same-origin proxy adapter",
                    "required": False,
                    "authoritativeComputation": False,
                    "canonicalState": False,
                }
            ],
            "futureStandaloneClients": [
                {
                    "name": "standalone-web-client",
                    "role": "first-party web client consuming canonical backend contracts",
                    "requiredForBackend": False,
                }
            ],
        },
        "stateOwnership": {
            "calculationExecution": "backend",
            "calculationResults": "backend-contract",
            "calculationProvenance": "backend-contract",
            "runtimeConfiguration": "backend",
            "wordpressStateCanonical": False,
        },
    }
    body["inventoryHash"] = _hash({k: v for k, v in body.items() if k not in {"ok", "inventoryHash"}})
    return body

def routing_policy() -> Dict[str, Any]:
    backend_routes: List[Dict[str, Any]] = [
        {"path": "/health", "method": "GET", "owner": "backend", "authoritative": True},
        {"path": "/v10100/status", "method": "GET", "owner": "backend", "authoritative": True},
        {"path": "/numerical/capabilities", "method": "GET", "owner": "backend", "authoritative": True},
        {"path": "/numerical/plan", "method": "POST", "owner": "backend", "authoritative": True},
        {"path": "/numerical/compute", "method": "POST", "owner": "backend", "authoritative": True},
        {"path": "/standalone/bootstrap", "method": "GET", "owner": "backend", "authoritative": True},
        {"path": "/v10101/status", "method": "GET", "owner": "backend", "authoritative": True},
        {"path": "/decoupling/dependencies", "method": "GET", "owner": "backend", "authoritative": True},
        {"path": "/decoupling/routes", "method": "GET", "owner": "backend", "authoritative": True},
    ]
    adapter_routes = [
        {"wordpressPath": "/wp-json/sc-workbench/v1/v10101/dependencies", "backendPath": "/decoupling/dependencies", "mode": "read-only-proxy"},
        {"wordpressPath": "/wp-json/sc-workbench/v1/v10101/routes", "backendPath": "/decoupling/routes", "mode": "read-only-proxy"},
        {"wordpressPath": "/wp-json/sc-workbench/v1/v10101/status", "backendPath": "/v10101/status", "mode": "read-only-proxy"},
    ]
    body = {
        "ok": True,
        "schema": ROUTING_SCHEMA,
        "version": VERSION,
        "wordpressRequired": False,
        "canonicalRouteOwner": "backend",
        "backendRoutes": backend_routes,
        "optionalAdapterRoutes": adapter_routes,
        "isolationRules": {
            "wordpressMayProxyBackend": True,
            "wordpressMayExecuteAuthoritativeMath": False,
            "wordpressMayOwnCanonicalCalculationState": False,
            "wordpressMayReplaceBackendContracts": False,
            "standaloneClientMayCallBackendDirectly": True,
            "backendMayRunWithoutWordPress": True,
        },
        "migrationRules": {
            "newComputationRoutesMustLandInBackendFirst": True,
            "wordpressRoutesMustBeAdaptersOrPresentationOnly": True,
            "standaloneRoutesMustNotDependOnWpRestNonce": True,
            "sharedContractsMustRemainClientAgnostic": True,
        },
    }
    body["routingPolicyHash"] = _hash({k: v for k, v in body.items() if k not in {"ok", "routingPolicyHash"}})
    return body

def adapter_contract() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": ADAPTER_SCHEMA,
        "version": VERSION,
        "adapter": "wordpress",
        "required": False,
        "role": "optional-presentation-and-proxy-adapter",
        "canonicalBackend": "FastAPI",
        "capabilities": {
            "renderWorkbenchUI": True,
            "proxyBackendReadRoutes": True,
            "proxyBackendComputeRoutes": True,
            "executeAuthoritativeMath": False,
            "ownCanonicalRuntimeState": False,
            "requiredForStandalone": False,
        },
        "removalTest": {
            "backendStartsWithoutWordPress": True,
            "healthRouteAvailableWithoutWordPress": True,
            "numericalComputeAvailableWithoutWordPress": True,
            "standaloneBootstrapAvailableWithoutWordPress": True,
        },
    }
    body["adapterContractHash"] = _hash({k: v for k, v in body.items() if k not in {"ok", "adapterContractHash"}})
    return body

def status() -> Dict[str, Any]:
    deps = dependency_inventory()
    routes = routing_policy()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "WordPress Dependency Inventory & Routing Isolation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "backendFirst": True,
        "wordpressRequired": False,
        "canonicalApplication": "FastAPI",
        "dependencyInventoryReady": True,
        "routingIsolationReady": True,
        "standaloneMigrationReady": True,
        "inventoryHash": deps["inventoryHash"],
        "routingPolicyHash": routes["routingPolicyHash"],
    }

@router.get("/v10101/status")
def status_route():
    return status()

@router.get("/decoupling/dependencies")
def dependency_inventory_route():
    return dependency_inventory()

@router.get("/decoupling/routes")
def routing_policy_route():
    return routing_policy()

@router.get("/decoupling/adapters/wordpress")
def wordpress_adapter_contract_route():
    return adapter_contract()
