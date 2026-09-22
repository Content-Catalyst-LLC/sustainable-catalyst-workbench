"""Workbench v7.6.0 — Engineering Systems Runtime.

Canonical bounded engineering analyses across mechanical, thermal, fluids,
civil/infrastructure, electrical, controls/mechatronics, and energy systems.
The layer normalizes engineering problem specifications, units, diagnostics,
execution-object provenance, v7.3 workspace bindings and Platform Core
computation-lineage plans. It does not perform licensed design certification,
code compliance determinations, physical actuation, or automatic Core writes.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite, log10, pi
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v230 import ActuatorRequest, actuator
from .v510 import content_hash
from .v580 import ResistorNetworkInput, resistor_network_object
from .energy_workbench_runtime import execute as execute_energy_handoff
from .v640 import _authorize_core_route
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT, CORE_PATHS, OutputItem, _output_data, _request
from .v700 import RESULT_SCHEMA, RUNTIME_REF as UNIFIED_RUNTIME_REF
from .v710 import _execution_object_from_result
from .v730 import _workspace_ok, _set_path

VERSION = APP_VERSION
SCHEMA = "sc-workbench-engineering-systems-runtime/1.0"
RESULT = "sc-workbench-engineering-analysis-result/1.0"
SYSTEM_RESULT = "sc-workbench-engineering-system-result/1.0"
BINDING_SCHEMA = "sc-workbench-engineering-workspace-binding-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-engineering-core-lineage-plan/1.0"
ENGINEERING_REF = "workbench:/runtime/engineering-systems"
CORE_LINEAGE_CONTRACT_LITERAL = "sc.research.computation-analysis-execution-lineage.v1"
MAX_BINDINGS = 200
MAX_SYSTEM_ANALYSES = 24

router = APIRouter(tags=["workbench-v760-engineering-systems-runtime"])

AnalysisKey = Literal[
    "mechanical.axial-member",
    "mechanical.simply-supported-beam",
    "thermal.conduction",
    "thermal.convection",
    "fluids.pipe-flow",
    "civil.axial-capacity",
    "electrical.dc-circuit",
    "controls.actuator-sizing",
    "energy.explicit-handoff",
]

CATALOG: Dict[str, Dict[str, Any]] = {
    "mechanical.axial-member": {"domain":"mechanical","method":"linear-axial-stress-strain","units":"SI","bounded":True},
    "mechanical.simply-supported-beam": {"domain":"mechanical","method":"small-deflection-euler-bernoulli","units":"SI","bounded":True},
    "thermal.conduction": {"domain":"thermal","method":"steady-one-dimensional-fourier","units":"SI","bounded":True},
    "thermal.convection": {"domain":"thermal","method":"steady-newton-cooling","units":"SI","bounded":True},
    "fluids.pipe-flow": {"domain":"fluids","method":"darcy-weisbach-haaland","units":"SI","bounded":True},
    "civil.axial-capacity": {"domain":"civil-infrastructure","method":"declared-allowable-axial-capacity","units":"SI","bounded":True},
    "electrical.dc-circuit": {"domain":"electrical","method":"dc-ohm-power-balance","units":"SI","bounded":True},
    "controls.actuator-sizing": {"domain":"controls-mechatronics","method":"existing-v2.3-actuator-sizing","units":"SI","bounded":True},
    "energy.explicit-handoff": {"domain":"energy-systems","method":"existing-explicit-energy-handoff","units":"declared-by-handoff","bounded":True},
}


class EngineeringAnalysisRequest(BaseModel):
    analysisKey: AnalysisKey
    inputs: Dict[str, Any]
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    workspaceRef: str = Field(default="", max_length=1000)
    workspaceHash: str = Field(default="", max_length=128)
    inputRefs: List[str] = Field(default_factory=list, max_length=200)
    datasetRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemItem(BaseModel):
    itemKey: str = Field(min_length=1, max_length=120)
    analysisKey: AnalysisKey
    inputs: Dict[str, Any]
    label: str = Field(default="", max_length=400)


class EngineeringSystemRequest(BaseModel):
    systemKey: str = Field(min_length=1, max_length=120)
    analyses: List[SystemItem] = Field(min_length=1, max_length=MAX_SYSTEM_ANALYSES)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    workspaceRef: str = Field(default="", max_length=1000)
    workspaceHash: str = Field(default="", max_length=128)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_keys(self):
        keys=[x.itemKey for x in self.analyses]
        if len(keys)!=len(set(keys)): raise ValueError("itemKey values must be unique")
        return self


class BindingSpec(BaseModel):
    sourceKind: Literal["variable", "parameter", "dataset"]
    sourceKey: str
    parameterSetKey: str = Field(default="", max_length=120)
    targetField: str = Field(default="", max_length=300)


class WorkspaceEngineeringBindingRequest(BaseModel):
    workspace: Dict[str, Any]
    analysisKey: AnalysisKey
    inputs: Dict[str, Any] = Field(default_factory=dict)
    bindings: List[BindingSpec] = Field(default_factory=list, max_length=MAX_BINDINGS)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoreEngineeringLineagePlanRequest(BaseModel):
    engineeringResult: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _num(d: Dict[str, Any], key: str, *, positive: bool=False, nonnegative: bool=False, default: Any=None) -> float:
    if key not in d:
        if default is not None: return float(default)
        raise ValueError(f"missing required input: {key}")
    v=float(d[key])
    if not isfinite(v): raise ValueError(f"{key} must be finite")
    if positive and v<=0: raise ValueError(f"{key} must be > 0")
    if nonnegative and v<0: raise ValueError(f"{key} must be >= 0")
    return v


def _axial(inputs: Dict[str, Any]) -> Dict[str, Any]:
    f=_num(inputs,"force_n"); a=_num(inputs,"area_m2",positive=True); stress=f/a
    out={"forceN":f,"areaM2":a,"stressPa":stress,"stressMPa":stress/1e6}
    if "length_m" in inputs and "elongation_m" in inputs:
        L=_num(inputs,"length_m",positive=True); dl=_num(inputs,"elongation_m"); strain=dl/L
        out.update({"lengthM":L,"elongationM":dl,"strain":strain})
        if abs(strain)>0: out["inferredElasticModulusPa"]=stress/strain
    if "elastic_modulus_pa" in inputs:
        E=_num(inputs,"elastic_modulus_pa",positive=True); out["elasticModulusPa"]=E; out["elasticStrainEstimate"]=stress/E
    if "yield_strength_pa" in inputs:
        y=_num(inputs,"yield_strength_pa",positive=True); out["yieldStrengthPa"]=y; out["factorOfSafetyToYield"]=y/abs(stress) if stress else None
    return out


def _beam(inputs: Dict[str, Any]) -> Dict[str, Any]:
    L=_num(inputs,"span_m",positive=True); E=_num(inputs,"elastic_modulus_pa",positive=True); I=_num(inputs,"second_moment_m4",positive=True)
    P=_num(inputs,"center_point_load_n",default=0.0); w=_num(inputs,"uniform_load_n_per_m",default=0.0)
    if P==0 and w==0: raise ValueError("at least one beam load must be non-zero")
    reaction=(P+w*L)/2
    moment=P*L/4+w*L*L/8
    deflection=P*L**3/(48*E*I)+5*w*L**4/(384*E*I)
    return {"spanM":L,"reactionEachN":reaction,"maximumMomentNm":moment,"maximumDeflectionM":deflection,"maximumDeflectionMm":deflection*1000,"assumption":"simply-supported-small-deflection-linear-elastic"}


def _conduction(inputs: Dict[str, Any]) -> Dict[str, Any]:
    k=_num(inputs,"conductivity_w_mk",positive=True); A=_num(inputs,"area_m2",positive=True); L=_num(inputs,"thickness_m",positive=True); th=_num(inputs,"hot_temp_c"); tc=_num(inputs,"cold_temp_c")
    r=L/(k*A); q=(th-tc)/r
    return {"thermalResistanceKPerW":r,"heatRateW":q,"heatFluxWPerM2":q/A,"temperatureDifferenceK":th-tc}


def _convection(inputs: Dict[str, Any]) -> Dict[str, Any]:
    h=_num(inputs,"coefficient_w_m2k",positive=True); A=_num(inputs,"area_m2",positive=True); ts=_num(inputs,"surface_temp_c"); tf=_num(inputs,"fluid_temp_c")
    r=1/(h*A); q=(ts-tf)/r
    return {"thermalResistanceKPerW":r,"heatRateW":q,"heatFluxWPerM2":q/A,"temperatureDifferenceK":ts-tf}


def _pipe(inputs: Dict[str, Any]) -> Dict[str, Any]:
    D=_num(inputs,"diameter_m",positive=True); L=_num(inputs,"length_m",positive=True); rho=_num(inputs,"density_kg_m3",positive=True); mu=_num(inputs,"dynamic_viscosity_pa_s",positive=True); q=_num(inputs,"volumetric_flow_m3_s",nonnegative=True); rough=_num(inputs,"roughness_m",nonnegative=True,default=0.0)
    area=pi*D*D/4; v=q/area; re=rho*v*D/mu if mu else 0
    if re<=0: f=0.0; regime="no-flow"
    elif re<2300: f=64/re; regime="laminar"
    else:
        term=(rough/(3.7*D)) + (6.9/re); f=1/(-1.8*log10(term))**2; regime="turbulent" if re>=4000 else "transition"
    dp=f*(L/D)*(rho*v*v/2) if v else 0.0
    return {"crossSectionAreaM2":area,"velocityMps":v,"reynoldsNumber":re,"flowRegime":regime,"darcyFrictionFactor":f,"pressureDropPa":dp,"headLossM":dp/(rho*9.80665) if rho else None,"correlation":"Haaland for Re>=2300; 64/Re for laminar"}


def _civil_capacity(inputs: Dict[str, Any]) -> Dict[str, Any]:
    load=abs(_num(inputs,"axial_load_n")); area=_num(inputs,"area_m2",positive=True); allowable=_num(inputs,"allowable_stress_pa",positive=True); material_capacity=area*allowable
    buckling=None
    if "buckling_capacity_n" in inputs: buckling=_num(inputs,"buckling_capacity_n",positive=True)
    capacity=min(material_capacity,buckling) if buckling is not None else material_capacity
    util=load/capacity
    return {"demandN":load,"materialCapacityN":material_capacity,"bucklingCapacityN":buckling,"governingCapacityN":capacity,"utilization":util,"capacityMarginN":capacity-load,"declaredCapacityStatus":"within-declared-capacity" if util<=1 else "exceeds-declared-capacity","codeComplianceDetermined":False}


def _dc(inputs: Dict[str, Any]) -> Dict[str, Any]:
    vals={k:(float(inputs[k]) if k in inputs and inputs[k] is not None else None) for k in ("voltage_v","current_a","resistance_ohm")}
    if sum(v is not None for v in vals.values())<2: raise ValueError("provide at least two of voltage_v, current_a, resistance_ohm")
    V,I,R=vals["voltage_v"],vals["current_a"],vals["resistance_ohm"]
    if R is not None and R<=0: raise ValueError("resistance_ohm must be > 0")
    if V is None: V=I*R
    elif I is None: I=V/R
    elif R is None:
        if I==0: raise ValueError("cannot infer resistance from zero current")
        R=V/I
    p=V*I
    out={"voltageV":V,"currentA":I,"resistanceOhm":R,"powerW":p}
    if "duration_s" in inputs:
        t=_num(inputs,"duration_s",nonnegative=True); out["durationS"]=t; out["energyJ"]=p*t; out["energyWh"]=p*t/3600
    return out


def _actuator(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return actuator(ActuatorRequest.model_validate(inputs))


def _resistor(inputs: Dict[str, Any]) -> Dict[str, Any]:
    return resistor_network_object(ResistorNetworkInput.model_validate(inputs))


def _energy(inputs: Dict[str, Any]) -> Dict[str, Any]:
    if not inputs: raise ValueError("energy explicit handoff requires a complete explicit payload")
    return execute_energy_handoff(inputs)


EXECUTORS = {
    "mechanical.axial-member": _axial,
    "mechanical.simply-supported-beam": _beam,
    "thermal.conduction": _conduction,
    "thermal.convection": _convection,
    "fluids.pipe-flow": _pipe,
    "civil.axial-capacity": _civil_capacity,
    "electrical.dc-circuit": _dc,
    "controls.actuator-sizing": _actuator,
    "energy.explicit-handoff": _energy,
}


def _source_envelope(request: EngineeringAnalysisRequest, raw: Dict[str, Any]) -> Dict[str, Any]:
    stable={"analysisKey":request.analysisKey,"inputs":request.inputs,"projectRef":request.projectRef,"coreSessionId":request.coreSessionId,"requestKey":request.requestKey,"workspaceRef":request.workspaceRef,"workspaceHash":request.workspaceHash,"inputRefs":sorted(set(request.inputRefs)),"datasetRefs":sorted(set(request.datasetRefs)),"metadata":request.metadata}
    request_hash=content_hash(stable); execution_id="wbe-eng-"+request_hash[:20]; execution_ref=f"sc://workbench/execution/{execution_id}"; result_hash=content_hash(raw); output_ref=f"{execution_ref}/result/{result_hash[:16]}"
    return {"ok":bool(raw.get("ok",True)) if isinstance(raw,dict) else True,"schema":RESULT_SCHEMA,"version":VERSION,"runtimeRef":ENGINEERING_REF,"executionId":execution_id,"executionRef":execution_ref,"requestKey":request.requestKey or execution_id,"label":request.label or request.analysisKey,"operation":request.analysisKey,"category":"engineering-systems","executionType":"engineering_calculation","runtimeKind":"workbench","sourceRelease":"7.6.0","deterministicOperation":True,"projectRef":request.projectRef,"coreSessionId":request.coreSessionId,"inputRefs":sorted(set(request.inputRefs)),"outputRef":output_ref,"outputType":"result_bundle","requestHash":request_hash,"resultHash":result_hash,"result":raw,"provenance":{"product":PRODUCT_KEY,"workbenchVersion":VERSION,"runtimeRef":ENGINEERING_REF,"specialistSourceRelease":"7.6.0","operation":request.analysisKey,"inputContentHash":content_hash(request.inputs),"resultContentHash":result_hash},"lineageHints":{"executionType":"engineering_calculation","runtimeKind":"workbench","workbenchExecutionRef":execution_ref,"inputRefs":sorted(set(request.inputRefs)),"outputRefs":[output_ref]},"boundaries":{"specialistComputationPerformedByWorkbench":True,"arbitraryCodeExecuted":False,"automaticCoreDispatchPerformed":False,"automaticCorePersistencePerformed":False,"scientificValidityCertified":False}}


def analyze(request: EngineeringAnalysisRequest) -> Dict[str, Any]:
    try: raw=EXECUTORS[request.analysisKey](deepcopy(request.inputs))
    except HTTPException: raise
    except Exception as exc: raise HTTPException(status_code=422,detail={"analysisKey":request.analysisKey,"error":str(exc)}) from exc
    domain=CATALOG[request.analysisKey]["domain"]
    diagnostics={"domain":domain,"method":CATALOG[request.analysisKey]["method"],"units":CATALOG[request.analysisKey]["units"],"bounded":True,"finiteScalarOutputs":all(isfinite(float(v)) for v in raw.values() if isinstance(v,(int,float)) and not isinstance(v,bool))}
    diagnostics["diagnosticsHash"]=content_hash(diagnostics)
    source=_source_envelope(request,raw)
    obj=_execution_object_from_result(source,declared_request={"payload":request.inputs,"inputRefs":request.inputRefs,"requestKey":request.requestKey,"metadata":request.metadata},object_key=request.requestKey,label=request.label,project_ref=request.projectRef,core_session_id=request.coreSessionId,dataset_refs=request.datasetRefs,method_refs=[f"{ENGINEERING_REF}/{request.analysisKey}"],tags=request.tags,metadata={"engineeringDomain":domain,"workspaceRef":request.workspaceRef,"workspaceHash":request.workspaceHash})
    record={"ok":source["ok"],"schema":RESULT,"version":VERSION,"engineeringRuntimeRef":ENGINEERING_REF,"analysisKey":request.analysisKey,"domain":domain,"inputs":request.inputs,"workspaceRef":request.workspaceRef,"workspaceHash":request.workspaceHash,"result":raw,"diagnostics":diagnostics,"executionObject":obj,"automaticDesignSelectionPerformed":False,"automaticCoreDispatchPerformed":False,"automaticCorePersistencePerformed":False,"licensedEngineeringCertificationPerformed":False,"codeComplianceDetermined":False,"physicalSafetyCertified":False}
    record["engineeringRunHash"]=content_hash({"analysisKey":record["analysisKey"],"inputs":record["inputs"],"result":record["result"],"diagnosticsHash":diagnostics["diagnosticsHash"],"executionObjectHash":obj["objectHash"]})
    return record


def validate_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reasons=[]
    if result.get("schema")!=RESULT: reasons.append("schema-mismatch")
    if result.get("version")!=VERSION: reasons.append("version-mismatch")
    if result.get("analysisKey") not in CATALOG: reasons.append("unknown-analysis-key")
    diag=result.get("diagnostics") or {}; expected_diag=content_hash({k:v for k,v in diag.items() if k!="diagnosticsHash"}) if diag else ""
    if diag.get("diagnosticsHash")!=expected_diag: reasons.append("diagnostics-hash-mismatch")
    expected=content_hash({"analysisKey":result.get("analysisKey"),"inputs":result.get("inputs"),"result":result.get("result"),"diagnosticsHash":diag.get("diagnosticsHash"),"executionObjectHash":(result.get("executionObject") or {}).get("objectHash")})
    if result.get("engineeringRunHash")!=expected: reasons.append("engineering-run-hash-mismatch")
    return {"ok":not reasons,"schema":"sc-workbench-engineering-analysis-validation/1.0","version":VERSION,"valid":not reasons,"reasons":reasons,"engineeringRunHash":result.get("engineeringRunHash","")}


def run_system(request: EngineeringSystemRequest) -> Dict[str, Any]:
    results=[]
    for item in request.analyses:
        r=analyze(EngineeringAnalysisRequest(analysisKey=item.analysisKey,inputs=item.inputs,projectRef=request.projectRef,coreSessionId=request.coreSessionId,requestKey=f"{request.systemKey}:{item.itemKey}",label=item.label or item.itemKey,workspaceRef=request.workspaceRef,workspaceHash=request.workspaceHash,metadata={"systemKey":request.systemKey,"systemItemKey":item.itemKey,**request.metadata}))
        results.append({"itemKey":item.itemKey,"analysisKey":item.analysisKey,"engineeringRunHash":r["engineeringRunHash"],"result":r})
    record={"ok":all(x["result"].get("ok",False) for x in results),"schema":SYSTEM_RESULT,"version":VERSION,"systemKey":request.systemKey,"analysisCount":len(results),"results":results,"automaticCrossDomainCouplingPerformed":False,"hiddenOutputSubstitutionPerformed":False,"licensedEngineeringCertificationPerformed":False}
    record["systemHash"]=content_hash(record)
    return record


def workspace_binding_plan(request: WorkspaceEngineeringBindingRequest) -> Dict[str, Any]:
    ws=request.workspace; _workspace_ok(ws)
    variables={x["variableKey"]:x for x in ws.get("variables",[]) if isinstance(x,dict)}; datasets={x["datasetKey"]:x for x in ws.get("datasets",[]) if isinstance(x,dict)}; psets={x["parameterSetKey"]:x for x in ws.get("parameterSets",[]) if isinstance(x,dict)}
    inputs=deepcopy(request.inputs); refs=[]; drefs=[]; materialized=[]
    for b in request.bindings:
        if b.sourceKind=="variable":
            src=variables.get(b.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown variable: {b.sourceKey}")
            value=src.get("derivedValue") if src.get("expression") else src.get("value")
            if value is None or not b.targetField: raise HTTPException(status_code=422,detail="variable bindings require scalar value and targetField")
            _set_path(inputs,b.targetField,value); ref=src["variableRef"]
        elif b.sourceKind=="parameter":
            ps=psets.get(b.parameterSetKey)
            if not ps: raise HTTPException(status_code=422,detail=f"unknown parameter set: {b.parameterSetKey}")
            src=next((x for x in ps.get("parameters",[]) if x.get("parameterKey")==b.sourceKey),None)
            if not src or not b.targetField: raise HTTPException(status_code=422,detail="parameter binding requires known parameter and targetField")
            _set_path(inputs,b.targetField,src.get("value")); ref=src["parameterRef"]
        else:
            src=datasets.get(b.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown dataset: {b.sourceKey}")
            ref=src["datasetRef"]; drefs.append(ref)
            if b.targetField: _set_path(inputs,b.targetField,ref)
        refs.append(ref); materialized.append({"sourceKind":b.sourceKind,"sourceKey":b.sourceKey,"sourceRef":ref,"targetField":b.targetField})
    analysis_request={"analysisKey":request.analysisKey,"inputs":inputs,"projectRef":ws.get("projectRef",""),"coreSessionId":ws.get("coreSessionId",""),"requestKey":request.requestKey or f"{ws.get('workspaceKey','workspace')}:engineering:{request.analysisKey}","label":request.label,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"inputRefs":sorted(set(refs)),"datasetRefs":sorted(set(drefs)),"metadata":{"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],**request.metadata}}
    EngineeringAnalysisRequest.model_validate(analysis_request)
    record={"ok":True,"schema":BINDING_SCHEMA,"version":VERSION,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"materializedBindings":materialized,"engineeringRequest":analysis_request,"executionPath":"/engineering/analyze","executionPerformed":False,"automaticDispatchAuthorized":False}
    record["bindingPlanHash"]=content_hash(record); return record


def core_lineage_plan(request: CoreEngineeringLineagePlanRequest) -> Dict[str, Any]:
    result=request.engineeringResult; validation=validate_result(result)
    if not validation["valid"]: raise HTTPException(status_code=422,detail={"engineeringResultInvalid":validation["reasons"]})
    eid=(request.coreExecutionId or "").strip(); obj=result.get("executionObject") or {}; regs=[]
    if eid:
        item=OutputItem(outputKey="engineering-system-result",outputType="result_bundle",objectRef=obj.get("objectRef",""),contentHash=result.get("engineeringRunHash",""),schema={"schema":RESULT,"version":VERSION},metadata={"analysisKey":result.get("analysisKey"),"domain":result.get("domain"),"diagnosticsHash":(result.get("diagnostics") or {}).get("diagnosticsHash"),"workbenchVersion":VERSION},provenance={"engineeringRuntimeRef":ENGINEERING_REF,"executionObjectHash":obj.get("objectHash","")},createdBy=request.createdBy)
        regs=[_request(CORE_PATHS["outputs"].format(execution_id=eid),_output_data(item),"register-engineering-system-result")]
    record={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"engineeringRunHash":result.get("engineeringRunHash"),"coreExecutionIdProvided":bool(eid),"coreExecutionIdMustComeFromCore":not bool(eid),"outputRegistrations":regs,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreExecutesEngineeringAnalysis":False,"licensedEngineeringCertificationPerformed":False,"codeComplianceDetermined":False}
    record["planHash"]=content_hash(record); return record


def manifest() -> Dict[str, Any]:
    domains=sorted(set(x["domain"] for x in CATALOG.values()))
    record={"ok":True,"schema":SCHEMA,"version":VERSION,"product":PRODUCT_KEY,"runtime":RUNTIME_KIND,"engineeringRuntimeRef":ENGINEERING_REF,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"analysisKeys":sorted(CATALOG),"domains":domains,"capabilities":{"canonicalEngineeringAnalysisSpecifications":True,"mechanicalAnalysis":True,"thermalAnalysis":True,"fluidAnalysis":True,"civilInfrastructureAnalysis":True,"electricalAnalysis":True,"controlsMechatronicsAnalysis":True,"energySystemsHandoffReuse":True,"engineeringSystemBundles":True,"workspaceBindingPlanning":True,"executionObjectProjection":True,"coreLineagePlanning":True},"boundaries":{"boundedAnalysesOnly":True,"arbitraryCodeExecutionAuthorized":False,"physicalActuationAuthorized":False,"automaticDesignSelectionAuthorized":False,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"licensedEngineeringCertificationAuthorized":False,"codeComplianceCertificationAuthorized":False,"physicalSafetyCertificationAuthorized":False}}
    record["manifestHash"]=content_hash(record); return record


def catalog() -> Dict[str, Any]:
    return {"ok":True,"schema":"sc-workbench-engineering-analysis-catalog/1.0","version":VERSION,"analysisCount":len(CATALOG),"analyses":[{"analysisKey":k,**CATALOG[k]} for k in sorted(CATALOG)]}


@router.get("/engineering/manifest")
def get_manifest(): return manifest()
@router.get("/engineering/catalog")
def get_catalog(): return catalog()
@router.post("/engineering/analyze")
def post_analyze(request: EngineeringAnalysisRequest): return analyze(request)
@router.post("/engineering/validate")
def post_validate(result: Dict[str, Any]): return validate_result(result)
@router.post("/engineering/system/run")
def post_system(request: EngineeringSystemRequest): return run_system(request)
@router.post("/engineering/workspace-binding/plan")
def post_binding(request: WorkspaceEngineeringBindingRequest): return workspace_binding_plan(request)
@router.post("/integration/core/engineering-lineage/plan")
def post_core(request: CoreEngineeringLineagePlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token); return core_lineage_plan(request)
@router.get("/v760/status")
def status():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Engineering Systems Runtime","analysisCount":len(CATALOG),"domains":sorted(set(x["domain"] for x in CATALOG.values())),"engineeringSystemBundles":True,"workspaceBindingPlanning":True,"coreLineagePlanning":True,"automaticDesignSelection":False,"licensedEngineeringCertification":False,"codeComplianceCertification":False,"automaticCoreDispatch":False}
