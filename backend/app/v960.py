"""Workbench v9.6.0 — Scientific Results & Narrative Synthesis.

Reproducible, researcher-authored synthesis of Workbench statistical analyses,
uncertainty/sensitivity studies, model calibrations, analysis-board snapshots,
and publication/evidence handoff packages. The workspace preserves source hashes,
statement-to-source traceability, limitations, interpretation, and narrative text.

This is a synthesis and packaging layer, not an autonomous scientific author:
it does not invent findings, accept hypotheses, infer causality/significance,
resolve contradictions, publish, or dispatch governed objects to Platform Core.
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
from .v8100 import load_snapshot, list_snapshots
from .v8110 import load_package, list_packages
from .v930 import load_analysis, list_analyses
from .v940 import load_study, list_studies
from .v950 import load_calibration, list_calibrations

VERSION = APP_VERSION
SCHEMA = "sc-workbench-scientific-results-narrative-synthesis/1.0"
SYNTHESIS_SCHEMA = "sc-workbench-scientific-results-synthesis/1.0"
CATALOG_SCHEMA = "sc-workbench-scientific-results-source-catalog/1.0"
PUBLICATION_PLAN_SCHEMA = "sc-workbench-scientific-results-publication-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-scientific-results-core-plan/1.0"
router = APIRouter(tags=["workbench-v960-scientific-results-narrative-synthesis"])

StatementKind = Literal["result", "interpretation", "limitation", "conclusion", "context"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _synthesis_dir(project_key: str) -> Path:
    return _store_root() / "scientific-results-syntheses" / _stable_id(project_key)


def _synthesis_path(project_key: str, synthesis_hash: str) -> Path:
    return _synthesis_dir(project_key) / f"{synthesis_hash}.json"


class NarrativeStatement(BaseModel):
    statementKey: str = Field(min_length=1, max_length=160)
    kind: StatementKind = "result"
    statement: str = Field(min_length=1, max_length=12000)
    sourceRefs: List[str] = Field(default_factory=list, max_length=100)
    evidenceRefs: List[str] = Field(default_factory=list, max_length=100)
    qualification: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.statementKey = self.statementKey.strip()
        self.statement = self.statement.strip()
        self.sourceRefs = list(dict.fromkeys(x.strip() for x in self.sourceRefs if x.strip()))
        self.evidenceRefs = list(dict.fromkeys(x.strip() for x in self.evidenceRefs if x.strip()))
        self.qualification = self.qualification.strip()
        return self


class ScientificResultsSynthesisRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    synthesisKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    statisticalAnalysisHashes: List[str] = Field(default_factory=list, max_length=100)
    uncertaintyStudyHashes: List[str] = Field(default_factory=list, max_length=100)
    calibrationHashes: List[str] = Field(default_factory=list, max_length=100)
    analysisSnapshotHashes: List[str] = Field(default_factory=list, max_length=50)
    publicationPackageHashes: List[str] = Field(default_factory=list, max_length=50)
    statements: List[NarrativeStatement] = Field(default_factory=list, max_length=300)
    abstract: str = Field(default="", max_length=12000)
    methodsNarrative: str = Field(default="", max_length=24000)
    resultsNarrative: str = Field(default="", max_length=30000)
    interpretation: str = Field(default="", max_length=24000)
    limitations: List[str] = Field(default_factory=list, max_length=200)
    conclusion: str = Field(default="", max_length=12000)
    assumptions: List[str] = Field(default_factory=list, max_length=200)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def validate_request(self):
        self.projectKey = self.projectKey.strip(); self.synthesisKey = self.synthesisKey.strip(); self.title = self.title.strip()
        self.statisticalAnalysisHashes = list(dict.fromkeys(x.strip() for x in self.statisticalAnalysisHashes if x.strip()))
        self.uncertaintyStudyHashes = list(dict.fromkeys(x.strip() for x in self.uncertaintyStudyHashes if x.strip()))
        self.calibrationHashes = list(dict.fromkeys(x.strip() for x in self.calibrationHashes if x.strip()))
        self.analysisSnapshotHashes = list(dict.fromkeys(x.strip() for x in self.analysisSnapshotHashes if x.strip()))
        self.publicationPackageHashes = list(dict.fromkeys(x.strip() for x in self.publicationPackageHashes if x.strip()))
        keys = [s.statementKey for s in self.statements]
        if len(keys) != len(set(keys)):
            raise ValueError("statementKey values must be unique")
        return self


class SaveSynthesisRequest(ScientificResultsSynthesisRequest):
    createdBy: str = Field(default="workbench", max_length=160)
    recordLabel: str = Field(default="Scientific results synthesis", max_length=500)


class PublicationPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    synthesisHash: str = Field(min_length=64, max_length=64)
    includePublicationHandoff: bool = True
    includeKnowledgeLibrary: bool = True
    createdBy: str = Field(default="workbench", max_length=160)


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    synthesisHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "release": "Scientific Results & Narrative Synthesis",
        "product": PRODUCT_KEY, "runtime": RUNTIME_KIND,
        "capabilities": {
            "researcherAuthoredNarrative": True,
            "statisticalAnalysisBinding": True,
            "uncertaintySensitivityBinding": True,
            "modelCalibrationBinding": True,
            "analysisSnapshotBinding": True,
            "publicationPackageBinding": True,
            "statementSourceTraceability": True,
            "evidenceReferencePreservation": True,
            "limitationsAndAssumptionsPreservation": True,
            "contentAddressedSynthesisRecords": True,
            "publicationPlanning": True,
            "platformCoreSynthesisPlanning": True,
        },
        "boundaries": {
            "automaticNarrativeGeneration": False,
            "automaticFindingGeneration": False,
            "automaticHypothesisAcceptance": False,
            "automaticSignificanceDecision": False,
            "automaticCausalInference": False,
            "automaticContradictionResolution": False,
            "automaticPublication": False,
            "automaticCoreDispatch": False,
            "governedClaimObjectCreated": False,
            "platformCoreGovernanceReplaced": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _resolve_sources(req: ScientificResultsSynthesisRequest) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    load_project(req.projectKey)
    sources: list[dict[str, Any]] = []
    by_ref: dict[str, dict[str, Any]] = {}

    def add(kind: str, h: str, obj: Dict[str, Any], canonical_ref: str | None = None):
        alias = f"{kind}:{h}"
        ref = canonical_ref or str(obj.get(f"{kind}Ref") or obj.get("analysisRef") or obj.get("studyRef") or obj.get("calibrationRef") or obj.get("snapshotRef") or obj.get("packageRef") or alias)
        row = {"sourceRef": alias, "sourceType": kind, "sourceHash": h, "canonicalRef": ref, "schema": obj.get("schema"), "version": obj.get("version"), "recordHash": obj.get("recordHash")}
        sources.append(row); by_ref[alias] = row; by_ref[ref] = row

    for h in req.statisticalAnalysisHashes:
        obj = load_analysis(req.projectKey, h); add("analysis", h, obj, obj.get("analysisRef"))
    for h in req.uncertaintyStudyHashes:
        obj = load_study(req.projectKey, h); add("uncertainty", h, obj, obj.get("studyRef"))
    for h in req.calibrationHashes:
        obj = load_calibration(req.projectKey, h); add("calibration", h, obj, obj.get("calibrationRef"))
    for h in req.analysisSnapshotHashes:
        obj = load_snapshot(req.projectKey, h); add("snapshot", h, obj, obj.get("snapshotRef"))
    for h in req.publicationPackageHashes:
        obj = load_package(req.projectKey, h); add("publication", h, obj, obj.get("packageRef"))
    return sources, by_ref


def compose_synthesis(req: ScientificResultsSynthesisRequest) -> Dict[str, Any]:
    sources, by_ref = _resolve_sources(req)
    traceability = []
    supported = 0
    unresolved_total = 0
    for st in req.statements:
        resolved = [r for r in st.sourceRefs if r in by_ref]
        unresolved = [r for r in st.sourceRefs if r not in by_ref]
        if resolved: supported += 1
        unresolved_total += len(unresolved)
        traceability.append({
            "statementKey": st.statementKey, "kind": st.kind,
            "resolvedSourceRefs": resolved, "unresolvedSourceRefs": unresolved,
            "evidenceRefs": st.evidenceRefs,
            "sourceSupported": bool(resolved),
            "scientificValidityInferred": False,
        })
    source_manifest_hash = content_hash(sources)
    statement_count = len(req.statements)
    readiness = {
        "sourceCount": len(sources),
        "statementCount": statement_count,
        "sourceSupportedStatementCount": supported,
        "unsupportedStatementCount": statement_count - supported,
        "unresolvedSourceReferenceCount": unresolved_total,
        "traceabilityCoverage": 1.0 if statement_count == 0 else supported / statement_count,
        "narrativePresent": any([req.abstract, req.methodsNarrative, req.resultsNarrative, req.interpretation, req.conclusion]),
        "readyForResearcherReview": bool(sources) and bool(req.resultsNarrative or req.statements),
        "readyDoesNotMeanScientificallyValid": True,
    }
    seed = {
        "projectKey": req.projectKey, "synthesisKey": req.synthesisKey, "title": req.title,
        "sourceManifestHash": source_manifest_hash, "sources": sources,
        "statements": [s.model_dump() for s in req.statements], "traceability": traceability,
        "abstract": req.abstract, "methodsNarrative": req.methodsNarrative,
        "resultsNarrative": req.resultsNarrative, "interpretation": req.interpretation,
        "limitations": req.limitations, "conclusion": req.conclusion,
        "assumptions": req.assumptions, "notes": req.notes, "readiness": readiness,
    }
    synthesis_hash = content_hash(seed)
    return {
        "ok": True, "schema": SYNTHESIS_SCHEMA, "version": VERSION,
        **seed,
        "synthesisHash": synthesis_hash,
        "synthesisRef": f"sc://workbench/scientific-results-syntheses/{req.projectKey}/{synthesis_hash}",
        "researcherAuthored": True,
        "provenance": {"sourceManifestHash": source_manifest_hash, "sourceHashes": [x["sourceHash"] for x in sources]},
        "boundaries": manifest()["boundaries"],
    }


def _record_hash(rec: Dict[str, Any]) -> str:
    return content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})


def save_synthesis(req: SaveSynthesisRequest) -> Dict[str, Any]:
    base_fields = set(ScientificResultsSynthesisRequest.model_fields)
    out = compose_synthesis(ScientificResultsSynthesisRequest(**req.model_dump(include=base_fields)))
    rec = {**out, "createdBy": req.createdBy, "recordLabel": req.recordLabel, "createdAt": _now()}
    rec["recordHash"] = _record_hash(rec)
    path = _synthesis_path(req.projectKey, rec["synthesisHash"]); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = _json_read(path)
        if old.get("recordHash") != rec["recordHash"]:
            raise ValueError("existing synthesis hash collision or record mismatch")
        old["idempotent"] = True; return old
    _atomic_json_write(path, rec); rec["idempotent"] = False; return rec


def load_synthesis(project_key: str, synthesis_hash: str) -> Dict[str, Any]:
    load_project(project_key); path = _synthesis_path(project_key, synthesis_hash)
    if not path.exists(): raise FileNotFoundError("scientific results synthesis not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("synthesisHash") != synthesis_hash:
        raise ValueError("scientific results synthesis identity mismatch")
    if rec.get("recordHash") != _record_hash(rec):
        raise ValueError("scientific results synthesis failed integrity validation")
    return rec


def list_syntheses(project_key: str) -> Dict[str, Any]:
    load_project(project_key); rows=[]; root=_synthesis_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_json_read(p)
                if r.get("projectKey")==project_key:
                    rows.append({k:r.get(k) for k in ("synthesisHash","synthesisRef","synthesisKey","title","createdBy","createdAt","recordHash")})
            except Exception: pass
    rows.sort(key=lambda x:str(x.get("createdAt") or ""), reverse=True)
    return {"ok":True,"schema":SYNTHESIS_SCHEMA,"version":VERSION,"projectKey":project_key,"synthesisCount":len(rows),"syntheses":rows}


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    a=list_analyses(project_key); u=list_studies(project_key); c=list_calibrations(project_key); s=list_snapshots(project_key); p=list_packages(project_key); y=list_syntheses(project_key)
    out={"ok":True,"schema":CATALOG_SCHEMA,"version":VERSION,"projectKey":project_key,
         "statisticalAnalysisCount":a.get("analysisCount",0),"statisticalAnalyses":a.get("analyses",[]),
         "uncertaintyStudyCount":u.get("studyCount",0),"uncertaintyStudies":u.get("studies",[]),
         "calibrationCount":c.get("calibrationCount",0),"calibrations":c.get("calibrations",[]),
         "analysisSnapshotCount":s.get("snapshotCount",0),"analysisSnapshots":s.get("snapshots",[]),
         "publicationPackageCount":p.get("packageCount",0),"publicationPackages":p.get("packages",[]),
         "synthesisCount":y.get("synthesisCount",0),"syntheses":y.get("syntheses",[]),
         "boundaries":{"catalogGeneratesNarrative":False,"catalogInfersScientificValidity":False,"catalogPublishes":False}}
    out["catalogHash"]=content_hash(out); return out


def publication_plan(req: PublicationPlanRequest) -> Dict[str, Any]:
    rec=load_synthesis(req.projectKey,req.synthesisHash); planned=[]
    if req.includePublicationHandoff: planned.append({"target":"research-publication-evidence-handoff","purpose":"prepare-researcher-reviewed-publication-package","automaticDispatch":False})
    if req.includeKnowledgeLibrary: planned.append({"target":"knowledge-library","purpose":"publish-reviewable-synthesis-and-provenance","automaticDispatch":False})
    out={"ok":True,"schema":PUBLICATION_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"synthesisHash":req.synthesisHash,"synthesisRef":rec.get("synthesisRef"),"createdBy":req.createdBy,"plannedHandoffs":planned,"boundaries":{"automaticPublication":False,"automaticPublicationDispatch":False,"researcherReviewRequired":True,"scientificValidityInferred":False}}
    out["planHash"]=content_hash(out); return out


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    rec=load_synthesis(req.projectKey,req.synthesisHash); cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"synthesisHash":req.synthesisHash,"synthesisRef":rec.get("synthesisRef"),"coreProjectEntityId":req.coreProjectEntityId or req.projectKey,"coreSessionId":req.coreSessionId,"visibility":req.visibility,"createdBy":req.createdBy,"coreEnabled":bool(cfg.get("enabled")),"coreTarget":cfg.get("baseUrl") or "","bindingPlan":{"objectType":"workbench.scientific-results-synthesis","objectRef":rec.get("synthesisRef"),"objectHash":req.synthesisHash,"sourceManifestHash":rec.get("sourceManifestHash"),"role":"researcher-authored-scientific-results-synthesis"},"boundaries":{"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreGovernanceAuthorityPreserved":True,"governedClaimObjectsCreated":False,"scientificValidityInferred":False}}
    out["planHash"]=content_hash(out); return out


def _wrap(fn,*args):
    try: return fn(*args)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc


@router.get("/results-synthesis/manifest")
def route_manifest(): return manifest()
@router.get("/results-synthesis/source-catalog/{project_key}")
def route_catalog(project_key:str): return _wrap(source_catalog,project_key)
@router.post("/results-synthesis/compose")
def route_compose(req:ScientificResultsSynthesisRequest): return _wrap(compose_synthesis,req)
@router.post("/results-synthesis/syntheses")
def route_save(req:SaveSynthesisRequest): return _wrap(save_synthesis,req)
@router.get("/results-synthesis/syntheses/{project_key}")
def route_list(project_key:str): return _wrap(list_syntheses,project_key)
@router.get("/results-synthesis/syntheses/{project_key}/{synthesis_hash}")
def route_get(project_key:str,synthesis_hash:str): return _wrap(load_synthesis,project_key,synthesis_hash)
@router.post("/results-synthesis/publication-plan")
def route_publication(req:PublicationPlanRequest): return _wrap(publication_plan,req)
@router.post("/integration/core/results-synthesis/plan")
def route_core(req:CorePlanRequest): return _wrap(core_plan,req)
@router.get("/v960/status")
def status():
    m=manifest(); return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":m["release"],"scientificResultsNarrativeSynthesis":True,"researcherAuthoredNarrative":True,"statementSourceTraceability":True,"automaticNarrativeGeneration":False,"automaticScientificValidityInference":False,"automaticPublication":False,"automaticCoreDispatch":False,"manifestHash":m["manifestHash"]}
