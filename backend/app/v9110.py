"""Workbench v9.11.0 — End-to-End Research Study Certification.

Structural certification of the Workbench v9 research lifecycle. Certification checks
whether selected research objects resolve, retain content-addressed integrity, form a
coherent lineage, satisfy a researcher-selected certification profile, and are ready
for reproducibility/portability/handoff workflows. Certification is deliberately not
scientific validity, peer review, hypothesis acceptance, or a governed Platform Core
claim.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v900 import load_study as load_scientific_study, list_studies as list_scientific_studies
from .v910 import load_protocol, list_protocols
from .v920 import load_campaign, list_campaigns
from .v930 import load_analysis as load_statistical_analysis, list_analyses as list_statistical_analyses
from .v940 import load_study as load_uncertainty_study, list_studies as list_uncertainty_studies
from .v950 import load_calibration, list_calibrations
from .v960 import load_synthesis, list_syntheses
from .v970 import load_workflow, list_workflows
from .v980 import load_analysis as load_meta_analysis, list_analyses as list_meta_analyses
from .v990 import load_package, list_packages, _package_archive_path
from .v9100 import load_handoff, list_handoffs

VERSION = APP_VERSION
SCHEMA = "sc-workbench-end-to-end-research-study-certification/1.0"
CERTIFICATION_SCHEMA = "sc-workbench-research-study-certification-record/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-research-study-certification-core-plan/1.0"
router = APIRouter(tags=["workbench-v9110-end-to-end-research-study-certification"])

CertificationProfile = Literal[
    "study-foundation",
    "analysis-complete",
    "reproducible-study",
    "portable-study",
    "handoff-ready",
    "full-v9",
]

STAGE_ORDER = [
    "scientific-study",
    "research-protocol",
    "computational-campaign",
    "statistical-analysis",
    "uncertainty-sensitivity-study",
    "model-calibration",
    "results-synthesis",
    "reproduction-replication-workflow",
    "cross-study-meta-analysis",
    "portable-research-package",
    "platform-wide-research-handoff",
]

PROFILE_REQUIRED: Dict[str, List[str]] = {
    "study-foundation": ["scientific-study", "research-protocol", "computational-campaign"],
    "analysis-complete": ["scientific-study", "research-protocol", "computational-campaign", "statistical-analysis", "results-synthesis"],
    "reproducible-study": ["scientific-study", "research-protocol", "computational-campaign", "statistical-analysis", "uncertainty-sensitivity-study", "model-calibration", "results-synthesis", "reproduction-replication-workflow"],
    "portable-study": ["scientific-study", "research-protocol", "computational-campaign", "statistical-analysis", "results-synthesis", "reproduction-replication-workflow", "portable-research-package"],
    "handoff-ready": ["scientific-study", "research-protocol", "computational-campaign", "statistical-analysis", "results-synthesis", "reproduction-replication-workflow", "portable-research-package", "platform-wide-research-handoff"],
    "full-v9": STAGE_ORDER,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cert_dir(project_key: str) -> Path:
    return _store_root() / "research-study-certifications" / _stable_id(project_key)


def _cert_path(project_key: str, certification_hash: str) -> Path:
    return _cert_dir(project_key) / f"{certification_hash}.json"


class CertificationRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    certificationKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    profile: CertificationProfile = "reproducible-study"
    studyHash: str = Field(min_length=64, max_length=64)
    protocolHash: str = Field(default="", max_length=64)
    campaignHash: str = Field(default="", max_length=64)
    statisticalAnalysisHash: str = Field(default="", max_length=64)
    uncertaintyStudyHash: str = Field(default="", max_length=64)
    calibrationHash: str = Field(default="", max_length=64)
    synthesisHash: str = Field(default="", max_length=64)
    reproductionWorkflowHash: str = Field(default="", max_length=64)
    metaAnalysisHash: str = Field(default="", max_length=64)
    portablePackageHash: str = Field(default="", max_length=64)
    handoffHash: str = Field(default="", max_length=64)
    reviewer: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for name in (
            "projectKey", "certificationKey", "title", "studyHash", "protocolHash",
            "campaignHash", "statisticalAnalysisHash", "uncertaintyStudyHash",
            "calibrationHash", "synthesisHash", "reproductionWorkflowHash",
            "metaAnalysisHash", "portablePackageHash", "handoffHash", "reviewer",
        ):
            value = getattr(self, name)
            if isinstance(value, str):
                setattr(self, name, value.strip())
        for name in (
            "studyHash", "protocolHash", "campaignHash", "statisticalAnalysisHash",
            "uncertaintyStudyHash", "calibrationHash", "synthesisHash",
            "reproductionWorkflowHash", "metaAnalysisHash", "portablePackageHash",
            "handoffHash",
        ):
            value = getattr(self, name)
            if value and len(value) != 64:
                raise ValueError(f"{name} must be a 64-character content hash")
        return self


class CoreCertificationPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    certificationHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "End-to-End Research Study Certification",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "certificationSchema": CERTIFICATION_SCHEMA,
        "profiles": PROFILE_REQUIRED,
        "stageOrder": STAGE_ORDER,
        "capabilities": {
            "endToEndResearchStudyCertification": True,
            "profileBasedCertificationRequirements": True,
            "researchObjectIntegrityValidation": True,
            "crossStageLineageCoherence": True,
            "reproducibilityReadinessAssessment": True,
            "portabilityReadinessAssessment": True,
            "handoffReadinessAssessment": True,
            "explicitGapAndWarningReporting": True,
            "contentAddressedCertificationRecords": True,
            "platformCoreCertificationPlanning": True,
        },
        "boundaries": {
            "certificationIsScientificValidity": False,
            "certificationIsPeerReview": False,
            "automaticStudyApproval": False,
            "automaticHypothesisAcceptance": False,
            "automaticScientificValidityInference": False,
            "automaticPublication": False,
            "automaticRemediation": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _refs(req: CertificationRequest) -> Dict[str, str]:
    return {
        "scientific-study": req.studyHash,
        "research-protocol": req.protocolHash,
        "computational-campaign": req.campaignHash,
        "statistical-analysis": req.statisticalAnalysisHash,
        "uncertainty-sensitivity-study": req.uncertaintyStudyHash,
        "model-calibration": req.calibrationHash,
        "results-synthesis": req.synthesisHash,
        "reproduction-replication-workflow": req.reproductionWorkflowHash,
        "cross-study-meta-analysis": req.metaAnalysisHash,
        "portable-research-package": req.portablePackageHash,
        "platform-wide-research-handoff": req.handoffHash,
    }


def _load_stage(project: str, stage: str, h: str) -> Dict[str, Any]:
    if stage == "scientific-study": return load_scientific_study(project, h)
    if stage == "research-protocol": return load_protocol(project, h)
    if stage == "computational-campaign": return load_campaign(project, h)
    if stage == "statistical-analysis": return load_statistical_analysis(project, h)
    if stage == "uncertainty-sensitivity-study": return load_uncertainty_study(project, h)
    if stage == "model-calibration": return load_calibration(project, h)
    if stage == "results-synthesis": return load_synthesis(project, h)
    if stage == "reproduction-replication-workflow": return load_workflow(project, h)
    if stage == "cross-study-meta-analysis": return load_meta_analysis(project, h)
    if stage == "portable-research-package": return load_package(project, h)
    if stage == "platform-wide-research-handoff": return load_handoff(project, h)
    raise ValueError(f"unsupported certification stage: {stage}")


def _package_hash_basis(package: Dict[str, Any]) -> Dict[str, Any]:
    return {k: package.get(k) for k in (
        "packageSchema", "packageFormatVersion", "sourceProduct", "sourceRuntime",
        "sourceWorkbenchVersion", "minimumCompatibleWorkbenchMajor", "projectKey",
        "packageKey", "title", "description", "license", "objects", "objectCount",
        "dependencyInventory", "strictDependencyClosure", "notes",
    )}


def _handoff_hash_basis(handoff: Dict[str, Any]) -> Dict[str, Any]:
    return {k: handoff.get(k) for k in (
        "handoffSchema", "projectKey", "handoffKey", "title", "description",
        "portablePackageHash", "portablePackageRef", "portableArchiveSha256",
        "sourceWorkbenchVersion", "dependencyInventory", "objectInventory",
        "destinations", "destinationPlans", "visibility", "notes",
    )}


def _integrity_check(stage: str, h: str, obj: Dict[str, Any], project_key: str) -> Dict[str, Any]:
    # Most native loaders validate record hashes before returning. Package and handoff
    # objects have their own content-addressed roots and are verified explicitly here.
    if stage == "portable-research-package":
        computed = content_hash(_package_hash_basis(obj))
        archive = _package_archive_path(project_key, h)
        archive_present = archive.exists()
        archive_sha_ok: Optional[bool] = None
        if archive_present and obj.get("archiveSha256"):
            archive_sha_ok = hashlib.sha256(archive.read_bytes()).hexdigest() == obj.get("archiveSha256")
        valid = computed == h and (archive_sha_ok is not False)
        return {"valid": valid, "computedHash": computed, "archivePresent": archive_present, "archiveSha256Valid": archive_sha_ok}
    if stage == "platform-wide-research-handoff":
        computed = content_hash(_handoff_hash_basis(obj))
        return {"valid": computed == h, "computedHash": computed}
    return {"valid": True, "loaderValidatedNativeIntegrity": True, "recordHash": obj.get("recordHash")}


def _source_hashes(synthesis: Dict[str, Any]) -> set[str]:
    return {str(x.get("sourceHash")) for x in (synthesis.get("sources") or []) if x.get("sourceHash")}


def _package_objects(package: Dict[str, Any]) -> set[tuple[str, str]]:
    return {(str(x.get("objectType")), str(x.get("sourceObjectHash"))) for x in (package.get("objects") or [])}


def _lineage_checks(refs: Dict[str, str], objects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    def add(name: str, expected: Any, observed: Any, applies: bool = True):
        if not applies: return
        checks.append({"check": name, "expected": expected, "observed": observed, "coherent": expected == observed})

    study = objects.get("scientific-study")
    protocol = objects.get("research-protocol")
    campaign = objects.get("computational-campaign")
    analysis = objects.get("statistical-analysis")
    uncertainty = objects.get("uncertainty-sensitivity-study")
    calibration = objects.get("model-calibration")
    synthesis = objects.get("results-synthesis")
    workflow = objects.get("reproduction-replication-workflow")
    meta = objects.get("cross-study-meta-analysis")
    package = objects.get("portable-research-package")
    handoff = objects.get("platform-wide-research-handoff")

    if study and protocol: add("protocol→study", refs["scientific-study"], protocol.get("studyHash"))
    if campaign and protocol: add("campaign→protocol", refs["research-protocol"], campaign.get("protocolHash"))
    if campaign and study: add("campaign→study", refs["scientific-study"], campaign.get("studyHash"))
    if analysis and campaign and analysis.get("campaignHash"): add("statistical-analysis→campaign", refs["computational-campaign"], analysis.get("campaignHash"))
    if uncertainty and campaign and uncertainty.get("campaignHash"): add("uncertainty-study→campaign", refs["computational-campaign"], uncertainty.get("campaignHash"))
    if calibration and campaign: add("calibration→campaign", refs["computational-campaign"], calibration.get("campaignHash"))
    if synthesis:
        sources = _source_hashes(synthesis)
        for stage in ("statistical-analysis", "uncertainty-sensitivity-study", "model-calibration"):
            if refs.get(stage):
                checks.append({"check": f"synthesis-source→{stage}", "expected": refs[stage], "observed": refs[stage] if refs[stage] in sources else None, "coherent": refs[stage] in sources})
    if workflow and synthesis: add("reproduction-workflow→synthesis", refs["results-synthesis"], (workflow.get("target") or {}).get("synthesisHash"))
    if meta and (synthesis or workflow):
        matched = False
        for row in meta.get("studies") or []:
            source = row.get("source") or {}
            if refs.get("results-synthesis") and source.get("sourceSynthesisHash") == refs["results-synthesis"]: matched = True
            if refs.get("reproduction-replication-workflow") and source.get("sourceWorkflowHash") == refs["reproduction-replication-workflow"]: matched = True
        checks.append({"check": "meta-analysis→study-lineage", "expected": "current synthesis or workflow represented", "observed": matched, "coherent": matched})
    if package:
        included = _package_objects(package)
        mapping = {
            "scientific-study": "scientific-study", "research-protocol": "research-protocol",
            "computational-campaign": "computational-campaign", "statistical-analysis": "statistical-analysis",
            "uncertainty-sensitivity-study": "uncertainty-sensitivity-study", "model-calibration": "model-calibration",
            "results-synthesis": "results-synthesis", "reproduction-replication-workflow": "reproduction-replication-workflow",
            "cross-study-meta-analysis": "cross-study-meta-analysis",
        }
        for stage, typ in mapping.items():
            if refs.get(stage):
                ok = (typ, refs[stage]) in included
                checks.append({"check": f"portable-package-includes→{stage}", "expected": refs[stage], "observed": refs[stage] if ok else None, "coherent": ok})
    if handoff and package: add("handoff→portable-package", refs["portable-research-package"], handoff.get("portablePackageHash"))
    return checks


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    catalogs = {
        "scientificStudies": list_scientific_studies(project_key),
        "researchProtocols": list_protocols(project_key),
        "computationalCampaigns": list_campaigns(project_key),
        "statisticalAnalyses": list_statistical_analyses(project_key),
        "uncertaintySensitivityStudies": list_uncertainty_studies(project_key),
        "modelCalibrations": list_calibrations(project_key),
        "resultsSyntheses": list_syntheses(project_key),
        "reproductionReplicationWorkflows": list_workflows(project_key),
        "crossStudyMetaAnalyses": list_meta_analyses(project_key),
        "portableResearchPackages": list_packages(project_key),
        "platformWideResearchHandoffs": list_handoffs(project_key),
        "researchStudyCertifications": list_certifications(project_key),
    }
    out = {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "catalogs": catalogs,
           "boundaries": {"catalogCertifiesAutomatically": False, "catalogInfersScientificValidity": False}}
    out["catalogHash"] = content_hash(out)
    return out


def evaluate_certification(req: CertificationRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    # The study is the root identity and must resolve; downstream missing objects are gaps.
    root_study = load_scientific_study(req.projectKey, req.studyHash)
    refs = _refs(req)
    required = set(PROFILE_REQUIRED[req.profile])
    objects: Dict[str, Dict[str, Any]] = {"scientific-study": root_study}
    stages: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    for stage in STAGE_ORDER:
        h = refs.get(stage, "")
        required_stage = stage in required
        if stage == "scientific-study":
            obj = root_study
            integrity = _integrity_check(stage, h, obj, req.projectKey)
            stages.append({"stage": stage, "required": required_stage, "provided": True, "resolved": True, "objectHash": h, "integrity": integrity})
            continue
        if not h:
            stages.append({"stage": stage, "required": required_stage, "provided": False, "resolved": False, "objectHash": "", "integrity": {"valid": False if required_stage else None}})
            if required_stage: gaps.append({"stage": stage, "code": "required-object-missing", "message": f"{stage} is required by profile {req.profile}"})
            continue
        try:
            obj = _load_stage(req.projectKey, stage, h)
            objects[stage] = obj
            integrity = _integrity_check(stage, h, obj, req.projectKey)
            stages.append({"stage": stage, "required": required_stage, "provided": True, "resolved": True, "objectHash": h, "integrity": integrity})
            if not integrity.get("valid"):
                gaps.append({"stage": stage, "code": "integrity-check-failed", "message": f"{stage} failed content-addressed integrity verification"})
            if stage == "portable-research-package" and integrity.get("archivePresent") is False:
                warnings.append({"stage": stage, "code": "archive-bytes-unavailable", "message": "package manifest resolves but portable ZIP bytes are unavailable for archive SHA-256 verification"})
        except Exception as exc:
            stages.append({"stage": stage, "required": required_stage, "provided": True, "resolved": False, "objectHash": h, "integrity": {"valid": False}, "error": str(exc)})
            gaps.append({"stage": stage, "code": "object-unresolved", "message": str(exc)})

    lineage = _lineage_checks(refs, objects)
    for row in lineage:
        if not row["coherent"]:
            gaps.append({"stage": "lineage", "code": "lineage-mismatch", "check": row["check"], "expected": row["expected"], "observed": row["observed"]})

    required_rows = [x for x in stages if x["required"]]
    resolved_required = [x for x in required_rows if x["resolved"] and x["integrity"].get("valid") is not False]
    lineage_ok = all(x["coherent"] for x in lineage)
    profile_complete = len(resolved_required) == len(required_rows) and lineage_ok
    portability_ready = bool(objects.get("portable-research-package")) and next((x["integrity"].get("valid") for x in stages if x["stage"] == "portable-research-package"), False) is True
    handoff = objects.get("platform-wide-research-handoff")
    handoff_ready = bool(handoff and (handoff.get("readiness") or {}).get("allRequestedDestinationsReady"))
    reproducibility_ready = all(objects.get(x) for x in ("research-protocol", "computational-campaign", "results-synthesis", "reproduction-replication-workflow"))

    dimensions = {
        "profileCompleteness": {"complete": profile_complete, "requiredStageCount": len(required_rows), "resolvedRequiredStageCount": len(resolved_required)},
        "objectIntegrity": {"complete": not any(g.get("code") in {"integrity-check-failed", "object-unresolved"} for g in gaps)},
        "lineageCoherence": {"complete": lineage_ok, "checkCount": len(lineage), "coherentCheckCount": sum(1 for x in lineage if x["coherent"])},
        "reproducibilityReadiness": {"ready": reproducibility_ready},
        "portabilityReadiness": {"ready": portability_ready},
        "handoffReadiness": {"ready": handoff_ready},
    }
    status = "complete" if profile_complete and not gaps else "incomplete"
    seed = {
        "projectKey": req.projectKey,
        "certificationKey": req.certificationKey,
        "title": req.title,
        "profile": req.profile,
        "objectRefs": refs,
        "stageAssessments": stages,
        "lineageChecks": lineage,
        "dimensions": dimensions,
        "gaps": gaps,
        "warnings": warnings,
        "reviewer": req.reviewer,
        "notes": req.notes,
        "certificationStatus": status,
    }
    certification_hash = content_hash(seed)
    return {
        "ok": True,
        "schema": CERTIFICATION_SCHEMA,
        "version": VERSION,
        **seed,
        "certificationHash": certification_hash,
        "certificationRef": f"sc://workbench/research-study-certification/{req.projectKey}/{certification_hash}",
        "structuralCertificationOnly": True,
        "scientificValidityCertified": False,
        "createdBy": req.createdBy,
        "boundaries": manifest()["boundaries"],
    }


def save_certification(req: CertificationRequest) -> Dict[str, Any]:
    rec = evaluate_certification(req)
    path = _cert_path(req.projectKey, rec["certificationHash"])
    if path.exists():
        old = _json_read(path)
        return {**old, "idempotent": True}
    stored = {**rec, "createdAt": _now()}
    stored["recordHash"] = content_hash({k: v for k, v in stored.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(path, stored)
    return {**stored, "idempotent": False}


def load_certification(project_key: str, certification_hash: str) -> Dict[str, Any]:
    path = _cert_path(project_key, certification_hash)
    if not path.exists(): raise FileNotFoundError(f"research study certification not found: {certification_hash}")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("certificationHash") != certification_hash: raise ValueError("research study certification identity mismatch")
    expected = content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    if rec.get("recordHash") != expected: raise ValueError("research study certification failed integrity validation")
    return rec


def list_certifications(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _cert_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r = _json_read(p)
                rows.append({k: r.get(k) for k in ("certificationHash", "certificationRef", "certificationKey", "title", "profile", "certificationStatus", "reviewer", "createdBy", "createdAt", "recordHash")})
            except Exception:
                continue
    return {"ok": True, "schema": CERTIFICATION_SCHEMA, "version": VERSION, "projectKey": project_key, "certificationCount": len(rows), "certifications": rows}


def core_plan(req: CoreCertificationPlanRequest) -> Dict[str, Any]:
    rec = load_certification(req.projectKey, req.certificationHash)
    cfg = core_config()
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "certificationHash": req.certificationHash,
        "certificationRef": rec.get("certificationRef"),
        "core": {"enabled": bool(cfg.get("enabled")), "baseUrlConfigured": bool(cfg.get("baseUrl"))},
        "bindingPlan": {
            "objectType": "workbench.research-study-certification",
            "objectHash": req.certificationHash,
            "objectRef": rec.get("certificationRef"),
            "studyHash": (rec.get("objectRefs") or {}).get("scientific-study"),
            "profile": rec.get("profile"),
            "certificationStatus": rec.get("certificationStatus"),
            "structuralCertificationOnly": True,
            "scientificValidityCertified": False,
            "coreProjectEntityId": req.coreProjectEntityId,
            "coreSessionId": req.coreSessionId,
            "visibility": req.visibility,
            "createdBy": req.createdBy,
        },
        "boundaries": {"automaticCoreDispatch": False, "governedCoreObjectCreated": False, "scientificValidityInferred": False, "certificationPromotedToPeerReview": False},
    }
    out["planHash"] = content_hash(out)
    return out


def _wrap(fn, *args):
    try: return fn(*args)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/research-study-certification/manifest")
def route_manifest(): return manifest()

@router.get("/research-study-certification/source-catalog/{project_key}")
def route_catalog(project_key: str): return _wrap(source_catalog, project_key)

@router.post("/research-study-certification/evaluate")
def route_evaluate(req: CertificationRequest): return _wrap(evaluate_certification, req)

@router.post("/research-study-certification/certifications")
def route_save(req: CertificationRequest): return _wrap(save_certification, req)

@router.get("/research-study-certification/certifications/{project_key}")
def route_list(project_key: str): return list_certifications(project_key)

@router.get("/research-study-certification/certifications/{project_key}/{certification_hash}")
def route_get(project_key: str, certification_hash: str): return _wrap(load_certification, project_key, certification_hash)

@router.post("/integration/core/research-study-certification/plan")
def route_core(req: CoreCertificationPlanRequest): return _wrap(core_plan, req)

@router.get("/v9110/status")
def status():
    m = manifest()
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
        "endToEndResearchStudyCertification": True,
        "profileBasedCertificationRequirements": True,
        "crossStageLineageCoherence": True,
        "contentAddressedCertificationRecords": True,
        "certificationIsScientificValidity": False,
        "automaticStudyApproval": False,
        "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }
