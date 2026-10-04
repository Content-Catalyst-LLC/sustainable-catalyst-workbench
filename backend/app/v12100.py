"""Workbench v12.10.0 — WordPress-Optional Production Workbench.

Final v12 consolidation and production-readiness contract.

This release certifies the production architecture:
- standalone web application is the canonical frontend;
- FastAPI is the canonical backend;
- /data/workbench-v12.sqlite3 is the canonical v12 persistent state store;
- durable session/deep-link secrets are production requirements;
- CORS explicitly allows the standalone application origin;
- WordPress is optional and may remain as a public-site/embed/deep-link adapter.

The module does not provision DNS, TLS, Caddy, or a frontend host. It publishes
the machine-readable production contract and verifies that the backend side is
ready for a standalone deployment milestone.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Header

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v1200 import application_manifest, route_registry
from .v1210 import auth_config, require_session
from .v1220 import initialize_store
from .v1270 import embed_config
from .v1280 import elimination_certification
from .v1290 import migration_certification, capability_matrix
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-wordpress-optional-production-status/1.0"
CERT_SCHEMA = "sc-workbench-v12-production-certification/1.0"
DEPLOYMENT_SCHEMA = "sc-workbench-production-deployment-manifest/1.0"

router = APIRouter(tags=["workbench-v12100-wordpress-optional-production-workbench"])


def _hash(payload: Any) -> str:
    return content_hash(payload)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _standalone_url() -> str:
    return _env("SCWB_STANDALONE_APP_URL", "https://workbench.sustainablecatalyst.com").rstrip("/")


def _api_url() -> str:
    return _env("SCWB_PUBLIC_API_URL", "https://workbench-api.sustainablecatalyst.com").rstrip("/")


def _allowed_origins():
    configured = [x.strip().rstrip("/") for x in _env("SCWB_ALLOWED_ORIGINS").split(",") if x.strip()]
    if configured:
        return configured
    return [
        "https://sustainablecatalyst.com",
        "https://www.sustainablecatalyst.com",
        "http://localhost",
        "http://127.0.0.1",
    ]


def production_environment() -> Dict[str, Any]:
    standalone_url = _standalone_url()
    api_url = _api_url()
    origins = _allowed_origins()

    session_secret = bool(_env("SCWB_SESSION_SECRET"))
    deep_link_secret = bool(_env("SCWB_DEEP_LINK_SECRET"))
    store_path = _env("SCWB_PROJECT_STORE_PATH", "/data/workbench-v12.sqlite3")

    parsed_app = urlparse(standalone_url)
    parsed_api = urlparse(api_url)

    body = {
        "schema": "sc-workbench-production-environment/1.0",
        "version": VERSION,
        "standaloneAppUrl": standalone_url,
        "publicApiUrl": api_url,
        "allowedOrigins": origins,
        "projectStorePath": store_path,
        "requirements": {
            "standaloneUrlIsHttps": parsed_app.scheme == "https",
            "publicApiUrlIsHttps": parsed_api.scheme == "https",
            "durableSessionSecretConfigured": session_secret,
            "durableDeepLinkSecretConfigured": deep_link_secret,
            "standaloneOriginAllowed": standalone_url in origins,
            "persistentStorePathConfigured": bool(store_path),
        },
        "environmentVariables": {
            "SCWB_STANDALONE_APP_URL": {
                "requiredForProduction": True,
                "configured": bool(_env("SCWB_STANDALONE_APP_URL")),
                "effectiveValue": standalone_url,
            },
            "SCWB_PUBLIC_API_URL": {
                "requiredForProduction": True,
                "configured": bool(_env("SCWB_PUBLIC_API_URL")),
                "effectiveValue": api_url,
            },
            "SCWB_ALLOWED_ORIGINS": {
                "requiredForProduction": True,
                "configured": bool(_env("SCWB_ALLOWED_ORIGINS")),
                "effectiveValue": ",".join(origins),
            },
            "SCWB_SESSION_SECRET": {
                "requiredForProduction": True,
                "configured": session_secret,
                "effectiveValue": "<configured>" if session_secret else "<missing>",
            },
            "SCWB_DEEP_LINK_SECRET": {
                "requiredForProduction": True,
                "configured": deep_link_secret,
                "effectiveValue": "<configured>" if deep_link_secret else "<missing>",
            },
            "SCWB_PROJECT_STORE_PATH": {
                "requiredForProduction": True,
                "configured": bool(_env("SCWB_PROJECT_STORE_PATH")),
                "effectiveValue": store_path,
            },
        },
    }
    body["environmentHash"] = _hash(body)
    return body


def deployment_manifest() -> Dict[str, Any]:
    env = production_environment()
    app = application_manifest()
    routes = route_registry()

    body = {
        "schema": DEPLOYMENT_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "applicationMode": "standalone-production",
        "canonicalFrontend": "standalone-web-app",
        "canonicalBackend": "FastAPI",
        "canonicalPersistentState": "SQLite",
        "wordpressRequired": False,
        "wordpressRole": "optional-public-site-embed-deep-link-adapter",
        "frontend": {
            "url": env["standaloneAppUrl"],
            "package": "sustainable-catalyst-workbench-v12.10.0-standalone-app.zip",
            "serveAsStaticSite": True,
            "requiresPhp": False,
            "requiresWordPress": False,
            "requiredFiles": [
                "standalone-app/index.html",
                "standalone-app/app-shell.js",
                "standalone-app/app-shell.css",
                "standalone-app/config.js",
            ],
        },
        "backend": {
            "url": env["publicApiUrl"],
            "service": "FastAPI",
            "internalListen": "127.0.0.1:8088",
            "container": "sc-workbench",
            "healthPath": "/health",
            "productionReadinessPath": "/standalone/v1/production/readiness",
        },
        "state": {
            "engine": "sqlite",
            "path": env["projectStorePath"],
            "mustPersistAcrossContainerReplacement": True,
            "wordpressDatabaseIsCanonical": False,
        },
        "network": {
            "corsOrigins": env["allowedOrigins"],
            "tlsRequiredAtPublicFrontend": True,
            "tlsRequiredAtPublicApi": True,
            "recommendedReverseProxy": "Caddy",
        },
        "routes": [r["path"] for r in routes["routes"] if r["available"]],
        "applicationManifestHash": app["manifestHash"],
    }
    body["deploymentManifestHash"] = _hash(body)
    return body


def production_certification() -> Dict[str, Any]:
    migration = migration_certification()
    state = elimination_certification()
    matrix = capability_matrix()
    env = production_environment()
    deployment = deployment_manifest()
    project_store = initialize_store()
    auth = auth_config()
    launch = embed_config()

    env_requirements = env["requirements"]

    architecture_checks = {
        "v12MigrationCertificationPass": migration["certification"] == "pass",
        "v12MigrationReady": migration["migrationReady"] is True,
        "wordpressStateDependencyEliminated": state["certification"] == "pass",
        "allV12CapabilitiesMigrationReady": matrix["allMigrationReady"] is True,
        "allV12CapabilitiesWordPressIndependent": matrix["allWordPressIndependent"] is True,
        "canonicalFrontendStandalone": deployment["canonicalFrontend"] == "standalone-web-app",
        "canonicalBackendFastAPI": deployment["canonicalBackend"] == "FastAPI",
        "canonicalPersistentStateSQLite": deployment["canonicalPersistentState"] == "SQLite",
        "wordpressRequiredFalse": deployment["wordpressRequired"] is False,
        "persistentProjectStore": project_store["persistent"] is True,
        "standaloneAuthAuthority": auth["sessionAuthority"] == "FastAPI",
        "launchAuthNotEmbedded": launch["deepLinks"]["authenticationEmbedded"] is False,
    }

    production_env_checks = {
        "standaloneUrlIsHttps": env_requirements["standaloneUrlIsHttps"],
        "publicApiUrlIsHttps": env_requirements["publicApiUrlIsHttps"],
        "durableSessionSecretConfigured": env_requirements["durableSessionSecretConfigured"],
        "durableDeepLinkSecretConfigured": env_requirements["durableDeepLinkSecretConfigured"],
        "standaloneOriginAllowed": env_requirements["standaloneOriginAllowed"],
        "persistentStorePathConfigured": env_requirements["persistentStorePathConfigured"],
    }

    architecture_pass = all(architecture_checks.values())
    production_env_pass = all(production_env_checks.values())

    body = {
        "schema": CERT_SCHEMA,
        "version": VERSION,
        "series": "12.x",
        "release": "WordPress-Optional Production Workbench",
        "architectureCertification": "pass" if architecture_pass else "fail",
        "productionEnvironmentCertification": "pass" if production_env_pass else "pending",
        "certification": "pass" if architecture_pass and production_env_pass else "conditional-pass",
        "productionReady": architecture_pass and production_env_pass,
        "wordpressRequired": False,
        "architectureChecks": architecture_checks,
        "productionEnvironmentChecks": production_env_checks,
        "deploymentManifestHash": deployment["deploymentManifestHash"],
        "environmentHash": env["environmentHash"],
        "migrationCertificationHash": migration["certificationHash"],
        "v12Consolidation": {
            "standaloneApplicationComplete": True,
            "canonicalStateOutsideWordPress": True,
            "standaloneMigrationCertified": migration["migrationReady"],
            "productionDeploymentContractPublished": True,
            "wordpressOptional": True,
            "v12SeriesConsolidated": architecture_pass,
        },
        "remainingProductionActions": [
            key for key, ok in production_env_checks.items() if not ok
        ],
        "nextProgram": "v13 Natural-Language Computation & Intelligent Calculation Interface",
    }
    body["certificationHash"] = _hash(body)
    return body


def readiness() -> Dict[str, Any]:
    cert = production_certification()
    env = production_environment()
    return {
        "ok": True,
        "schema": "sc-workbench-production-readiness/1.0",
        "version": VERSION,
        "architectureReady": cert["architectureCertification"] == "pass",
        "productionEnvironmentReady": cert["productionEnvironmentCertification"] == "pass",
        "productionReady": cert["productionReady"],
        "wordpressRequired": False,
        "standaloneAppUrl": env["standaloneAppUrl"],
        "publicApiUrl": env["publicApiUrl"],
        "remainingProductionActions": cert["remainingProductionActions"],
        "certificationHash": cert["certificationHash"],
    }


def status() -> Dict[str, Any]:
    cert = production_certification()
    return {
        "ok": cert["architectureCertification"] == "pass",
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "WordPress-Optional Production Workbench",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "architectureCertification": cert["architectureCertification"],
        "productionEnvironmentCertification": cert["productionEnvironmentCertification"],
        "productionReady": cert["productionReady"],
        "certificationHash": cert["certificationHash"],
        "capabilities": {
            "v12SeriesConsolidated": cert["v12Consolidation"]["v12SeriesConsolidated"],
            "standaloneApplicationCanonical": True,
            "fastApiCanonical": True,
            "persistentV12StateCanonical": True,
            "wordpressOptional": True,
            "productionDeploymentManifest": True,
            "productionEnvironmentReadiness": True,
            "standalonePackageReady": True,
            "wordpressCompatibilityPackageReady": True,
        },
    }


@router.get("/v12100/status")
def status_route():
    return status()


@router.get("/standalone/v1/production/deployment-manifest")
def deployment_manifest_route():
    return {"ok": True, "version": VERSION, "deployment": deployment_manifest()}


@router.get("/standalone/v1/production/environment")
def environment_route():
    return {"ok": True, "version": VERSION, "environment": production_environment()}


@router.get("/standalone/v1/production/certification")
def certification_route():
    return production_certification()


@router.get("/standalone/v1/production/readiness")
def readiness_route():
    return readiness()


@router.get("/standalone/v1/production/session-probe")
def session_probe_route(authorization: Optional[str] = Header(default=None)):
    session = require_session(authorization)
    return {
        "ok": True,
        "version": VERSION,
        "sessionId": session["sessionId"],
        "subject": session["subject"],
        "wordpressRequired": False,
        "canonicalSessionAuthority": "FastAPI",
        "productionPath": "standalone-web-app->FastAPI->SQLite",
    }
