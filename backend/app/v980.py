"""Workbench v9.8.0 — Cross-Study Comparison & Meta-Analysis Workspace.

Researcher-controlled cross-study comparison and quantitative synthesis over explicit
study effect records. The workspace normalizes declared effect inputs, computes
fixed- and random-effects meta-analysis, heterogeneity diagnostics, subgroup pools,
leave-one-out sensitivity, pairwise effect differences, and renderer-neutral
visualization/Core handoff plans while preserving source lineage.

This layer does not decide whether studies are scientifically comparable, select a
preferred model, infer causality, declare significance as a scientific conclusion,
resolve publication bias, or create governed Platform Core claims automatically.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from scipy import stats

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v960 import load_synthesis, list_syntheses
from .v970 import load_workflow, list_workflows

VERSION = APP_VERSION
SCHEMA = "sc-workbench-cross-study-meta-analysis-workspace/1.0"
ANALYSIS_SCHEMA = "sc-workbench-cross-study-meta-analysis/1.0"
CATALOG_SCHEMA = "sc-workbench-cross-study-source-catalog/1.0"
VISUALIZATION_PLAN_SCHEMA = "sc-workbench-cross-study-meta-visualization-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-cross-study-meta-core-plan/1.0"
router = APIRouter(tags=["workbench-v980-cross-study-meta-analysis-workspace"])

EffectMeasure = Literal[
    "generic", "mean-difference", "standardized-mean-difference",
    "log-odds-ratio", "log-risk-ratio", "fisher-z-correlation",
]
InputScale = Literal["effect", "ratio", "correlation"]
MetaModel = Literal["fixed-effect", "random-effects"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _analysis_dir(project_key: str) -> Path:
    return _store_root() / "cross-study-meta-analyses" / _stable_id(project_key)


def _analysis_path(project_key: str, analysis_hash: str) -> Path:
    return _analysis_dir(project_key) / f"{analysis_hash}.json"


def _finite(value: Any) -> Optional[float]:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


class StudyEffectInput(BaseModel):
    studyKey: str = Field(min_length=1, max_length=160)
    label: str = Field(default="", max_length=500)
    sourceProjectKey: str = Field(default="", max_length=160)
    sourceSynthesisHash: str = Field(default="", max_length=64)
    sourceWorkflowHash: str = Field(default="", max_length=64)
    subgroup: str = Field(default="", max_length=160)
    inputScale: InputScale = "effect"
    effectValue: float
    standardError: Optional[float] = Field(default=None, gt=0)
    variance: Optional[float] = Field(default=None, gt=0)
    sampleSize: Optional[int] = Field(default=None, ge=2)
    unit: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_effect(self):
        self.studyKey = self.studyKey.strip()
        self.label = self.label.strip()
        self.sourceProjectKey = self.sourceProjectKey.strip()
        self.sourceSynthesisHash = self.sourceSynthesisHash.strip()
        self.sourceWorkflowHash = self.sourceWorkflowHash.strip()
        self.subgroup = self.subgroup.strip()
        if self.sourceSynthesisHash and len(self.sourceSynthesisHash) != 64:
            raise ValueError("sourceSynthesisHash must be a 64-character content hash")
        if self.sourceWorkflowHash and len(self.sourceWorkflowHash) != 64:
            raise ValueError("sourceWorkflowHash must be a 64-character content hash")
        if self.inputScale == "ratio" and self.effectValue <= 0:
            raise ValueError("ratio inputScale requires effectValue > 0")
        if self.inputScale == "correlation" and not (-1 < self.effectValue < 1):
            raise ValueError("correlation inputScale requires -1 < effectValue < 1")
        if self.standardError is None and self.variance is None:
            if not (self.inputScale == "correlation" and self.sampleSize and self.sampleSize > 3):
                raise ValueError("standardError or variance is required unless correlation sampleSize > 3")
        return self


class MetaAnalysisRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    analysisKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    researchQuestion: str = Field(default="", max_length=8000)
    effectMeasure: EffectMeasure = "generic"
    studies: List[StudyEffectInput] = Field(min_length=2, max_length=500)
    models: List[MetaModel] = Field(default_factory=lambda: ["fixed-effect", "random-effects"], min_length=1, max_length=2)
    confidenceLevel: float = Field(default=0.95, gt=0.5, lt=1.0)
    subgroupAnalysis: bool = True
    leaveOneOut: bool = True
    researcherInterpretation: str = Field(default="", max_length=16000)
    limitations: List[str] = Field(default_factory=list, max_length=200)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def validate_request(self):
        self.projectKey = self.projectKey.strip()
        self.analysisKey = self.analysisKey.strip()
        self.title = self.title.strip()
        keys = [x.studyKey for x in self.studies]
        if len(keys) != len(set(keys)):
            raise ValueError("studyKey values must be unique")
        self.models = list(dict.fromkeys(self.models))
        self.limitations = list(dict.fromkeys(x.strip() for x in self.limitations if x.strip()))
        if any(x.inputScale == "ratio" for x in self.studies) and self.effectMeasure not in {"log-odds-ratio", "log-risk-ratio"}:
            raise ValueError("ratio inputScale requires log-odds-ratio or log-risk-ratio effectMeasure")
        if any(x.inputScale == "correlation" for x in self.studies) and self.effectMeasure != "fisher-z-correlation":
            raise ValueError("correlation inputScale requires fisher-z-correlation effectMeasure")
        return self


class SaveMetaAnalysisRequest(MetaAnalysisRequest):
    createdBy: str = Field(default="workbench", max_length=160)
    recordLabel: str = Field(default="Cross-study meta-analysis", max_length=500)


class VisualizationPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    analysisHash: str = Field(min_length=64, max_length=64)
    includeForest: bool = True
    includeFunnel: bool = True
    includeSubgroups: bool = True
    includeLeaveOneOut: bool = True
    createdBy: str = Field(default="workbench", max_length=160)


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    analysisHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "release": "Cross-Study Comparison & Meta-Analysis Workspace",
        "product": PRODUCT_KEY, "runtime": RUNTIME_KIND,
        "effectMeasures": ["generic", "mean-difference", "standardized-mean-difference", "log-odds-ratio", "log-risk-ratio", "fisher-z-correlation"],
        "models": ["fixed-effect", "random-effects"],
        "capabilities": {
            "explicitStudyEffectRecords": True,
            "effectScaleNormalization": True,
            "inverseVarianceFixedEffect": True,
            "dersimonianLairdRandomEffects": True,
            "heterogeneityDiagnostics": True,
            "subgroupMetaAnalysis": True,
            "leaveOneOutSensitivity": True,
            "pairwiseStudyComparison": True,
            "contentAddressedMetaAnalysisRecords": True,
            "rendererNeutralVisualizationPlanning": True,
            "platformCoreMetaAnalysisPlanning": True,
        },
        "boundaries": {
            "automaticStudyComparabilityDecision": False,
            "automaticPreferredModelSelection": False,
            "automaticSignificanceConclusion": False,
            "automaticCausalInference": False,
            "automaticPublicationBiasConclusion": False,
            "automaticScientificValidityInference": False,
            "automaticResearchInterpretation": False,
            "automaticCoreDispatch": False,
            "governedCrossStudyClaimCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _source_binding(owner_project: str, study: StudyEffectInput) -> Dict[str, Any]:
    project = study.sourceProjectKey or owner_project
    binding: Dict[str, Any] = {"sourceProjectKey": project}
    if study.sourceSynthesisHash:
        syn = load_synthesis(project, study.sourceSynthesisHash)
        binding.update({
            "sourceSynthesisHash": study.sourceSynthesisHash,
            "sourceSynthesisRef": syn.get("synthesisRef"),
            "sourceSynthesisRecordHash": syn.get("recordHash"),
        })
    if study.sourceWorkflowHash:
        wf = load_workflow(project, study.sourceWorkflowHash)
        binding.update({
            "sourceWorkflowHash": study.sourceWorkflowHash,
            "sourceWorkflowRef": wf.get("workflowRef"),
            "sourceWorkflowRecordHash": wf.get("recordHash"),
        })
    return binding


def _normalize_study(owner_project: str, study: StudyEffectInput) -> Dict[str, Any]:
    raw = float(study.effectValue)
    if study.inputScale == "ratio":
        effect = math.log(raw)
        transform = "natural-log"
    elif study.inputScale == "correlation":
        effect = float(np.arctanh(raw))
        transform = "fisher-z"
    else:
        effect = raw
        transform = "identity"
    if study.standardError is not None:
        se = float(study.standardError)
    elif study.variance is not None:
        se = math.sqrt(float(study.variance))
    else:
        se = 1.0 / math.sqrt(float(study.sampleSize) - 3.0)
    variance = se * se
    return {
        "studyKey": study.studyKey,
        "label": study.label or study.studyKey,
        "subgroup": study.subgroup,
        "inputScale": study.inputScale,
        "rawEffectValue": raw,
        "normalizedEffect": effect,
        "standardError": se,
        "variance": variance,
        "sampleSize": study.sampleSize,
        "unit": study.unit,
        "normalizationTransform": transform,
        "notes": study.notes,
        "source": _source_binding(owner_project, study),
    }


def _back_transform(effect_measure: str, value: float) -> float:
    if effect_measure in {"log-odds-ratio", "log-risk-ratio"}:
        return math.exp(value)
    if effect_measure == "fisher-z-correlation":
        return math.tanh(value)
    return value


def _heterogeneity(studies: List[Dict[str, Any]]) -> Dict[str, Any]:
    y = np.asarray([x["normalizedEffect"] for x in studies], dtype=float)
    v = np.asarray([x["variance"] for x in studies], dtype=float)
    w = 1.0 / v
    sw = float(np.sum(w))
    fixed = float(np.sum(w * y) / sw)
    q = float(np.sum(w * np.square(y - fixed)))
    df = len(studies) - 1
    p = float(stats.chi2.sf(q, df)) if df > 0 else None
    c = sw - float(np.sum(np.square(w))) / sw
    tau2 = max(0.0, (q - df) / c) if df > 0 and c > 0 else 0.0
    i2 = max(0.0, (q - df) / q) * 100.0 if q > 0 and df > 0 else 0.0
    return {"q": q, "df": df, "pValue": p, "iSquaredPercent": i2, "tauSquaredDL": tau2}


def _pool(studies: List[Dict[str, Any]], model: str, confidence: float, effect_measure: str) -> Dict[str, Any]:
    if not studies:
        raise ValueError("at least one study is required")
    y = np.asarray([x["normalizedEffect"] for x in studies], dtype=float)
    v = np.asarray([x["variance"] for x in studies], dtype=float)
    hetero = _heterogeneity(studies)
    tau2 = float(hetero["tauSquaredDL"]) if model == "random-effects" else 0.0
    w = 1.0 / (v + tau2)
    sw = float(np.sum(w))
    estimate = float(np.sum(w * y) / sw)
    se = math.sqrt(1.0 / sw)
    zcrit = float(stats.norm.ppf(0.5 + confidence / 2.0))
    lo, hi = estimate - zcrit * se, estimate + zcrit * se
    normalized_weights = (w / sw) * 100.0
    out = {
        "model": model,
        "studyCount": len(studies),
        "estimate": estimate,
        "standardError": se,
        "confidenceLevel": confidence,
        "confidenceInterval": [float(lo), float(hi)],
        "naturalScaleEstimate": _back_transform(effect_measure, estimate),
        "naturalScaleConfidenceInterval": [_back_transform(effect_measure, lo), _back_transform(effect_measure, hi)],
        "tauSquared": tau2,
        "heterogeneity": hetero,
        "studyWeightsPercent": {s["studyKey"]: float(weight) for s, weight in zip(studies, normalized_weights)},
    }
    if model == "random-effects" and len(studies) > 1:
        pred_se = math.sqrt(tau2 + se * se)
        out["predictionInterval"] = [float(estimate - zcrit * pred_se), float(estimate + zcrit * pred_se)]
        out["naturalScalePredictionInterval"] = [_back_transform(effect_measure, out["predictionInterval"][0]), _back_transform(effect_measure, out["predictionInterval"][1])]
    return out


def _pairwise(studies: List[Dict[str, Any]], confidence: float) -> List[Dict[str, Any]]:
    zcrit = float(stats.norm.ppf(0.5 + confidence / 2.0))
    rows: List[Dict[str, Any]] = []
    for i in range(len(studies)):
        for j in range(i + 1, len(studies)):
            a, b = studies[i], studies[j]
            delta = float(a["normalizedEffect"] - b["normalizedEffect"])
            se = math.sqrt(float(a["variance"]) + float(b["variance"]))
            rows.append({
                "studyA": a["studyKey"], "studyB": b["studyKey"],
                "effectDifference": delta, "standardError": se,
                "confidenceInterval": [delta - zcrit * se, delta + zcrit * se],
                "scientificDifferenceInferred": False,
            })
    return rows


def analyze(req: MetaAnalysisRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    studies = [_normalize_study(req.projectKey, x) for x in req.studies]
    pooled = {model: _pool(studies, model, req.confidenceLevel, req.effectMeasure) for model in req.models}
    subgroups: Dict[str, Any] = {}
    if req.subgroupAnalysis:
        labels = sorted({x["subgroup"] for x in studies if x["subgroup"]})
        for label in labels:
            subset = [x for x in studies if x["subgroup"] == label]
            subgroups[label] = {
                "studyCount": len(subset),
                "models": {model: _pool(subset, model, req.confidenceLevel, req.effectMeasure) for model in req.models},
                "scientificSubgroupDifferenceInferred": False,
            }
    leave_one_out: List[Dict[str, Any]] = []
    if req.leaveOneOut and len(studies) >= 3:
        preferred_for_sensitivity = "random-effects" if "random-effects" in req.models else req.models[0]
        for omitted in studies:
            subset = [x for x in studies if x["studyKey"] != omitted["studyKey"]]
            leave_one_out.append({
                "omittedStudyKey": omitted["studyKey"],
                "model": preferred_for_sensitivity,
                "pooled": _pool(subset, preferred_for_sensitivity, req.confidenceLevel, req.effectMeasure),
                "influenceConclusionInferred": False,
            })
    source_manifest = [{
        "studyKey": x["studyKey"], "source": x["source"], "normalizationTransform": x["normalizationTransform"],
        "normalizedEffect": x["normalizedEffect"], "variance": x["variance"],
    } for x in studies]
    source_manifest_hash = content_hash(source_manifest)
    seed = {
        "projectKey": req.projectKey, "analysisKey": req.analysisKey, "title": req.title,
        "researchQuestion": req.researchQuestion, "effectMeasure": req.effectMeasure,
        "confidenceLevel": req.confidenceLevel, "requestedModels": req.models,
        "studies": studies, "pooledModels": pooled, "subgroups": subgroups,
        "leaveOneOut": leave_one_out, "pairwiseComparisons": _pairwise(studies, req.confidenceLevel),
        "researcherInterpretation": req.researcherInterpretation, "limitations": req.limitations,
        "notes": req.notes, "sourceManifestHash": source_manifest_hash,
    }
    analysis_hash = content_hash(seed)
    return {
        "ok": True, "schema": ANALYSIS_SCHEMA, "version": VERSION, **seed,
        "analysisHash": analysis_hash,
        "analysisRef": f"sc://workbench/cross-study-meta-analysis/{req.projectKey}/{analysis_hash}",
        "studyCount": len(studies),
        "researcherControlled": True,
        "boundaries": manifest()["boundaries"],
    }


def _record_hash(rec: Dict[str, Any]) -> str:
    return content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})


def save_analysis(req: SaveMetaAnalysisRequest) -> Dict[str, Any]:
    base_fields = set(MetaAnalysisRequest.model_fields)
    out = analyze(MetaAnalysisRequest(**req.model_dump(include=base_fields)))
    rec = {**out, "createdBy": req.createdBy, "recordLabel": req.recordLabel, "createdAt": _now()}
    rec["recordHash"] = _record_hash(rec)
    path = _analysis_path(req.projectKey, rec["analysisHash"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = _json_read(path)
        if old.get("recordHash") != rec["recordHash"]:
            raise ValueError("existing meta-analysis hash collision or record mismatch")
        old["idempotent"] = True
        return old
    _atomic_json_write(path, rec)
    rec["idempotent"] = False
    return rec


def load_analysis(project_key: str, analysis_hash: str) -> Dict[str, Any]:
    load_project(project_key)
    path = _analysis_path(project_key, analysis_hash)
    if not path.exists():
        raise FileNotFoundError("cross-study meta-analysis not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("analysisHash") != analysis_hash:
        raise ValueError("meta-analysis identity mismatch")
    if rec.get("recordHash") != _record_hash(rec):
        raise ValueError("meta-analysis failed integrity validation")
    return rec


def list_analyses(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    rows: List[Dict[str, Any]] = []
    root = _analysis_dir(project_key)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                r = _json_read(path)
                if r.get("projectKey") == project_key:
                    rows.append({k: r.get(k) for k in ("analysisHash", "analysisRef", "analysisKey", "title", "effectMeasure", "studyCount", "createdBy", "createdAt", "recordHash")})
            except Exception:
                pass
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return {"ok": True, "schema": ANALYSIS_SCHEMA, "version": VERSION, "projectKey": project_key, "analysisCount": len(rows), "analyses": rows}


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    syntheses = list_syntheses(project_key)
    workflows = list_workflows(project_key)
    analyses = list_analyses(project_key)
    out = {
        "ok": True, "schema": CATALOG_SCHEMA, "version": VERSION, "projectKey": project_key,
        "localSynthesisCount": syntheses.get("synthesisCount", 0), "localSyntheses": syntheses.get("syntheses", []),
        "localWorkflowCount": workflows.get("workflowCount", 0), "localWorkflows": workflows.get("workflows", []),
        "metaAnalysisCount": analyses.get("analysisCount", 0), "metaAnalyses": analyses.get("analyses", []),
        "explicitExternalStudyRecordsSupported": True,
        "boundaries": {"catalogInfersStudyComparability": False, "catalogInfersEvidenceQuality": False, "catalogExecutesAnalysis": False},
    }
    out["catalogHash"] = content_hash(out)
    return out


def visualization_plan(req: VisualizationPlanRequest) -> Dict[str, Any]:
    rec = load_analysis(req.projectKey, req.analysisHash)
    views: List[Dict[str, Any]] = []
    if req.includeForest:
        views.append({"viewKey": "forest", "kind": "forest-plot", "source": "studies+pooledModels", "rendererNeutral": True})
    if req.includeFunnel:
        views.append({"viewKey": "funnel", "kind": "funnel-diagnostic", "x": "normalizedEffect", "y": "standardError", "publicationBiasConclusionInferred": False})
    if req.includeSubgroups and rec.get("subgroups"):
        views.append({"viewKey": "subgroups", "kind": "subgroup-forest", "source": "subgroups", "subgroupDifferenceConclusionInferred": False})
    if req.includeLeaveOneOut and rec.get("leaveOneOut"):
        views.append({"viewKey": "leave-one-out", "kind": "influence-plot", "source": "leaveOneOut", "influenceConclusionInferred": False})
    out = {
        "ok": True, "schema": VISUALIZATION_PLAN_SCHEMA, "version": VERSION,
        "projectKey": req.projectKey, "analysisHash": req.analysisHash, "analysisRef": rec.get("analysisRef"),
        "views": views, "createdBy": req.createdBy,
        "boundaries": {"rendererInvoked": False, "publicationBiasConclusionInferred": False, "scientificInterpretationInferred": False},
    }
    out["planHash"] = content_hash(out)
    return out


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    rec = load_analysis(req.projectKey, req.analysisHash)
    cfg = core_config()
    binding = {
        "objectType": "workbench.cross-study-meta-analysis",
        "objectHash": req.analysisHash,
        "objectRef": rec.get("analysisRef"),
        "sourceManifestHash": rec.get("sourceManifestHash"),
        "coreProjectEntityId": req.coreProjectEntityId,
        "coreSessionId": req.coreSessionId,
        "visibility": req.visibility,
        "createdBy": req.createdBy,
    }
    out = {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
        "projectKey": req.projectKey, "analysisHash": req.analysisHash,
        "bindingPlan": binding,
        "core": {"enabled": bool(cfg.get("enabled")), "baseUrlConfigured": bool(cfg.get("baseUrl"))},
        "boundaries": {
            "automaticCoreDispatch": False, "governedCrossStudyClaimCreated": False,
            "scientificValidityInferred": False, "preferredMetaAnalysisModelSelected": False,
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


@router.get("/cross-study-meta/manifest")
def route_manifest(): return manifest()

@router.get("/cross-study-meta/source-catalog/{project_key}")
def route_catalog(project_key: str): return _wrap(source_catalog, project_key)

@router.post("/cross-study-meta/analyze")
def route_analyze(req: MetaAnalysisRequest): return _wrap(analyze, req)

@router.post("/cross-study-meta/meta-analyses")
def route_save(req: SaveMetaAnalysisRequest): return _wrap(save_analysis, req)

@router.get("/cross-study-meta/meta-analyses/{project_key}")
def route_list(project_key: str): return _wrap(list_analyses, project_key)

@router.get("/cross-study-meta/meta-analyses/{project_key}/{analysis_hash}")
def route_get(project_key: str, analysis_hash: str): return _wrap(load_analysis, project_key, analysis_hash)

@router.post("/cross-study-meta/visualization-plan")
def route_visualization(req: VisualizationPlanRequest): return _wrap(visualization_plan, req)

@router.post("/integration/core/cross-study-meta/plan")
def route_core(req: CorePlanRequest): return _wrap(core_plan, req)

@router.get("/v980/status")
def status():
    m = manifest()
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
        "crossStudyMetaAnalysisWorkspace": True, "fixedEffectMetaAnalysis": True,
        "randomEffectsMetaAnalysis": True, "heterogeneityDiagnostics": True,
        "subgroupMetaAnalysis": True, "leaveOneOutSensitivity": True,
        "automaticPreferredModelSelection": False, "automaticScientificValidityInference": False,
        "automaticCoreDispatch": False, "manifestHash": m["manifestHash"],
    }
