"""Workbench v8.9.0 — Interactive Scientific Figure & Visualization Composer.

Renderer-neutral, provenance-preserving scientific figure composition over completed
Workbench execution jobs. Researchers explicitly choose source jobs, metrics, marks,
axes, layout, labels, and annotations. The composer does not rewrite scientific
results, infer statistical significance, rank models, infer causality, or silently
choose scientific encodings. Platform Core integration remains explicit and plan-only.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project
from .v840 import _load_job, list_jobs
from .v880 import _flatten_numbers

VERSION = APP_VERSION
SCHEMA = "sc-workbench-interactive-scientific-figure-visualization-composer/1.0"
FIGURE_SCHEMA = "sc-workbench-scientific-figure-specification/1.0"
CATALOG_SCHEMA = "sc-workbench-scientific-figure-source-catalog/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-scientific-figure-core-plan/1.0"
MAX_JOBS = 20
MAX_PANELS = 12
MAX_SERIES = 8
MAX_CATALOG_JOBS = 100
router = APIRouter(tags=["workbench-v890-interactive-scientific-figure-visualization-composer"])

MarkKind = Literal["line", "scatter", "bar", "point", "table"]
MetricScope = Literal["request", "result"]
FigureTheme = Literal["light", "dark", "publication"]


class FigurePanelRequest(BaseModel):
    panelId: str = Field(min_length=1, max_length=80)
    title: str = Field(default="", max_length=300)
    mark: MarkKind = "line"
    metricScope: MetricScope = "result"
    xMetric: str = Field(default="", max_length=240)
    yMetrics: List[str] = Field(min_length=1, max_length=MAX_SERIES)
    jobIds: List[str] = Field(default_factory=list, max_length=MAX_JOBS)
    xLabel: str = Field(default="", max_length=160)
    yLabel: str = Field(default="", max_length=160)
    note: str = Field(default="", max_length=1000)
    showLegend: bool = True

    @model_validator(mode="after")
    def validate_panel(self):
        self.panelId = self.panelId.strip()
        self.yMetrics = [str(x).strip() for x in self.yMetrics if str(x).strip()]
        self.jobIds = [str(x).strip() for x in self.jobIds if str(x).strip()]
        if len(self.yMetrics) != len(set(self.yMetrics)):
            raise ValueError("yMetrics must be unique")
        if len(self.jobIds) != len(set(self.jobIds)):
            raise ValueError("panel jobIds must be unique")
        if self.mark == "scatter" and not self.xMetric.strip():
            raise ValueError("scatter panels require xMetric")
        return self


class FigureComposeRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    jobIds: List[str] = Field(min_length=1, max_length=MAX_JOBS)
    title: str = Field(default="Scientific figure", max_length=400)
    subtitle: str = Field(default="", max_length=800)
    caption: str = Field(default="", max_length=2000)
    panels: List[FigurePanelRequest] = Field(min_length=1, max_length=MAX_PANELS)
    columns: int = Field(default=1, ge=1, le=4)
    width: int = Field(default=1000, ge=320, le=4000)
    height: int = Field(default=700, ge=240, le=4000)
    theme: FigureTheme = "publication"
    linkedSelectionJobIds: List[str] = Field(default_factory=list, max_length=MAX_JOBS)
    baselineJobId: str = Field(default="", max_length=255)

    @model_validator(mode="after")
    def validate_figure(self):
        self.jobIds = [str(x).strip() for x in self.jobIds if str(x).strip()]
        self.linkedSelectionJobIds = [str(x).strip() for x in self.linkedSelectionJobIds if str(x).strip()]
        if len(self.jobIds) != len(set(self.jobIds)):
            raise ValueError("jobIds must be unique")
        if len(self.linkedSelectionJobIds) != len(set(self.linkedSelectionJobIds)):
            raise ValueError("linkedSelectionJobIds must be unique")
        if self.baselineJobId and self.baselineJobId not in self.jobIds:
            raise ValueError("baselineJobId must be included in jobIds")
        unknown_selection = set(self.linkedSelectionJobIds) - set(self.jobIds)
        if unknown_selection:
            raise ValueError("linkedSelectionJobIds must be included in jobIds")
        panel_ids = [p.panelId for p in self.panels]
        if len(panel_ids) != len(set(panel_ids)):
            raise ValueError("panelId values must be unique")
        for panel in self.panels:
            if panel.jobIds and not set(panel.jobIds).issubset(set(self.jobIds)):
                raise ValueError(f"panel {panel.panelId} jobIds must be included in figure jobIds")
        return self


class CoreFigurePlanRequest(FigureComposeRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def _metric_maps(job: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    return {
        "request": _flatten_numbers(job.get("request") or {}, "request"),
        "result": _flatten_numbers(job.get("result") or {}, "result"),
    }


def _load_completed_jobs(project_key: str, job_ids: List[str]) -> List[Dict[str, Any]]:
    load_project(project_key)
    jobs: List[Dict[str, Any]] = []
    for jid in job_ids:
        try:
            job = _load_job(jid)
        except FileNotFoundError as exc:
            raise FileNotFoundError(str(exc)) from exc
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if job.get("projectKey") != project_key:
            raise ValueError(f"job {jid} belongs to another project")
        if job.get("status") != "completed":
            raise RuntimeError(f"job {jid} is not completed")
        jobs.append(job)
    return jobs


def _source_record(job: Dict[str, Any]) -> Dict[str, Any]:
    metrics = _metric_maps(job)
    return {
        "jobId": job.get("jobId"),
        "label": job.get("label") or job.get("jobId"),
        "runtimeKind": job.get("runtimeKind"),
        "jobRevision": job.get("jobRevision"),
        "requestHash": job.get("requestHash"),
        "resultHash": job.get("resultHash"),
        "jobHash": job.get("jobHash"),
        "createdAt": job.get("createdAt"),
        "completedAt": job.get("completedAt"),
        "tags": job.get("tags") or [],
        "metrics": metrics,
        "requestMetricCount": len(metrics["request"]),
        "resultMetricCount": len(metrics["result"]),
    }


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    summary = list_jobs(project_key=project_key, status="completed")
    records: List[Dict[str, Any]] = []
    for row in (summary.get("jobs") or [])[:MAX_CATALOG_JOBS]:
        try:
            records.append(_source_record(_load_job(str(row.get("jobId") or ""))))
        except (FileNotFoundError, ValueError):
            continue
    request_keys = sorted(set().union(*(set(r["metrics"]["request"]) for r in records))) if records else []
    result_keys = sorted(set().union(*(set(r["metrics"]["result"]) for r in records))) if records else []
    out = {
        "ok": True,
        "schema": CATALOG_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "completedJobCount": len(records),
        "jobs": [
            {
                k: r[k]
                for k in (
                    "jobId", "label", "runtimeKind", "jobRevision", "requestHash", "resultHash",
                    "jobHash", "createdAt", "completedAt", "tags", "requestMetricCount", "resultMetricCount"
                )
            }
            for r in records
        ],
        "requestMetrics": [
            {"metric": key, "presentCount": sum(1 for r in records if key in r["metrics"]["request"])}
            for key in request_keys
        ],
        "resultMetrics": [
            {"metric": key, "presentCount": sum(1 for r in records if key in r["metrics"]["result"])}
            for key in result_keys
        ],
        "boundaries": {
            "catalogMutatesScientificObjects": False,
            "catalogInfersScientificValidity": False,
            "catalogSelectsPreferredMetrics": False,
        },
    }
    out["catalogHash"] = content_hash(out)
    return out


def _panel_spec(panel: FigurePanelRequest, records_by_id: Dict[str, Dict[str, Any]], default_job_ids: List[str], selected: set[str]) -> Dict[str, Any]:
    job_ids = panel.jobIds or default_job_ids
    rows: List[Dict[str, Any]] = []
    for index, jid in enumerate(job_ids):
        record = records_by_id[jid]
        scope = record["metrics"][panel.metricScope]
        row: Dict[str, Any] = {
            "jobId": jid,
            "label": record["label"],
            "runtimeKind": record["runtimeKind"],
            "jobOrder": index + 1,
            "selected": jid in selected,
        }
        if panel.xMetric:
            row["x"] = scope.get(panel.xMetric)
        else:
            row["x"] = index + 1
        for metric in panel.yMetrics:
            row[metric] = scope.get(metric)
        rows.append(row)

    scope_union = set().union(*(set(records_by_id[jid]["metrics"][panel.metricScope]) for jid in job_ids)) if job_ids else set()
    missing_metrics = [m for m in panel.yMetrics if m not in scope_union]
    if missing_metrics:
        raise ValueError(f"panel {panel.panelId} metrics not found in selected {panel.metricScope} sources: {', '.join(missing_metrics)}")
    if panel.xMetric and panel.xMetric not in scope_union:
        raise ValueError(f"panel {panel.panelId} xMetric not found in selected {panel.metricScope} sources: {panel.xMetric}")

    non_null_y = sum(1 for row in rows for metric in panel.yMetrics if row.get(metric) is not None)
    non_null_x = sum(1 for row in rows if row.get("x") is not None)
    return {
        "panelId": panel.panelId,
        "title": panel.title or panel.panelId,
        "mark": panel.mark,
        "metricScope": panel.metricScope,
        "sourceJobIds": job_ids,
        "encoding": {
            "x": {"field": panel.xMetric or "jobOrder", "label": panel.xLabel or (panel.xMetric or "Run order"), "explicit": bool(panel.xMetric)},
            "y": [{"field": metric, "label": metric} for metric in panel.yMetrics],
            "series": "jobId" if len(panel.yMetrics) == 1 else "metric",
            "selection": "jobId",
        },
        "showLegend": panel.showLegend,
        "yLabel": panel.yLabel,
        "note": panel.note,
        "rows": rows,
        "rowCount": len(rows),
        "nonNullXCount": non_null_x,
        "nonNullYValueCount": non_null_y,
        "incompleteRowsPresent": any(any(row.get(metric) is None for metric in panel.yMetrics) for row in rows),
        "scientificEncodingWasExplicitlyRequested": True,
        "automaticEncodingSelectionPerformed": False,
    }


def compose_figure(req: FigureComposeRequest) -> Dict[str, Any]:
    jobs = _load_completed_jobs(req.projectKey, req.jobIds)
    records = [_source_record(job) for job in jobs]
    by_id = {r["jobId"]: r for r in records}
    selected = set(req.linkedSelectionJobIds)
    panels = [_panel_spec(panel, by_id, req.jobIds, selected) for panel in req.panels]
    provenance = [
        {
            "jobId": r["jobId"],
            "jobRevision": r["jobRevision"],
            "runtimeKind": r["runtimeKind"],
            "requestHash": r["requestHash"],
            "resultHash": r["resultHash"],
            "jobHash": r["jobHash"],
        }
        for r in records
    ]
    out: Dict[str, Any] = {
        "ok": True,
        "schema": FIGURE_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "title": req.title,
        "subtitle": req.subtitle,
        "caption": req.caption,
        "theme": req.theme,
        "layout": {
            "columns": req.columns,
            "panelCount": len(panels),
            "width": req.width,
            "height": req.height,
            "responsive": True,
        },
        "sourceJobIds": req.jobIds,
        "baselineJobId": req.baselineJobId or None,
        "linkedSelection": {
            "jobIds": req.linkedSelectionJobIds,
            "selectionIsViewStateOnly": True,
        },
        "panels": panels,
        "rendererContract": {
            "contract": "sc.workbench.figure-renderer.v1",
            "rendererNeutral": True,
            "supportedMarks": list(MarkKind.__args__),
            "tooltip": True,
            "linkedSelection": True,
            "responsive": True,
        },
        "provenance": {
            "sourceType": "completed-workbench-execution-jobs",
            "jobs": provenance,
            "sourceHashesPreserved": True,
            "scientificPayloadsCopiedAsSourceOfTruth": False,
        },
        "exportPlan": {
            "json": {"available": True, "serverRendered": True, "source": "figure-specification"},
            "csv": {"available": True, "serverRendered": True, "scope": "panel-rows"},
            "svg": {"available": True, "serverRendered": False, "scope": "client-rendered-preview"},
            "png": {"available": False, "planned": True, "serverRendered": False},
            "pdf": {"available": False, "planned": True, "serverRendered": False},
        },
        "boundaries": {
            "figureIsScientificSourceOfTruth": False,
            "sourceJobsMutated": False,
            "sourceResultsMutated": False,
            "automaticScientificEncodingSelectionPerformed": False,
            "automaticWinnerSelectionPerformed": False,
            "scientificValidityInferred": False,
            "causalInferencePerformed": False,
            "statisticalSignificanceInferred": False,
            "automaticCoreDispatchPerformed": False,
        },
    }
    out["figureHash"] = content_hash(out)
    return out


def core_figure_plan(req: CoreFigurePlanRequest) -> Dict[str, Any]:
    compose_fields = {
        "projectKey", "jobIds", "title", "subtitle", "caption", "panels", "columns", "width", "height",
        "theme", "linkedSelectionJobIds", "baselineJobId"
    }
    figure = compose_figure(FigureComposeRequest(**req.model_dump(include=compose_fields)))
    project = load_project(req.projectKey)
    ws = project["workspace"]
    sid = str(req.coreSessionId or ws.get("coreSessionId") or "").strip()[:255]
    base = core_project_plan(ProjectCorePlanRequest(
        projectKey=req.projectKey,
        coreProjectEntityId=req.coreProjectEntityId or req.projectKey,
        coreSessionId=sid,
        visibility=req.visibility,
        createdBy=req.createdBy,
    ))
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "phase": base.get("phase"),
        "coreSessionId": sid or None,
        "coreSessionIdMustComeFromCore": True,
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "projectPlan": base,
        "figureHash": figure["figureHash"],
        "sourceJobIds": req.jobIds,
        "coreRequests": list(base.get("coreRequests") or []),
        "figureBindingIsAnalyticalViewOnly": True,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "automaticScientificEncodingSelectionAuthorized": False,
        "scientificValidityInferenceAuthorized": False,
    }
    if sid:
        out["coreRequests"].append({
            "path": CORE_PATHS["objectBindings"],
            "method": "POST",
            "phase": "scientific-figure-bind",
            "data": {
                "session_id": sid,
                "object_type": "workbench.scientific-figure-composition",
                "object_ref": f"sc://workbench/figures/{req.projectKey}/{figure['figureHash'][:24]}",
                "version_ref": f"sc://workbench/figures/{req.projectKey}@{VERSION}",
                "content_hash": figure["figureHash"],
                "role": "visual-analytical-view",
                "visibility": req.visibility,
                "metadata": {
                    "workbenchVersion": VERSION,
                    "projectKey": req.projectKey,
                    "sourceJobIds": req.jobIds,
                    "panelCount": len(req.panels),
                    "scientificSourceOfTruth": False,
                    "automaticEncodingSelection": False,
                },
            },
            "dispatchPerformed": False,
        })
    out["planHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Interactive Scientific Figure & Visualization Composer",
        "capabilities": {
            "completedRunDataBinding": True,
            "requestAndResultMetricCatalog": True,
            "multiPanelFigureComposition": True,
            "explicitScientificEncoding": True,
            "barLineScatterPointTableMarks": True,
            "linkedSelectionMetadata": True,
            "provenanceManifest": True,
            "deterministicFigureHash": True,
            "jsonCsvExportPlanning": True,
            "clientSvgPreviewContract": True,
            "coreFigurePlanning": True,
        },
        "authorities": {
            "projects": "v8.2",
            "executionsAndResults": "v8.4",
            "linkedViews": "v8.7",
            "comparativeMetrics": "v8.8",
        },
        "boundaries": {
            "figureIsScientificSourceOfTruth": False,
            "automaticScientificEncodingSelectionAuthorized": False,
            "automaticWinnerSelectionAuthorized": False,
            "scientificValidityInferenceAuthorized": False,
            "causalInferenceAuthorized": False,
            "statisticalSignificanceInferenceAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


@router.get("/figure-composer/manifest")
def manifest_route():
    return manifest()


@router.get("/figure-composer/source-catalog/{project_key}")
def source_catalog_route(project_key: str):
    try:
        return source_catalog(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/figure-composer/compose")
def compose_route(req: FigureComposeRequest):
    try:
        return compose_figure(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/integration/core/figure-composer/plan")
def core_plan_route(req: CoreFigurePlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_figure_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/v890/status")
def status_route():
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Interactive Scientific Figure & Visualization Composer",
        "multiPanelFigureComposition": True,
        "explicitScientificEncoding": True,
        "provenanceManifest": True,
        "clientSvgPreviewContract": True,
        "automaticScientificEncodingSelection": False,
        "scientificValidityInference": False,
        "automaticCoreDispatch": False,
    }
