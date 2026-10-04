"""Workbench v12.0.0 — Standalone Workbench Application Shell.

Defines the canonical standalone application shell contract. FastAPI remains
the authoritative computation backend. The standalone browser application can
bootstrap, discover routes/capabilities, inspect backend readiness, and operate
without WordPress, wpApiSettings, or a WordPress REST nonce.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-standalone-app-shell-status/1.0"
MANIFEST_SCHEMA = "sc-workbench-standalone-app-manifest/1.0"
SHELL_SCHEMA = "sc-workbench-standalone-app-shell/1.0"

router = APIRouter(tags=["workbench-v1200-standalone-application-shell"])


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def application_manifest() -> Dict[str, Any]:
    body = {
        "schema": MANIFEST_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "applicationMode": "standalone-primary",
        "canonicalBackend": "FastAPI",
        "wordpressRequired": False,
        "wordpressRole": "optional-compatibility-adapter",
        "frontendAuthority": "standalone-app",
        "backendAuthority": "fastapi",
        "defaultApiBaseUrl": "https://workbench-api.sustainablecatalyst.com",
        "shell": {
            "rootRoute": "/",
            "calculatorRoute": "/calculator",
            "workspaceRoute": "/workspace",
            "graphsRoute": "/graphs",
            "historyRoute": "/history",
            "packagesRoute": "/packages",
            "settingsRoute": "/settings",
        },
        "phase": {
            "authentication": "planned-v12.1",
            "persistentProjectStore": "planned-v12.2",
            "calculatorWorkspace": "active-v12.3",
            "mathematicalRenderer": "active-v12.4",
            "notebookHistory": "active-v12.5",
            "reproducibilityBrowser": "active-v12.6",
            "wordpressEmbedDeepLink": "active-v12.7",
            "wordpressStateDependency": "eliminated-v12.8",
            "standaloneMigrationCertification": "active-v12.9",
            "v12ProductionConsolidation": "active-v12.10",
        },
    }
    body["manifestHash"] = _hash(body)
    return body


def route_registry() -> Dict[str, Any]:
    routes = [
        {"id": "home", "path": "/", "label": "Workbench", "available": True},
        {"id": "calculator", "path": "/calculator", "label": "Calculator", "available": True},
        {"id": "workspace", "path": "/workspace", "label": "Workspace", "available": True},
        {"id": "graphs", "path": "/graphs", "label": "Graphs", "available": True},
        {"id": "history", "path": "/history", "label": "History", "available": True},
        {"id": "packages", "path": "/packages", "label": "Reproducibility", "available": True},
        {"id": "settings", "path": "/settings", "label": "Settings", "available": True},
    ]
    body = {
        "schema": "sc-workbench-standalone-route-registry/1.0",
        "version": VERSION,
        "routes": routes,
        "defaultRoute": "/calculator",
        "unknownRouteFallback": "/calculator",
    }
    body["registryHash"] = _hash(body)
    return body


def shell_contract() -> Dict[str, Any]:
    manifest = application_manifest()
    routes = route_registry()
    body = {
        "schema": SHELL_SCHEMA,
        "version": VERSION,
        "application": {
            "product": PRODUCT_KEY,
            "name": PRODUCT_NAME,
            "mode": "standalone-primary",
        },
        "architecture": {
            "backend": "FastAPI",
            "frontend": "framework-neutral-static-shell",
            "wordpressRequired": False,
            "wordpressCanBeUnavailable": True,
            "authoritativeComputationInBrowser": False,
            "directBackendApi": True,
        },
        "startup": {
            "requiredChecks": [
                "/standalone/v1/health",
                "/standalone/v1/bootstrap",
                "/standalone/v1/app-manifest",
            ],
            "degradedModeAllowed": True,
            "backendUnavailableState": "offline",
        },
        "manifestHash": manifest["manifestHash"],
        "routeRegistryHash": routes["registryHash"],
    }
    body["shellHash"] = _hash(body)
    return body


def status() -> Dict[str, Any]:
    manifest = application_manifest()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Standalone Workbench Application Shell",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "applicationMode": "standalone-primary",
        "canonicalBackend": "FastAPI",
        "manifestHash": manifest["manifestHash"],
        "capabilities": {
            "standaloneApplicationShell": True,
            "directFastApiClient": True,
            "routeRegistry": True,
            "applicationManifest": True,
            "backendReadinessBootstrap": True,
            "offlineShellState": True,
            "wordpressOptionalCompatibility": True,
            "frameworkNeutralShell": True,
            "calculationEnginePreserved": True,
        },
    }


@router.get("/v1200/status")
def status_route():
    return status()


@router.get("/standalone/v1/app-manifest")
def app_manifest_route():
    return {"ok": True, "version": VERSION, "manifest": application_manifest()}


@router.get("/standalone/v1/app-routes")
def app_routes_route():
    return {"ok": True, "version": VERSION, "routeRegistry": route_registry()}


@router.get("/standalone/v1/app-shell")
def app_shell_route():
    return {"ok": True, "version": VERSION, "shell": shell_contract()}
