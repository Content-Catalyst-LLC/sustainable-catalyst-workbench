"""Workbench v6.0.1 — Unified Experience, Runtime Identity & Interface Hardening.

Patch-status surface for the v6 unified Workbench. v6.0.1 keeps the bounded
v6.0 computational-project API while certifying one release identity across
backend, WordPress, primary studio router, graph runtime, and public experience.
"""
from fastapi import APIRouter

VERSION = "6.0.1"
SCHEMA = "sc-workbench-unified-experience-status/1.0"
router = APIRouter(prefix="/v601", tags=["workbench-v601-unified-experience"])


def status_record():
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "inheritsComputationalProjectContract": "/v600",
        "capabilities": [
            "canonical-release-identity",
            "unified-public-experience",
            "grouped-studio-navigation",
            "studio-search-and-filtering",
            "browser-favorites-and-recents",
            "internal-studio-navigation-scroll",
            "graph-resize-observation",
            "graph-studio-activation-redraw",
            "normal-flow-public-graph",
            "shortcode-registration-certification",
        ],
        "homepageInstrumentOnWorkbenchPage": False,
        "automaticCodeExecutionAuthorized": False,
        "remoteShellAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
    }


@router.get("/status")
def status():
    return status_record()
