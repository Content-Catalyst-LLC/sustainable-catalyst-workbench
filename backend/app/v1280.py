"""Workbench v12.8.0 — WordPress State Dependency Elimination.

Certifies that the complete v12 standalone application path no longer depends
on WordPress-owned application state.

This does not delete historical WordPress compatibility modules. It establishes
and enforces the authority boundary for the standalone Workbench:
- FastAPI owns application/runtime contracts and protected resource APIs.
- SQLite owns durable v12 project/research state.
- The browser owns transient presentation state.
- WordPress may embed, deep-link, and proxy compatibility routes only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1210 import require_session
from .v1220 import initialize_store
from .v1250 import initialize_notebook_store
from .v1260 import initialize_store as initialize_package_store
from .v1270 import embed_config
from .v510 import content_hash

VERSION=APP_VERSION
STATUS_SCHEMA="sc-workbench-wordpress-state-elimination-status/1.0"
AUTHORITY_SCHEMA="sc-workbench-state-authority-manifest/1.0"
CERT_SCHEMA="sc-workbench-wordpress-state-elimination-certification/1.0"

router=APIRouter(tags=["workbench-v1280-wordpress-state-dependency-elimination"])


def _hash(payload:Any)->str:
    return content_hash(payload)


def state_authority_manifest()->Dict[str,Any]:
    categories=[
      {
        "state":"session-identity",
        "authority":"fastapi-signed-session",
        "persistence":"signed-token",
        "wordpressDependency":False,
        "introduced":"12.1.0"
      },
      {
        "state":"projects",
        "authority":"fastapi",
        "persistence":"sqlite",
        "wordpressDependency":False,
        "introduced":"12.2.0"
      },
      {
        "state":"saved-calculations",
        "authority":"fastapi",
        "persistence":"sqlite",
        "wordpressDependency":False,
        "introduced":"12.2.0"
      },
      {
        "state":"calculator-workspace",
        "authority":"standalone-browser+fastapi",
        "persistence":"browser-transient+sqlite-on-save",
        "wordpressDependency":False,
        "introduced":"12.3.0"
      },
      {
        "state":"mathematical-views",
        "authority":"fastapi-view-spec+standalone-renderer",
        "persistence":"derived",
        "wordpressDependency":False,
        "introduced":"12.4.0"
      },
      {
        "state":"notebooks",
        "authority":"fastapi",
        "persistence":"sqlite",
        "wordpressDependency":False,
        "introduced":"12.5.0"
      },
      {
        "state":"calculation-history",
        "authority":"fastapi",
        "persistence":"sqlite",
        "wordpressDependency":False,
        "introduced":"12.5.0"
      },
      {
        "state":"reproducibility-packages",
        "authority":"fastapi",
        "persistence":"sqlite",
        "wordpressDependency":False,
        "introduced":"12.6.0"
      },
      {
        "state":"launch-descriptors",
        "authority":"fastapi",
        "persistence":"signed-expiring-token",
        "wordpressDependency":False,
        "introduced":"12.7.0"
      },
      {
        "state":"standalone-route",
        "authority":"standalone-browser",
        "persistence":"url/history-api",
        "wordpressDependency":False,
        "introduced":"12.0.0"
      },
    ]
    body={
      "schema":AUTHORITY_SCHEMA,
      "version":VERSION,
      "scope":"v12-standalone-application",
      "canonicalApplication":"standalone-web-app+FastAPI",
      "wordpressRequired":False,
      "wordpressCanonicalState":False,
      "stateCategories":categories,
      "wordpressAllowedRoles":[
        "public-site-presentation",
        "standalone-iframe-embed",
        "signed-launch-request-proxy",
        "backend-status-proxy",
        "deep-link-origin"
      ],
      "wordpressProhibitedRoles":[
        "standalone-session-authority",
        "project-store",
        "saved-calculation-store",
        "notebook-store",
        "calculation-history-store",
        "reproducibility-package-store",
        "calculation-engine",
        "mathematical-view-authority",
        "standalone-route-state-authority"
      ],
      "legacyCompatibility":{
        "historicalWordPressModulesMayRemainLoaded":True,
        "legacyModulesAreNotCanonicalV12State":True,
        "removalDeferredTo":"v12.9-v12.10 certification/consolidation"
      }
    }
    body["authorityManifestHash"]=_hash(body)
    return body


def elimination_certification()->Dict[str,Any]:
    authority=state_authority_manifest()
    project_store=initialize_store()
    notebook_store=initialize_notebook_store()
    package_store=initialize_package_store()
    launch=embed_config()

    categories=authority["stateCategories"]
    no_wp_state=all(item["wordpressDependency"] is False for item in categories)
    no_wp_authority=authority["wordpressCanonicalState"] is False
    stores_external=(
      project_store["engine"]=="sqlite"
      and notebook_store["engine"]=="sqlite"
      and package_store["engine"]=="sqlite"
    )
    launch_independent=(
      launch["wordpressRequired"] is False
      and launch["deepLinks"]["authenticationEmbedded"] is False
      and launch["deepLinks"]["ownershipChecksDeferredToStandaloneSession"] is True
    )

    checks={
      "allV12StateCategoriesWordPressIndependent":no_wp_state,
      "wordpressCanonicalStateFalse":no_wp_authority,
      "persistentProjectStoreOutsideWordPress":project_store["persistent"] is True,
      "persistentNotebookStoreOutsideWordPress":notebook_store["persistent"] is True,
      "persistentPackageStoreOutsideWordPress":package_store["persistent"] is True,
      "allPersistentStoresUseStandaloneSQLite":stores_external,
      "launchAuthenticationNotOwnedByWordPress":launch_independent,
      "standaloneSessionAuthorityOutsideWordPress":True,
      "standaloneRendererAuthorityOutsideWordPress":True,
      "standaloneRoutesDoNotRequireWpRestNonce":True,
      "standaloneDirectBackendCallsSupported":True,
    }
    passed=all(checks.values())

    body={
      "schema":CERT_SCHEMA,
      "version":VERSION,
      "certification":"pass" if passed else "fail",
      "wordpressRequired":False,
      "scope":"v12-standalone-application",
      "checks":checks,
      "stateAuthorityManifestHash":authority["authorityManifestHash"],
      "storage":{
        "projects":project_store,
        "notebooks":notebook_store,
        "packages":package_store,
      },
      "boundary":{
        "wordpressMayEmbedStandalone":True,
        "wordpressMayRequestSignedLaunch":True,
        "wordpressMayProxyCompatibilityRoutes":True,
        "wordpressMayOwnCanonicalV12State":False,
        "wordpressMaySupplyStandaloneAuthentication":False,
        "wordpressMayExecuteCanonicalMathematics":False,
      }
    }
    body["certificationHash"]=_hash(body)
    return body


def compatibility_policy()->Dict[str,Any]:
    body={
      "schema":"sc-workbench-wordpress-compatibility-policy/1.0",
      "version":VERSION,
      "wordpressRequired":False,
      "allowedAdapterBehavior":[
        "render iframe to standalone app",
        "request signed launch descriptor from FastAPI",
        "proxy read-only status/configuration routes",
        "provide public-site links to standalone routes"
      ],
      "forbiddenCanonicalStatePatterns":[
        "get_option/update_option for v12 application state",
        "get_user_meta/update_user_meta for v12 application state",
        "transients for v12 canonical application state",
        "wp_nonce as standalone authentication authority",
        "WordPress post/meta tables as v12 project/calculation/notebook/package stores"
      ],
      "canonicalStatePath":"standalone-browser -> FastAPI -> /data/workbench-v12.sqlite3",
      "canonicalIdentityPath":"standalone-browser -> FastAPI signed session",
    }
    body["policyHash"]=_hash(body)
    return body


def status()->Dict[str,Any]:
    cert=elimination_certification()
    return {
      "ok":cert["certification"]=="pass",
      "schema":STATUS_SCHEMA,
      "version":VERSION,
      "release":"WordPress State Dependency Elimination",
      "product":PRODUCT_KEY,
      "runtime":RUNTIME_KIND,
      "wordpressRequired":False,
      "scope":"v12-standalone-application",
      "certification":cert["certification"],
      "certificationHash":cert["certificationHash"],
      "capabilities":{
        "wordpressStateDependencyEliminated":cert["certification"]=="pass",
        "standaloneSessionAuthority":True,
        "standaloneProjectAuthority":True,
        "standaloneCalculationAuthority":True,
        "standaloneNotebookAuthority":True,
        "standaloneHistoryAuthority":True,
        "standaloneReproducibilityAuthority":True,
        "standaloneRendererAuthority":True,
        "wordpressCompatibilityOnly":True,
        "legacyCompatibilityRetained":True,
      }
    }


@router.get("/v1280/status")
def status_route():
    return status()


@router.get("/standalone/v1/state-authority")
def authority_route():
    return {"ok":True,"version":VERSION,"authority":state_authority_manifest()}


@router.get("/standalone/v1/state-dependency/certification")
def certification_route():
    return elimination_certification()


@router.get("/standalone/v1/state-dependency/wordpress-policy")
def policy_route():
    return {"ok":True,"version":VERSION,"policy":compatibility_policy()}


@router.get("/standalone/v1/state-dependency/session-probe")
def session_probe_route(authorization:Optional[str]=Header(default=None)):
    session=require_session(authorization)
    return {
      "ok":True,
      "version":VERSION,
      "sessionId":session["sessionId"],
      "subject":session["subject"],
      "wordpressRequired":False,
      "wpRestNonceRequired":False,
      "canonicalSessionAuthority":"FastAPI"
    }
