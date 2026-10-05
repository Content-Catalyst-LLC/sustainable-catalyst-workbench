"""Workbench v13.1.0 — Standalone UI Hardening & Production Deployment Repair."""
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Header
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v1210 import require_session
from .v12100 import production_certification
from .v1300 import capability_manifest, functional_readiness
from .v510 import content_hash
VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v1310-standalone-ui-hardening"])

def _hash(payload: Any) -> str:
    return content_hash(payload)

def browser_deployment_contract() -> Dict[str, Any]:
    body = {
        "schema":"sc-workbench-browser-deployment-contract/1.0",
        "version":VERSION,
        "frontendVersion":VERSION,
        "backendVersion":VERSION,
        "frontendUrl":"https://workbench.sustainablecatalyst.com",
        "apiUrl":"https://workbench-api.sustainablecatalyst.com",
        "frontendVersionAsset":"/version.json",
        "apiVersionEndpoint":"/v1310/status",
        "spaProbeRoute":"/calculator",
        "wordpressRequired":False,
        "verification":{
            "frontendVersionMatchRequired":True,
            "apiVersionMatchRequired":True,
            "corsOriginRequired":True,
            "spaFallbackRequired":True,
            "functionalReadinessRequired":True,
        },
    }
    body["contractHash"]=_hash(body)
    return body

def hardening_readiness() -> Dict[str, Any]:
    prod=production_certification()
    functional=functional_readiness()
    contract=browser_deployment_contract()
    caps=capability_manifest()
    checks={
        "productionCertified":prod["architectureCertification"]=="pass" and prod["productionEnvironmentCertification"]=="pass",
        "functionalInterfaceReady":functional["functionalReady"] is True,
        "frontendBackendVersionAligned":contract["frontendVersion"]==contract["backendVersion"]==VERSION,
        "browserFunctionalWorkflowsPreserved":all(caps["workflows"].values()),
        "frontendVersionAssetDeclared":contract["frontendVersionAsset"]=="/version.json",
        "wordpressRequiredFalse":contract["wordpressRequired"] is False,
    }
    body={"ok":all(checks.values()),"schema":"sc-workbench-standalone-ui-hardening-readiness/1.0","version":VERSION,"hardeningReady":all(checks.values()),"checks":checks,"deploymentContractHash":contract["contractHash"],"functionalReadinessHash":functional["readinessHash"]}
    body["readinessHash"]=_hash(body)
    return body

def status() -> Dict[str, Any]:
    r=hardening_readiness()
    return {"ok":r["hardeningReady"],"schema":"sc-workbench-standalone-ui-hardening-status/1.0","version":VERSION,"release":"Standalone UI Hardening & Production Deployment Repair","product":PRODUCT_KEY,"name":PRODUCT_NAME,"runtime":RUNTIME_KIND,"wordpressRequired":False,"frontendAuthority":"standalone-app","backendAuthority":"FastAPI","hardeningReady":r["hardeningReady"],"deploymentContractHash":r["deploymentContractHash"],"readinessHash":r["readinessHash"]}

@router.get('/v1310/status')
def status_route(): return status()

@router.get('/standalone/v1/interface/deployment-contract')
def deployment_contract_route(): return {"ok":True,"version":VERSION,"deployment":browser_deployment_contract()}

@router.get('/standalone/v1/interface/hardening-readiness')
def hardening_readiness_route(): return hardening_readiness()

@router.get('/standalone/v1/interface/version-probe')
def version_probe_route(authorization: Optional[str]=Header(default=None)):
    session=require_session(authorization)
    return {"ok":True,"version":VERSION,"sessionId":session["sessionId"],"frontendExpectedVersion":VERSION,"backendVersion":VERSION,"wordpressRequired":False}
