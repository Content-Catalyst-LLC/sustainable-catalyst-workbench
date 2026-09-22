"""Workbench v6.11.0 — Forensic Quantitative Reconstruction Runtime.

Consumes Platform Core Open Forensics quantitative reconstruction handoffs,
executes bounded specialist numerical reconstruction in Workbench, and prepares
result-binding / reproduction / lineage plans back to Core. Core owns evidence,
chain of custody, claims, hypotheses, investigation state, and forensic
semantics. Workbench performs numerical calculations only and does not assign
truth, probability, guilt, responsibility, rankings, winners, or verdicts.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import PRODUCT_REF
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT
from .v680 import SCHEMA as UNCERTAINTY_RUNTIME_SCHEMA
from .v690 import CORE_UNIFIED_VISUAL_CONTRACT

VERSION = APP_VERSION
SCHEMA = "sc-workbench-forensic-quantitative-reconstruction-runtime/1.0"
HANDOFF_CONSUME_SCHEMA = "sc-workbench-forensic-handoff-consumption/1.0"
TRAJECTORY_SCHEMA = "sc-workbench-forensic-trajectory-reconstruction/1.0"
TEMPORAL_SCHEMA = "sc-workbench-forensic-temporal-comparison/1.0"
UNCERTAINTY_SCHEMA = "sc-workbench-forensic-measurement-uncertainty/1.0"
HYPOTHESIS_SCHEMA = "sc-workbench-forensic-hypothesis-metrics/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-forensic-request/1.0"
BRIDGE_REF = "workbench:/integration/core/forensic-quantitative-reconstruction"

CORE_FORENSIC_QUANTITATIVE_CONTRACT = "sc.open-forensics.quantitative-reconstruction.v1"
CORE_FORENSIC_HANDOFF_CONTRACT = "sc.forensic-quantitative-handoff.v1"
CORE_FORENSIC_REPRODUCTION_PACKAGE_CONTRACT = "sc.open-forensics.quantitative-reproduction-package.v1"
CORE_FORENSIC_TIMELINE_CONTRACT = "sc.open-forensics.forensic-timeline.v1"
CORE_FORENSIC_SPATIAL_CONTRACT = "sc.open-forensics.spatial-temporal-evidence.v1"
CORE_FORENSIC_HYPOTHESIS_CONTRACT = "sc.open-forensics.competing-hypothesis-matrix.v1"

CORE_PATHS = {
    "readiness": "/v1/open-forensics/readiness",
    "quantitativeBundle": "/v1/open-forensics/investigations/{investigation_id}/quantitative-reconstructions",
    "handoffContract": "/v1/open-forensics/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/handoff/workbench",
    "resultBindings": "/v1/open-forensics/investigations/{investigation_id}/quantitative-handoffs/{handoff_id}/results",
    "reproductionPackages": "/v1/open-forensics/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/reproduction-packages",
    "timeline": "/v1/open-forensics/investigations/{investigation_id}/timeline",
    "spatialTemporalEvidence": "/v1/open-forensics/investigations/{investigation_id}/spatial-temporal-evidence",
    "hypothesisMatrix": "/v1/open-forensics/investigations/{investigation_id}/hypothesis-matrix",
}

SUPPORTED_RECONSTRUCTION_KINDS = {"kinematic", "energetic", "statistical", "physical", "financial", "engineering", "environmental", "other"}
router = APIRouter(tags=["workbench-v6110-forensic-quantitative-reconstruction"])


def _bad(exc: Exception) -> HTTPException:
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _finite(value: Any, field: str = "value") -> float:
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"{field} must be finite")
    return v


def _core_request(path: str, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
    out = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "method": "POST",
        "path": path,
        "phase": phase,
        "data": data,
        "payload": {"data": data},
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": True,
    }
    out["requestHash"] = content_hash(out)
    return out


def forensic_manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "bridgeRef": BRIDGE_REF,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "coreUnifiedVisualContract": CORE_UNIFIED_VISUAL_CONTRACT,
        "workbenchUncertaintyRuntimeSchema": UNCERTAINTY_RUNTIME_SCHEMA,
        "coreForensicQuantitativeContract": CORE_FORENSIC_QUANTITATIVE_CONTRACT,
        "coreForensicHandoffContract": CORE_FORENSIC_HANDOFF_CONTRACT,
        "coreForensicReproductionPackageContract": CORE_FORENSIC_REPRODUCTION_PACKAGE_CONTRACT,
        "coreForensicTimelineContract": CORE_FORENSIC_TIMELINE_CONTRACT,
        "coreForensicSpatialContract": CORE_FORENSIC_SPATIAL_CONTRACT,
        "coreForensicHypothesisContract": CORE_FORENSIC_HYPOTHESIS_CONTRACT,
        "corePaths": dict(CORE_PATHS),
        "reconstructionKinds": sorted(SUPPORTED_RECONSTRUCTION_KINDS),
        "capabilities": [
            "core-forensic-quantitative-handoff-consumption",
            "planar-and-geodetic-trajectory-reconstruction",
            "segment-speed-and-acceleration-calculation",
            "temporal-window-overlap-and-gap-calculation",
            "first-order-independent-uncertainty-propagation",
            "descriptive-hypothesis-residual-metrics",
            "core-forensic-result-binding-planning",
            "core-forensic-reproduction-package-planning",
            "v670-forensic-computation-lineage-integration",
            "v680-uncertainty-context-preservation",
            "v690-forensic-visual-result-compatibility",
        ],
        "boundaries": {
            "workbenchExecutesQuantitativeReconstruction": True,
            "coreOwnsEvidenceAndChainOfCustody": True,
            "coreOwnsClaimsAndHypotheses": True,
            "coreExecutesQuantitativeModels": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "arbitraryCoreCodeExecution": False,
            "probabilityAssignmentAuthorized": False,
            "hypothesisRankingAuthorized": False,
            "winnerSelectionAuthorized": False,
            "truthDeterminationAuthorized": False,
            "guiltOrResponsibilityDeterminationAuthorized": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


class CoreHandoffConsumeRequest(BaseModel):
    handoff: Dict[str, Any]


class TrajectoryPoint(BaseModel):
    pointKey: str
    timeSeconds: float
    x: float
    y: float
    z: float | None = None
    sourceRef: str = ""
    uncertainty: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("pointKey")
    @classmethod
    def key_required(cls, value: str) -> str:
        value = _bounded(value, 180)
        if not value:
            raise ValueError("pointKey is required")
        return value


class TrajectoryReconstructionRequest(BaseModel):
    reconstructionKey: str
    coordinateMode: Literal["planar", "geodetic-degrees"] = "planar"
    distanceUnit: str = "m"
    timeUnit: str = "s"
    points: List[TrajectoryPoint] = Field(min_length=2)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("reconstructionKey")
    @classmethod
    def reconstruction_key_required(cls, value: str) -> str:
        value = _bounded(value, 240)
        if not value:
            raise ValueError("reconstructionKey is required")
        return value


class TemporalWindow(BaseModel):
    windowKey: str
    startSeconds: float
    endSeconds: float
    sourceRef: str = ""

    @field_validator("windowKey")
    @classmethod
    def window_key_required(cls, value: str) -> str:
        value = _bounded(value, 180)
        if not value:
            raise ValueError("windowKey is required")
        return value


class TemporalComparisonRequest(BaseModel):
    windows: List[TemporalWindow] = Field(min_length=2)
    toleranceSeconds: float = Field(default=0.0, ge=0.0)


class MeasurementValue(BaseModel):
    key: str
    value: float
    stddev: float = Field(default=0.0, ge=0.0)
    unit: str = ""
    sourceRef: str = ""

    @field_validator("key")
    @classmethod
    def key_required(cls, value: str) -> str:
        value = _bounded(value, 180)
        if not value:
            raise ValueError("measurement key is required")
        return value


class UncertaintyPropagationRequest(BaseModel):
    operation: Literal["sum", "difference", "product", "ratio", "weighted-sum"]
    measurements: List[MeasurementValue] = Field(min_length=2)
    weights: List[float] = Field(default_factory=list)
    outputUnit: str = ""


class HypothesisPrediction(BaseModel):
    hypothesisRef: str
    predictions: List[float] = Field(min_length=1)

    @field_validator("hypothesisRef")
    @classmethod
    def ref_required(cls, value: str) -> str:
        value = _bounded(value, 1000)
        if not value:
            raise ValueError("hypothesisRef is required")
        return value


class HypothesisMetricsRequest(BaseModel):
    observations: List[float] = Field(min_length=1)
    hypotheses: List[HypothesisPrediction] = Field(min_length=1)
    observationStddev: List[float] = Field(default_factory=list)


class ResultBindingPlanRequest(BaseModel):
    investigationId: str
    reconstructionId: str
    handoffId: str
    result: Dict[str, Any]
    resultKey: str = "workbench-result"
    resultKind: str = "quantitative-reconstruction-result"
    externalResultRef: str = ""
    evidenceItemId: str = ""
    producedAt: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("investigationId", "reconstructionId", "handoffId")
    @classmethod
    def ids_required(cls, value: str) -> str:
        value = _bounded(value, 256)
        if not value:
            raise ValueError("Core-issued investigation, reconstruction, and handoff IDs are required")
        return value


class ReproductionPackagePlanRequest(BaseModel):
    investigationId: str
    reconstructionId: str
    result: Dict[str, Any]
    packageKey: str = "workbench-reconstruction"
    createdBy: str = "workbench"
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("investigationId", "reconstructionId")
    @classmethod
    def ids_required(cls, value: str) -> str:
        value = _bounded(value, 256)
        if not value:
            raise ValueError("Core-issued investigation and reconstruction IDs are required")
        return value


class LineagePlanRequest(BaseModel):
    projectRef: str
    reconstructionRef: str
    result: Dict[str, Any]
    coreSessionId: str = ""
    workbenchExecutionRef: str = ""
    evidenceRefs: List[str] = Field(default_factory=list)

    @field_validator("projectRef", "reconstructionRef")
    @classmethod
    def refs_required(cls, value: str) -> str:
        value = _bounded(value, 1000)
        if not value:
            raise ValueError("projectRef and reconstructionRef are required")
        return value


def consume_core_handoff(request: CoreHandoffConsumeRequest) -> Dict[str, Any]:
    h = dict(request.handoff)
    contract = h.get("contract")
    if contract != CORE_FORENSIC_HANDOFF_CONTRACT:
        raise ValueError(f"handoff.contract must be {CORE_FORENSIC_HANDOFF_CONTRACT}")
    target = str(h.get("target_product") or "").lower()
    if target != "workbench":
        raise ValueError("forensic quantitative handoff target_product must be workbench")
    if h.get("execute_by_core") is True:
        raise ValueError("Core forensic handoffs must not request execute_by_core=true")
    manifest = dict(h.get("input_manifest") or {})
    if manifest.get("contract") != CORE_FORENSIC_QUANTITATIVE_CONTRACT:
        raise ValueError(f"input_manifest.contract must be {CORE_FORENSIC_QUANTITATIVE_CONTRACT}")
    out = {
        "ok": True,
        "schema": HANDOFF_CONSUME_SCHEMA,
        "version": VERSION,
        "investigationId": h.get("investigation_id") or manifest.get("investigation_id"),
        "reconstructionId": h.get("reconstruction_id"),
        "targetProduct": target,
        "modelRef": h.get("model_ref"),
        "modelVersionRef": h.get("model_version_ref"),
        "inputManifest": manifest,
        "executionPlan": {
            "specialistRuntime": "workbench",
            "explicitOperationRequired": True,
            "automaticExecutionAuthorized": False,
            "automaticCoreWritebackAuthorized": False,
            "availableOperations": ["trajectory", "temporal-comparison", "uncertainty-propagation", "hypothesis-metrics"],
        },
    }
    out["handoffHash"] = content_hash(out)
    return out


def _segment_distance(a: TrajectoryPoint, b: TrajectoryPoint, mode: str) -> float:
    if mode == "planar":
        dz = (float(b.z) - float(a.z)) if a.z is not None and b.z is not None else 0.0
        return math.sqrt((float(b.x)-float(a.x))**2 + (float(b.y)-float(a.y))**2 + dz**2)
    # x=longitude, y=latitude in degrees. Haversine on a spherical Earth.
    lon1, lat1, lon2, lat2 = map(math.radians, [float(a.x), float(a.y), float(b.x), float(b.y)])
    dlon, dlat = lon2-lon1, lat2-lat1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371008.8 * 2 * math.asin(min(1.0, math.sqrt(h)))


def execute_trajectory(request: TrajectoryReconstructionRequest) -> Dict[str, Any]:
    pts = list(request.points)
    for p in pts:
        _finite(p.timeSeconds, "timeSeconds"); _finite(p.x, "x"); _finite(p.y, "y")
        if p.z is not None: _finite(p.z, "z")
    pts.sort(key=lambda p: p.timeSeconds)
    for i in range(len(pts)-1):
        if pts[i+1].timeSeconds <= pts[i].timeSeconds:
            raise ValueError("trajectory point times must be unique and strictly increasing")
    segments=[]; speeds=[]; total_distance=0.0
    for i,(a,b) in enumerate(zip(pts,pts[1:]),1):
        dt=float(b.timeSeconds-a.timeSeconds); dist=_segment_distance(a,b,request.coordinateMode); speed=dist/dt
        total_distance += dist; speeds.append(speed)
        segments.append({"segment":i,"from":a.pointKey,"to":b.pointKey,"duration":dt,"distance":dist,"speed":speed,"fromSourceRef":a.sourceRef or None,"toSourceRef":b.sourceRef or None})
    for i,seg in enumerate(segments):
        if i==0: seg["accelerationFromPreviousSegment"]=None
        else:
            mid_prev=(pts[i-1].timeSeconds+pts[i].timeSeconds)/2
            mid_cur=(pts[i].timeSeconds+pts[i+1].timeSeconds)/2
            seg["accelerationFromPreviousSegment"]=(speeds[i]-speeds[i-1])/(mid_cur-mid_prev)
    elapsed=float(pts[-1].timeSeconds-pts[0].timeSeconds)
    out={"ok":True,"schema":TRAJECTORY_SCHEMA,"version":VERSION,"reconstructionKey":request.reconstructionKey,"coordinateMode":request.coordinateMode,"distanceUnit":"m" if request.coordinateMode=="geodetic-degrees" else request.distanceUnit,"timeUnit":request.timeUnit,"pointCount":len(pts),"segmentCount":len(segments),"segments":segments,"summary":{"totalDistance":total_distance,"elapsedTime":elapsed,"averageSpeed":total_distance/elapsed,"minimumSegmentSpeed":min(speeds),"maximumSegmentSpeed":max(speeds)},"metadata":dict(request.metadata),"calculated_by_workbench":True,"calculated_by_core":False,"descriptive_only":True,"truth_determination":False}
    out["resultHash"]=content_hash(out); return out


def execute_temporal_comparison(request: TemporalComparisonRequest) -> Dict[str, Any]:
    windows=[]
    for w in request.windows:
        s=_finite(w.startSeconds,"startSeconds"); e=_finite(w.endSeconds,"endSeconds")
        if e < s: raise ValueError("temporal window endSeconds must be >= startSeconds")
        windows.append((w.windowKey,s,e,w.sourceRef))
    comparisons=[]; tol=float(request.toleranceSeconds)
    for i in range(len(windows)):
        for j in range(i+1,len(windows)):
            ak,as_,ae,ar=windows[i]; bk,bs,be,br=windows[j]
            overlap=max(0.0,min(ae,be)-max(as_,bs))
            if overlap>0: relation="overlaps"; gap=0.0
            elif abs(ae-bs)<=tol or abs(be-as_)<=tol: relation="touches-within-tolerance"; gap=0.0
            elif ae < bs: relation="before"; gap=bs-ae
            else: relation="after"; gap=as_-be
            comparisons.append({"left":ak,"right":bk,"relation":relation,"overlapSeconds":overlap,"gapSeconds":gap,"leftSourceRef":ar or None,"rightSourceRef":br or None})
    out={"ok":True,"schema":TEMPORAL_SCHEMA,"version":VERSION,"windowCount":len(windows),"comparisonCount":len(comparisons),"toleranceSeconds":tol,"comparisons":comparisons,"calculated_by_workbench":True,"calculated_by_core":False,"confirmed_sequence":False,"descriptive_only":True}
    out["resultHash"]=content_hash(out); return out


def execute_uncertainty(request: UncertaintyPropagationRequest) -> Dict[str, Any]:
    vals=[_finite(m.value,m.key) for m in request.measurements]; sig=[_finite(m.stddev,m.key+".stddev") for m in request.measurements]
    op=request.operation
    if op=="sum": result=sum(vals); variance=sum(s*s for s in sig); weights=[1.0]*len(vals)
    elif op=="difference":
        if len(vals)!=2: raise ValueError("difference requires exactly two measurements")
        result=vals[0]-vals[1]; variance=sig[0]**2+sig[1]**2; weights=[1.0,-1.0]
    elif op=="weighted-sum":
        if len(request.weights)!=len(vals): raise ValueError("weighted-sum requires one weight per measurement")
        weights=[_finite(x,"weight") for x in request.weights]; result=sum(w*v for w,v in zip(weights,vals)); variance=sum((w*s)**2 for w,s in zip(weights,sig))
    elif op=="product":
        result=math.prod(vals); weights=[]; rel=0.0
        for v,s in zip(vals,sig):
            if v==0 and s>0: raise ValueError("product uncertainty with zero-valued uncertain input is undefined for relative first-order propagation")
            if v!=0: rel += (s/v)**2
        variance=(abs(result)*math.sqrt(rel))**2
    else:
        if len(vals)!=2: raise ValueError("ratio requires exactly two measurements")
        if vals[1]==0: raise ValueError("ratio denominator must be non-zero")
        result=vals[0]/vals[1]; rel=(sig[0]/vals[0])**2 if vals[0]!=0 else 0.0; rel += (sig[1]/vals[1])**2
        variance=(abs(result)*math.sqrt(rel))**2; weights=[]
    out={"ok":True,"schema":UNCERTAINTY_SCHEMA,"version":VERSION,"operation":op,"result":result,"stddev":math.sqrt(max(0.0,variance)),"variance":variance,"outputUnit":request.outputUnit,"inputs":[m.model_dump() for m in request.measurements],"weights":weights,"assumptions":{"independentInputs":True,"firstOrderPropagation":True,"distributionShapeNotInferred":True},"calculated_by_workbench":True,"calculated_by_core":False}
    out["resultHash"]=content_hash(out); return out


def execute_hypothesis_metrics(request: HypothesisMetricsRequest) -> Dict[str, Any]:
    obs=[_finite(x,"observation") for x in request.observations]
    std=[]
    if request.observationStddev:
        if len(request.observationStddev)!=len(obs): raise ValueError("observationStddev must be empty or match observations length")
        std=[_finite(x,"observationStddev") for x in request.observationStddev]
        if any(x<0 for x in std): raise ValueError("observationStddev values must be >= 0")
    rows=[]
    for h in request.hypotheses:
        pred=[_finite(x,"prediction") for x in h.predictions]
        if len(pred)!=len(obs): raise ValueError("every hypothesis prediction vector must match observations length")
        residuals=[p-o for p,o in zip(pred,obs)]; absres=[abs(x) for x in residuals]
        row={"hypothesisRef":h.hypothesisRef,"sampleCount":len(obs),"mae":statistics.fmean(absres),"rmse":math.sqrt(statistics.fmean(x*x for x in residuals)),"maxAbsoluteResidual":max(absres),"residuals":residuals}
        if std:
            normalized=[r/s if s>0 else None for r,s in zip(residuals,std)]
            finite_norm=[x for x in normalized if x is not None]
            row["normalizedResiduals"]=normalized; row["meanAbsoluteNormalizedResidual"]=statistics.fmean(abs(x) for x in finite_norm) if finite_norm else None
        rows.append(row)
    out={"ok":True,"schema":HYPOTHESIS_SCHEMA,"version":VERSION,"observations":obs,"metrics":rows,"descriptive_only":True,"ranked":False,"probabilities_assigned":False,"winner":None,"verdict":None,"truth_determination":False,"calculated_by_workbench":True,"calculated_by_core":False}
    out["resultHash"]=content_hash(out); return out


def _require_result(result: Dict[str,Any]) -> Dict[str,Any]:
    accepted={TRAJECTORY_SCHEMA,TEMPORAL_SCHEMA,UNCERTAINTY_SCHEMA,HYPOTHESIS_SCHEMA}
    if result.get("schema") not in accepted: raise ValueError("result schema is not a Workbench v6.11 forensic reconstruction result")
    if not result.get("resultHash"): raise ValueError("resultHash is required")
    return result


def build_result_binding_plan(request: ResultBindingPlanRequest) -> Dict[str,Any]:
    r=_require_result(dict(request.result)); external=_bounded(request.externalResultRef,1000) or f"workbench:forensic-result:{r['resultHash']}"
    data={"result_key":_bounded(request.resultKey,180) or "workbench-result","result_kind":_bounded(request.resultKind,180) or "quantitative-reconstruction-result","external_result_ref":external,"output_manifest":r,"metrics":{"schema":r.get("schema"),"result_hash":r.get("resultHash"),"descriptive_only":r.get("descriptive_only",True)},"content_hash":r.get("resultHash"),"hash_algorithm":"sha256","evidence_item_id":_bounded(request.evidenceItemId,256) or None,"produced_at":_bounded(request.producedAt,128) or None,"provenance":{"source_product":"workbench","workbench_version":VERSION,"bridge_ref":BRIDGE_REF,"reconstruction_id":request.reconstructionId},"metadata":dict(request.metadata)}
    path=CORE_PATHS["resultBindings"].format(investigation_id=request.investigationId,handoff_id=request.handoffId)
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"forensic-result-binding","coreForensicHandoffContract":CORE_FORENSIC_HANDOFF_CONTRACT,"coreRequest":_core_request(path,data,"bind-quantitative-result"),"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"truthPromotionAuthorized":False}
    out["planHash"]=content_hash(out);return out


def build_reproduction_package_plan(request: ReproductionPackagePlanRequest) -> Dict[str,Any]:
    r=_require_result(dict(request.result)); data={"package_key":_bounded(request.packageKey,180) or "workbench-reconstruction","created_by":_bounded(request.createdBy,180) or "workbench","provenance":{"source_product":"workbench","workbench_version":VERSION,"workbench_result_hash":r.get("resultHash"),**dict(request.provenance)},"metadata":{"workbench_result_schema":r.get("schema"),"workbench_result_hash":r.get("resultHash"),"specialist_execution_runtime":"workbench"}}
    path=CORE_PATHS["reproductionPackages"].format(investigation_id=request.investigationId,reconstruction_id=request.reconstructionId)
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"forensic-reproduction-package","coreForensicReproductionPackageContract":CORE_FORENSIC_REPRODUCTION_PACKAGE_CONTRACT,"coreRequest":_core_request(path,data,"create-quantitative-reproduction-package"),"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"reproducibilityEqualsTruth":False}
    out["planHash"]=content_hash(out);return out


def build_lineage_plan(request: LineagePlanRequest) -> Dict[str,Any]:
    r=_require_result(dict(request.result)); workbench_ref=_bounded(request.workbenchExecutionRef,1000) or f"workbench:forensic-execution:{r['resultHash']}"
    execution={"executionKey":f"forensic-{r['resultHash'][:16]}","title":"Workbench forensic quantitative reconstruction","executionType":"forensic_reconstruction","runtimeKind":"workbench","status":"completed","visibility":"internal","projectRef":request.projectRef,"coreSessionId":request.coreSessionId,"workbenchExecutionRef":workbench_ref,"methodPlanRef":request.reconstructionRef,"provenance":{"sourceProduct":"workbench","workbenchVersion":VERSION,"workbenchResultHash":r['resultHash']},"metadata":{"forensicResultSchema":r['schema'],"reconstructionRef":request.reconstructionRef,"descriptiveOnly":r.get("descriptive_only",True)}}
    output={"outputKey":"forensic-result","outputType":"result_bundle","objectRef":f"workbench:forensic-result:{r['resultHash']}","contentHash":r['resultHash'],"schema":{"contract":r['schema']},"metadata":{"descriptiveOnly":r.get("descriptive_only",True)},"provenance":{"sourceProduct":"workbench"}}
    bindings=[{"bindingKey":f"evidence-{i+1}","targetType":"evidence","targetRef":ref,"sourceOutputRef":output["objectRef"],"relation":"basis_for","bindingRole":"forensic-quantitative-input"} for i,ref in enumerate(request.evidenceRefs)]
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"v670-lineage-handoff","coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"executionCreateRequest":execution,"postExecutionComponents":{"outputs":[output],"researchBindings":bindings,"verifications":[{"verificationKey":"boundary-check","verificationType":"forensic-boundary","status":"recorded","evidence":{"ranked":False,"probabilitiesAssigned":False,"truthDetermination":False},"performedBy":"workbench-v6.11.0"}]},"coreExecutionIdMustComeFromCore":True,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


@router.get("/integration/core/forensic-quantitative/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token); return forensic_manifest()

@router.post("/integration/core/forensic-quantitative/handoff/consume")
def handoff_consume(request: CoreHandoffConsumeRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return consume_core_handoff(request)
    except Exception as exc:raise _bad(exc)

@router.post("/forensics/reconstruction/trajectory")
def trajectory(request: TrajectoryReconstructionRequest) -> Dict[str,Any]:
    try:return execute_trajectory(request)
    except Exception as exc:raise _bad(exc)

@router.post("/forensics/reconstruction/temporal-comparison")
def temporal_comparison(request: TemporalComparisonRequest) -> Dict[str,Any]:
    try:return execute_temporal_comparison(request)
    except Exception as exc:raise _bad(exc)

@router.post("/forensics/reconstruction/uncertainty")
def uncertainty(request: UncertaintyPropagationRequest) -> Dict[str,Any]:
    try:return execute_uncertainty(request)
    except Exception as exc:raise _bad(exc)

@router.post("/forensics/reconstruction/hypothesis-metrics")
def hypothesis_metrics(request: HypothesisMetricsRequest) -> Dict[str,Any]:
    try:return execute_hypothesis_metrics(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/forensic-quantitative/result/plan")
def result_plan(request: ResultBindingPlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_result_binding_plan(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/forensic-quantitative/reproduction/plan")
def reproduction_plan(request: ReproductionPackagePlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_reproduction_package_plan(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/forensic-quantitative/lineage/plan")
def lineage_plan(request: LineagePlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_lineage_plan(request)
    except Exception as exc:raise _bad(exc)

@router.get("/v6110/status")
def status() -> Dict[str,Any]:
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Forensic Quantitative Reconstruction Runtime","coreForensicQuantitativeContract":CORE_FORENSIC_QUANTITATIVE_CONTRACT,"coreForensicHandoffContract":CORE_FORENSIC_HANDOFF_CONTRACT,"coreForensicTimelineContract":CORE_FORENSIC_TIMELINE_CONTRACT,"coreForensicSpatialContract":CORE_FORENSIC_SPATIAL_CONTRACT,"trajectoryReconstruction":True,"temporalComparison":True,"uncertaintyPropagation":True,"descriptiveHypothesisMetrics":True,"v670LineageIntegration":True,"v680UncertaintyIntegration":True,"v690VisualCompatibility":True,"coreIssuedForensicIdsRequired":True,"automaticCoreDispatch":False,"automaticCorePersistence":False,"hypothesisRanking":False,"probabilityAssignment":False,"truthDetermination":False}
