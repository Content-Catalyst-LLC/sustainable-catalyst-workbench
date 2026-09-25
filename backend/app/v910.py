"""Workbench v9.1.0 — Experimental Design & Research Protocol Builder.

Formal, researcher-authored research protocols bound to v9 scientific studies.
The builder captures hypotheses, variables, experimental arms, sampling,
randomization/blinding, measurement, analysis, stopping criteria, and
preregistration metadata. It reports protocol completeness and creates
content-addressed protocol records plus explicit execution/Core handoff plans.
It never infers scientific validity, statistical significance, ethical approval,
or automatically dispatches execution/Core operations.
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
from .v900 import load_study, list_studies

VERSION = APP_VERSION
SCHEMA = "sc-workbench-experimental-design-research-protocol-builder/1.0"
PROTOCOL_SCHEMA = "sc-workbench-research-protocol/1.0"
CATALOG_SCHEMA = "sc-workbench-research-protocol-source-catalog/1.0"
EXECUTION_PLAN_SCHEMA = "sc-workbench-research-protocol-execution-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-research-protocol-core-plan/1.0"
router = APIRouter(tags=["workbench-v910-experimental-design-research-protocol-builder"])

ProtocolStatus = Literal["draft", "preregistered", "amended", "locked", "archived"]
VariableRole = Literal["outcome", "exposure", "treatment", "covariate", "control", "mediator", "moderator", "blocking", "randomization", "derived"]
ArmKind = Literal["control", "treatment", "comparator", "sham", "observational"]
SamplingMethod = Literal["unspecified", "census", "simple-random", "systematic", "stratified", "cluster", "multistage", "convenience", "purposive", "quota", "snowball", "simulation"]
StoppingRule = Literal["fixed", "precision", "sequential", "resource", "manual"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _protocol_dir(project_key: str) -> Path:
    return _store_root() / "research-protocols" / _stable_id(project_key)


def _protocol_path(project_key: str, protocol_hash: str) -> Path:
    return _protocol_dir(project_key) / f"{protocol_hash}.json"


class HypothesisSpec(BaseModel):
    hypothesisId: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=8000)
    kind: Literal["primary", "secondary", "exploratory", "null", "alternative"] = "primary"
    directional: bool = False
    expectedDirection: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def normalize(self):
        self.hypothesisId = self.hypothesisId.strip()
        self.statement = self.statement.strip()
        return self


class VariableSpec(BaseModel):
    variableId: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=500)
    role: VariableRole
    dataType: Literal["continuous", "integer", "binary", "categorical", "ordinal", "count", "time", "text", "other"] = "continuous"
    unit: str = Field(default="", max_length=120)
    operationalDefinition: str = Field(default="", max_length=4000)
    measurementRef: str = Field(default="", max_length=1200)

    @model_validator(mode="after")
    def normalize(self):
        self.variableId = self.variableId.strip(); self.label = self.label.strip(); self.unit = self.unit.strip()
        return self


class ExperimentalArm(BaseModel):
    armId: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=500)
    kind: ArmKind
    intervention: str = Field(default="", max_length=4000)
    allocationWeight: float = Field(default=1.0, ge=0.0)

    @model_validator(mode="after")
    def normalize(self):
        self.armId = self.armId.strip(); self.label = self.label.strip(); self.intervention = self.intervention.strip()
        return self


class SamplingPlan(BaseModel):
    population: str = Field(default="", max_length=4000)
    samplingFrame: str = Field(default="", max_length=4000)
    method: SamplingMethod = "unspecified"
    targetSampleSize: int | None = Field(default=None, ge=1, le=10_000_000)
    strata: List[str] = Field(default_factory=list, max_length=100)
    clusters: List[str] = Field(default_factory=list, max_length=100)
    inclusionCriteria: List[str] = Field(default_factory=list, max_length=100)
    exclusionCriteria: List[str] = Field(default_factory=list, max_length=100)
    sampleSizeRationale: str = Field(default="", max_length=8000)


class RandomizationPlan(BaseModel):
    enabled: bool = False
    unit: str = Field(default="", max_length=500)
    method: str = Field(default="", max_length=1000)
    seedPolicy: str = Field(default="", max_length=1000)
    stratificationVariableIds: List[str] = Field(default_factory=list, max_length=100)
    blinding: Literal["none", "single", "double", "triple", "not-applicable"] = "not-applicable"
    allocationConcealment: str = Field(default="", max_length=2000)


class MeasurementPlan(BaseModel):
    schedule: List[str] = Field(default_factory=list, max_length=200)
    instrumentRefs: List[str] = Field(default_factory=list, max_length=200)
    primaryOutcomeIds: List[str] = Field(default_factory=list, max_length=50)
    secondaryOutcomeIds: List[str] = Field(default_factory=list, max_length=100)
    missingDataPlan: str = Field(default="", max_length=8000)
    qualityControls: List[str] = Field(default_factory=list, max_length=100)


class AnalysisPlan(BaseModel):
    primaryEstimand: str = Field(default="", max_length=4000)
    statisticalMethods: List[str] = Field(default_factory=list, max_length=100)
    modelRefs: List[str] = Field(default_factory=list, max_length=100)
    covariateIds: List[str] = Field(default_factory=list, max_length=100)
    multiplicityPlan: str = Field(default="", max_length=4000)
    missingDataMethod: str = Field(default="", max_length=4000)
    robustnessChecks: List[str] = Field(default_factory=list, max_length=100)
    decisionCriteria: List[str] = Field(default_factory=list, max_length=100)


class StoppingPlan(BaseModel):
    ruleType: StoppingRule = "fixed"
    target: str = Field(default="", max_length=4000)
    interimLooks: List[str] = Field(default_factory=list, max_length=100)
    safetyRules: List[str] = Field(default_factory=list, max_length=100)
    resourceLimits: List[str] = Field(default_factory=list, max_length=100)


class ProtocolRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    studyHash: str = Field(min_length=64, max_length=64)
    protocolKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    protocolVersion: str = Field(default="1.0", min_length=1, max_length=80)
    status: ProtocolStatus = "draft"
    hypotheses: List[HypothesisSpec] = Field(default_factory=list, max_length=100)
    variables: List[VariableSpec] = Field(default_factory=list, max_length=300)
    arms: List[ExperimentalArm] = Field(default_factory=list, max_length=50)
    sampling: SamplingPlan = Field(default_factory=SamplingPlan)
    randomization: RandomizationPlan = Field(default_factory=RandomizationPlan)
    measurement: MeasurementPlan = Field(default_factory=MeasurementPlan)
    analysis: AnalysisPlan = Field(default_factory=AnalysisPlan)
    stopping: StoppingPlan = Field(default_factory=StoppingPlan)
    preregistrationRef: str = Field(default="", max_length=1200)
    ethicsApprovalRef: str = Field(default="", max_length=1200)
    amendmentReason: str = Field(default="", max_length=8000)
    notes: str = Field(default="", max_length=12000)
    tags: List[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_links(self):
        self.projectKey = self.projectKey.strip(); self.protocolKey = self.protocolKey.strip(); self.title = self.title.strip()
        hids=[x.hypothesisId for x in self.hypotheses]; vids=[x.variableId for x in self.variables]; aids=[x.armId for x in self.arms]
        if len(hids)!=len(set(hids)): raise ValueError("hypothesisId values must be unique")
        if len(vids)!=len(set(vids)): raise ValueError("variableId values must be unique")
        if len(aids)!=len(set(aids)): raise ValueError("armId values must be unique")
        known=set(vids)
        refs=set(self.randomization.stratificationVariableIds+self.measurement.primaryOutcomeIds+self.measurement.secondaryOutcomeIds+self.analysis.covariateIds)
        unknown=sorted(refs-known)
        if unknown: raise ValueError(f"unknown variable references: {', '.join(unknown)}")
        outcomes={x.variableId for x in self.variables if x.role in {"outcome","derived"}}
        bad=sorted((set(self.measurement.primaryOutcomeIds)|set(self.measurement.secondaryOutcomeIds))-outcomes)
        if bad: raise ValueError(f"outcome references must use outcome/derived variables: {', '.join(bad)}")
        if self.arms and sum(x.allocationWeight for x in self.arms)<=0: raise ValueError("experimental arm allocation weights must sum to more than zero")
        if self.status=="preregistered" and not self.preregistrationRef.strip(): raise ValueError("preregistered protocols require preregistrationRef")
        if self.status=="amended" and not self.amendmentReason.strip(): raise ValueError("amended protocols require amendmentReason")
        return self


class SaveProtocolRequest(ProtocolRequest):
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)
    recordLabel: str = Field(default="Research protocol", max_length=500)


class ExecutionPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    protocolHash: str = Field(min_length=64, max_length=64)
    runtimeKind: str = Field(default="python", max_length=120)
    requestedBy: str = Field(default="workbench", max_length=160)


class CoreProtocolPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    protocolHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private","internal","public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out={
        "ok":True,"schema":SCHEMA,"version":VERSION,"release":"Experimental Design & Research Protocol Builder","product":PRODUCT_KEY,"runtime":RUNTIME_KIND,
        "protocolSections":["hypotheses","variables","arms","sampling","randomization","measurement","analysis","stopping","preregistration"],
        "capabilities":{
            "formalResearchProtocolObject":True,"hypothesisRegistry":True,"variableRoleRegistry":True,"experimentalArmDesign":True,
            "samplingPlan":True,"randomizationAndBlindingPlan":True,"measurementPlan":True,"analysisPlan":True,"stoppingCriteria":True,
            "preregistrationMetadata":True,"contentAddressedProtocolRecords":True,"protocolExecutionPlanning":True,"platformCoreProtocolPlanning":True,
        },
        "boundaries":{
            "protocolCompletenessIsScientificValidity":False,"automaticSampleSizeCalculation":False,"automaticHypothesisAcceptance":False,
            "automaticStatisticalMethodSelection":False,"automaticCausalInference":False,"automaticSignificanceInference":False,
            "ethicsApprovalInferred":False,"automaticExecutionDispatch":False,"automaticCoreDispatch":False,"platformCoreGovernanceReplaced":False,
        },
    }
    out["manifestHash"]=content_hash(out); return out


def _section(name:str, ready:bool, evidence:Dict[str,Any], note:str="") -> Dict[str,Any]:
    return {"section":name,"ready":bool(ready),"evidence":evidence,"note":note}


def compose_protocol(req: ProtocolRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    study=load_study(req.projectKey, req.studyHash)
    outcome_ids=[x.variableId for x in req.variables if x.role in {"outcome","derived"}]
    treatment_ids=[x.variableId for x in req.variables if x.role in {"treatment","exposure"}]
    sections=[
        _section("hypotheses",bool(req.hypotheses),{"count":len(req.hypotheses),"primaryCount":sum(1 for x in req.hypotheses if x.kind=="primary")}),
        _section("variables",bool(req.variables),{"count":len(req.variables),"outcomeCount":len(outcome_ids),"treatmentOrExposureCount":len(treatment_ids)}),
        _section("arms",bool(req.arms) or req.sampling.method in {"observational","simulation"},{"count":len(req.arms),"allocationWeightTotal":sum(x.allocationWeight for x in req.arms)}),
        _section("sampling",bool(req.sampling.population.strip() or req.sampling.targetSampleSize or req.sampling.method!="unspecified"),{"method":req.sampling.method,"targetSampleSize":req.sampling.targetSampleSize}),
        _section("randomization",(not req.randomization.enabled) or bool(req.randomization.method.strip()),{"enabled":req.randomization.enabled,"method":req.randomization.method,"blinding":req.randomization.blinding}),
        _section("measurement",bool(req.measurement.primaryOutcomeIds or req.measurement.schedule or req.measurement.instrumentRefs),{"primaryOutcomeCount":len(req.measurement.primaryOutcomeIds),"secondaryOutcomeCount":len(req.measurement.secondaryOutcomeIds),"scheduleCount":len(req.measurement.schedule)}),
        _section("analysis",bool(req.analysis.primaryEstimand.strip() or req.analysis.statisticalMethods or req.analysis.modelRefs),{"primaryEstimandPresent":bool(req.analysis.primaryEstimand.strip()),"methodCount":len(req.analysis.statisticalMethods),"robustnessCheckCount":len(req.analysis.robustnessChecks)}),
        _section("stopping",bool(req.stopping.target.strip() or req.stopping.ruleType=="manual"),{"ruleType":req.stopping.ruleType,"interimLookCount":len(req.stopping.interimLooks)}),
        _section("preregistration",bool(req.preregistrationRef.strip()) if req.status=="preregistered" else True,{"status":req.status,"preregistrationRefPresent":bool(req.preregistrationRef.strip())}),
    ]
    ready=sum(1 for x in sections if x["ready"])
    body={
        "ok":True,"schema":PROTOCOL_SCHEMA,"version":VERSION,"release":"Experimental Design & Research Protocol Builder",
        "projectKey":req.projectKey,"studyHash":req.studyHash,"studyRef":study.get("studyRef"),"studyKey":study.get("studyKey"),
        "protocolKey":req.protocolKey,"title":req.title,"protocolVersion":req.protocolVersion,"status":req.status,
        "hypotheses":[x.model_dump() for x in req.hypotheses],"variables":[x.model_dump() for x in req.variables],"arms":[x.model_dump() for x in req.arms],
        "sampling":req.sampling.model_dump(),"randomization":req.randomization.model_dump(),"measurement":req.measurement.model_dump(),
        "analysis":req.analysis.model_dump(),"stopping":req.stopping.model_dump(),"preregistrationRef":req.preregistrationRef,
        "ethicsApprovalRef":req.ethicsApprovalRef,"amendmentReason":req.amendmentReason,"notes":req.notes,"tags":req.tags,
        "sectionReadiness":sections,"readinessSummary":{"ready":ready,"total":len(sections),"allSectionsReady":ready==len(sections)},
        "sourceHashes":{"studyHash":study.get("studyHash"),"studyRecordHash":study.get("recordHash")},"boundaries":manifest()["boundaries"],
    }
    body["protocolHash"]=content_hash({k:v for k,v in body.items() if k!="protocolHash"})
    body["protocolRef"]=f"sc://workbench/protocol/{req.projectKey}/{body['protocolHash']}"
    return body


def save_protocol(req: SaveProtocolRequest) -> Dict[str, Any]:
    base=set(ProtocolRequest.model_fields); protocol=compose_protocol(ProtocolRequest(**req.model_dump(include=base)))
    record={**protocol,"recordLabel":req.recordLabel,"createdBy":req.createdBy,"createdAt":_now()}
    record["recordHash"]=content_hash({k:v for k,v in record.items() if k not in {"createdAt","recordHash","idempotent"}})
    path=_protocol_path(req.projectKey,protocol["protocolHash"])
    if path.exists():
        existing=_json_read(path); expected=content_hash({k:v for k,v in existing.items() if k not in {"createdAt","recordHash","idempotent"}})
        if existing.get("recordHash")!=expected: raise ValueError("stored research protocol failed integrity validation")
        existing["idempotent"]=True; return existing
    _atomic_json_write(path,record); record["idempotent"]=False; return record


def list_protocols(project_key:str) -> Dict[str,Any]:
    load_project(project_key); rows=[]; root=_protocol_dir(project_key)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                rec=_json_read(path)
                if rec.get("projectKey")!=project_key: continue
                rows.append({k:rec.get(k) for k in ("protocolHash","protocolRef","protocolKey","title","protocolVersion","status","studyHash","recordLabel","createdBy","createdAt","recordHash")})
            except Exception: continue
    rows.sort(key=lambda x:str(x.get("createdAt") or ""),reverse=True)
    return {"ok":True,"schema":PROTOCOL_SCHEMA,"version":VERSION,"projectKey":project_key,"protocolCount":len(rows),"protocols":rows}


def load_protocol(project_key:str, protocol_hash:str) -> Dict[str,Any]:
    load_project(project_key); path=_protocol_path(project_key,protocol_hash)
    if not path.exists(): raise FileNotFoundError("research protocol not found")
    rec=_json_read(path)
    if rec.get("projectKey")!=project_key or rec.get("protocolHash")!=protocol_hash: raise ValueError("research protocol identity mismatch")
    expected=content_hash({k:v for k,v in rec.items() if k not in {"createdAt","recordHash","idempotent"}})
    if rec.get("recordHash")!=expected: raise ValueError("research protocol failed integrity validation")
    return rec


def source_catalog(project_key:str) -> Dict[str,Any]:
    load_project(project_key); studies=list_studies(project_key); protocols=list_protocols(project_key)
    out={"ok":True,"schema":CATALOG_SCHEMA,"version":VERSION,"projectKey":project_key,"studyCount":studies.get("studyCount",0),"studies":studies.get("studies",[]),"protocolCount":protocols.get("protocolCount",0),"protocols":protocols.get("protocols",[]),"boundaries":{"catalogMutatesSources":False,"catalogInfersScientificValidity":False,"catalogDispatchesExecution":False,"catalogDispatchesToCore":False}}
    out["catalogHash"]=content_hash(out); return out


def execution_plan(req:ExecutionPlanRequest) -> Dict[str,Any]:
    protocol=load_protocol(req.projectKey,req.protocolHash)
    out={"ok":True,"schema":EXECUTION_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"protocolHash":req.protocolHash,"protocolRef":protocol.get("protocolRef"),"studyHash":protocol.get("studyHash"),"runtimeKind":req.runtimeKind,"requestedBy":req.requestedBy,"executionContract":{"hypotheses":protocol.get("hypotheses",[]),"variables":protocol.get("variables",[]),"arms":protocol.get("arms",[]),"sampling":protocol.get("sampling",{}),"randomization":protocol.get("randomization",{}),"measurement":protocol.get("measurement",{}),"analysis":protocol.get("analysis",{}),"stopping":protocol.get("stopping",{})},"boundaries":{"automaticExecutionDispatchAuthorized":False,"automaticRuntimeSelectionAuthorized":False,"scientificValidityInferred":False,"analysisOutcomePredetermined":False}}
    out["planHash"]=content_hash(out); return out


def core_plan(req:CoreProtocolPlanRequest) -> Dict[str,Any]:
    protocol=load_protocol(req.projectKey,req.protocolHash); cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"protocolHash":req.protocolHash,"protocolRef":protocol.get("protocolRef"),"studyHash":protocol.get("studyHash"),"coreProjectEntityId":req.coreProjectEntityId or req.projectKey,"coreSessionId":req.coreSessionId,"visibility":req.visibility,"createdBy":req.createdBy,"coreEnabled":bool(cfg.get("enabled")),"coreTarget":cfg.get("baseUrl") or "","bindingPlan":{"objectType":"workbench.research-protocol","objectRef":protocol.get("protocolRef"),"objectHash":req.protocolHash,"studyHash":protocol.get("studyHash"),"protocolVersion":protocol.get("protocolVersion"),"status":protocol.get("status"),"sourceHashes":protocol.get("sourceHashes",{})},"boundaries":{"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreGovernanceAuthorityPreserved":True,"scientificValidityInferred":False,"ethicsApprovalInferred":False}}
    out["planHash"]=content_hash(out); return out


def _wrap(fn,*args):
    try: return fn(*args)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.get("/protocol-builder/manifest")
def route_manifest(): return manifest()
@router.get("/protocol-builder/source-catalog/{project_key}")
def route_catalog(project_key:str): return _wrap(source_catalog,project_key)
@router.post("/protocol-builder/compose")
def route_compose(req:ProtocolRequest): return _wrap(compose_protocol,req)
@router.post("/protocol-builder/protocols")
def route_save(req:SaveProtocolRequest): return _wrap(save_protocol,req)
@router.get("/protocol-builder/protocols/{project_key}")
def route_list(project_key:str): return _wrap(list_protocols,project_key)
@router.get("/protocol-builder/protocols/{project_key}/{protocol_hash}")
def route_get(project_key:str,protocol_hash:str): return _wrap(load_protocol,project_key,protocol_hash)
@router.post("/protocol-builder/execution-plan")
def route_execution_plan(req:ExecutionPlanRequest): return _wrap(execution_plan,req)
@router.post("/integration/core/protocol-builder/plan")
def route_core_plan(req:CoreProtocolPlanRequest): return _wrap(core_plan,req)
@router.get("/v910/status")
def status():
    m=manifest(); return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":m["release"],"experimentalDesignResearchProtocolBuilder":True,"contentAddressedProtocolRecords":True,"protocolExecutionPlanning":True,"preregistrationMetadata":True,"automaticScientificValidityInference":False,"automaticExecutionDispatch":False,"automaticCoreDispatch":False,"manifestHash":m["manifestHash"]}
