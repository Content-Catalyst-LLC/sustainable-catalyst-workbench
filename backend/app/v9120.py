"""Workbench v9.12.0 — Workbench v9 Production Certification.

Final v9 operational certification layer. This module verifies canonical release identity,
runtime health/readiness, writable persistence, retained v9 milestone manifests and capability
flags, Platform Core non-dispatch boundaries, portability/handoff/study-certification surfaces,
and deployment contract metadata. Certification is software/operational certification only;
it never certifies scientific validity, evidence truth, causal correctness, statistical merit,
peer-review acceptance, or publication merit.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v640 import capabilities_record, core_config, health_record, runtime_record
from .v810 import _atomic_json_write, _json_read, _store_root
from .v900 import manifest as v900_manifest
from .v910 import manifest as v910_manifest
from .v920 import manifest as v920_manifest
from .v930 import manifest as v930_manifest
from .v940 import manifest as v940_manifest
from .v950 import manifest as v950_manifest
from .v960 import manifest as v960_manifest
from .v970 import manifest as v970_manifest
from .v980 import manifest as v980_manifest
from .v990 import manifest as v990_manifest
from .v9100 import manifest as v9100_manifest
from .v9110 import manifest as v9110_manifest

VERSION = APP_VERSION
SCHEMA = "sc-workbench-v9-production-certification/1.0"
REPORT_SCHEMA = "sc-workbench-v9-production-certification-report/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-v9-production-certification-core-plan/1.0"
router = APIRouter(tags=["workbench-v9120-v9-production-certification"])

V9_MILESTONES = [
    ("v9.0.0", "unified-scientific-study-composer", "unifiedScientificStudyComposer", v900_manifest),
    ("v9.1.0", "experimental-design-research-protocol-builder", "experimentalDesignResearchProtocolBuilder", v910_manifest),
    ("v9.2.0", "batch-experiment-computational-campaign-manager", "batchExperimentComputationalCampaignManager", v920_manifest),
    ("v9.3.0", "statistical-analysis-diagnostic-workspace", "statisticalAnalysisDiagnosticWorkspace", v930_manifest),
    ("v9.4.0", "uncertainty-sensitivity-study-composer", "uncertaintySensitivityStudyComposer", v940_manifest),
    ("v9.5.0", "model-calibration-parameter-estimation", "modelCalibrationParameterEstimation", v950_manifest),
    ("v9.6.0", "scientific-results-narrative-synthesis", "scientificResultsNarrativeSynthesis", v960_manifest),
    ("v9.7.0", "reproduction-replication-workflow", "reproductionReplicationWorkflow", v970_manifest),
    ("v9.8.0", "cross-study-comparison-meta-analysis", "crossStudyMetaAnalysisWorkspace", v980_manifest),
    ("v9.9.0", "research-package-exchange-portability", "researchPackageExchangePortability", v990_manifest),
    ("v9.10.0", "platform-wide-scientific-research-handoff", "platformWideScientificResearchHandoff", v9100_manifest),
    ("v9.11.0", "end-to-end-research-study-certification", "endToEndResearchStudyCertification", v9110_manifest),
]


class CertificationRequest(BaseModel):
    certificationKey: str = Field(default="workbench-v9-production", min_length=1, max_length=160)
    requestedBy: str = Field(default="workbench", min_length=1, max_length=160)
    includeStoreWriteProbe: bool = True
    includeCoreConfiguration: bool = True
    includeMilestoneManifestAudit: bool = True
    notes: str = Field(default="", max_length=12000)


class CoreProductionCertificationPlanRequest(BaseModel):
    certificationHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: str = Field(default="internal", pattern="^(private|internal|public)$")
    createdBy: str = Field(default="workbench", max_length=160)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _cert_dir() -> Path:
    return _store_root() / "workbench-v9-production-certifications"


def _cert_path(certification_hash: str) -> Path:
    return _cert_dir() / f"{certification_hash}.json"


def _store_probe(write_probe: bool) -> Dict[str, Any]:
    root = _store_root()
    out: Dict[str, Any] = {
        "path": str(root), "exists": root.exists(), "directory": root.is_dir() if root.exists() else False,
        "writable": False, "writeProbePerformed": False, "writeProbePassed": None,
    }
    try:
        root.mkdir(parents=True, exist_ok=True)
        out["exists"] = True; out["directory"] = root.is_dir(); out["writable"] = os.access(root, os.W_OK)
        if write_probe:
            probe = root / ".scwb-v9120-production-certification-probe"
            probe.write_text(f"v{VERSION} Workbench v9 production certification\n", encoding="utf-8")
            probe.unlink()
            out["writeProbePerformed"] = True; out["writeProbePassed"] = True
    except Exception as exc:
        out["writeProbePerformed"] = bool(write_probe); out["writeProbePassed"] = False if write_probe else None
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _milestone_audit() -> Dict[str, Any]:
    caps = capabilities_record()
    integ = caps.get("coreIntegration") or {}
    rows: List[Dict[str, Any]] = []
    for release, name, capability_key, manifest_fn in V9_MILESTONES:
        try:
            m = manifest_fn()
            manifest_ok = bool(m.get("ok")) and m.get("version") == VERSION and len(str(m.get("manifestHash") or "")) == 64
            capability_ok = integ.get(capability_key) is True
            rows.append({
                "release": release, "milestone": name, "capabilityKey": capability_key,
                "manifestVersion": m.get("version"), "manifestHash": m.get("manifestHash"),
                "manifestReady": manifest_ok, "capabilityRetained": capability_ok,
                "passed": manifest_ok and capability_ok,
            })
        except Exception as exc:
            rows.append({"release": release, "milestone": name, "capabilityKey": capability_key,
                         "manifestReady": False, "capabilityRetained": False, "passed": False,
                         "error": f"{type(exc).__name__}: {exc}"})
    return {
        "milestones": rows,
        "passedCount": sum(1 for x in rows if x["passed"]),
        "requiredCount": len(rows),
        "allRequiredRetained": all(x["passed"] for x in rows),
        "capabilityRegistryVersion": caps.get("version"),
    }


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Workbench v9 Production Certification",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "reportSchema": REPORT_SCHEMA,
        "certificationDomains": [
            "canonical-release-identity", "runtime-health-readiness", "persistent-store-readiness",
            "retained-v9-milestones", "capability-registry", "platform-core-boundary",
            "research-package-portability", "platform-wide-handoff", "research-study-certification",
            "wordpress-release-identity", "deployment-invariants", "public-api-readiness",
        ],
        "requiredV9Milestones": [x[0] for x in V9_MILESTONES],
        "capabilities": {
            "workbenchV9ProductionCertification": True,
            "canonicalReleaseIdentityAudit": True,
            "runtimeHealthReadinessAudit": True,
            "persistentStoreWriteProbe": True,
            "retainedV9MilestoneAudit": True,
            "capabilityRegistryAudit": True,
            "platformCoreBoundaryAudit": True,
            "portabilityHandoffCertificationAudit": True,
            "contentAddressedProductionCertificates": True,
            "productionCertificateCorePlanning": True,
        },
        "deploymentContract": {
            "localPort": 8088,
            "healthPath": "/health",
            "statusPath": "/v9120/status",
            "manifestPath": "/v9-production-certification/manifest",
            "dockerImage": f"sustainable-catalyst-workbench:{VERSION}",
            "wordpressPluginVersion": VERSION,
        },
        "boundaries": {
            "productionCertificationIsScientificValidity": False,
            "scientificCorrectnessCertified": False,
            "evidenceTruthCertified": False,
            "causalClaimsCertified": False,
            "statisticalMeritCertified": False,
            "peerReviewCertified": False,
            "publicationMeritCertified": False,
            "automaticRemediation": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def run_certification(req: CertificationRequest) -> Dict[str, Any]:
    health = health_record(); runtime = runtime_record(); caps = capabilities_record()
    store = _store_probe(req.includeStoreWriteProbe)
    core = core_config() if req.includeCoreConfiguration else {}
    milestones = _milestone_audit() if req.includeMilestoneManifestAudit else {"milestones": [], "allRequiredRetained": True, "passedCount": 0, "requiredCount": 0, "capabilityRegistryVersion": caps.get("version")}
    package_manifest = v990_manifest(); handoff_manifest = v9100_manifest(); study_cert_manifest = v9110_manifest()

    checks: List[Dict[str, Any]] = [
        {"check": "canonical-release-identity", "passed": VERSION == APP_VERSION, "observed": VERSION},
        {"check": "product-identity", "passed": PRODUCT_KEY == "workbench", "observed": PRODUCT_KEY},
        {"check": "runtime-kind", "passed": RUNTIME_KIND == "scientific-engineering-compute", "observed": RUNTIME_KIND},
        {"check": "health-readiness", "passed": health.get("ok") is True and health.get("readiness") == "ready" and health.get("version") == VERSION, "observed": health.get("readiness")},
        {"check": "runtime-identity", "passed": runtime.get("version") == VERSION, "observed": runtime.get("version")},
        {"check": "capability-registry-identity", "passed": caps.get("version") == VERSION, "observed": caps.get("version")},
        {"check": "persistent-store-directory", "passed": bool(store.get("directory")), "observed": store.get("path")},
        {"check": "persistent-store-writable", "passed": bool(store.get("writable")), "observed": store.get("writable")},
        {"check": "retained-v9-milestones", "passed": milestones.get("allRequiredRetained") is True, "observed": f"{milestones.get('passedCount')}/{milestones.get('requiredCount')}"},
        {"check": "research-package-portability", "passed": package_manifest.get("version") == VERSION and package_manifest.get("capabilities", {}).get("perObjectIntegrityHashes") is True, "observed": package_manifest.get("version")},
        {"check": "platform-wide-handoff", "passed": handoff_manifest.get("version") == VERSION and handoff_manifest.get("capabilities", {}).get("platformWideScientificResearchHandoff") is True, "observed": handoff_manifest.get("version")},
        {"check": "research-study-certification", "passed": study_cert_manifest.get("version") == VERSION and study_cert_manifest.get("capabilities", {}).get("endToEndResearchStudyCertification") is True, "observed": study_cert_manifest.get("version")},
        {"check": "core-outbound-dispatch-disabled", "passed": core.get("outboundDispatchEnabled") is False if core else True, "observed": core.get("outboundDispatchEnabled") if core else "not-requested"},
    ]
    if req.includeStoreWriteProbe:
        checks.append({"check": "persistent-store-write-probe", "passed": store.get("writeProbePassed") is True, "observed": store.get("writeProbePassed")})
    passed = all(bool(x["passed"]) for x in checks)
    out: Dict[str, Any] = {
        "ok": passed,
        "schema": REPORT_SCHEMA,
        "version": VERSION,
        "release": "Workbench v9 Production Certification",
        "certificationKey": req.certificationKey,
        "certifiedAt": _now(),
        "requestedBy": req.requestedBy,
        "notes": req.notes,
        "certificationStatus": "pass" if passed else "fail",
        "productionReady": passed,
        "checks": checks,
        "summary": {"passed": sum(1 for x in checks if x["passed"]), "failed": sum(1 for x in checks if not x["passed"]), "total": len(checks)},
        "health": health,
        "runtime": runtime,
        "persistentStore": store,
        "retainedV9Milestones": milestones,
        "coreConfiguration": core,
        "criticalSurfaces": {
            "researchPackageExchange": {"version": package_manifest.get("version"), "manifestHash": package_manifest.get("manifestHash")},
            "platformWideHandoff": {"version": handoff_manifest.get("version"), "manifestHash": handoff_manifest.get("manifestHash")},
            "researchStudyCertification": {"version": study_cert_manifest.get("version"), "manifestHash": study_cert_manifest.get("manifestHash")},
        },
        "deploymentContract": manifest()["deploymentContract"],
        "boundaries": manifest()["boundaries"],
    }
    out["reportHash"] = content_hash({k: v for k, v in out.items() if k not in {"certifiedAt", "reportHash"}})
    return out


def save_certification(req: CertificationRequest) -> Dict[str, Any]:
    report = run_certification(req)
    certification_hash = report["reportHash"]
    path = _cert_path(certification_hash)
    idempotent = path.exists()
    record = {**report, "certificationHash": certification_hash,
              "certificationRef": f"sc://workbench/v9-production-certification/{certification_hash}"}
    record["recordHash"] = content_hash({k: v for k, v in record.items() if k != "recordHash"})
    if not idempotent:
        _atomic_json_write(path, record)
    else:
        # The content-addressed report hash excludes certifiedAt, so rerunning the
        # same certification intentionally resolves to the original immutable record.
        record = load_certification(certification_hash)
    return {**record, "idempotent": idempotent}


def load_certification(certification_hash: str) -> Dict[str, Any]:
    path = _cert_path(certification_hash)
    if not path.exists():
        raise HTTPException(status_code=404, detail="production certification not found")
    record = _json_read(path)
    expected = record.get("recordHash")
    computed = content_hash({k: v for k, v in record.items() if k != "recordHash"})
    if expected != computed:
        raise HTTPException(status_code=409, detail="production certification record integrity failure")
    return record


def list_certifications() -> Dict[str, Any]:
    root = _cert_dir(); rows: List[Dict[str, Any]] = []
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                d = load_certification(path.stem)
                rows.append({"certificationHash": d.get("certificationHash"), "certificationKey": d.get("certificationKey"),
                             "certificationStatus": d.get("certificationStatus"), "version": d.get("version"),
                             "certifiedAt": d.get("certifiedAt"), "recordHash": d.get("recordHash")})
            except Exception:
                rows.append({"certificationHash": path.stem, "integrityError": True})
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "certificationCount": len(rows), "certifications": rows}


def core_plan(req: CoreProductionCertificationPlanRequest) -> Dict[str, Any]:
    cert = load_certification(req.certificationHash)
    cfg = core_config()
    return {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
        "bindingPlan": {
            "objectType": "workbench.v9-production-certification",
            "sourceRef": cert.get("certificationRef"), "sourceHash": req.certificationHash,
            "recordHash": cert.get("recordHash"), "certificationStatus": cert.get("certificationStatus"),
            "productionReady": cert.get("productionReady"), "scientificValidityCertified": False,
            "coreProjectEntityId": req.coreProjectEntityId, "coreSessionId": req.coreSessionId,
            "visibility": req.visibility, "createdBy": req.createdBy,
        },
        "coreConfiguration": {"enabled": cfg.get("enabled"), "required": cfg.get("required"), "outboundDispatchEnabled": cfg.get("outboundDispatchEnabled")},
        "boundaries": {"automaticCoreDispatch": False, "automaticCorePersistence": False, "governedCoreObjectCreated": False,
                       "scientificValidityCertified": False, "automaticRemediation": False},
    }


@router.get("/v9-production-certification/manifest")
def production_manifest() -> Dict[str, Any]: return manifest()

@router.post("/v9-production-certification/run")
def production_run(req: CertificationRequest) -> Dict[str, Any]: return run_certification(req)

@router.post("/v9-production-certification/certifications")
def production_save(req: CertificationRequest) -> Dict[str, Any]: return save_certification(req)

@router.get("/v9-production-certification/certifications")
def production_list() -> Dict[str, Any]: return list_certifications()

@router.get("/v9-production-certification/certifications/{certification_hash}")
def production_get(certification_hash: str) -> Dict[str, Any]: return load_certification(certification_hash)

@router.post("/integration/core/v9-production-certification/plan")
def production_core_plan(req: CoreProductionCertificationPlanRequest) -> Dict[str, Any]: return core_plan(req)

@router.get("/v9120/status")
def status() -> Dict[str, Any]:
    m = manifest()
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
            "workbenchV9ProductionCertification": True, "retainedV9MilestoneAudit": True,
            "contentAddressedProductionCertificates": True, "productionCertificationIsScientificValidity": False,
            "automaticRemediation": False, "automaticCoreDispatch": False, "manifestHash": m["manifestHash"]}
