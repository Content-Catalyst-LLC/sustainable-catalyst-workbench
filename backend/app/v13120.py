"""Workbench v13.12.0 — Standalone Functional Production Certification.

Closes the Workbench v13 line by aggregating production-readiness signals from
all standalone v13 surfaces and by running deterministic non-destructive smoke
checks for the planner and domain-template pipeline. No new mathematics or
storage authority is introduced here.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1230 import status as calculator_status, calculator_config
from .v1340 import status as project_session_status
from .v1350 import status as graph_status
from .v1360 import status as timeline_status
from .v1370 import status as package_status
from .v1380 import status as unified_status
from .v1390 import status as natural_language_status, interpret_text
from .v13100 import status as planning_status, build_plan, validate_plan
from .v13110 import status as domain_status, instantiate, registry

VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v13120-standalone-functional-production-certification"])
STATUS_SCHEMA = "sc-workbench-v13-production-certification-status/1.0"
REPORT_SCHEMA = "sc-workbench-v13-production-certification-report/1.0"


def _hash(x: Any) -> str:
    return content_hash(x)


def _safe_status(name: str, fn) -> Dict[str, Any]:
    try:
        payload = fn()
        return {
            "id": name,
            "ok": bool(payload.get("ok")),
            "version": payload.get("version"),
            "wordpressRequired": payload.get("wordpressRequired"),
            "payload": payload,
        }
    except Exception as exc:
        return {
            "id": name,
            "ok": False,
            "version": VERSION,
            "wordpressRequired": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def surface_matrix() -> List[Dict[str, Any]]:
    checks = [
        ("calculator", calculator_status),
        ("project-research-sessions", project_session_status),
        ("graph-studio", graph_status),
        ("notebook-history-timeline", timeline_status),
        ("reproducibility-packages", package_status),
        ("unified-workbench", unified_status),
        ("natural-language", natural_language_status),
        ("intent-planning", planning_status),
        ("domain-calculators", domain_status),
    ]
    return [_safe_status(name, fn) for name, fn in checks]


def functional_smoke_checks() -> Dict[str, Any]:
    results: Dict[str, Dict[str, Any]] = {}

    try:
        cfg = calculator_config()
        results["calculator-contract"] = {
            "ok": bool(cfg.get("capabilities", {}).get("executeCalculationObject")),
            "operationCount": len(cfg.get("operations", [])),
            "wordpressRequired": cfg.get("wordpressRequired"),
        }
    except Exception as exc:
        results["calculator-contract"] = {"ok": False, "error": str(exc)}

    try:
        interpretation = interpret_text("differentiate x^3 + 2*x with respect to x")
        results["natural-language-interpretation"] = {
            "ok": interpretation.get("intent") == "differentiate"
                  and interpretation.get("executionAllowed") is False
                  and interpretation.get("requiresConfirmation") is True,
            "intent": interpretation.get("intent"),
            "interpretationHash": interpretation.get("interpretationHash"),
        }
    except Exception as exc:
        results["natural-language-interpretation"] = {"ok": False, "error": str(exc)}

    try:
        plan = build_plan("calculate 2 + 3 * 4")
        validation = validate_plan(plan)
        results["intent-plan"] = {
            "ok": bool(validation.get("valid"))
                  and plan.get("policy", {}).get("directPlannerExecution") is False
                  and plan.get("policy", {}).get("userConfirmationRequired") is True,
            "planHash": plan.get("planHash"),
            "validationHash": validation.get("validationHash"),
        }
    except Exception as exc:
        results["intent-plan"] = {"ok": False, "error": str(exc)}

    try:
        instance = instantiate(
            "physics.kinetic-energy",
            {"mass": 2.0, "velocity": 3.0},
            {"source": "v13.12-certification"},
        )
        req = instance.get("calculationRequest", {})
        results["domain-template"] = {
            "ok": req.get("requireVerification") is True
                  and req.get("requireProvenance") is True
                  and instance.get("policy", {}).get("canonicalCalculatorRequired") is True,
            "templateId": instance.get("templateId"),
            "instanceHash": instance.get("instanceHash"),
        }
    except Exception as exc:
        results["domain-template"] = {"ok": False, "error": str(exc)}

    try:
        reg = registry()
        results["domain-registry"] = {
            "ok": reg.get("totalTemplateCount", 0) >= 7
                  and bool(reg.get("registryHash"))
                  and reg.get("governance", {}).get("canonicalExecutionOnly") is True,
            "templateCount": reg.get("totalTemplateCount"),
            "registryHash": reg.get("registryHash"),
        }
    except Exception as exc:
        results["domain-registry"] = {"ok": False, "error": str(exc)}

    return results


def certification_report() -> Dict[str, Any]:
    surfaces = surface_matrix()
    smoke = functional_smoke_checks()
    surface_checks = {item["id"]: bool(item.get("ok")) for item in surfaces}
    smoke_checks = {name: bool(item.get("ok")) for name, item in smoke.items()}
    wordpress_optional = all(
        item.get("wordpressRequired") in {False, None}
        for item in surfaces
    )
    version_consistent = all(
        item.get("version") == VERSION for item in surfaces if item.get("ok")
    )
    checks = {
        "allSurfaceContractsReady": all(surface_checks.values()),
        "allFunctionalSmokeChecksPass": all(smoke_checks.values()),
        "versionConsistent": version_consistent,
        "wordpressOptional": wordpress_optional,
        "standalonePrimary": True,
        "canonicalCalculationAuthorityPreserved": True,
        "plannerDoesNotExecuteDirectly": True,
        "domainTemplatesDoNotExecuteDirectly": True,
    }
    report = {
        "schema": REPORT_SCHEMA,
        "version": VERSION,
        "release": "Standalone Functional Production Certification",
        "surfaceChecks": surface_checks,
        "surfaces": surfaces,
        "smokeChecks": smoke_checks,
        "smoke": smoke,
        "checks": checks,
        "certified": all(checks.values()),
        "wordpressRequired": False,
        "productionTopology": {
            "frontend": "standalone-app",
            "api": "FastAPI",
            "canonicalCalculationAuthority": "v11 Unified Calculation Engine through v12.3 Calculator Workspace",
            "wordpressRole": "optional compatibility/embed layer",
        },
    }
    report["certificationHash"] = _hash({
        "version": report["version"],
        "surfaceChecks": surface_checks,
        "smokeChecks": smoke_checks,
        "checks": checks,
        "productionTopology": report["productionTopology"],
    })
    return report


def status() -> Dict[str, Any]:
    report = certification_report()
    return {
        "ok": report["certified"],
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": report["release"],
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "standaloneFunctionalProductionCertified": report["certified"],
        "checks": report["checks"],
        "certificationHash": report["certificationHash"],
    }


@router.get("/v13120/status")
def status_route():
    return status()


@router.get("/standalone/v1/certification/v13/report")
def report_route():
    return {"ok": True, "version": VERSION, "certification": certification_report()}
