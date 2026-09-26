"""Workbench v9.10.0 — Platform-Wide Scientific Research Handoff.

Immutable, content-addressed handoff envelopes over v9.9 portable research packages.
The handoff translates one portable package into explicit destination contracts for
Platform Core, Knowledge Library, Research Lab, Decision Studio, external publication,
and archival workflows. Destination readiness is transparent and requirement-based;
no destination receives data automatically and no governed object is created here.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v990 import load_package, list_packages, source_catalog as package_source_catalog

VERSION = APP_VERSION
SCHEMA = "sc-workbench-platform-wide-scientific-research-handoff/1.0"
HANDOFF_SCHEMA = "sc-workbench-platform-wide-scientific-research-handoff-envelope/1.0"
DESTINATION_PLAN_SCHEMA = "sc-workbench-scientific-research-destination-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-platform-core-scientific-research-handoff-plan/1.0"
router = APIRouter(tags=["workbench-v9100-platform-wide-scientific-research-handoff"])

Destination = Literal[
    "platform-core",
    "knowledge-library",
    "research-lab",
    "decision-studio",
    "external-publication",
    "archive",
]
Visibility = Literal["private", "internal", "public"]

DESTINATION_CONTRACTS: Dict[str, Dict[str, Any]] = {
    "platform-core": {
        "contract": "sc-platform-core-scientific-research-handoff/1.0",
        "targetObjectType": "workbench.scientific-research-handoff",
        "requiredAny": ["research-project-workspace"],
        "purpose": "Governed research/evidence/provenance intake and cross-product exchange planning.",
    },
    "knowledge-library": {
        "contract": "sc-knowledge-library-research-handoff/1.0",
        "targetObjectType": "knowledge-library.research-source-package",
        "requiredAny": ["results-synthesis", "cross-study-meta-analysis"],
        "purpose": "Research-source, publication, and connected-knowledge intake planning.",
    },
    "research-lab": {
        "contract": "sc-research-lab-reproducible-study-handoff/1.0",
        "targetObjectType": "research-lab.reproducible-study-package",
        "requiredAny": ["scientific-study", "research-protocol", "computational-campaign", "reproduction-replication-workflow"],
        "purpose": "Reproducible experimentation, replication, and study continuation planning.",
    },
    "decision-studio": {
        "contract": "sc-decision-studio-research-evidence-handoff/1.0",
        "targetObjectType": "decision-studio.research-evidence-package",
        "requiredAny": ["results-synthesis", "cross-study-meta-analysis", "statistical-analysis", "model-calibration"],
        "purpose": "Decision-support evidence intake without converting research outputs into decisions automatically.",
    },
    "external-publication": {
        "contract": "sc-external-publication-research-handoff/1.0",
        "targetObjectType": "external-publication.research-package",
        "requiredAny": ["results-synthesis", "cross-study-meta-analysis"],
        "purpose": "Publication/export preparation with traceable computational provenance.",
    },
    "archive": {
        "contract": "sc-portable-research-archive-handoff/1.0",
        "targetObjectType": "archive.portable-scientific-research-package",
        "requiredAny": ["research-project-workspace"],
        "purpose": "Long-term portable research package preservation.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _handoff_dir(project_key: str) -> Path:
    return _store_root() / "scientific-research-handoffs" / _stable_id(project_key)


def _handoff_path(project_key: str, handoff_hash: str) -> Path:
    return _handoff_dir(project_key) / f"{handoff_hash}.json"


class HandoffRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    handoffKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    portablePackageHash: str = Field(min_length=64, max_length=64)
    description: str = Field(default="", max_length=12000)
    destinations: List[Destination] = Field(default_factory=lambda: ["platform-core", "knowledge-library"], min_length=1, max_length=6)
    requireAllDestinationsReady: bool = False
    visibility: Visibility = "internal"
    createdBy: str = Field(default="workbench", max_length=160)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def normalize(self):
        self.projectKey = self.projectKey.strip()
        self.handoffKey = self.handoffKey.strip()
        self.title = self.title.strip()
        self.destinations = list(dict.fromkeys(self.destinations))
        if len(self.portablePackageHash) != 64:
            raise ValueError("portablePackageHash must be a 64-character content hash")
        return self


class DestinationPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    handoffHash: str = Field(min_length=64, max_length=64)
    destination: Destination
    requestedBy: str = Field(default="workbench", max_length=160)


class CoreHandoffPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    handoffHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Visibility = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Platform-Wide Scientific Research Handoff",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "handoffSchema": HANDOFF_SCHEMA,
        "destinations": list(DESTINATION_CONTRACTS),
        "capabilities": {
            "platformWideScientificResearchHandoff": True,
            "portablePackageTransportBinding": True,
            "destinationSpecificContracts": True,
            "destinationReadinessAssessment": True,
            "unresolvedRequirementReporting": True,
            "contentAddressedHandoffEnvelopes": True,
            "crossProductResearchExchangePlanning": True,
            "platformCoreGovernancePlanning": True,
        },
        "boundaries": {
            "automaticDestinationDispatch": False,
            "automaticNativeImportActivation": False,
            "automaticScientificValidityInference": False,
            "automaticEvidencePromotion": False,
            "automaticPublication": False,
            "automaticDecisionRecommendation": False,
            "governedCoreObjectCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _object_inventory(package: Dict[str, Any]) -> Dict[str, Any]:
    objects = package.get("objects") or []
    rows = []
    counts: Dict[str, int] = {}
    for obj in objects:
        typ = str(obj.get("objectType") or "unknown")
        counts[typ] = counts.get(typ, 0) + 1
        rows.append({
            "objectType": typ,
            "sourceProjectKey": obj.get("sourceProjectKey"),
            "sourceObjectHash": obj.get("sourceObjectHash"),
            "payloadHash": obj.get("payloadHash"),
            "label": obj.get("label"),
        })
    return {"objectCount": len(rows), "objectTypeCounts": counts, "objects": rows}


def _destination_readiness(destination: str, inventory: Dict[str, Any]) -> Dict[str, Any]:
    contract = DESTINATION_CONTRACTS[destination]
    present = set(inventory["objectTypeCounts"])
    required_any = list(contract["requiredAny"])
    matched = sorted(present.intersection(required_any))
    ready = bool(matched)
    missing = [] if ready else required_any
    return {
        "destination": destination,
        "contract": contract["contract"],
        "targetObjectType": contract["targetObjectType"],
        "purpose": contract["purpose"],
        "requiredAny": required_any,
        "matchedObjectTypes": matched,
        "missingRequirements": missing,
        "readyForExplicitDispatchPlanning": ready,
        "dispatchState": "not-dispatched",
        "automaticDispatch": False,
    }


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    portable = list_packages(project_key)
    handoffs = list_handoffs(project_key)
    upstream = package_source_catalog(project_key)
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "portablePackages": portable.get("packages", []),
        "portablePackageCount": portable.get("packageCount", 0),
        "handoffs": handoffs.get("handoffs", []),
        "handoffCount": handoffs.get("handoffCount", 0),
        "upstreamCatalogs": upstream.get("catalogs", {}),
        "boundaries": {
            "catalogDispatchesAutomatically": False,
            "catalogActivatesImports": False,
            "catalogInfersScientificValidity": False,
        },
    }
    out["catalogHash"] = content_hash(out)
    return out


def compose_handoff(req: HandoffRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    package = load_package(req.projectKey, req.portablePackageHash)
    inventory = _object_inventory(package)
    plans = [_destination_readiness(d, inventory) for d in req.destinations]
    unresolved = [
        {"destination": p["destination"], "missingRequirements": p["missingRequirements"]}
        for p in plans if not p["readyForExplicitDispatchPlanning"]
    ]
    if req.requireAllDestinationsReady and unresolved:
        raise ValueError("one or more requested destinations are not ready for explicit dispatch planning")
    seed = {
        "handoffSchema": HANDOFF_SCHEMA,
        "projectKey": req.projectKey,
        "handoffKey": req.handoffKey,
        "title": req.title,
        "description": req.description,
        "portablePackageHash": req.portablePackageHash,
        "portablePackageRef": package.get("packageRef"),
        "portableArchiveSha256": package.get("archiveSha256"),
        "sourceWorkbenchVersion": package.get("sourceWorkbenchVersion"),
        "dependencyInventory": package.get("dependencyInventory") or {},
        "objectInventory": inventory,
        "destinations": req.destinations,
        "destinationPlans": plans,
        "visibility": req.visibility,
        "notes": req.notes,
    }
    handoff_hash = content_hash(seed)
    ready_count = sum(1 for p in plans if p["readyForExplicitDispatchPlanning"])
    return {
        "ok": True,
        "schema": HANDOFF_SCHEMA,
        "version": VERSION,
        **seed,
        "handoffHash": handoff_hash,
        "handoffRef": f"sc://workbench/scientific-research-handoff/{req.projectKey}/{handoff_hash}",
        "readiness": {
            "requestedDestinationCount": len(plans),
            "readyDestinationCount": ready_count,
            "unresolvedDestinationCount": len(unresolved),
            "allRequestedDestinationsReady": ready_count == len(plans),
            "unresolvedRequirements": unresolved,
        },
        "lifecycle": {"state": "prepared", "dispatchState": "not-dispatched"},
        "createdBy": req.createdBy,
        "boundaries": manifest()["boundaries"],
    }


def save_handoff(req: HandoffRequest) -> Dict[str, Any]:
    record = compose_handoff(req)
    path = _handoff_path(req.projectKey, record["handoffHash"])
    if path.exists():
        old = _json_read(path)
        return {**old, "idempotent": True}
    stored = {**record, "createdAt": _now()}
    _atomic_json_write(path, stored)
    return {**stored, "idempotent": False}


def load_handoff(project_key: str, handoff_hash: str) -> Dict[str, Any]:
    path = _handoff_path(project_key, handoff_hash)
    if not path.exists():
        raise FileNotFoundError(f"scientific research handoff not found: {handoff_hash}")
    return _json_read(path)


def list_handoffs(project_key: str) -> Dict[str, Any]:
    root = _handoff_dir(project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r = _json_read(p)
                rows.append({
                    "handoffKey": r.get("handoffKey"),
                    "title": r.get("title"),
                    "handoffHash": r.get("handoffHash"),
                    "handoffRef": r.get("handoffRef"),
                    "portablePackageHash": r.get("portablePackageHash"),
                    "destinations": r.get("destinations"),
                    "readiness": r.get("readiness"),
                    "createdAt": r.get("createdAt"),
                    "createdBy": r.get("createdBy"),
                })
            except Exception:
                continue
    return {"ok": True, "schema": HANDOFF_SCHEMA, "version": VERSION, "projectKey": project_key, "handoffCount": len(rows), "handoffs": rows}


def destination_plan(req: DestinationPlanRequest) -> Dict[str, Any]:
    handoff = load_handoff(req.projectKey, req.handoffHash)
    row = next((p for p in handoff.get("destinationPlans", []) if p.get("destination") == req.destination), None)
    if row is None:
        inventory = handoff.get("objectInventory") or {"objectTypeCounts": {}}
        row = _destination_readiness(req.destination, inventory)
    out = {
        "ok": True,
        "schema": DESTINATION_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "handoffHash": req.handoffHash,
        "handoffRef": handoff.get("handoffRef"),
        "portablePackageHash": handoff.get("portablePackageHash"),
        "portableArchiveSha256": handoff.get("portableArchiveSha256"),
        "destinationPlan": row,
        "requestedBy": req.requestedBy,
        "boundaries": {
            "automaticDispatch": False,
            "destinationStateMutated": False,
            "governedObjectCreated": False,
            "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def core_plan(req: CoreHandoffPlanRequest) -> Dict[str, Any]:
    handoff = load_handoff(req.projectKey, req.handoffHash)
    cfg = core_config()
    inventory = handoff.get("objectInventory") or {"objectTypeCounts": {}}
    readiness = _destination_readiness("platform-core", inventory)
    binding = {
        "objectType": "workbench.scientific-research-handoff",
        "objectHash": req.handoffHash,
        "objectRef": handoff.get("handoffRef"),
        "portablePackageHash": handoff.get("portablePackageHash"),
        "portableArchiveSha256": handoff.get("portableArchiveSha256"),
        "destinationContract": readiness["contract"],
        "coreProjectEntityId": req.coreProjectEntityId,
        "coreSessionId": req.coreSessionId,
        "visibility": req.visibility,
        "createdBy": req.createdBy,
    }
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "handoffHash": req.handoffHash,
        "readyForExplicitDispatchPlanning": readiness["readyForExplicitDispatchPlanning"],
        "bindingPlan": binding,
        "core": {"enabled": bool(cfg.get("enabled")), "baseUrlConfigured": bool(cfg.get("baseUrl"))},
        "boundaries": {
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
            "portablePackageImported": False,
            "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def _wrap(fn, *args):
    try:
        return fn(*args)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/scientific-research-handoff/manifest")
def route_manifest(): return manifest()

@router.get("/scientific-research-handoff/source-catalog/{project_key}")
def route_catalog(project_key: str): return _wrap(source_catalog, project_key)

@router.post("/scientific-research-handoff/compose")
def route_compose(req: HandoffRequest): return _wrap(compose_handoff, req)

@router.post("/scientific-research-handoff/handoffs")
def route_save(req: HandoffRequest): return _wrap(save_handoff, req)

@router.get("/scientific-research-handoff/handoffs/{project_key}")
def route_list(project_key: str): return list_handoffs(project_key)

@router.get("/scientific-research-handoff/handoffs/{project_key}/{handoff_hash}")
def route_get(project_key: str, handoff_hash: str): return _wrap(load_handoff, project_key, handoff_hash)

@router.post("/scientific-research-handoff/destination-plan")
def route_destination_plan(req: DestinationPlanRequest): return _wrap(destination_plan, req)

@router.post("/integration/core/scientific-research-handoff/plan")
def route_core(req: CoreHandoffPlanRequest): return _wrap(core_plan, req)

@router.get("/v9100/status")
def status():
    m = manifest()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": m["release"],
        "platformWideScientificResearchHandoff": True,
        "portablePackageTransportBinding": True,
        "destinationSpecificContracts": True,
        "destinationReadinessAssessment": True,
        "automaticDestinationDispatch": False,
        "governedCoreObjectCreated": False,
        "manifestHash": m["manifestHash"],
    }
