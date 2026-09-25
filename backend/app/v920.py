"""Workbench v9.2.0 — Batch Experiment & Computational Campaign Manager.

Researcher-defined computational campaigns bound to v9.1 research protocols.
The manager expands explicit parameter axes and replication counts into
content-addressed planned runs, enforces user-defined run/resource budgets,
persists campaign definitions and resumable mutable campaign state, materializes
planned runs into v8.4 execution-console jobs only on explicit request, refreshes
job/result lineage, and prepares neutral analysis/Core handoff plans.

The manager does not automatically queue/run jobs, choose a preferred result,
infer scientific validity/significance/causality, alter protocol intent, or
dispatch anything to Platform Core.
"""
from __future__ import annotations

import hashlib
import itertools
import re
from copy import deepcopy
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
from .v840 import PrepareJobRequest, RuntimeKind, _load_job, prepare_job
from .v910 import load_protocol, list_protocols

VERSION = APP_VERSION
SCHEMA = "sc-workbench-batch-experiment-computational-campaign-manager/1.0"
CAMPAIGN_SCHEMA = "sc-workbench-computational-campaign/1.0"
STATE_SCHEMA = "sc-workbench-computational-campaign-state/1.0"
CATALOG_SCHEMA = "sc-workbench-computational-campaign-source-catalog/1.0"
ANALYSIS_PLAN_SCHEMA = "sc-workbench-computational-campaign-analysis-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-computational-campaign-core-plan/1.0"
router = APIRouter(tags=["workbench-v920-batch-experiment-computational-campaign-manager"])

MAX_AXES = 12
MAX_AXIS_VALUES = 100
MAX_PLANNED_RUNS = 5000
MAX_MATERIALIZE_BATCH = 500
_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
CampaignStatus = Literal["draft", "ready", "active", "completed", "paused", "archived"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _campaign_dir(project_key: str) -> Path:
    return _store_root() / "computational-campaigns" / _stable_id(project_key)


def _campaign_path(project_key: str, campaign_hash: str) -> Path:
    return _campaign_dir(project_key) / "definitions" / f"{campaign_hash}.json"


def _state_path(project_key: str, campaign_hash: str) -> Path:
    return _campaign_dir(project_key) / "state" / f"{campaign_hash}.json"


def _json_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


class ParameterAxis(BaseModel):
    path: str = Field(min_length=1, max_length=240)
    values: List[Any] = Field(min_length=1, max_length=MAX_AXIS_VALUES)
    label: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_axis(self):
        self.path = self.path.strip()
        self.label = self.label.strip()
        if not _PATH_RE.fullmatch(self.path):
            raise ValueError("parameter axis path must be a dot-separated JSON object path")
        if not all(_json_scalar(v) for v in self.values):
            raise ValueError("parameter axis values must be JSON scalar values")
        hashes = [content_hash({"value": v}) for v in self.values]
        if len(hashes) != len(set(hashes)):
            raise ValueError("parameter axis values must be unique")
        return self


class CampaignBudget(BaseModel):
    maxRuns: int = Field(default=1000, ge=1, le=MAX_PLANNED_RUNS)
    maxPreparedJobs: int = Field(default=1000, ge=1, le=MAX_PLANNED_RUNS)
    maxFailures: int | None = Field(default=None, ge=0, le=MAX_PLANNED_RUNS)
    maxWallMinutes: float | None = Field(default=None, gt=0, le=10_000_000)
    notes: str = Field(default="", max_length=4000)


class CampaignRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    protocolHash: str = Field(min_length=64, max_length=64)
    campaignKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    status: CampaignStatus = "draft"
    runtimeKind: RuntimeKind
    requestTemplate: Dict[str, Any]
    parameterAxes: List[ParameterAxis] = Field(default_factory=list, max_length=MAX_AXES)
    replications: int = Field(default=1, ge=1, le=500)
    budget: CampaignBudget = Field(default_factory=CampaignBudget)
    tags: List[str] = Field(default_factory=list, max_length=100)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def validate_campaign(self):
        self.projectKey = self.projectKey.strip()
        self.campaignKey = self.campaignKey.strip()
        self.title = self.title.strip()
        paths = [x.path for x in self.parameterAxes]
        if len(paths) != len(set(paths)):
            raise ValueError("parameter axis paths must be unique")
        if not self.requestTemplate:
            raise ValueError("requestTemplate must not be empty")
        return self


class SaveCampaignRequest(CampaignRequest):
    recordLabel: str = Field(default="Computational campaign", max_length=500)
    createdBy: str = Field(default="workbench", max_length=160)


class MaterializeRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    campaignHash: str = Field(min_length=64, max_length=64)
    limit: int = Field(default=100, ge=1, le=MAX_MATERIALIZE_BATCH)
    actor: str = Field(default="workbench", min_length=1, max_length=160)


class CampaignPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    campaignHash: str = Field(min_length=64, max_length=64)


class CoreCampaignPlanRequest(CampaignPlanRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Batch Experiment & Computational Campaign Manager",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "campaignLifecycle": ["define", "save", "materialize-prepared-jobs", "explicit-run", "refresh", "analyze"],
        "capabilities": {
            "contentAddressedCampaignDefinitions": True,
            "deterministicCartesianParameterSweeps": True,
            "explicitReplicationSets": True,
            "runAndResourceBudgets": True,
            "resumableCampaignState": True,
            "executionConsoleJobMaterialization": True,
            "campaignResultLineageRefresh": True,
            "neutralAnalysisHandoffPlanning": True,
            "platformCoreCampaignPlanning": True,
        },
        "boundaries": {
            "automaticJobQueueing": False,
            "automaticJobExecution": False,
            "hiddenBackgroundExecution": False,
            "automaticBestResultSelection": False,
            "automaticStatisticalSignificanceInference": False,
            "automaticCausalInference": False,
            "automaticScientificValidityInference": False,
            "automaticProtocolMutation": False,
            "automaticAnalysisDispatch": False,
            "automaticCoreDispatch": False,
            "platformCoreGovernanceReplaced": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _deep_set(obj: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur = obj
    for key in parts[:-1]:
        nxt = cur.get(key)
        if nxt is None:
            nxt = {}
            cur[key] = nxt
        if not isinstance(nxt, dict):
            raise ValueError(f"parameter axis path crosses a non-object value: {path}")
        cur = nxt
    cur[parts[-1]] = value


def _axis_combinations(axes: List[ParameterAxis]) -> List[Dict[str, Any]]:
    if not axes:
        return [{}]
    value_lists = [axis.values for axis in axes]
    rows: List[Dict[str, Any]] = []
    for combo in itertools.product(*value_lists):
        rows.append({axis.path: value for axis, value in zip(axes, combo)})
    return rows


def compose_campaign(req: CampaignRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    protocol = load_protocol(req.projectKey, req.protocolHash)
    combos = _axis_combinations(req.parameterAxes)
    run_count = len(combos) * req.replications
    if run_count > MAX_PLANNED_RUNS:
        raise ValueError(f"campaign expands to {run_count} runs; hard limit is {MAX_PLANNED_RUNS}")
    if run_count > req.budget.maxRuns:
        raise ValueError(f"campaign expands to {run_count} runs; budget.maxRuns is {req.budget.maxRuns}")

    campaign_seed = {
        "projectKey": req.projectKey,
        "protocolHash": req.protocolHash,
        "campaignKey": req.campaignKey,
        "title": req.title,
        "status": req.status,
        "runtimeKind": req.runtimeKind,
        "requestTemplate": req.requestTemplate,
        "parameterAxes": [x.model_dump() for x in req.parameterAxes],
        "replications": req.replications,
        "budget": req.budget.model_dump(),
        "tags": sorted(set(req.tags)),
        "notes": req.notes,
    }
    definition_hash = content_hash(campaign_seed)
    runs: List[Dict[str, Any]] = []
    order = 0
    for combo_index, params in enumerate(combos):
        for replicate_index in range(1, req.replications + 1):
            order += 1
            request = deepcopy(req.requestTemplate)
            for path, value in params.items():
                _deep_set(request, path, value)
            rid = content_hash({
                "definitionHash": definition_hash,
                "comboIndex": combo_index,
                "replicateIndex": replicate_index,
                "parameterValues": params,
                "requestHash": content_hash(request),
            })
            runs.append({
                "plannedRunId": rid,
                "order": order,
                "comboIndex": combo_index,
                "replicateIndex": replicate_index,
                "parameterValues": params,
                "request": request,
                "requestHash": content_hash(request),
            })

    readiness = {
        "protocolBound": True,
        "requestTemplatePresent": bool(req.requestTemplate),
        "withinRunBudget": run_count <= req.budget.maxRuns,
        "withinHardRunLimit": run_count <= MAX_PLANNED_RUNS,
        "allAxesPopulated": all(bool(x.values) for x in req.parameterAxes),
    }
    out: Dict[str, Any] = {
        "ok": True,
        "schema": CAMPAIGN_SCHEMA,
        "version": VERSION,
        "release": "Batch Experiment & Computational Campaign Manager",
        "projectKey": req.projectKey,
        "protocolHash": req.protocolHash,
        "protocolRef": protocol.get("protocolRef"),
        "studyHash": protocol.get("studyHash"),
        "campaignKey": req.campaignKey,
        "title": req.title,
        "status": req.status,
        "runtimeKind": req.runtimeKind,
        "requestTemplate": req.requestTemplate,
        "parameterAxes": [x.model_dump() for x in req.parameterAxes],
        "replications": req.replications,
        "budget": req.budget.model_dump(),
        "plannedRunCount": run_count,
        "plannedRuns": runs,
        "readiness": readiness,
        "campaignReady": all(readiness.values()),
        "tags": sorted(set(req.tags)),
        "notes": req.notes,
        "sourceHashes": {
            "protocolHash": protocol.get("protocolHash"),
            "protocolRecordHash": protocol.get("recordHash"),
            "studyHash": protocol.get("studyHash"),
        },
        "boundaries": manifest()["boundaries"],
    }
    out["campaignHash"] = content_hash({k: v for k, v in out.items() if k != "campaignHash"})
    out["campaignRef"] = f"sc://workbench/campaign/{req.projectKey}/{out['campaignHash']}"
    return out


def _state_hash(state: Dict[str, Any]) -> str:
    return content_hash({k: v for k, v in state.items() if k not in {"updatedAt", "stateHash"}})


def _initial_state(campaign: Dict[str, Any]) -> Dict[str, Any]:
    state = {
        "ok": True,
        "schema": STATE_SCHEMA,
        "version": VERSION,
        "projectKey": campaign["projectKey"],
        "campaignHash": campaign["campaignHash"],
        "campaignRef": campaign["campaignRef"],
        "stateRevision": 1,
        "updatedAt": _now(),
        "jobs": {},
        "summary": {
            "planned": campaign["plannedRunCount"],
            "materialized": 0,
            "prepared": 0,
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "unmaterialized": campaign["plannedRunCount"],
        },
        "automaticQueueingPerformed": False,
        "automaticExecutionPerformed": False,
        "automaticAnalysisPerformed": False,
        "automaticCoreDispatchPerformed": False,
    }
    state["stateHash"] = _state_hash(state)
    return state


def _write_state(state: Dict[str, Any]) -> Dict[str, Any]:
    state = deepcopy(state)
    state["updatedAt"] = _now()
    state["stateHash"] = _state_hash(state)
    _atomic_json_write(_state_path(state["projectKey"], state["campaignHash"]), state)
    return state


def _load_state(project_key: str, campaign_hash: str) -> Dict[str, Any]:
    path = _state_path(project_key, campaign_hash)
    if not path.exists():
        campaign = load_campaign(project_key, campaign_hash)
        return _write_state(_initial_state(campaign))
    state = _json_read(path)
    if state.get("projectKey") != project_key or state.get("campaignHash") != campaign_hash:
        raise ValueError("campaign state identity mismatch")
    if state.get("stateHash") != _state_hash(state):
        raise ValueError("campaign state failed integrity validation")
    return state


def save_campaign(req: SaveCampaignRequest) -> Dict[str, Any]:
    base = set(CampaignRequest.model_fields)
    campaign = compose_campaign(CampaignRequest(**req.model_dump(include=base)))
    record = {**campaign, "recordLabel": req.recordLabel, "createdBy": req.createdBy, "createdAt": _now()}
    record["recordHash"] = content_hash({k: v for k, v in record.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    path = _campaign_path(req.projectKey, campaign["campaignHash"])
    if path.exists():
        existing = _json_read(path)
        expected = content_hash({k: v for k, v in existing.items() if k not in {"createdAt", "recordHash", "idempotent"}})
        if existing.get("recordHash") != expected:
            raise ValueError("stored computational campaign failed integrity validation")
        _load_state(req.projectKey, campaign["campaignHash"])
        existing["idempotent"] = True
        return existing
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(path, record)
    _write_state(_initial_state(record))
    record["idempotent"] = False
    return record


def list_campaigns(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    rows: List[Dict[str, Any]] = []
    root = _campaign_dir(project_key) / "definitions"
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                rec = _json_read(path)
                if rec.get("projectKey") != project_key:
                    continue
                state = _load_state(project_key, rec["campaignHash"])
                row = {k: rec.get(k) for k in ("campaignHash", "campaignRef", "campaignKey", "title", "status", "runtimeKind", "protocolHash", "studyHash", "plannedRunCount", "recordLabel", "createdBy", "createdAt", "recordHash")}
                row["stateSummary"] = state.get("summary", {})
                rows.append(row)
            except Exception:
                continue
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return {"ok": True, "schema": CAMPAIGN_SCHEMA, "version": VERSION, "projectKey": project_key, "campaignCount": len(rows), "campaigns": rows}


def load_campaign(project_key: str, campaign_hash: str) -> Dict[str, Any]:
    load_project(project_key)
    path = _campaign_path(project_key, campaign_hash)
    if not path.exists():
        raise FileNotFoundError("computational campaign not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("campaignHash") != campaign_hash:
        raise ValueError("computational campaign identity mismatch")
    expected = content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    if rec.get("recordHash") != expected:
        raise ValueError("computational campaign failed integrity validation")
    return rec


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    protocols = list_protocols(project_key)
    campaigns = list_campaigns(project_key)
    out = {
        "ok": True,
        "schema": CATALOG_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "protocolCount": protocols.get("protocolCount", 0),
        "protocols": protocols.get("protocols", []),
        "campaignCount": campaigns.get("campaignCount", 0),
        "campaigns": campaigns.get("campaigns", []),
        "boundaries": {
            "catalogMutatesSources": False,
            "catalogQueuesJobs": False,
            "catalogRunsJobs": False,
            "catalogInfersScientificValidity": False,
        },
    }
    out["catalogHash"] = content_hash(out)
    return out


def _summary(campaign: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, int]:
    statuses = {"prepared": 0, "queued": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
    jobs = state.get("jobs", {})
    for row in jobs.values():
        status = row.get("status")
        if status in statuses:
            statuses[status] += 1
    statuses["planned"] = int(campaign.get("plannedRunCount") or 0)
    statuses["materialized"] = len(jobs)
    statuses["unmaterialized"] = max(0, statuses["planned"] - statuses["materialized"])
    return statuses


def materialize_campaign(req: MaterializeRequest) -> Dict[str, Any]:
    campaign = load_campaign(req.projectKey, req.campaignHash)
    state = _load_state(req.projectKey, req.campaignHash)
    jobs: Dict[str, Any] = deepcopy(state.get("jobs", {}))
    prepared_cap = int(campaign.get("budget", {}).get("maxPreparedJobs") or campaign["plannedRunCount"])
    remaining_cap = max(0, prepared_cap - len(jobs))
    limit = min(req.limit, remaining_cap)
    created: List[Dict[str, Any]] = []
    if limit > 0:
        for run in campaign["plannedRuns"]:
            run_id = run["plannedRunId"]
            if run_id in jobs:
                continue
            job = prepare_job(PrepareJobRequest(
                projectKey=req.projectKey,
                runtimeKind=campaign["runtimeKind"],
                request=run["request"],
                label=f"{campaign['title']} · run {run['order']}",
                tags=sorted(set(list(campaign.get("tags", [])) + [f"campaign:{campaign['campaignKey']}"])),
                metadata={
                    "campaignHash": req.campaignHash,
                    "campaignRef": campaign["campaignRef"],
                    "protocolHash": campaign["protocolHash"],
                    "studyHash": campaign.get("studyHash"),
                    "plannedRunId": run_id,
                    "runOrder": run["order"],
                    "comboIndex": run["comboIndex"],
                    "replicateIndex": run["replicateIndex"],
                    "parameterValues": run["parameterValues"],
                },
                queueImmediately=False,
                actor=req.actor,
            ))
            jobs[run_id] = {
                "plannedRunId": run_id,
                "jobId": job["jobId"],
                "status": job["status"],
                "jobHash": job.get("jobHash"),
                "requestHash": job.get("requestHash"),
                "resultHash": job.get("resultHash"),
                "parameterValues": run["parameterValues"],
                "replicateIndex": run["replicateIndex"],
                "materializedAt": _now(),
            }
            created.append(jobs[run_id])
            if len(created) >= limit:
                break
    state["jobs"] = jobs
    state["stateRevision"] = int(state.get("stateRevision") or 0) + 1
    state["summary"] = _summary(campaign, state)
    state = _write_state(state)
    return {
        "ok": True,
        "schema": STATE_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "campaignHash": req.campaignHash,
        "createdJobCount": len(created),
        "createdJobs": created,
        "state": state,
        "budget": campaign.get("budget", {}),
        "automaticQueueingPerformed": False,
        "automaticExecutionPerformed": False,
    }


def refresh_campaign(req: CampaignPlanRequest) -> Dict[str, Any]:
    campaign = load_campaign(req.projectKey, req.campaignHash)
    state = _load_state(req.projectKey, req.campaignHash)
    jobs = deepcopy(state.get("jobs", {}))
    missing = 0
    for run_id, row in jobs.items():
        try:
            job = _load_job(row["jobId"])
            row.update({
                "status": job.get("status"),
                "jobHash": job.get("jobHash"),
                "requestHash": job.get("requestHash"),
                "resultHash": job.get("resultHash"),
                "updatedAt": job.get("updatedAt"),
                "completedAt": job.get("completedAt"),
                "jobMissing": False,
            })
        except Exception:
            row["jobMissing"] = True
            missing += 1
    state["jobs"] = jobs
    state["stateRevision"] = int(state.get("stateRevision") or 0) + 1
    state["summary"] = _summary(campaign, state)
    state = _write_state(state)
    return {"ok": True, "schema": STATE_SCHEMA, "version": VERSION, "campaignHash": req.campaignHash, "missingJobCount": missing, "state": state}


def analysis_plan(req: CampaignPlanRequest) -> Dict[str, Any]:
    campaign = load_campaign(req.projectKey, req.campaignHash)
    state = refresh_campaign(req)["state"]
    completed = []
    for run_id, row in state.get("jobs", {}).items():
        if row.get("status") == "completed":
            completed.append({
                "plannedRunId": run_id,
                "jobId": row.get("jobId"),
                "requestHash": row.get("requestHash"),
                "resultHash": row.get("resultHash"),
                "parameterValues": row.get("parameterValues", {}),
                "replicateIndex": row.get("replicateIndex"),
            })
    completed.sort(key=lambda x: x["plannedRunId"])
    out = {
        "ok": True,
        "schema": ANALYSIS_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "campaignHash": req.campaignHash,
        "campaignRef": campaign.get("campaignRef"),
        "protocolHash": campaign.get("protocolHash"),
        "studyHash": campaign.get("studyHash"),
        "completedRunCount": len(completed),
        "completedRuns": completed,
        "stateSummary": state.get("summary", {}),
        "suggestedTargets": ["comparative-analysis", "reproducible-analysis-board"],
        "boundaries": {
            "automaticAnalysisDispatchAuthorized": False,
            "automaticWinnerSelectionAuthorized": False,
            "automaticScientificInterpretationAuthorized": False,
            "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def core_plan(req: CoreCampaignPlanRequest) -> Dict[str, Any]:
    campaign = load_campaign(req.projectKey, req.campaignHash)
    state = _load_state(req.projectKey, req.campaignHash)
    cfg = core_config()
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "campaignHash": req.campaignHash,
        "campaignRef": campaign.get("campaignRef"),
        "protocolHash": campaign.get("protocolHash"),
        "studyHash": campaign.get("studyHash"),
        "coreProjectEntityId": req.coreProjectEntityId or req.projectKey,
        "coreSessionId": req.coreSessionId,
        "visibility": req.visibility,
        "createdBy": req.createdBy,
        "coreEnabled": bool(cfg.get("enabled")),
        "coreTarget": cfg.get("baseUrl") or "",
        "bindingPlan": {
            "objectType": "workbench.computational-campaign",
            "objectRef": campaign.get("campaignRef"),
            "objectHash": req.campaignHash,
            "protocolHash": campaign.get("protocolHash"),
            "studyHash": campaign.get("studyHash"),
            "plannedRunCount": campaign.get("plannedRunCount"),
            "campaignStateHash": state.get("stateHash"),
            "sourceHashes": campaign.get("sourceHashes", {}),
        },
        "boundaries": {
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "coreGovernanceAuthorityPreserved": True,
            "scientificValidityInferred": False,
            "preferredRunInferred": False,
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
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/campaign-manager/manifest")
def route_manifest(): return manifest()

@router.get("/campaign-manager/source-catalog/{project_key}")
def route_catalog(project_key: str): return _wrap(source_catalog, project_key)

@router.post("/campaign-manager/compose")
def route_compose(req: CampaignRequest): return _wrap(compose_campaign, req)

@router.post("/campaign-manager/campaigns")
def route_save(req: SaveCampaignRequest): return _wrap(save_campaign, req)

@router.get("/campaign-manager/campaigns/{project_key}")
def route_list(project_key: str): return _wrap(list_campaigns, project_key)

@router.get("/campaign-manager/campaigns/{project_key}/{campaign_hash}")
def route_get(project_key: str, campaign_hash: str): return _wrap(load_campaign, project_key, campaign_hash)

@router.get("/campaign-manager/campaigns/{project_key}/{campaign_hash}/state")
def route_state(project_key: str, campaign_hash: str): return _wrap(_load_state, project_key, campaign_hash)

@router.post("/campaign-manager/materialize")
def route_materialize(req: MaterializeRequest): return _wrap(materialize_campaign, req)

@router.post("/campaign-manager/refresh")
def route_refresh(req: CampaignPlanRequest): return _wrap(refresh_campaign, req)

@router.post("/campaign-manager/analysis-plan")
def route_analysis_plan(req: CampaignPlanRequest): return _wrap(analysis_plan, req)

@router.post("/integration/core/campaign-manager/plan")
def route_core_plan(req: CoreCampaignPlanRequest): return _wrap(core_plan, req)

@router.get("/v920/status")
def status():
    m = manifest()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": m["release"],
        "batchExperimentComputationalCampaignManager": True,
        "deterministicParameterSweeps": True,
        "resumableCampaignState": True,
        "executionConsoleJobMaterialization": True,
        "automaticJobExecution": False,
        "automaticWinnerSelection": False,
        "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }
