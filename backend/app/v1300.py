"""Workbench v13.0.0 — Functional Standalone Workbench Interface."""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Header

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v1210 import require_session
from .v1220 import initialize_store as initialize_project_store
from .v1250 import initialize_notebook_store
from .v1260 import initialize_store as initialize_package_store
from .v12100 import production_certification
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-functional-standalone-interface-status/1.0"
CAPABILITY_SCHEMA = "sc-workbench-functional-interface-capabilities/1.0"

router = APIRouter(tags=["workbench-v1300-functional-standalone-interface"])


def _hash(payload: Any) -> str:
    return content_hash(payload)


def capability_manifest() -> Dict[str, Any]:
    body = {
        "schema": CAPABILITY_SCHEMA,
        "version": VERSION,
        "interfaceMode": "functional-standalone",
        "canonicalFrontend": "standalone-web-app",
        "canonicalBackend": "FastAPI",
        "wordpressRequired": False,
        "routes": {
            "home": "/",
            "calculator": "/calculator",
            "workspace": "/workspace",
            "graphs": "/graphs",
            "history": "/history",
            "packages": "/packages",
            "settings": "/settings",
        },
        "workflows": {
            "sessionBootstrap": True,
            "projectCreateSelect": True,
            "calculationExecute": True,
            "calculationSave": True,
            "graphViewSpec": True,
            "graphBrowserRenderer": True,
            "notebookCreate": True,
            "notebookEntries": True,
            "projectHistory": True,
            "projectTimeline": True,
            "reproducibilityCapture": True,
            "reproducibilityVerify": True,
            "reproducibilityReplay": True,
            "deepLinkResolution": True,
        },
        "browserResponsibilities": {
            "renderApplicationShell": True,
            "renderMathematicalViews": True,
            "maintainEphemeralSessionToken": True,
            "callFastApiDirectly": True,
            "performCanonicalMathematics": False,
            "ownCanonicalProjectState": False,
        },
    }
    body["manifestHash"] = _hash(body)
    return body


def functional_readiness() -> Dict[str, Any]:
    production = production_certification()
    project_store = initialize_project_store()
    notebook_store = initialize_notebook_store()
    package_store = initialize_package_store()
    capabilities = capability_manifest()

    checks = {
        "productionArchitectureCertified": production["architectureCertification"] == "pass",
        "productionEnvironmentCertified": production["productionEnvironmentCertification"] == "pass",
        "projectStorePersistent": project_store["persistent"] is True,
        "notebookStorePersistent": notebook_store["persistent"] is True,
        "packageStorePersistent": package_store["persistent"] is True,
        "functionalBrowserWorkflowsDeclared": all(capabilities["workflows"].values()),
        "wordpressRequiredFalse": capabilities["wordpressRequired"] is False,
    }

    body = {
        "ok": all(checks.values()),
        "schema": "sc-workbench-functional-interface-readiness/1.0",
        "version": VERSION,
        "functionalReady": all(checks.values()),
        "checks": checks,
        "projectStore": project_store,
        "notebookStore": notebook_store,
        "packageStore": package_store,
        "capabilityManifestHash": capabilities["manifestHash"],
    }
    body["readinessHash"] = _hash(body)
    return body


def status() -> Dict[str, Any]:
    readiness = functional_readiness()
    capabilities = capability_manifest()
    return {
        "ok": readiness["functionalReady"],
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Functional Standalone Workbench Interface",
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "applicationMode": "standalone-functional",
        "wordpressRequired": False,
        "frontendAuthority": "standalone-app",
        "backendAuthority": "FastAPI",
        "functionalReady": readiness["functionalReady"],
        "capabilities": capabilities["workflows"],
        "manifestHash": capabilities["manifestHash"],
        "readinessHash": readiness["readinessHash"],
    }


@router.get("/v1300/status")
def status_route():
    return status()


@router.get("/standalone/v1/interface/capabilities")
def capabilities_route():
    return {"ok": True, "version": VERSION, "capabilities": capability_manifest()}


@router.get("/standalone/v1/interface/readiness")
def readiness_route():
    return functional_readiness()


@router.get("/standalone/v1/interface/session-probe")
def session_probe_route(authorization: Optional[str] = Header(default=None)):
    session = require_session(authorization)
    return {
        "ok": True,
        "version": VERSION,
        "sessionId": session["sessionId"],
        "subject": session["subject"],
        "functionalStandalone": True,
        "wordpressRequired": False,
    }
