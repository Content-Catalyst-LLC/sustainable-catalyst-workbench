"""Workbench v7.3.0 — Dataset, Variable & Parameter Workspace.

v7.3 introduces a deterministic, content-addressed research input workspace above
v7.0 unified execution, v7.1 execution objects and v7.2 runtime orchestration.
It defines portable datasets, variables, parameter sets, assumptions and derived
scalar values, validates units, and prepares explicit execution bindings into the
existing bounded execution/orchestration APIs.

The workspace is stateless by design in v7.3: objects are returned with stable
references and hashes but are not automatically persisted. Platform Core handoff
uses the exact computation-lineage contract for datasets, parameters and
assumptions once a Core-issued execution id exists. No arbitrary code execution,
automatic Core dispatch, hidden data fetching, or scientific-validity claims are
performed here.
"""
from __future__ import annotations

import math
import re
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

import sympy as sp
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
try:
    from pint import UnitRegistry
except ImportError:
    UnitRegistry = None  # type: ignore[assignment]

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import RestrictedSympyParser, content_hash
from .v640 import _authorize_core_route
from .v670 import (
    CORE_COMPUTATION_LINEAGE_CONTRACT,
    CORE_PATHS,
    InputItem,
    ParameterItem,
    AssumptionItem,
    _input_data,
    _parameter_data,
    _assumption_data,
    _request,
)
from .v700 import OPERATIONS

VERSION = APP_VERSION
SCHEMA = "sc-workbench-data-variable-parameter-workspace/1.0"
DATASET_SCHEMA = "sc-workbench-dataset-object/1.0"
VARIABLE_SCHEMA = "sc-workbench-variable-object/1.0"
PARAMETER_SET_SCHEMA = "sc-workbench-parameter-set-object/1.0"
ASSUMPTION_SCHEMA = "sc-workbench-assumption-object/1.0"
DERIVED_SCHEMA = "sc-workbench-derived-value/1.0"
BINDING_SCHEMA = "sc-workbench-data-workspace-execution-binding-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-data-workspace-core-lineage-plan/1.0"
CORE_LINEAGE_CONTRACT_LITERAL = "sc.research.computation-analysis-execution-lineage.v1"
WORKSPACE_REF = "workbench:/workspace/data-variables-parameters"
MAX_DATASET_ROWS = 500
MAX_DATASET_COLUMNS = 120
MAX_TOTAL_CELLS = 20000
MAX_BINDINGS = 200
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,119}$")
TARGET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,79}(?:\.[A-Za-z][A-Za-z0-9_]{0,79}){0,5}$")
_ureg = UnitRegistry(autoconvert_offset_to_baseunit=True) if UnitRegistry is not None else None
_FALLBACK_UNITS = {
    "w": ("power", 1.0), "kw": ("power", 1e3), "mw": ("power", 1e6), "gw": ("power", 1e9),
    "j": ("energy", 1.0), "kj": ("energy", 1e3), "mj": ("energy", 1e6), "gj": ("energy", 1e9),
    "wh": ("energy", 3600.0), "kwh": ("energy", 3.6e6), "mwh": ("energy", 3.6e9),
    "s": ("time", 1.0), "sec": ("time", 1.0), "second": ("time", 1.0), "min": ("time", 60.0), "h": ("time", 3600.0), "hour": ("time", 3600.0),
    "m": ("length", 1.0), "cm": ("length", 0.01), "mm": ("length", 0.001), "km": ("length", 1000.0),
    "kg": ("mass", 1.0), "g": ("mass", 0.001),
    "v": ("voltage", 1.0), "mv": ("voltage", 0.001), "a": ("current", 1.0), "ma": ("current", 0.001),
    "ohm": ("resistance", 1.0), "%": ("ratio", 0.01), "dimensionless": ("ratio", 1.0),
}
router = APIRouter(tags=["workbench-v730-data-variable-parameter-workspace"])


def _key(value: str) -> str:
    value = (value or "").strip()
    if not KEY_RE.fullmatch(value):
        raise ValueError("key must start with a letter and contain only letters, digits, _, ., :, or -")
    return value


def _unit(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) > 128:
        raise ValueError("unit exceeds 128 characters")
    if _ureg is not None:
        try:
            _ureg.parse_units(value)
        except Exception as exc:
            raise ValueError(f"invalid unit: {value}") from exc
    elif value.lower().replace(" ", "_") not in _FALLBACK_UNITS:
        raise ValueError(f"invalid or unsupported fallback unit: {value}")
    return value


def _object_ref(kind: str, digest: str) -> str:
    return f"sc://workbench/{kind}/{digest[:24]}"


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


class ColumnSpec(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dataType: Literal["number", "integer", "string", "boolean", "datetime"] = "number"
    unit: str = Field(default="", max_length=128)
    role: Literal["feature", "target", "index", "time", "group", "weight", "uncertainty", "other"] = "feature"
    nullable: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str: return _unit(v)


class DatasetSpec(BaseModel):
    datasetKey: str
    label: str = Field(default="", max_length=400)
    columns: List[ColumnSpec] = Field(default_factory=list, max_length=MAX_DATASET_COLUMNS)
    rows: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_DATASET_ROWS)
    sourceRef: str = Field(default="", max_length=1000)
    versionRef: str = Field(default="", max_length=1000)
    licenseRef: str = Field(default="", max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("datasetKey")
    @classmethod
    def dataset_key(cls, v: str) -> str: return _key(v)

    @model_validator(mode="after")
    def validate_rows(self):
        names=[c.name for c in self.columns]
        if len(names)!=len(set(names)): raise ValueError("dataset column names must be unique")
        if self.rows and not self.columns: raise ValueError("inline rows require declared columns")
        if len(self.rows)*max(1,len(self.columns)) > MAX_TOTAL_CELLS: raise ValueError("dataset exceeds inline cell limit")
        allowed=set(names)
        for row in self.rows:
            unknown=set(row)-allowed
            if unknown: raise ValueError(f"row contains undeclared columns: {sorted(unknown)}")
        if not self.rows and not self.sourceRef: raise ValueError("dataset requires inline rows or sourceRef")
        return self


class VariableSpec(BaseModel):
    variableKey: str
    label: str = Field(default="", max_length=400)
    symbol: str = Field(default="", max_length=120)
    kind: Literal["input", "derived", "output", "index", "state", "control", "uncertainty", "other"] = "input"
    dataType: Literal["number", "integer", "string", "boolean", "datetime"] = "number"
    unit: str = Field(default="", max_length=128)
    value: Any = None
    expression: str = Field(default="", max_length=2000)
    dependsOn: List[str] = Field(default_factory=list, max_length=100)
    datasetKey: str = Field(default="", max_length=120)
    column: str = Field(default="", max_length=120)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("variableKey")
    @classmethod
    def variable_key(cls, v: str) -> str: return _key(v)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str: return _unit(v)

    @model_validator(mode="after")
    def validate_source(self):
        if self.expression and self.dataType not in {"number","integer"}: raise ValueError("derived expressions require numeric variables")
        if self.column and not self.datasetKey: raise ValueError("column requires datasetKey")
        return self


class ParameterSpec(BaseModel):
    parameterKey: str
    label: str = Field(default="", max_length=400)
    value: Any
    dataType: Literal["number", "integer", "string", "boolean"] = "number"
    unit: str = Field(default="", max_length=128)
    lowerBound: Optional[float] = None
    upperBound: Optional[float] = None
    sensitivityRole: str = Field(default="", max_length=180)
    sourceRef: str = Field(default="", max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("parameterKey")
    @classmethod
    def parameter_key(cls, v: str) -> str: return _key(v)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str: return _unit(v)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.lowerBound is not None and self.upperBound is not None and self.lowerBound > self.upperBound: raise ValueError("lowerBound cannot exceed upperBound")
        if self.dataType in {"number","integer"} and not _finite_number(self.value): raise ValueError("numeric parameter values must be finite")
        if _finite_number(self.value):
            x=float(self.value)
            if self.lowerBound is not None and x < self.lowerBound: raise ValueError("parameter value below lowerBound")
            if self.upperBound is not None and x > self.upperBound: raise ValueError("parameter value above upperBound")
        return self


class ParameterSetSpec(BaseModel):
    parameterSetKey: str
    label: str = Field(default="", max_length=400)
    parameters: List[ParameterSpec] = Field(default_factory=list, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("parameterSetKey")
    @classmethod
    def set_key(cls, v: str) -> str: return _key(v)

    @model_validator(mode="after")
    def unique_parameters(self):
        keys=[p.parameterKey for p in self.parameters]
        if len(keys)!=len(set(keys)): raise ValueError("parameter keys must be unique within a parameter set")
        return self


class AssumptionSpec(BaseModel):
    assumptionKey: str
    statement: str = Field(min_length=1, max_length=4000)
    status: Literal["declared", "testable", "supported", "challenged", "retired"] = "declared"
    evidenceRefs: List[str] = Field(default_factory=list, max_length=100)
    protocolAssumptionRef: str = Field(default="", max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("assumptionKey")
    @classmethod
    def assumption_key(cls, v: str) -> str: return _key(v)


class WorkspaceRequest(BaseModel):
    workspaceKey: str = "workbench-data-workspace"
    title: str = Field(default="", max_length=400)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    datasets: List[DatasetSpec] = Field(default_factory=list, max_length=100)
    variables: List[VariableSpec] = Field(default_factory=list, max_length=300)
    parameterSets: List[ParameterSetSpec] = Field(default_factory=list, max_length=100)
    assumptions: List[AssumptionSpec] = Field(default_factory=list, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("workspaceKey")
    @classmethod
    def workspace_key(cls, v: str) -> str: return _key(v)

    @model_validator(mode="after")
    def validate_references(self):
        dkeys=[d.datasetKey for d in self.datasets]; vkeys=[v.variableKey for v in self.variables]; pkeys=[p.parameterSetKey for p in self.parameterSets]; akeys=[a.assumptionKey for a in self.assumptions]
        for label,keys in (("dataset",dkeys),("variable",vkeys),("parameter set",pkeys),("assumption",akeys)):
            if len(keys)!=len(set(keys)): raise ValueError(f"{label} keys must be unique")
        dmap={d.datasetKey:d for d in self.datasets}
        vset=set(vkeys)
        for v in self.variables:
            if v.datasetKey:
                if v.datasetKey not in dmap: raise ValueError(f"variable {v.variableKey} references unknown dataset {v.datasetKey}")
                if v.column and v.column not in {c.name for c in dmap[v.datasetKey].columns}: raise ValueError(f"variable {v.variableKey} references unknown column {v.column}")
            missing=[x for x in v.dependsOn if x not in vset]
            if missing: raise ValueError(f"variable {v.variableKey} has unknown dependencies: {missing}")
        return self


class UnitConversionRequest(BaseModel):
    value: float
    fromUnit: str = Field(min_length=1, max_length=128)
    toUnit: str = Field(min_length=1, max_length=128)

    @field_validator("fromUnit","toUnit")
    @classmethod
    def unit_valid(cls, v: str) -> str: return _unit(v)


class DerivedValueRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=2000)
    values: Dict[str, float] = Field(default_factory=dict, max_length=100)
    unit: str = Field(default="", max_length=128)
    precision: int = Field(default=15, ge=1, le=50)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str: return _unit(v)


class BindingSpec(BaseModel):
    sourceKind: Literal["variable", "parameter", "dataset"]
    sourceKey: str
    targetField: str = ""
    parameterSetKey: str = ""

    @field_validator("sourceKey")
    @classmethod
    def source_key(cls, v: str) -> str: return _key(v)

    @field_validator("targetField")
    @classmethod
    def target_field(cls, v: str) -> str:
        v=(v or "").strip()
        if v and not TARGET_RE.fullmatch(v): raise ValueError("targetField must be a bounded dotted object path")
        return v


class ExecutionBindingPlanRequest(BaseModel):
    workspace: Dict[str, Any]
    operation: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    bindings: List[BindingSpec] = Field(default_factory=list, max_length=MAX_BINDINGS)
    preferredRuntime: str = Field(default="", max_length=180)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("operation")
    @classmethod
    def known_operation(cls, v: str) -> str:
        if v not in OPERATIONS: raise ValueError("operation is not registered in the unified execution runtime")
        return v


class CoreLineagePlanRequest(BaseModel):
    workspace: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _dataset_record(spec: DatasetSpec) -> Dict[str, Any]:
    columns=[c.model_dump() for c in spec.columns]
    basis={"datasetKey":spec.datasetKey,"label":spec.label,"columns":columns,"rows":spec.rows,"sourceRef":spec.sourceRef,"versionRef":spec.versionRef,"licenseRef":spec.licenseRef,"metadata":spec.metadata}
    digest=content_hash(basis)
    return {"schema":DATASET_SCHEMA,"version":VERSION,"datasetKey":spec.datasetKey,"datasetRef":_object_ref("dataset",digest),"datasetHash":digest,"label":spec.label,"columns":columns,"rowCount":len(spec.rows),"columnCount":len(columns),"inlineRows":spec.rows,"sourceRef":spec.sourceRef,"versionRef":spec.versionRef,"licenseRef":spec.licenseRef,"metadata":spec.metadata,"automaticFetchPerformed":False}


def _parameter_set_record(spec: ParameterSetSpec) -> Dict[str, Any]:
    params=[]
    for p in spec.parameters:
        basis=p.model_dump(); digest=content_hash(basis)
        params.append({**basis,"parameterRef":_object_ref("parameter",digest),"parameterHash":digest})
    basis={"parameterSetKey":spec.parameterSetKey,"label":spec.label,"parameters":params,"metadata":spec.metadata}
    digest=content_hash(basis)
    return {"schema":PARAMETER_SET_SCHEMA,"version":VERSION,"parameterSetKey":spec.parameterSetKey,"parameterSetRef":_object_ref("parameter-set",digest),"parameterSetHash":digest,"label":spec.label,"parameters":params,"metadata":spec.metadata}


def _assumption_record(spec: AssumptionSpec) -> Dict[str, Any]:
    basis=spec.model_dump(); digest=content_hash(basis)
    return {"schema":ASSUMPTION_SCHEMA,"version":VERSION,"assumptionRef":_object_ref("assumption",digest),"assumptionHash":digest,**basis}


def _scalar_context(variables: List[VariableSpec], parameter_sets: List[ParameterSetSpec]) -> Dict[str, Any]:
    ctx={}
    for v in variables:
        if v.value is not None and v.dataType in {"number","integer"} and _finite_number(v.value): ctx[v.symbol or v.variableKey]=v.value
    for ps in parameter_sets:
        for p in ps.parameters:
            if p.dataType in {"number","integer"} and _finite_number(p.value): ctx[p.parameterKey]=p.value
    return ctx


def derive_value(request: DerivedValueRequest) -> Dict[str, Any]:
    for k,v in request.values.items():
        _key(k)
        if not _finite_number(v): raise HTTPException(status_code=422, detail=f"non-finite scalar value for {k}")
    parser=RestrictedSympyParser(list(request.values.keys()))
    try:
        expr=parser.parse(request.expression)
        subs={parser.symbol(k): sp.Float(v) for k,v in request.values.items()}
        result=sp.simplify(expr.subs(subs))
        if result.free_symbols: raise ValueError(f"unbound symbols remain: {sorted(str(x) for x in result.free_symbols)}")
        numeric=sp.N(result,request.precision)
        value=float(numeric)
        if not math.isfinite(value): raise ValueError("derived value is not finite")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record={"ok":True,"schema":DERIVED_SCHEMA,"version":VERSION,"expression":request.expression,"values":request.values,"unit":request.unit,"exactText":str(result),"decimalText":str(numeric),"value":value,"arbitraryCodeExecutionAuthorized":False,"pythonEvalAuthorized":False}
    record["derivedValueHash"]=content_hash(record)
    return record


def build_workspace(request: WorkspaceRequest) -> Dict[str, Any]:
    datasets=[_dataset_record(d) for d in request.datasets]
    parameter_sets=[_parameter_set_record(p) for p in request.parameterSets]
    assumptions=[_assumption_record(a) for a in request.assumptions]
    context=_scalar_context(request.variables,request.parameterSets)
    variables=[]
    for v in request.variables:
        derived=None
        if v.expression:
            values={k:float(context[k]) for k in v.dependsOn if k in context}
            if len(values)!=len(v.dependsOn):
                missing=[k for k in v.dependsOn if k not in context]
                raise HTTPException(status_code=422, detail=f"derived variable {v.variableKey} missing scalar dependencies: {missing}")
            derived=derive_value(DerivedValueRequest(expression=v.expression,values=values,unit=v.unit)).get("value")
            context[v.symbol or v.variableKey]=derived
        basis={**v.model_dump(),"derivedValue":derived}
        digest=content_hash(basis)
        variables.append({"schema":VARIABLE_SCHEMA,"version":VERSION,"variableRef":_object_ref("variable",digest),"variableHash":digest,**basis})
    core={"workspaceKey":request.workspaceKey,"title":request.title,"projectRef":request.projectRef,"coreSessionId":request.coreSessionId,"datasets":datasets,"variables":variables,"parameterSets":parameter_sets,"assumptions":assumptions,"metadata":request.metadata}
    digest=content_hash(core)
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"workspaceRef":_object_ref("data-workspace",digest),"workspaceHash":digest,**core,"counts":{"datasets":len(datasets),"variables":len(variables),"parameterSets":len(parameter_sets),"parameters":sum(len(x["parameters"]) for x in parameter_sets),"assumptions":len(assumptions)},"boundaries":{"automaticPersistencePerformed":False,"automaticDataFetchPerformed":False,"automaticExecutionPerformed":False,"automaticCoreDispatchPerformed":False,"scientificValidityCertified":False,"truthDetermined":False}}


def _workspace_ok(workspace: Dict[str, Any]) -> None:
    if workspace.get("schema")!=SCHEMA or workspace.get("version")!=VERSION or not workspace.get("workspaceHash"):
        raise HTTPException(status_code=422, detail=f"workspace must be a v{VERSION} {SCHEMA} object")
    expected=content_hash({k:v for k,v in workspace.items() if k not in {"ok","schema","version","workspaceRef","workspaceHash","counts","boundaries"}})
    if expected!=workspace.get("workspaceHash"): raise HTTPException(status_code=422, detail="workspace integrity hash mismatch")


def _set_path(target: Dict[str, Any], path: str, value: Any) -> None:
    parts=path.split('.')
    cur=target
    for part in parts[:-1]:
        nxt=cur.get(part)
        if nxt is None: cur[part]={}; nxt=cur[part]
        if not isinstance(nxt,dict): raise HTTPException(status_code=422, detail=f"target path collides with non-object at {part}")
        cur=nxt
    cur[parts[-1]]=value


def execution_binding_plan(request: ExecutionBindingPlanRequest) -> Dict[str, Any]:
    ws=request.workspace; _workspace_ok(ws)
    variables={x["variableKey"]:x for x in ws.get("variables",[]) if isinstance(x,dict)}
    datasets={x["datasetKey"]:x for x in ws.get("datasets",[]) if isinstance(x,dict)}
    parameter_sets={x["parameterSetKey"]:x for x in ws.get("parameterSets",[]) if isinstance(x,dict)}
    payload=deepcopy(request.payload); input_refs=[]; dataset_refs=[]; materialized=[]
    for b in request.bindings:
        if b.sourceKind=="variable":
            src=variables.get(b.sourceKey)
            if not src: raise HTTPException(status_code=422, detail=f"unknown variable: {b.sourceKey}")
            value=src.get("derivedValue") if src.get("expression") else src.get("value")
            if value is None: raise HTTPException(status_code=422, detail=f"variable has no scalar materializable value: {b.sourceKey}")
            if not b.targetField: raise HTTPException(status_code=422, detail="variable bindings require targetField")
            _set_path(payload,b.targetField,value); input_refs.append(src["variableRef"]); materialized.append({"binding":b.model_dump(),"sourceRef":src["variableRef"],"valueHash":content_hash(value)})
        elif b.sourceKind=="parameter":
            ps=parameter_sets.get(b.parameterSetKey)
            if not ps: raise HTTPException(status_code=422, detail=f"unknown parameter set: {b.parameterSetKey}")
            src=next((x for x in ps.get("parameters",[]) if x.get("parameterKey")==b.sourceKey),None)
            if not src: raise HTTPException(status_code=422, detail=f"unknown parameter: {b.sourceKey}")
            if not b.targetField: raise HTTPException(status_code=422, detail="parameter bindings require targetField")
            _set_path(payload,b.targetField,src.get("value")); input_refs.append(src["parameterRef"]); materialized.append({"binding":b.model_dump(),"sourceRef":src["parameterRef"],"valueHash":content_hash(src.get("value"))})
        else:
            src=datasets.get(b.sourceKey)
            if not src: raise HTTPException(status_code=422, detail=f"unknown dataset: {b.sourceKey}")
            dataset_refs.append(src["datasetRef"]); input_refs.append(src["datasetRef"])
            if b.targetField: _set_path(payload,b.targetField,src["datasetRef"])
            materialized.append({"binding":b.model_dump(),"sourceRef":src["datasetRef"],"valueHash":src["datasetHash"]})
    orchestrator_request={"operation":request.operation,"payload":payload,"projectRef":ws.get("projectRef",''),"coreSessionId":ws.get("coreSessionId",''),"requestKey":request.requestKey or f"{ws.get('workspaceKey','workspace')}:{request.operation}","label":request.label,"inputRefs":sorted(set(input_refs)),"datasetRefs":sorted(set(dataset_refs)),"preferredRuntime":request.preferredRuntime,"tags":request.tags,"metadata":{"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],**request.metadata}}
    record={"ok":True,"schema":BINDING_SCHEMA,"version":VERSION,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"operation":request.operation,"materializedBindings":materialized,"orchestratorRequest":orchestrator_request,"executionPath":"/execution/orchestrator/execute","executionPerformed":False,"automaticDispatchAuthorized":False}
    record["bindingPlanHash"]=content_hash(record)
    return record


def core_lineage_plan(request: CoreLineagePlanRequest) -> Dict[str, Any]:
    ws=request.workspace; _workspace_ok(ws); eid=(request.coreExecutionId or '').strip()
    input_requests=[]; parameter_requests=[]; assumption_requests=[]
    if eid:
        for d in ws.get("datasets",[]):
            item=InputItem(inputKey=d["datasetKey"],inputType="dataset",objectRef=d["datasetRef"],versionRef=d.get("versionRef",''),contentHash=d["datasetHash"],role="workspace_dataset",selector={"columns":[c.get("name") for c in d.get("columns",[])]},provenance={"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"]},createdBy=request.createdBy)
            input_requests.append(_request(CORE_PATHS["inputs"].format(execution_id=eid),_input_data(item),"register-workspace-dataset"))
        for ps in ws.get("parameterSets",[]):
            for p in ps.get("parameters",[]):
                item=ParameterItem(parameterKey=p["parameterKey"],value=p.get("value"),unit=p.get("unit",''),sourceRef=p.get("sourceRef") or p.get("parameterRef",''),sensitivityRole=p.get("sensitivityRole",''),provenance={"workspaceRef":ws["workspaceRef"],"parameterSetRef":ps["parameterSetRef"],"parameterHash":p["parameterHash"]},createdBy=request.createdBy)
                parameter_requests.append(_request(CORE_PATHS["parameters"].format(execution_id=eid),_parameter_data(item),"register-workspace-parameter"))
        for a in ws.get("assumptions",[]):
            item=AssumptionItem(assumptionKey=a["assumptionKey"],statementText=a["statement"],protocolAssumptionRef=a.get("protocolAssumptionRef",''),evidenceRefs=a.get("evidenceRefs",[]),provenance={"workspaceRef":ws["workspaceRef"],"assumptionHash":a["assumptionHash"],"status":a.get("status")},createdBy=request.createdBy)
            assumption_requests.append(_request(CORE_PATHS["assumptions"].format(execution_id=eid),_assumption_data(item),"register-workspace-assumption"))
    record={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"coreExecutionIdProvided":bool(eid),"coreExecutionIdMustComeFromCore":not bool(eid),"datasetInputRegistrations":input_requests,"parameterRegistrations":parameter_requests,"assumptionRegistrations":assumption_requests,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreExecutesSpecialistWork":False}
    record["planHash"]=content_hash(record)
    return record


def manifest() -> Dict[str, Any]:
    record={"ok":True,"schema":SCHEMA,"version":VERSION,"product":PRODUCT_KEY,"runtime":RUNTIME_KIND,"workspaceRef":WORKSPACE_REF,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"limits":{"maxDatasetRows":MAX_DATASET_ROWS,"maxDatasetColumns":MAX_DATASET_COLUMNS,"maxInlineCells":MAX_TOTAL_CELLS,"maxBindings":MAX_BINDINGS},"capabilities":{"contentAddressedDatasets":True,"canonicalVariables":True,"parameterSets":True,"declaredAssumptions":True,"unitValidationAndConversion":True,"safeDerivedScalarValues":True,"executionBindingPlanning":True,"coreLineagePlanning":True},"boundaries":{"statelessWorkspaceObjects":True,"arbitraryCodeExecutionAuthorized":False,"pythonEvalAuthorized":False,"automaticPersistenceAuthorized":False,"automaticDataFetchAuthorized":False,"automaticExecutionAuthorized":False,"automaticCoreDispatchAuthorized":False,"scientificValidityCertified":False}}
    record["manifestHash"]=content_hash(record)
    return record


@router.get('/data-workspace/manifest')
def get_manifest(): return manifest()

@router.post('/data-workspace/build')
def post_workspace(request: WorkspaceRequest): return build_workspace(request)

@router.post('/data-workspace/units/convert')
def convert_units(request: UnitConversionRequest):
    try:
        if _ureg is not None:
            q=request.value*_ureg(request.fromUnit); converted=q.to(request.toUnit); converted_value=float(converted.magnitude); dimensionality=str(converted.dimensionality); engine="pint"
        else:
            fk=request.fromUnit.lower().replace(" ", "_"); tk=request.toUnit.lower().replace(" ", "_"); fd,ff=_FALLBACK_UNITS[fk]; td,tf=_FALLBACK_UNITS[tk]
            if fd!=td: raise ValueError(f"incompatible dimensions: {fd} -> {td}")
            converted_value=float(request.value)*ff/tf; dimensionality=fd; engine="bounded-fallback"
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    record={"ok":True,"schema":"sc-workbench-unit-conversion/1.0","version":VERSION,"value":request.value,"fromUnit":request.fromUnit,"toUnit":request.toUnit,"convertedValue":converted_value,"dimensionality":dimensionality,"engine":engine}
    record["conversionHash"]=content_hash(record); return record

@router.post('/data-workspace/derive')
def post_derive(request: DerivedValueRequest): return derive_value(request)

@router.post('/data-workspace/execution-binding/plan')
def post_binding_plan(request: ExecutionBindingPlanRequest): return execution_binding_plan(request)

@router.post('/integration/core/data-workspace/lineage/plan')
def post_core_plan(request: CoreLineagePlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias='X-SC-Service-Token')):
    _authorize_core_route(x_sc_service_token); return core_lineage_plan(request)

@router.get('/v730/status')
def status():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Dataset, Variable & Parameter Workspace","contentAddressedWorkspace":True,"unitAware":True,"derivedScalarValues":True,"executionBindingPlanning":True,"coreLineagePlanning":True,"automaticPersistence":False,"automaticExecution":False,"automaticCoreDispatch":False}
