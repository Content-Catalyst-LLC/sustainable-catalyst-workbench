"""Workbench v8.4.0 — Interactive Execution Console.

Durable project-scoped execution console over the bounded v7 scientific runtimes.
Jobs are explicit: prepare -> queue -> run. Running is synchronous and occurs only
when the run endpoint is called; no hidden/background execution is implied. The
console stores job metadata/results in the persistent v8 data store, supports
pending-job cancellation, inspection/listing, neutral run comparison, and two-phase
Platform Core binding plans. Arbitrary code/shell execution is not supported.
"""
from __future__ import annotations

import fcntl
import uuid
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v700 import UnifiedExecutionRequest, _execute_request
from .v740 import SolverRequest, solve
from .v750 import SimulationRequest, run_simulation
from .v760 import EngineeringAnalysisRequest, analyze
from .v770 import OptimizationRequest, optimize
from .v790 import GraphRunRequest, run_graph
from .v7100 import NotebookRunRequest, run_notebook
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project

VERSION = APP_VERSION
SCHEMA = "sc-workbench-interactive-execution-console/1.0"
JOB_SCHEMA = "sc-workbench-execution-console-job/1.0"
COMPARE_SCHEMA = "sc-workbench-execution-console-comparison/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-execution-console-core-plan/1.0"
MAX_JOBS_RETURNED = 500
MAX_COMPARE_JOBS = 20

RuntimeKind = Literal["unified", "solver", "simulation", "engineering", "design-space", "workflow", "notebook"]
JobStatus = Literal["prepared", "queued", "running", "completed", "failed", "cancelled"]

router = APIRouter(tags=["workbench-v840-interactive-execution-console"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(value: str) -> str:
    return content_hash({"id": value})[:32]


def _jobs_root() -> Path:
    return _store_root() / "execution-console" / "jobs"


def _job_path(job_id: str) -> Path:
    return _jobs_root() / f"{_id(job_id)}.json"


@contextmanager
def _job_lock(job_id: str):
    path = _store_root() / "locks" / f"execution-console-{_id(job_id)}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _job_hash(job: Dict[str, Any]) -> str:
    candidate = deepcopy(job)
    candidate.pop("jobHash", None)
    return content_hash(candidate)


def _write_job(job: Dict[str, Any]) -> Dict[str, Any]:
    job = deepcopy(job)
    job["jobHash"] = _job_hash(job)
    _atomic_json_write(_job_path(job["jobId"]), job)
    return job


def _load_job(job_id: str) -> Dict[str, Any]:
    path = _job_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"execution-console job {job_id} not found")
    job = _json_read(path)
    if job.get("jobId") != job_id or job.get("jobHash") != _job_hash(job):
        raise ValueError("execution-console job failed integrity validation")
    return job


class PrepareJobRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    runtimeKind: RuntimeKind
    request: Dict[str, Any]
    label: str = Field(default="", max_length=400)
    tags: List[str] = Field(default_factory=list, max_length=64)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    queueImmediately: bool = False
    actor: str = Field(default="workbench", min_length=1, max_length=160)


class JobTransitionRequest(BaseModel):
    expectedJobRevision: Optional[int] = Field(default=None, ge=1)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="user-request", min_length=1, max_length=500)


class CompareJobsRequest(BaseModel):
    jobIds: List[str] = Field(min_length=2, max_length=MAX_COMPARE_JOBS)


class CoreConsolePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    jobIds: List[str] = Field(default_factory=list, max_length=100)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "runtimeKinds": list(RuntimeKind.__args__),
        "jobStatuses": list(JobStatus.__args__),
        "capabilities": {
            "durableProjectExecutionJobs": True,
            "explicitPrepareQueueRunLifecycle": True,
            "pendingJobCancellation": True,
            "jobInspectionAndMonitoring": True,
            "neutralRunComparison": True,
            "specialistRuntimeDispatch": True,
            "projectEnvironmentAnchoring": True,
            "coreExecutionJobPlanning": True,
        },
        "boundaries": {
            "hiddenBackgroundWorkerImplied": False,
            "runEndpointExecutesSynchronously": True,
            "arbitraryCodeExecutionAuthorized": False,
            "shellExecutionAuthorized": False,
            "runningJobPreemptionAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "scientificValidityCertified": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def prepare_job(req: PrepareJobRequest) -> Dict[str, Any]:
    try:
        project = load_project(req.projectKey)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, FileNotFoundError) else 422, detail=str(exc)) from exc
    ws = project["workspace"]
    jid = "wbc-" + uuid.uuid4().hex[:24]
    status: JobStatus = "queued" if req.queueImmediately else "prepared"
    now = _now()
    job: Dict[str, Any] = {
        "ok": True,
        "schema": JOB_SCHEMA,
        "version": VERSION,
        "jobId": jid,
        "jobRevision": 1,
        "projectKey": req.projectKey,
        "projectRevision": project.get("projectRevision"),
        "workspaceHash": ws.get("workspaceHash"),
        "environmentKey": ws.get("activeEnvironmentKey"),
        "environmentRevision": ws.get("activeEnvironmentRevision"),
        "environmentHash": ws.get("activeEnvironmentHash"),
        "runtimeKind": req.runtimeKind,
        "request": deepcopy(req.request),
        "requestHash": content_hash(req.request),
        "label": req.label or f"{req.runtimeKind} execution",
        "tags": sorted(set(req.tags)),
        "metadata": deepcopy(req.metadata),
        "status": status,
        "createdAt": now,
        "updatedAt": now,
        "startedAt": None,
        "completedAt": None,
        "cancelledAt": None,
        "actor": req.actor,
        "result": None,
        "resultHash": None,
        "error": None,
        "history": [{"revision": 1, "status": status, "at": now, "actor": req.actor, "reason": "prepared"}],
        "scientificExecutionPerformed": False,
        "automaticDispatchPerformed": False,
        "hiddenBackgroundExecutionPerformed": False,
        "automaticCoreDispatchPerformed": False,
        "jobHash": "",
    }
    return _write_job(job)


def _transition(job: Dict[str, Any], status: JobStatus, req: JobTransitionRequest) -> Dict[str, Any]:
    current_rev = int(job.get("jobRevision") or 0)
    if req.expectedJobRevision is not None and req.expectedJobRevision != current_rev:
        raise HTTPException(status_code=409, detail={"message": "job revision conflict", "currentJobRevision": current_rev})
    job = deepcopy(job)
    job["jobRevision"] = current_rev + 1
    job["status"] = status
    job["updatedAt"] = _now()
    if status == "running": job["startedAt"] = job["updatedAt"]
    if status in ("completed", "failed"): job["completedAt"] = job["updatedAt"]
    if status == "cancelled": job["cancelledAt"] = job["updatedAt"]
    job.setdefault("history", []).append({"revision": job["jobRevision"], "status": status, "at": job["updatedAt"], "actor": req.actor, "reason": req.reason})
    return _write_job(job)


def queue_job(job_id: str, req: JobTransitionRequest) -> Dict[str, Any]:
    with _job_lock(job_id):
        job = _load_job(job_id)
        if job["status"] != "prepared":
            raise HTTPException(status_code=409, detail="only prepared jobs may be queued")
        return _transition(job, "queued", req)


def cancel_job(job_id: str, req: JobTransitionRequest) -> Dict[str, Any]:
    with _job_lock(job_id):
        job = _load_job(job_id)
        if job["status"] not in ("prepared", "queued"):
            raise HTTPException(status_code=409, detail="only prepared or queued jobs may be cancelled")
        out = _transition(job, "cancelled", req)
        out["scientificExecutionPerformed"] = False
        return _write_job(out)


def _dispatch(runtime_kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if runtime_kind == "unified": return _execute_request(UnifiedExecutionRequest.model_validate(payload))
    if runtime_kind == "solver": return solve(SolverRequest.model_validate(payload))
    if runtime_kind == "simulation": return run_simulation(SimulationRequest.model_validate(payload))
    if runtime_kind == "engineering": return analyze(EngineeringAnalysisRequest.model_validate(payload))
    if runtime_kind == "design-space": return optimize(OptimizationRequest.model_validate(payload))
    if runtime_kind == "workflow": return run_graph(GraphRunRequest.model_validate(payload))
    if runtime_kind == "notebook": return run_notebook(NotebookRunRequest.model_validate(payload))
    raise HTTPException(status_code=422, detail="runtime kind is not dispatchable")


def run_job(job_id: str, req: JobTransitionRequest) -> Dict[str, Any]:
    with _job_lock(job_id):
        job = _load_job(job_id)
        if job["status"] not in ("prepared", "queued"):
            raise HTTPException(status_code=409, detail="only prepared or queued jobs may be run")
        job = _transition(job, "running", req)
        try:
            result = _dispatch(job["runtimeKind"], job["request"])
            job = _load_job(job_id)
            job["result"] = result
            job["resultHash"] = content_hash(result)
            job["scientificExecutionPerformed"] = True
            job["automaticDispatchPerformed"] = False
            job["error"] = None
            return _transition(job, "completed", JobTransitionRequest(expectedJobRevision=job["jobRevision"], actor=req.actor, reason="execution-completed"))
        except Exception as exc:
            job = _load_job(job_id)
            job["scientificExecutionPerformed"] = True
            job["error"] = {"type": exc.__class__.__name__, "message": str(getattr(exc, "detail", exc))[:4000]}
            failed = _transition(job, "failed", JobTransitionRequest(expectedJobRevision=job["jobRevision"], actor=req.actor, reason="execution-failed"))
            if isinstance(exc, HTTPException):
                raise HTTPException(status_code=422, detail={"jobId": job_id, "executionError": exc.detail}) from exc
            raise HTTPException(status_code=422, detail={"jobId": job_id, "executionError": str(exc)}) from exc


def list_jobs(project_key: str = "", status: str = "", runtime_kind: str = "") -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _jobs_root()
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                raw = _json_read(path); job = _load_job(raw["jobId"])
            except Exception:
                continue
            if project_key and job.get("projectKey") != project_key: continue
            if status and job.get("status") != status: continue
            if runtime_kind and job.get("runtimeKind") != runtime_kind: continue
            rows.append({k: job.get(k) for k in ("jobId","projectKey","runtimeKind","label","status","jobRevision","requestHash","resultHash","createdAt","updatedAt","startedAt","completedAt")})
    rows.sort(key=lambda x: (x.get("createdAt") or "", x.get("jobId") or ""), reverse=True)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "jobCount": len(rows), "jobs": rows[:MAX_JOBS_RETURNED]}


def compare_jobs(req: CompareJobsRequest) -> Dict[str, Any]:
    jobs = []
    project_keys = set()
    for jid in req.jobIds:
        try: job = _load_job(jid)
        except (FileNotFoundError, ValueError) as exc: raise HTTPException(status_code=404 if isinstance(exc, FileNotFoundError) else 422, detail=str(exc)) from exc
        if job["status"] != "completed": raise HTTPException(status_code=409, detail=f"job {jid} is not completed")
        project_keys.add(job.get("projectKey")); jobs.append(job)
    rows = []
    for job in jobs:
        result = job.get("result") or {}
        rows.append({
            "jobId": job["jobId"], "runtimeKind": job["runtimeKind"], "label": job.get("label"),
            "requestHash": job.get("requestHash"), "resultHash": job.get("resultHash"),
            "resultSchema": result.get("schema") if isinstance(result, dict) else None,
            "resultOk": result.get("ok") if isinstance(result, dict) else None,
            "startedAt": job.get("startedAt"), "completedAt": job.get("completedAt"),
        })
    out = {"ok": True, "schema": COMPARE_SCHEMA, "version": VERSION, "sameProject": len(project_keys) == 1, "jobCount": len(rows), "jobs": rows, "automaticWinnerSelected": False, "automaticScientificInterpretationPerformed": False}
    out["comparisonHash"] = content_hash(out)
    return out


def core_console_plan(req: CoreConsolePlanRequest) -> Dict[str, Any]:
    base = core_project_plan(ProjectCorePlanRequest(projectKey=req.projectKey, coreProjectEntityId=req.coreProjectEntityId, coreSessionId=req.coreSessionId, visibility=req.visibility, createdBy=req.createdBy))
    selected = []
    for jid in req.jobIds:
        try: job = _load_job(jid)
        except (FileNotFoundError, ValueError) as exc: raise HTTPException(status_code=404 if isinstance(exc, FileNotFoundError) else 422, detail=str(exc)) from exc
        if job.get("projectKey") != req.projectKey: raise HTTPException(status_code=422, detail=f"job {jid} belongs to another project")
        selected.append({"jobId": jid, "status": job.get("status"), "runtimeKind": job.get("runtimeKind"), "requestHash": job.get("requestHash"), "resultHash": job.get("resultHash"), "jobHash": job.get("jobHash")})
    out = {"ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION, "projectKey": req.projectKey, "phase": base.get("phase"), "projectPlan": base, "jobs": selected, "jobCount": len(selected), "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False, "coreExecutesWorkbenchJobs": False}
    out["planHash"] = content_hash(out)
    return out


@router.get("/execution-console/manifest")
def manifest_route(): return manifest()

@router.post("/execution-console/jobs/prepare")
def prepare_route(req: PrepareJobRequest): return prepare_job(req)

@router.get("/execution-console/jobs")
def list_route(project_key: str = Query(default=""), status: str = Query(default=""), runtime_kind: str = Query(default="")): return list_jobs(project_key, status, runtime_kind)

@router.get("/execution-console/jobs/{job_id}")
def get_route(job_id: str):
    try: return _load_job(job_id)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/execution-console/jobs/{job_id}/queue")
def queue_route(job_id: str, req: JobTransitionRequest): return queue_job(job_id, req)

@router.post("/execution-console/jobs/{job_id}/run")
def run_route(job_id: str, req: JobTransitionRequest): return run_job(job_id, req)

@router.post("/execution-console/jobs/{job_id}/cancel")
def cancel_route(job_id: str, req: JobTransitionRequest): return cancel_job(job_id, req)

@router.post("/execution-console/compare")
def compare_route(req: CompareJobsRequest): return compare_jobs(req)

@router.post("/integration/core/execution-console/plan")
def core_plan_route(req: CoreConsolePlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token); return core_console_plan(req)

@router.get("/v840/status")
def status_route():
    m = manifest()
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "release": "Interactive Execution Console", "runtimeKinds": m["runtimeKinds"], "durableJobs": True, "explicitDispatch": True, "pendingJobCancellation": True, "jobComparison": True, "hiddenBackgroundExecution": False, "arbitraryCodeExecution": False, "automaticCoreDispatch": False}
