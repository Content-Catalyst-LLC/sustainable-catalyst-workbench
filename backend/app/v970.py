"""Workbench v9.7.0 — Reproduction & Replication Workflow.

Researcher-controlled workflows for reproducing an existing Workbench synthesis or
planning a replication with explicitly documented changes. The workflow captures
target lineage, environment/input expectations, rerun specifications, comparison
criteria, observed comparison values, discrepancies, and researcher notes.

This layer does not execute jobs automatically, infer scientific validity, decide
that a study has been replicated, or convert discrepancies into governed claims.
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
from .v960 import load_synthesis, list_syntheses

VERSION = APP_VERSION
SCHEMA = "sc-workbench-reproduction-replication-workflow/1.0"
WORKFLOW_SCHEMA = "sc-workbench-reproduction-replication-record/1.0"
CATALOG_SCHEMA = "sc-workbench-reproduction-replication-source-catalog/1.0"
EXECUTION_PLAN_SCHEMA = "sc-workbench-reproduction-execution-plan/1.0"
COMPARISON_SCHEMA = "sc-workbench-reproduction-comparison/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-reproduction-replication-core-plan/1.0"
router = APIRouter(tags=["workbench-v970-reproduction-replication-workflow"])

Mode = Literal["reproduction", "replication"]
Comparator = Literal["absolute", "relative", "exact"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _workflow_dir(project_key: str) -> Path:
    return _store_root() / "reproduction-replication-workflows" / _stable_id(project_key)


def _workflow_path(project_key: str, workflow_hash: str) -> Path:
    return _workflow_dir(project_key) / f"{workflow_hash}.json"


class EnvironmentCapture(BaseModel):
    runtime: str = Field(default="", max_length=160)
    runtimeVersion: str = Field(default="", max_length=160)
    operatingSystem: str = Field(default="", max_length=240)
    dependencyLockHash: str = Field(default="", max_length=128)
    containerImage: str = Field(default="", max_length=500)
    hardwareNotes: str = Field(default="", max_length=4000)
    environmentNotes: str = Field(default="", max_length=8000)


class InputCapture(BaseModel):
    inputKey: str = Field(min_length=1, max_length=160)
    role: str = Field(default="input", max_length=160)
    objectRef: str = Field(default="", max_length=1000)
    contentHash: str = Field(default="", max_length=128)
    version: str = Field(default="", max_length=160)
    notes: str = Field(default="", max_length=4000)


class ComparisonCriterion(BaseModel):
    criterionKey: str = Field(min_length=1, max_length=160)
    metric: str = Field(min_length=1, max_length=500)
    comparator: Comparator = "absolute"
    targetValue: Optional[float] = None
    tolerance: float = Field(default=0.0, ge=0.0)
    unit: str = Field(default="", max_length=120)
    rationale: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_exact(self):
        if self.comparator == "exact" and self.tolerance != 0:
            raise ValueError("exact comparison requires tolerance=0")
        return self


class WorkflowRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    workflowKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    mode: Mode = "reproduction"
    targetSynthesisHash: str = Field(min_length=64, max_length=64)
    researchQuestion: str = Field(default="", max_length=8000)
    protocolNotes: str = Field(default="", max_length=12000)
    environment: EnvironmentCapture = Field(default_factory=EnvironmentCapture)
    inputs: List[InputCapture] = Field(default_factory=list, max_length=200)
    comparisonCriteria: List[ComparisonCriterion] = Field(default_factory=list, max_length=200)
    plannedChanges: List[str] = Field(default_factory=list, max_length=200)
    invariants: List[str] = Field(default_factory=list, max_length=200)
    preregistrationRef: str = Field(default="", max_length=1000)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def normalize(self):
        self.projectKey = self.projectKey.strip(); self.workflowKey = self.workflowKey.strip(); self.title = self.title.strip()
        keys = [x.inputKey for x in self.inputs]
        if len(keys) != len(set(keys)): raise ValueError("inputKey values must be unique")
        ckeys = [x.criterionKey for x in self.comparisonCriteria]
        if len(ckeys) != len(set(ckeys)): raise ValueError("criterionKey values must be unique")
        self.plannedChanges = list(dict.fromkeys(x.strip() for x in self.plannedChanges if x.strip()))
        self.invariants = list(dict.fromkeys(x.strip() for x in self.invariants if x.strip()))
        if self.mode == "reproduction" and self.plannedChanges:
            raise ValueError("reproduction mode cannot declare plannedChanges; use replication mode")
        return self


class SaveWorkflowRequest(WorkflowRequest):
    createdBy: str = Field(default="workbench", max_length=160)
    recordLabel: str = Field(default="Reproduction/replication workflow", max_length=500)


class ExecutionPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    workflowHash: str = Field(min_length=64, max_length=64)
    executionRuntime: str = Field(default="python", max_length=160)
    executionEntryPoint: str = Field(default="", max_length=1000)
    parameterOverrides: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = Field(default="workbench", max_length=160)


class ObservedMetric(BaseModel):
    criterionKey: str = Field(min_length=1, max_length=160)
    observedValue: float


class ComparisonRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    workflowHash: str = Field(min_length=64, max_length=64)
    observedMetrics: List[ObservedMetric] = Field(default_factory=list, max_length=200)
    resultRefs: List[str] = Field(default_factory=list, max_length=200)
    discrepancyNotes: List[str] = Field(default_factory=list, max_length=200)
    researcherAssessment: str = Field(default="", max_length=12000)


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    workflowHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "release": "Reproduction & Replication Workflow",
        "product": PRODUCT_KEY, "runtime": RUNTIME_KIND,
        "capabilities": {
            "reproductionTargetBinding": True,
            "replicationVariantPlanning": True,
            "environmentCapture": True,
            "inputArtifactCapture": True,
            "comparisonCriteria": True,
            "executionPlanGeneration": True,
            "resultComparison": True,
            "discrepancyReporting": True,
            "contentAddressedWorkflowRecords": True,
            "platformCoreReproductionPlanning": True,
        },
        "boundaries": {
            "automaticExecution": False,
            "automaticReplicationVerdict": False,
            "automaticScientificValidityInference": False,
            "automaticHypothesisAcceptance": False,
            "automaticCausalInference": False,
            "automaticDiscrepancyResolution": False,
            "automaticCoreDispatch": False,
            "governedReplicationClaimCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def compose_workflow(req: WorkflowRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    target = load_synthesis(req.projectKey, req.targetSynthesisHash)
    seed = {
        "projectKey": req.projectKey, "workflowKey": req.workflowKey, "title": req.title, "mode": req.mode,
        "target": {"synthesisHash": req.targetSynthesisHash, "synthesisRef": target.get("synthesisRef"), "recordHash": target.get("recordHash"), "sourceManifestHash": target.get("sourceManifestHash")},
        "researchQuestion": req.researchQuestion,
        "protocolNotes": req.protocolNotes,
        "environment": req.environment.model_dump(),
        "inputs": [x.model_dump() for x in req.inputs],
        "comparisonCriteria": [x.model_dump() for x in req.comparisonCriteria],
        "plannedChanges": req.plannedChanges,
        "invariants": req.invariants,
        "preregistrationRef": req.preregistrationRef,
        "notes": req.notes,
    }
    completeness = {
        "targetBound": True,
        "environmentCaptured": any(req.environment.model_dump().values()),
        "inputCount": len(req.inputs),
        "comparisonCriterionCount": len(req.comparisonCriteria),
        "replicationChangesDeclared": req.mode == "reproduction" or bool(req.plannedChanges),
        "readyForExecutionPlanning": bool(req.comparisonCriteria),
        "readyDoesNotMeanScientificallyValid": True,
    }
    workflow_hash = content_hash({**seed, "completeness": completeness})
    return {
        "ok": True, "schema": WORKFLOW_SCHEMA, "version": VERSION, **seed,
        "completeness": completeness,
        "workflowHash": workflow_hash,
        "workflowRef": f"sc://workbench/reproduction-replication/{req.projectKey}/{workflow_hash}",
        "researcherControlled": True,
        "boundaries": manifest()["boundaries"],
    }


def _record_hash(rec: Dict[str, Any]) -> str:
    return content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})


def save_workflow(req: SaveWorkflowRequest) -> Dict[str, Any]:
    base_fields = set(WorkflowRequest.model_fields)
    out = compose_workflow(WorkflowRequest(**req.model_dump(include=base_fields)))
    rec = {**out, "createdBy": req.createdBy, "recordLabel": req.recordLabel, "createdAt": _now()}
    rec["recordHash"] = _record_hash(rec)
    path = _workflow_path(req.projectKey, rec["workflowHash"]); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = _json_read(path)
        if old.get("recordHash") != rec["recordHash"]: raise ValueError("existing workflow hash collision or record mismatch")
        old["idempotent"] = True; return old
    _atomic_json_write(path, rec); rec["idempotent"] = False; return rec


def load_workflow(project_key: str, workflow_hash: str) -> Dict[str, Any]:
    load_project(project_key); path = _workflow_path(project_key, workflow_hash)
    if not path.exists(): raise FileNotFoundError("reproduction/replication workflow not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("workflowHash") != workflow_hash: raise ValueError("workflow identity mismatch")
    if rec.get("recordHash") != _record_hash(rec): raise ValueError("workflow failed integrity validation")
    return rec


def list_workflows(project_key: str) -> Dict[str, Any]:
    load_project(project_key); rows=[]; root=_workflow_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_json_read(p)
                if r.get("projectKey")==project_key:
                    rows.append({k:r.get(k) for k in ("workflowHash","workflowRef","workflowKey","title","mode","createdBy","createdAt","recordHash")})
            except Exception: pass
    rows.sort(key=lambda x:str(x.get("createdAt") or ""), reverse=True)
    return {"ok":True,"schema":WORKFLOW_SCHEMA,"version":VERSION,"projectKey":project_key,"workflowCount":len(rows),"workflows":rows}


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key); syn=list_syntheses(project_key); wf=list_workflows(project_key)
    out={"ok":True,"schema":CATALOG_SCHEMA,"version":VERSION,"projectKey":project_key,
         "synthesisCount":syn.get("synthesisCount",0),"syntheses":syn.get("syntheses",[]),
         "workflowCount":wf.get("workflowCount",0),"workflows":wf.get("workflows",[]),
         "boundaries":{"catalogInfersReplicability":False,"catalogInfersScientificValidity":False,"catalogExecutes":False}}
    out["catalogHash"]=content_hash(out); return out


def execution_plan(req: ExecutionPlanRequest) -> Dict[str, Any]:
    rec=load_workflow(req.projectKey,req.workflowHash)
    out={"ok":True,"schema":EXECUTION_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,
         "workflowHash":req.workflowHash,"workflowRef":rec.get("workflowRef"),"mode":rec.get("mode"),
         "executionRuntime":req.executionRuntime,"executionEntryPoint":req.executionEntryPoint,
         "parameterOverrides":req.parameterOverrides,"environment":rec.get("environment",{}),"inputs":rec.get("inputs",[]),
         "createdBy":req.createdBy,
         "boundaries":{"automaticExecution":False,"jobQueued":False,"resultProduced":False,"scientificValidityInferred":False}}
    out["planHash"]=content_hash(out); return out


def compare_results(req: ComparisonRequest) -> Dict[str, Any]:
    rec=load_workflow(req.projectKey,req.workflowHash)
    criteria={x["criterionKey"]:x for x in rec.get("comparisonCriteria",[])}
    observed={x.criterionKey:x.observedValue for x in req.observedMetrics}
    rows=[]
    for key,c in criteria.items():
        if key not in observed:
            rows.append({"criterionKey":key,"metric":c.get("metric"),"observed":False,"withinTolerance":None,"difference":None,"relativeDifference":None})
            continue
        v=float(observed[key]); target=c.get("targetValue"); comp=c.get("comparator"); tol=float(c.get("tolerance") or 0.0)
        if target is None:
            rows.append({"criterionKey":key,"metric":c.get("metric"),"observed":True,"observedValue":v,"withinTolerance":None,"difference":None,"relativeDifference":None})
            continue
        t=float(target); diff=v-t; rel=None if t==0 else abs(diff)/abs(t)
        if comp=="exact": within=(v==t)
        elif comp=="relative": within=(rel is not None and rel<=tol)
        else: within=(abs(diff)<=tol)
        rows.append({"criterionKey":key,"metric":c.get("metric"),"observed":True,"observedValue":v,"targetValue":t,"comparator":comp,"tolerance":tol,"difference":diff,"relativeDifference":rel,"withinTolerance":within})
    evaluated=[x for x in rows if x.get("withinTolerance") is not None]
    within=sum(1 for x in evaluated if x["withinTolerance"] is True)
    out={"ok":True,"schema":COMPARISON_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"workflowHash":req.workflowHash,"mode":rec.get("mode"),
         "comparisons":rows,"summary":{"criterionCount":len(criteria),"evaluatedCount":len(evaluated),"withinToleranceCount":within,"outsideToleranceCount":len(evaluated)-within,"unevaluatedCount":len(criteria)-len(evaluated)},
         "resultRefs":list(dict.fromkeys(x.strip() for x in req.resultRefs if x.strip())),"discrepancyNotes":req.discrepancyNotes,"researcherAssessment":req.researcherAssessment,
         "boundaries":{"replicationVerdictInferred":False,"scientificValidityInferred":False,"hypothesisAcceptanceInferred":False,"causalInferencePerformed":False}}
    out["comparisonHash"]=content_hash(out); return out


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    rec=load_workflow(req.projectKey,req.workflowHash); cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"workflowHash":req.workflowHash,"workflowRef":rec.get("workflowRef"),
         "coreProjectEntityId":req.coreProjectEntityId or req.projectKey,"coreSessionId":req.coreSessionId,"visibility":req.visibility,"createdBy":req.createdBy,
         "coreEnabled":bool(cfg.get("enabled")),"coreTarget":cfg.get("baseUrl") or "",
         "bindingPlan":{"objectType":"workbench.reproduction-replication-workflow","objectRef":rec.get("workflowRef"),"objectHash":req.workflowHash,"mode":rec.get("mode"),"targetSynthesisHash":rec.get("target",{}).get("synthesisHash"),"role":"researcher-controlled-reproduction-replication-workflow"},
         "boundaries":{"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreGovernanceAuthorityPreserved":True,"governedReplicationClaimCreated":False,"scientificValidityInferred":False}}
    out["planHash"]=content_hash(out); return out


def _wrap(fn,*args):
    try: return fn(*args)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc


@router.get("/reproduction-replication/manifest")
def route_manifest(): return manifest()
@router.get("/reproduction-replication/source-catalog/{project_key}")
def route_catalog(project_key:str): return _wrap(source_catalog,project_key)
@router.post("/reproduction-replication/compose")
def route_compose(req:WorkflowRequest): return _wrap(compose_workflow,req)
@router.post("/reproduction-replication/workflows")
def route_save(req:SaveWorkflowRequest): return _wrap(save_workflow,req)
@router.get("/reproduction-replication/workflows/{project_key}")
def route_list(project_key:str): return _wrap(list_workflows,project_key)
@router.get("/reproduction-replication/workflows/{project_key}/{workflow_hash}")
def route_get(project_key:str,workflow_hash:str): return _wrap(load_workflow,project_key,workflow_hash)
@router.post("/reproduction-replication/execution-plan")
def route_execution_plan(req:ExecutionPlanRequest): return _wrap(execution_plan,req)
@router.post("/reproduction-replication/compare")
def route_compare(req:ComparisonRequest): return _wrap(compare_results,req)
@router.post("/integration/core/reproduction-replication/plan")
def route_core(req:CorePlanRequest): return _wrap(core_plan,req)
@router.get("/v970/status")
def status():
    m=manifest(); return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":m["release"],"reproductionReplicationWorkflow":True,"environmentCapture":True,"resultComparison":True,"automaticExecution":False,"automaticReplicationVerdict":False,"automaticScientificValidityInference":False,"automaticCoreDispatch":False,"manifestHash":m["manifestHash"]}
