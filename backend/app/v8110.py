"""Workbench v8.11.0 — Research Publication & Evidence Handoff.

Governed publication and evidence handoff over immutable v8.10 analysis-board snapshots.
The handoff preserves researcher-authored narrative, source hashes, evidence references,
figures, comparison provenance, and reproducibility anchors while producing explicit,
non-dispatching destination plans for Platform Core, Knowledge Library, Research Lab,
and external publication workflows. It does not generate findings, infer scientific
validity, rank models, resolve evidence conflicts, or publish automatically.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project
from .v8100 import list_snapshots, load_snapshot

VERSION = APP_VERSION
SCHEMA = "sc-workbench-research-publication-evidence-handoff/1.0"
PACKAGE_SCHEMA = "sc-workbench-research-publication-evidence-handoff-package/1.0"
CATALOG_SCHEMA = "sc-workbench-publication-handoff-source-catalog/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-publication-evidence-handoff-core-plan/1.0"
MAX_AUTHORS = 50
MAX_KEYWORDS = 50
MAX_DESTINATIONS = 4
router = APIRouter(tags=["workbench-v8110-research-publication-evidence-handoff"])

PublicationType = Literal["article", "report", "working-paper", "technical-note", "research-note"]
Destination = Literal["platform-core", "knowledge-library", "research-lab", "external-publication"]
Visibility = Literal["private", "internal", "public"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _package_dir(project_key: str) -> Path:
    return _store_root() / "publication-handoffs" / _stable_id(project_key) / "packages"


def _package_path(project_key: str, package_hash: str) -> Path:
    return _package_dir(project_key) / f"{package_hash}.json"


class Author(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    affiliation: str = Field(default="", max_length=500)
    orcid: str = Field(default="", max_length=80)


class PublicationHandoffRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    snapshotHash: str = Field(min_length=16, max_length=128)
    title: str = Field(default="", max_length=600)
    abstract: str = Field(default="", max_length=8000)
    authors: List[Author] = Field(default_factory=list, max_length=MAX_AUTHORS)
    keywords: List[str] = Field(default_factory=list, max_length=MAX_KEYWORDS)
    publicationType: PublicationType = "report"
    license: str = Field(default="", max_length=160)
    citationStyle: str = Field(default="author-date", max_length=80)
    destinations: List[Destination] = Field(default_factory=lambda: ["platform-core", "knowledge-library"], max_length=MAX_DESTINATIONS)
    includeFigures: bool = True
    includeEvidenceManifest: bool = True

    @model_validator(mode="after")
    def normalize(self):
        self.projectKey = self.projectKey.strip()
        self.snapshotHash = self.snapshotHash.strip()
        self.keywords = [str(x).strip() for x in self.keywords if str(x).strip()]
        self.destinations = list(dict.fromkeys(self.destinations))
        if len(self.keywords) != len(set(self.keywords)):
            raise ValueError("keywords must be unique")
        if not self.destinations:
            raise ValueError("at least one destination is required")
        return self


class SavePublicationHandoffRequest(PublicationHandoffRequest):
    packageLabel: str = Field(default="Research publication & evidence handoff", max_length=500)
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


class CorePublicationHandoffPlanRequest(PublicationHandoffRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Visibility = "internal"
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


def _source_index(board: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for job in ((board.get("sources") or {}).get("jobs") or []):
        jid = str(job.get("jobId") or "")
        if jid:
            idx[jid] = {"kind": "execution", **job}
        for k in ("jobHash", "requestHash", "resultHash"):
            if job.get(k): idx[str(job[k])] = {"kind": "execution", **job}
    for asset in ((board.get("sources") or {}).get("assets") or []):
        key = str(asset.get("assetKey") or "")
        if key:
            idx[key] = {"kind": "asset", **asset}
        for k in ("assetHash", "contentHash", "recordHash"):
            if asset.get(k): idx[str(asset[k])] = {"kind": "asset", **asset}
    return idx


def _evidence_manifest(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    board = snapshot.get("board") or {}
    idx = _source_index(board)
    narrative = board.get("narrative") or {}
    findings = narrative.get("findings") or []
    rows: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []
    findings_with_refs = 0
    for finding in findings:
        refs = list(finding.get("evidenceRefs") or [])
        if refs: findings_with_refs += 1
        resolved = []
        missing = []
        for ref in refs:
            source = idx.get(str(ref))
            if source is None:
                missing.append(str(ref))
                unresolved.append({"findingItemId": finding.get("itemId"), "evidenceRef": str(ref)})
            else:
                resolved.append({
                    "evidenceRef": str(ref),
                    "kind": source.get("kind"),
                    "jobId": source.get("jobId"),
                    "assetKey": source.get("assetKey"),
                    "jobHash": source.get("jobHash"),
                    "resultHash": source.get("resultHash"),
                    "assetHash": source.get("assetHash"),
                    "contentHash": source.get("contentHash"),
                    "recordHash": source.get("recordHash"),
                })
        rows.append({
            "findingItemId": finding.get("itemId"),
            "title": finding.get("title"),
            "text": finding.get("text"),
            "state": finding.get("state"),
            "evidenceRefs": refs,
            "resolvedEvidence": resolved,
            "unresolvedEvidenceRefs": missing,
        })
    source_hashes = ((board.get("provenance") or {}).get("sourceHashes") or {})
    out = {
        "schema": "sc-workbench-publication-evidence-manifest/1.0",
        "snapshotHash": snapshot.get("snapshotHash"),
        "boardHash": snapshot.get("boardHash"),
        "sourceHashes": source_hashes,
        "findings": rows,
        "summary": {
            "findingCount": len(findings),
            "findingsWithEvidenceRefs": findings_with_refs,
            "unresolvedEvidenceRefCount": len(unresolved),
            "sourceJobCount": len(((board.get("sources") or {}).get("jobs") or [])),
            "sourceAssetCount": len(((board.get("sources") or {}).get("assets") or [])),
        },
        "unresolvedEvidenceRefs": unresolved,
        "boundaries": {
            "evidenceCompletenessIsValidityAssessment": False,
            "unresolvedEvidenceAutomaticallyRejected": False,
            "conflictsAutomaticallyResolved": False,
        },
    }
    out["evidenceManifestHash"] = content_hash(out)
    return out


def source_catalog(project_key: str) -> Dict[str, Any]:
    project = load_project(project_key)
    snaps = list_snapshots(project_key)
    packages = list_packages(project_key)
    out = {
        "ok": True,
        "schema": CATALOG_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "projectRevision": ((project.get("workspace") or {}).get("projectRevision")),
        "analysisSnapshots": snaps.get("snapshots", []),
        "analysisSnapshotCount": snaps.get("snapshotCount", 0),
        "handoffPackages": packages.get("packages", []),
        "handoffPackageCount": packages.get("packageCount", 0),
        "boundaries": {
            "catalogPublishesAutomatically": False,
            "catalogMutatesAnalysisSnapshots": False,
            "catalogInfersScientificValidity": False,
        },
    }
    out["catalogHash"] = content_hash(out)
    return out


def build_handoff(req: PublicationHandoffRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    snapshot = load_snapshot(req.projectKey, req.snapshotHash)
    board = snapshot.get("board") or {}
    narrative = board.get("narrative") or {}
    figures = ((board.get("analysis") or {}).get("figures") or []) if req.includeFigures else []
    evidence = _evidence_manifest(snapshot) if req.includeEvidenceManifest else None
    title = req.title.strip() or str(board.get("title") or "Research publication")
    publication = {
        "title": title,
        "abstract": req.abstract,
        "authors": [x.model_dump() for x in req.authors],
        "keywords": req.keywords,
        "publicationType": req.publicationType,
        "license": req.license,
        "citationStyle": req.citationStyle,
        "methods": narrative.get("methods") or [],
        "assumptions": narrative.get("assumptions") or [],
        "findings": narrative.get("findings") or [],
        "notes": narrative.get("notes") or [],
        "figures": [
            {
                "figureHash": f.get("figureHash"),
                "title": f.get("title"),
                "caption": f.get("caption"),
                "provenance": f.get("provenance"),
                "exportPlan": f.get("exportPlan"),
            }
            for f in figures
        ],
    }
    package_ref_seed = content_hash({"projectKey": req.projectKey, "snapshotHash": req.snapshotHash, "publication": publication})
    destination_plans = []
    for dest in req.destinations:
        plan = {
            "destination": dest,
            "dispatchPerformed": False,
            "sourceSnapshotHash": req.snapshotHash,
            "sourceBoardHash": snapshot.get("boardHash"),
            "contentHash": package_ref_seed,
        }
        if dest == "platform-core":
            plan.update({"handoffKind": "governed-research-publication", "requiresCoreSession": True})
        elif dest == "knowledge-library":
            plan.update({"handoffKind": "publication-and-evidence-package", "suggestedObjectType": "research-publication"})
        elif dest == "research-lab":
            plan.update({"handoffKind": "reproducible-analysis-context", "suggestedUse": "replication-or-follow-on-study"})
        else:
            plan.update({"handoffKind": "export-bundle", "formats": ["json", "markdown", "csv", "svg-plan"]})
        destination_plans.append(plan)
    out: Dict[str, Any] = {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "snapshotHash": req.snapshotHash,
        "boardHash": snapshot.get("boardHash"),
        "snapshotRecordHash": snapshot.get("recordHash"),
        "publication": publication,
        "evidenceManifest": evidence,
        "destinationPlans": destination_plans,
        "provenance": {
            "analysisSnapshotImmutable": bool(snapshot.get("immutable")),
            "analysisSnapshotHash": snapshot.get("snapshotHash"),
            "analysisBoardHash": snapshot.get("boardHash"),
            "sourceHashes": ((board.get("provenance") or {}).get("sourceHashes") or {}),
            "researcherAuthoredNarrativePreserved": True,
            "figureHashesPreserved": [f.get("figureHash") for f in figures if f.get("figureHash")],
            "comparisonHash": (((board.get("analysis") or {}).get("comparison") or {}).get("comparisonHash")),
        },
        "reproducibility": {
            "contentAddressed": True,
            "immutableAnalysisSnapshotRequired": True,
            "sourceHashesPinned": True,
            "automaticReexecutionPerformed": False,
            "handoffPackageSaveEligible": True,
        },
        "boundaries": {
            "handoffIsPublicationDecision": False,
            "publicationPerformed": False,
            "sourceObjectsMutated": False,
            "findingsAutomaticallyGenerated": False,
            "scientificValidityInferred": False,
            "causalInferencePerformed": False,
            "statisticalSignificanceInferred": False,
            "automaticWinnerSelectionPerformed": False,
            "evidenceConflictsAutomaticallyResolved": False,
            "automaticCoreDispatchPerformed": False,
            "automaticLibraryDispatchPerformed": False,
            "automaticLabDispatchPerformed": False,
        },
    }
    out["packageHash"] = content_hash(out)
    out["packageRef"] = f"sc://workbench/publication-handoffs/{req.projectKey}/{out['packageHash'][:24]}"
    return out


def save_package(req: SavePublicationHandoffRequest) -> Dict[str, Any]:
    base_fields = set(PublicationHandoffRequest.model_fields)
    package = build_handoff(PublicationHandoffRequest(**req.model_dump(include=base_fields)))
    package_hash = package["packageHash"]
    path = _package_path(req.projectKey, package_hash)
    if path.exists():
        record = _json_read(path)
        if record.get("packageHash") != package_hash:
            raise ValueError("stored publication handoff package failed identity validation")
        record["idempotent"] = True
        return record
    record = {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "packageHash": package_hash,
        "packageRef": package["packageRef"],
        "packageLabel": req.packageLabel,
        "createdBy": req.createdBy,
        "createdAt": _now(),
        "projectKey": req.projectKey,
        "snapshotHash": req.snapshotHash,
        "package": package,
        "immutable": True,
        "idempotent": False,
    }
    record["recordHash"] = content_hash({k: v for k, v in record.items() if k not in ("recordHash", "idempotent")})
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(path, record)
    return record


def list_packages(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    root = _package_dir(project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try: r = _json_read(p)
            except Exception: continue
            if r.get("projectKey") != project_key: continue
            rows.append({k: r.get(k) for k in ("packageHash", "packageRef", "packageLabel", "snapshotHash", "createdBy", "createdAt", "recordHash")})
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return {"ok": True, "schema": PACKAGE_SCHEMA, "version": VERSION, "projectKey": project_key, "packageCount": len(rows), "packages": rows}


def load_package(project_key: str, package_hash: str) -> Dict[str, Any]:
    load_project(project_key)
    path = _package_path(project_key, package_hash)
    if not path.exists(): raise FileNotFoundError("publication handoff package not found")
    record = _json_read(path)
    if record.get("projectKey") != project_key or record.get("packageHash") != package_hash:
        raise ValueError("publication handoff package identity mismatch")
    expected = content_hash({k: v for k, v in record.items() if k not in ("recordHash", "idempotent")})
    if record.get("recordHash") != expected:
        raise ValueError("publication handoff package failed integrity validation")
    return record


def core_handoff_plan(req: CorePublicationHandoffPlanRequest) -> Dict[str, Any]:
    base_fields = set(PublicationHandoffRequest.model_fields)
    package = build_handoff(PublicationHandoffRequest(**req.model_dump(include=base_fields)))
    project = load_project(req.projectKey)
    workspace = project.get("workspace") or {}
    sid = str(req.coreSessionId or workspace.get("coreSessionId") or "").strip()[:255]
    project_plan = core_project_plan(ProjectCorePlanRequest(
        projectKey=req.projectKey,
        coreProjectEntityId=req.coreProjectEntityId or req.projectKey,
        coreSessionId=sid,
        visibility=req.visibility,
        createdBy=req.createdBy,
    ))
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "packageHash": package["packageHash"],
        "packageRef": package["packageRef"],
        "coreSessionId": sid or None,
        "coreSessionIdMustComeFromCore": True,
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "projectPlan": project_plan,
        "coreRequests": list(project_plan.get("coreRequests") or []),
        "publicationHandoffIsGovernedDerivedObjectOnly": True,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "publicationAuthorized": False,
        "scientificValidityInferenceAuthorized": False,
    }
    if sid:
        out["coreRequests"].append({
            "path": CORE_PATHS["objectBindings"],
            "method": "POST",
            "phase": "research-publication-evidence-handoff-bind",
            "data": {
                "session_id": sid,
                "object_type": "workbench.research-publication-evidence-handoff",
                "object_ref": package["packageRef"],
                "version_ref": f"sc://workbench/publication-handoffs/{req.projectKey}@{VERSION}",
                "content_hash": package["packageHash"],
                "role": "governed-publication-evidence-handoff",
                "visibility": req.visibility,
                "metadata": {
                    "workbenchVersion": VERSION,
                    "projectKey": req.projectKey,
                    "analysisSnapshotHash": req.snapshotHash,
                    "scientificSourceOfTruth": False,
                    "publicationPerformed": False,
                },
            },
            "dispatchPerformed": False,
        })
    out["planHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Research Publication & Evidence Handoff",
        "capabilities": {
            "immutableAnalysisSnapshotHandoff": True,
            "publicationMetadataAssembly": True,
            "researcherNarrativePreservation": True,
            "evidenceManifestGeneration": True,
            "evidenceReferenceResolution": True,
            "figureProvenancePreservation": True,
            "sourceHashPreservation": True,
            "contentAddressedHandoffPackages": True,
            "multiDestinationHandoffPlanning": True,
            "corePublicationHandoffPlanning": True,
            "knowledgeLibraryHandoffPlanning": True,
            "researchLabHandoffPlanning": True,
            "externalPublicationExportPlanning": True,
        },
        "authorities": {
            "analysisBoardSnapshots": "v8.10",
            "figures": "v8.9 via analysis board",
            "comparisons": "v8.8 via analysis board",
            "executions": "v8.4 via analysis board",
            "assets": "v8.3 via analysis board",
        },
        "boundaries": {
            "automaticPublicationAuthorized": False,
            "automaticFindingGenerationAuthorized": False,
            "scientificValidityInferenceAuthorized": False,
            "causalInferenceAuthorized": False,
            "statisticalSignificanceInferenceAuthorized": False,
            "automaticWinnerSelectionAuthorized": False,
            "evidenceConflictResolutionAuthorized": False,
            "automaticDestinationDispatchAuthorized": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


@router.get("/publication-handoff/manifest")
def manifest_route(): return manifest()

@router.get("/publication-handoff/source-catalog/{project_key}")
def catalog_route(project_key: str):
    try: return source_catalog(project_key)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/publication-handoff/build")
def build_route(req: PublicationHandoffRequest):
    try: return build_handoff(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.post("/publication-handoff/packages")
def save_route(req: SavePublicationHandoffRequest):
    try: return save_package(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.get("/publication-handoff/packages/{project_key}")
def list_route(project_key: str):
    try: return list_packages(project_key)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/publication-handoff/packages/{project_key}/{package_hash}")
def load_route(project_key: str, package_hash: str):
    try: return load_package(project_key, package_hash)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/integration/core/publication-handoff/plan")
def core_plan_route(req: CorePublicationHandoffPlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try: return core_handoff_plan(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.get("/v8110/status")
def status_route():
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Research Publication & Evidence Handoff",
        "immutableAnalysisSnapshotHandoff": True,
        "evidenceManifestGeneration": True,
        "contentAddressedHandoffPackages": True,
        "multiDestinationHandoffPlanning": True,
        "automaticPublication": False,
        "scientificValidityInference": False,
        "automaticDestinationDispatch": False,
    }
