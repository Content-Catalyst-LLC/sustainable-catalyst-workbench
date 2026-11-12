"""SC-FIG-01 / FIG-02A — default-disabled Plotly adapter for governed scientific figures.

Compiles either a v8.9 figure composition over completed Workbench execution jobs or an
explicitly authorized, hash-declared dataset into:

* an interactive Plotly figure specification (JSON only; no HTML, scripts or remote assets),
* an accessible data table and descriptive summary as the static/table alternative,
* an ``sc.figure-bundle.v1`` record with source, calculation, rendering and artifact hashes,
* optional PNG/SVG/PDF exports from an isolated, offline Kaleido/Chrome worker process.

The adapter is a renderer for existing Workbench results. It never mutates jobs, never fills
missing values, never infers uncertainty semantics, never pools series with different units,
measurement bases or durations into one connected trace, and never promotes modelled or
literature-derived values to observations. Review decisions are always emitted as pending.
Platform Core keeps ``contract.plotly`` as contract metadata; this module reports installed
runtime state separately and does not dispatch to Core.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import uncertainty_encodings as ue
from .release import APP_VERSION
from .v510 import content_hash
from .v890 import FigureComposeRequest, _load_completed_jobs, _source_record, compose_figure

VERSION = APP_VERSION
SCHEMA = "sc-workbench-plotly-figure-adapter/1.0"
BUILD_ID = "FIG-02A"
ADAPTER_ID = "workbench.plotly-figure-adapter"
CORE_RENDERER_KEY = "contract.plotly"
BUNDLE_SCHEMA = "sc.figure-bundle.v1"
RENDERING_PROFILE = "sc-institutional-research-v1"
PLOTLY_MEDIA_TYPE = "application/vnd.plotly.v1+json"
ENABLE_ENV = "SCWB_PLOTLY_ADAPTER_ENABLED"
EXPORT_ENV = "SCWB_PLOTLY_STATIC_EXPORT_ENABLED"
PINNED_PACKAGES = {"plotly": "6.5.2", "kaleido": "1.2.0"}
WORKER_PATH = Path(__file__).with_name("plotly_export_worker.py")
EXPORT_TIMEOUT_SECONDS = 90
MAX_EXPORT_BYTES = 10_000_000
MAX_DATASET_ROWS = 2000
MAX_TEXT = 400
STATIC_MAGIC = {"png": b"\x89PNG\r\n\x1a\n", "svg": b"<svg", "pdf": b"%PDF"}
# One headless Chrome export at a time per Workbench process; excess requests are refused, not queued.
_EXPORT_SLOT = threading.BoundedSemaphore(1)
STATIC_MEDIA = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}
# Okabe-Ito colour-blind-safe palette.
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
router = APIRouter(tags=["workbench-fig-02a-plotly-figure-adapter"])

ChartKind = Literal["line", "scatter", "bar", "time-series", "distribution", "heatmap", "band", "fan"]
# SC-FIG-05.3: panels drawn from a runtime band or ensemble-fan record (optionally over dataset observations).
UNCERTAINTY_CHARTS = {"band", "fan"}
UncertaintySemantics = Literal[
    "reported-plus-minus", "standard-deviation", "standard-error", "confidence-interval-95", "range-min-max"
]
EvidenceClass = Literal["observed", "literature-derived", "modelled", "hypothetical", "conceptual", "status-only"]
MeasurementStatus = Literal[
    "observed", "published-literature", "computed-from-specified-inputs", "hypothetical-only",
    "conceptual-only", "not-applicable",
]
EXPECTED_MEASUREMENT = {
    "observed": "observed",
    "literature-derived": "published-literature",
    "modelled": "computed-from-specified-inputs",
    "hypothetical": "hypothetical-only",
    "conceptual": "conceptual-only",
    "status-only": "not-applicable",
}
EVIDENCE_LABEL = {
    "observed": "Evidence: observed measurements from the cited sources",
    "literature-derived": "Evidence: published literature values; not measurements of this project",
    "modelled": "Evidence: modelled; computed from specified inputs, not measured",
    "hypothetical": "Evidence: hypothetical values only",
    "conceptual": "Evidence: conceptual illustration only",
    "status-only": "Evidence: status classification only; no quantities measured",
}
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_FIELD = re.compile(r"^[A-Za-z0-9_.\[\]-]{1,240}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ISO_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2}(T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:\d{2})?)?)?)?$")


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _text(value: str, limit: int = MAX_TEXT) -> str:
    """Escape user-supplied text so Plotly never interprets it as markup."""
    value = str(value or "")
    if _CONTROL.search(value):
        raise ValueError("control characters are not permitted in figure text")
    return html.escape(value.strip()[:limit], quote=True)


def _finite(value: Any, where: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where} must be a finite number or null")
    if not math.isfinite(float(value)):
        raise ValueError(f"{where} must be finite; NaN and infinity are rejected")
    return float(value)


class UncertaintyBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    semantics: UncertaintySemantics
    origin: Literal["as-published", "computed-by-workbench"]
    plusMinusField: str = Field(default="", max_length=240)
    lowerField: str = Field(default="", max_length=240)
    upperField: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def validate_shape(self):
        symmetric = bool(self.plusMinusField)
        bounded = bool(self.lowerField) and bool(self.upperField)
        if symmetric == bounded:
            raise ValueError("uncertainty requires exactly one of plusMinusField or lowerField+upperField")
        if self.semantics == "range-min-max" and not bounded:
            raise ValueError("range-min-max uncertainty requires lowerField and upperField")
        if self.semantics in {"reported-plus-minus", "standard-deviation", "standard-error"} and not symmetric:
            raise ValueError(f"{self.semantics} uncertainty requires plusMinusField")
        for name in (self.plusMinusField, self.lowerField, self.upperField):
            if name and not _FIELD.fullmatch(name):
                raise ValueError(f"invalid uncertainty field name: {name!r}")
        return self


class SeriesBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1, max_length=240)
    label: str = Field(default="", max_length=200)
    unit: str = Field(min_length=1, max_length=80)
    uncertainty: Optional[UncertaintyBinding] = None

    @model_validator(mode="after")
    def validate_field(self):
        if not _FIELD.fullmatch(self.field):
            raise ValueError(f"invalid series field name: {self.field!r}")
        return self


class PlotlyPanel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    panelId: str = Field(min_length=1, max_length=80)
    chart: ChartKind
    series: List[SeriesBinding] = Field(default_factory=list, max_length=8)
    xUnit: str = Field(default="", max_length=80)
    distributionKind: Literal["box", "histogram"] = "box"
    heatmapRowField: str = Field(default="", max_length=240)
    calculation: Optional[int] = Field(default=None, ge=0, le=7)

    @model_validator(mode="after")
    def validate_panel(self):
        if self.chart in UNCERTAINTY_CHARTS:
            if self.calculation is None:
                raise ValueError(f"{self.chart} panel {self.panelId} needs a calculation index")
        elif not self.series or self.calculation is not None:
            raise ValueError(f"panel {self.panelId} needs series and no calculation (calculations are for band and fan panels)")
        fields = [s.field for s in self.series]
        if len(fields) != len(set(fields)):
            raise ValueError(f"panel {self.panelId} series fields must be unique")
        if self.chart == "time-series" and not self.xUnit:
            raise ValueError(f"time-series panel {self.panelId} requires an explicit xUnit")
        return self


class AuthorizedDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    datasetId: str = Field(min_length=3, max_length=160)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidenceClass: EvidenceClass
    rows: List[Dict[str, Any]] = Field(min_length=1, max_length=MAX_DATASET_ROWS)
    xField: str = Field(min_length=1, max_length=240)
    xLabel: str = Field(default="", max_length=200)
    labelField: str = Field(default="", max_length=240)
    basisField: str = Field(default="", max_length=240)
    durationField: str = Field(default="", max_length=240)
    panelField: str = Field(default="", max_length=240)


class LinearFit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interceptKey: str = Field(min_length=1, max_length=120)
    slopeKey: str = Field(min_length=1, max_length=120)


class RuntimeUncertaintyInput(BaseModel):
    """SC-FIG-05.3: one verified Workspace run's exported values with its band or ensemble-fan record, passed through
    unchanged. Research binds the run itself; Workbench only checks and draws what the runtime computed."""
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=3, max_length=200)
    unit: str = Field(min_length=1, max_length=80)
    xLabel: str = Field(min_length=1, max_length=200)
    method: str = Field(min_length=3, max_length=300)
    runRef: str = Field(min_length=3, max_length=200)
    values: Dict[str, Any] = Field(min_length=1, max_length=256)
    bands: Optional[List[Dict[str, Any]]] = None
    quantileBands: Optional[Dict[str, Any]] = None
    linearFit: Optional[LinearFit] = None
    assumptions: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_record(self):
        if self.bands is not None and self.quantileBands is not None:
            raise ValueError("a calculation carries either bands or quantileBands, not both")
        if self.linearFit is not None and self.bands is None:
            raise ValueError("linearFit checks a band fit; this calculation has no bands")
        return self


class BundleSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceId: str = Field(min_length=1, max_length=240)
    provider: str = Field(min_length=1, max_length=240)
    sourceUri: str = Field(default="", max_length=600)
    doi: str = Field(default="", max_length=200)
    citationId: str = Field(default="", max_length=200)
    identityStatus: Literal["unverified", "source-identified", "source-hash-verified"]
    qualityStatus: Literal["pending", "qualified", "rejected", "not-applicable"]
    licenceStatus: Literal["pending", "verified-for-use", "restricted"]
    sha256: str = Field(default="", max_length=64)
    acquisitionDate: str = Field(default="", max_length=10)
    notes: str = Field(default="", max_length=1000)
    originalSourceVersion: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def validate_source(self):
        if self.sourceUri and not self.sourceUri.startswith("https://"):
            raise ValueError("sourceUri must be an https:// citation link; it is recorded, never fetched")
        if self.sha256 and not _HASH.fullmatch(self.sha256):
            raise ValueError("source sha256 must be 64 lowercase hex characters")
        if self.identityStatus == "source-hash-verified" and not self.sha256:
            raise ValueError("source-hash-verified sources require sha256")
        return self


class BundleMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    figureId: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{2,100}$")
    version: int = Field(default=1, ge=1)
    title: str = Field(min_length=5, max_length=220)
    projectRef: str = Field(min_length=1, max_length=200)
    ownerScope: Literal["isolated-synthetic", "unbound-local"]
    environment: Literal["staging", "local-review"]
    evidenceClass: EvidenceClass
    figureType: Literal["evidence-chart", "sensitivity-heatmap", "readiness-heatmap", "other"]
    interpretation: str = Field(min_length=8, max_length=2000)
    limitations: List[str] = Field(min_length=1, max_length=20)
    measurementStatus: MeasurementStatus
    temporalScope: str = Field(default="", max_length=400)
    claimIds: List[str] = Field(default_factory=list, max_length=50)
    doNotInfer: List[str] = Field(default_factory=list, max_length=20)
    caption: str = Field(min_length=15, max_length=2000)
    altText: str = Field(min_length=15, max_length=2000)
    palette: Literal["colorblind-safe", "monochrome"] = "colorblind-safe"
    sourceRefs: List[BundleSource] = Field(min_length=1, max_length=50)
    labels: List[str] = Field(default_factory=list, max_length=20)


class PlotlyCompileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workbenchFigure: Optional[FigureComposeRequest] = None
    dataset: Optional[AuthorizedDataset] = None
    panels: List[PlotlyPanel] = Field(min_length=1, max_length=12)
    bundle: BundleMetadata
    width: int = Field(default=1000, ge=320, le=4000)
    height: int = Field(default=640, ge=240, le=4000)
    staticFormats: List[Literal["png", "svg", "pdf"]] = Field(default_factory=list, max_length=3)
    calculations: List[RuntimeUncertaintyInput] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_source_choice(self):
        unc = [p for p in self.panels if p.chart in UNCERTAINTY_CHARTS]
        if self.workbenchFigure is not None and self.dataset is not None:
            raise ValueError("provide exactly one of workbenchFigure or dataset")
        if self.workbenchFigure is None and self.dataset is None:
            if not unc or len(unc) != len(self.panels) or any(p.series for p in unc):
                raise ValueError("provide exactly one of workbenchFigure or dataset (or only band/fan panels without series)")
        if unc and self.workbenchFigure is not None:
            raise ValueError("band and fan panels draw Workspace runtime records; they cannot be composed with workbenchFigure")
        for p in unc:
            if p.calculation >= len(self.calculations):
                raise ValueError(f"panel {p.panelId} calculation {p.calculation} is not in calculations")
            c = self.calculations[p.calculation]
            if (p.chart == "band" and c.quantileBands is not None) or (p.chart == "fan" and c.bands is not None):
                raise ValueError(f"panel {p.panelId} is a {p.chart} panel but its calculation carries the other record")
        if self.calculations and not unc:
            raise ValueError("calculations are drawn only by band or fan panels")
        if len(self.staticFormats) != len(set(self.staticFormats)):
            raise ValueError("staticFormats must be unique")
        ids = [p.panelId for p in self.panels]
        if len(ids) != len(set(ids)):
            raise ValueError("panelId values must be unique")
        return self


# ---------------------------------------------------------------------------
# Evidence and source gates
# ---------------------------------------------------------------------------

def _evidence_gate(req: PlotlyCompileRequest) -> None:
    b = req.bundle
    if EXPECTED_MEASUREMENT[b.evidenceClass] != b.measurementStatus:
        raise ValueError(
            f"evidenceClass {b.evidenceClass} requires measurementStatus {EXPECTED_MEASUREMENT[b.evidenceClass]}"
        )
    if req.calculations and b.evidenceClass != "modelled":
        raise ValueError("runtime bands and ensemble fans are model outputs and cannot be labelled " + b.evidenceClass)
    if req.workbenchFigure is not None and b.evidenceClass != "modelled":
        raise ValueError("completed Workbench computations are modelled results and cannot be labelled " + b.evidenceClass)
    if req.dataset is not None:
        if req.dataset.evidenceClass != b.evidenceClass:
            raise ValueError(
                f"dataset evidenceClass {req.dataset.evidenceClass} cannot be relabelled as {b.evidenceClass}"
            )
    restricted = [s.sourceId for s in b.sourceRefs if s.licenceStatus == "restricted"]
    if restricted:
        raise PermissionError("restricted sources cannot be rendered: " + ", ".join(restricted))
    pending = [s.sourceId for s in b.sourceRefs if s.licenceStatus == "pending"]
    if pending and b.environment != "local-review":
        raise PermissionError("sources with pending licence review may only render for local-review: " + ", ".join(pending))
    if b.evidenceClass == "observed":
        weak = [s.sourceId for s in b.sourceRefs
                if s.identityStatus != "source-hash-verified" or s.qualityStatus != "qualified"]
        if weak:
            raise ValueError("observed figures require source-hash-verified, qualified sources: " + ", ".join(weak))


def dataset_sha256(rows: List[Dict[str, Any]]) -> str:
    return content_hash(rows)


# ---------------------------------------------------------------------------
# Normalized panel tables
# ---------------------------------------------------------------------------

def _uncertainty_values(series: SeriesBinding, value: Optional[float], lookup, where: str) -> Dict[str, Any]:
    u = series.uncertainty
    if u is None:
        return {}
    if u.plusMinusField:
        pm = _finite(lookup(u.plusMinusField), f"{where} {u.plusMinusField}")
        if pm is not None and pm < 0:
            raise ValueError(f"{where} {u.plusMinusField} must be non-negative")
        lower = None if value is None or pm is None else value - pm
        upper = None if value is None or pm is None else value + pm
        return {"plusMinus": pm, "lower": lower, "upper": upper}
    lower = _finite(lookup(u.lowerField), f"{where} {u.lowerField}")
    upper = _finite(lookup(u.upperField), f"{where} {u.upperField}")
    if lower is not None and upper is not None and lower > upper:
        raise ValueError(f"{where} uncertainty lower bound exceeds upper bound")
    if value is not None and lower is not None and upper is not None and not lower <= value <= upper:
        raise ValueError(f"{where} value lies outside its declared uncertainty interval")
    return {"lower": lower, "upper": upper}


def _panels_from_workbench(req: PlotlyCompileRequest) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    spec = compose_figure(req.workbenchFigure)
    records = {r["jobId"]: r for r in (_source_record(j) for j in _load_completed_jobs(req.workbenchFigure.projectKey, req.workbenchFigure.jobIds))}
    by_panel = {p["panelId"]: p for p in spec["panels"]}
    tables = []
    for panel in req.panels:
        source_panel = by_panel.get(panel.panelId)
        if source_panel is None:
            raise ValueError(f"panel {panel.panelId} is not present in the Workbench figure composition")
        allowed = set(source_panel["encoding"]["y"][i]["field"] for i in range(len(source_panel["encoding"]["y"])))
        unknown = [s.field for s in panel.series if s.field not in allowed]
        if unknown:
            raise ValueError(f"panel {panel.panelId} series not composed by Workbench: {', '.join(unknown)}")
        scope = source_panel["metricScope"]
        rows = []
        for src in source_panel["rows"]:
            metrics = records[src["jobId"]]["metrics"][scope]
            row = {"label": src["label"], "x": src["x"], "jobId": src["jobId"], "values": {}, "uncertainty": {}}
            for s in panel.series:
                value = _finite(src.get(s.field), f"job {src['jobId']} {s.field}")
                row["values"][s.field] = value
                unc = _uncertainty_values(s, value, lambda f: _metric_or_missing(metrics, f, panel.panelId), f"job {src['jobId']}")
                if unc:
                    row["uncertainty"][s.field] = unc
            rows.append(row)
        tables.append({
            "panel": panel,
            "title": source_panel["title"],
            "xLabel": source_panel["encoding"]["x"]["label"],
            "xExplicit": source_panel["encoding"]["x"]["explicit"],
            "rows": rows,
        })
    calc_refs = [
        {"system": "workbench", "runRef": f"sc://workbench/jobs/{j['jobId']}@{j['jobRevision']}",
         "method": f"workbench-execution:{j['runtimeKind']}", "outputSha256": j["resultHash"]}
        for j in spec["provenance"]["jobs"]
    ]
    source = {
        "kind": "completed-workbench-execution-jobs",
        "figureSpecSchema": spec["schema"],
        "figureSpecHash": spec["figureHash"],
        "projectKey": spec["projectKey"],
        "jobs": spec["provenance"]["jobs"],
        "calculationRefs": calc_refs,
        "snapshotIds": [f"workbench-job:{j['jobId']}@{j['jobRevision']}:{j['jobHash']}" for j in spec["provenance"]["jobs"]],
        "inputManifestSha256": spec["figureHash"],
    }
    return tables, source


def _metric_or_missing(metrics: Dict[str, float], field: str, panel_id: str) -> Optional[float]:
    if field not in metrics:
        raise ValueError(f"panel {panel_id} uncertainty metric not present in source job: {field}")
    return metrics[field]


def _panels_from_dataset(req: PlotlyCompileRequest) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    ds = req.dataset
    actual = dataset_sha256(ds.rows)
    if actual != ds.sha256:
        raise PermissionError("dataset sha256 does not match the declared authorized dataset hash")
    for row in ds.rows:
        for key, value in row.items():
            if isinstance(value, str):
                if len(value) > MAX_TEXT:
                    raise ValueError(f"dataset text value for {key} exceeds {MAX_TEXT} characters")
                _text(value)
            elif value is not None:
                _finite(value, f"dataset field {key}")
    tables = []
    for panel in req.panels:
        if not panel.series:
            tables.append(_runtime_only_table(panel))
            continue
        rows_in = [r for r in ds.rows if not ds.panelField or r.get(ds.panelField) == panel.panelId]
        if not rows_in:
            raise ValueError(f"panel {panel.panelId} has no dataset rows")
        present = set().union(*(set(r) for r in rows_in))
        for s in panel.series:
            if s.field not in present:
                raise ValueError(f"panel {panel.panelId} series field not in dataset: {s.field}")
        if ds.basisField:
            bases = {r.get(ds.basisField) for r in rows_in}
            if len(bases) > 1:
                raise ValueError(
                    f"panel {panel.panelId} mixes measurement bases {sorted(map(str, bases))}; plot them in separate panels"
                )
        if ds.durationField and panel.chart in {"line", "time-series"}:
            durations = {r.get(ds.durationField) for r in rows_in}
            if len(durations) > 1:
                raise ValueError(
                    f"panel {panel.panelId} connects results with different durations; use scatter or bar panels"
                )
        rows = []
        for i, r in enumerate(rows_in):
            x = r.get(ds.xField)
            if panel.chart == "time-series" and not (isinstance(x, str) and _ISO_DATE.fullmatch(x)) and not isinstance(x, (int, float)):
                raise ValueError(f"panel {panel.panelId} time-series x values must be ISO dates or numbers")
            row = {
                "label": str(r.get(ds.labelField, "")) if ds.labelField else str(x),
                "x": x,
                "basis": r.get(ds.basisField) if ds.basisField else None,
                "duration": r.get(ds.durationField) if ds.durationField else None,
                "values": {},
                "uncertainty": {},
            }
            for s in panel.series:
                value = _finite(r.get(s.field), f"dataset row {i} {s.field}")
                row["values"][s.field] = value
                unc = _uncertainty_values(s, value, lambda f: _dataset_field(r, f, panel.panelId), f"dataset row {i}")
                if unc:
                    row["uncertainty"][s.field] = unc
            rows.append(row)
        tables.append({"panel": panel, "title": panel.panelId, "xLabel": ds.xLabel or ds.xField, "xExplicit": True, "rows": rows})
    source = {
        "kind": "authorized-dataset",
        "datasetId": ds.datasetId,
        "datasetSha256": actual,
        "calculationRefs": [],
        "snapshotIds": [f"dataset:{ds.datasetId}:{actual}"],
        "inputManifestSha256": actual,
    }
    return tables, source


def _runtime_only_table(panel: PlotlyPanel) -> Dict[str, Any]:
    return {"panel": panel, "title": panel.panelId, "xLabel": "", "xExplicit": True, "rows": []}


def _attach_uncertainty(tables: List[Dict[str, Any]], req: PlotlyCompileRequest) -> List[Dict[str, Any]]:
    """SC-FIG-05.3: check each band/fan panel's runtime record; a missing record is drawn as unavailable."""
    for table in tables:
        panel: PlotlyPanel = table["panel"]
        if panel.chart not in UNCERTAINTY_CHARTS:
            continue
        c = req.calculations[panel.calculation]
        at = f"panel {panel.panelId} calculation {panel.calculation}"
        record = c.bands if panel.chart == "band" else c.quantileBands
        if record is None:
            table["uncertainty"] = None
            table["unavailable"] = ("the Workspace run reported no " + ("confidence or prediction band" if panel.chart == "band"
                                    else "ensemble quantile fan") + " for this value; none is drawn or derived")
        elif panel.chart == "band":
            table["uncertainty"] = ue.check_bands(record, at, c.values, c.linearFit.model_dump() if c.linearFit else None)
        else:
            table["uncertainty"] = ue.check_fan(record, at)
        if c.assumptions is not None:
            a = c.assumptions
            if set(a) != {"declaredBy", "checked", "statements"} or a.get("declaredBy") != "model-revision" or a.get("checked") is not False \
                    or not isinstance(a.get("statements"), list) or not 0 < len(a["statements"]) <= 12:
                raise ValueError(f"{at}: assumptions must be the model revision's declared, unchecked statements")
        table.update(calc=c, unit=c.unit, xLabel=c.xLabel, title=c.label, recordSha256=content_hash(record) if record is not None else "")
    return tables


def _dataset_field(row: Dict[str, Any], field: str, panel_id: str) -> Any:
    if field not in row:
        raise ValueError(f"panel {panel_id} uncertainty field not in dataset row: {field}")
    return row[field]


# ---------------------------------------------------------------------------
# Plotly compilation
# ---------------------------------------------------------------------------

def _unit_check(table: Dict[str, Any]) -> str:
    units = {s.unit for s in table["panel"].series} | ({table["unit"]} if table.get("calc") else set())
    if len(units) != 1:
        raise ValueError(f"panel {table['panel'].panelId} mixes units {sorted(units)}; plot them in separate panels")
    return next(iter(units))


def _error_spec(series: SeriesBinding, rows: List[Dict[str, Any]], axis: str) -> Optional[Dict[str, Any]]:
    if series.uncertainty is None:
        return None
    plus, minus = [], []
    for row in rows:
        value = row["values"][series.field]
        unc = row["uncertainty"].get(series.field, {})
        lower, upper = unc.get("lower"), unc.get("upper")
        plus.append(None if value is None or upper is None else upper - value)
        minus.append(None if value is None or lower is None else value - lower)
    return {"type": "data", "symmetric": False, "array": plus, "arrayminus": minus, "visible": True}


def _hover(series: SeriesBinding, unit: str, has_duration: bool, has_basis: bool) -> str:
    parts = ["%{customdata[0]}", f"{_text(series.label or series.field)}: %{{y}} {_text(unit)}"]
    if series.uncertainty is not None:
        parts.append(f"uncertainty ({series.uncertainty.semantics}, {series.uncertainty.origin}): "
                     "%{customdata[1]} to %{customdata[2]}")
    if has_duration:
        parts.append("duration: %{customdata[3]}")
    if has_basis:
        parts.append("basis: %{customdata[4]}")
    return "<br>".join(parts) + "<extra></extra>"


def _customdata(series: SeriesBinding, rows: List[Dict[str, Any]]) -> List[List[Any]]:
    out = []
    for row in rows:
        unc = row["uncertainty"].get(series.field, {})
        out.append([
            _text(row["label"]),
            "not reported" if unc.get("lower") is None else unc["lower"],
            "not reported" if unc.get("upper") is None else unc["upper"],
            _text(str(row.get("duration") or "")),
            _text(str(row.get("basis") or "")),
        ])
    return out


def _category(row: Dict[str, Any], has_duration: bool) -> str:
    label = _text(row["x"])
    return f"{label}<br>({_text(str(row['duration']))})" if has_duration and row.get("duration") else label


def _traces(table: Dict[str, Any], axis_suffix: str, colours: List[str], offset: int = 0) -> List[Dict[str, Any]]:
    panel: PlotlyPanel = table["panel"]
    rows = table["rows"]
    unit = _unit_check(table)
    has_duration = any(r.get("duration") for r in rows)
    xs = [_category(r, has_duration) if isinstance(r["x"], str) else r["x"] for r in rows]
    has_basis = any(r.get("basis") for r in rows)
    axes = {"xaxis": "x" + axis_suffix, "yaxis": "y" + axis_suffix}
    traces: List[Dict[str, Any]] = []
    if panel.chart == "heatmap":
        row_labels = [_text(r["label"]) for r in rows]
        z = [[r["values"][s.field] for s in panel.series] for r in rows]
        traces.append({
            "type": "heatmap", **axes,
            "z": z, "x": [_text(s.label or s.field) for s in panel.series], "y": row_labels,
            "colorscale": "Viridis", "hoverongaps": False,
            "colorbar": {"title": {"text": _text(unit)}},
            "hovertemplate": "%{y} · %{x}: %{z} " + _text(unit) + "<extra></extra>",
        })
        return traces
    if panel.chart in UNCERTAINTY_CHARTS and table.get("uncertainty"):
        rec, label = table["uncertainty"], table["calc"].label
        sha = table["recordSha256"]
        traces.extend(ue.band_traces(rec, axes, unit, panel.panelId, label, sha) if rec["kind"] == "band"
                      else ue.fan_traces(rec, axes, unit, panel.panelId, label, sha))
    for i, s in enumerate(panel.series):
        colour = colours[(offset + i) % len(colours)]
        ys = [r["values"][s.field] for r in rows]
        name = _text(s.label or s.field)
        if s.uncertainty is not None:
            name += f" [{s.uncertainty.semantics}, {s.uncertainty.origin}]"
        if panel.chart == "distribution":
            values = [y for y in ys if y is not None]
            if panel.distributionKind == "histogram":
                traces.append({"type": "histogram", **axes, "x": values, "name": name,
                               "marker": {"color": colour}, "opacity": 0.75})
            else:
                traces.append({"type": "box", **axes, "y": values, "name": name, "boxpoints": "all",
                               "jitter": 0.3, "pointpos": 0, "marker": {"color": colour}})
            continue
        trace: Dict[str, Any] = {
            **axes, "x": xs, "y": ys, "name": name,
            "customdata": _customdata(s, rows),
            "hovertemplate": _hover(s, unit, has_duration, has_basis),
        }
        err = _error_spec(s, rows, "y")
        if err:
            trace["error_y"] = {**err, "color": colour, "thickness": 1.5, "width": 6}
        if panel.chart == "bar":
            trace.update({"type": "bar", "marker": {"color": colour}})
        elif panel.chart in {"scatter", "band", "fan"}:
            # band/fan panels draw their dataset series as observation markers over the runtime record.
            trace.update({"type": "scatter", "mode": "markers", "marker": {"color": colour, "size": 10}})
        else:
            # line and time-series: gaps stay gaps; values are never interpolated.
            trace.update({"type": "scatter", "mode": "lines+markers", "connectgaps": False,
                          "line": {"color": colour, "width": 2}, "marker": {"color": colour, "size": 7}})
        traces.append(trace)
    return traces


def compile_plotly(tables: List[Dict[str, Any]], req: PlotlyCompileRequest) -> Dict[str, Any]:
    colours = PALETTE if req.bundle.palette == "colorblind-safe" else ["#000000", "#555555", "#999999", "#333333"]
    n = len(tables)
    gap = 0.16 if n > 1 else 0.0
    height_each = (1.0 - gap * (n - 1)) / n
    layout: Dict[str, Any] = {
        "title": {"text": _text(req.bundle.title, 220) + "<br><sup>" + EVIDENCE_LABEL[req.bundle.evidenceClass] + "</sup>",
                  "x": 0.0, "xanchor": "left"},
        "width": req.width, "height": req.height,
        "font": {"family": "Arial, Helvetica, sans-serif", "size": 13, "color": "#1a1a1a"},
        "paper_bgcolor": "#ffffff", "plot_bgcolor": "#ffffff",
        "margin": {"l": 80, "r": 60, "t": 100, "b": 80},
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.18},
        "annotations": [],
    }
    data: List[Dict[str, Any]] = []
    for idx, table in enumerate(tables):
        suffix = "" if idx == 0 else str(idx + 1)
        top = 1.0 - idx * (height_each + gap)
        domain = [max(0.0, top - height_each), top]
        unit = _unit_check(table)
        panel: PlotlyPanel = table["panel"]
        x_title = _text(table["xLabel"]) + (f" ({_text(panel.xUnit)})" if panel.xUnit else "")
        y_title = _text(unit)
        xaxis: Dict[str, Any] = {"title": {"text": x_title if idx == n - 1 or n == 1 else ""}, "anchor": "y" + suffix,
                                 "automargin": True, "showline": True,
                                 "linecolor": "#333333", "ticks": "outside", "zeroline": False}
        yaxis: Dict[str, Any] = {"title": {"text": y_title}, "domain": domain, "anchor": "x" + suffix, "automargin": True,
                                 "showline": True, "linecolor": "#333333", "ticks": "outside",
                                 "gridcolor": "#e5e5e5", "zeroline": True, "zerolinecolor": "#999999"}
        if panel.chart == "time-series" and all(isinstance(r["x"], str) for r in table["rows"]):
            xaxis["type"] = "date"
        elif panel.chart in {"bar", "scatter"} and any(isinstance(r["x"], str) for r in table["rows"]):
            xaxis["type"] = "category"
        if panel.chart == "distribution":
            xaxis["title"] = {"text": y_title if panel.distributionKind == "histogram" else ""}
            yaxis["title"] = {"text": "count" if panel.distributionKind == "histogram" else y_title}
        layout["xaxis" + suffix] = xaxis
        layout["yaxis" + suffix] = yaxis
        layout["annotations"].append({
            "text": "<b>" + _text(table["title"]) + "</b>", "showarrow": False, "xref": "paper", "yref": "paper",
            "x": 0, "y": domain[1], "xanchor": "left", "yanchor": "bottom", "font": {"size": 13},
        })
        data.extend(_traces(table, suffix, colours, offset=sum(len(t["panel"].series) for t in tables[:idx])))
        if panel.chart in UNCERTAINTY_CHARTS and table.get("uncertainty") is None:
            layout["annotations"].append({
                "text": "Uncertainty unavailable: " + _text(table["unavailable"]), "showarrow": False,
                "xref": "x" + suffix + " domain", "yref": "y" + suffix + " domain", "x": 0.5, "y": 0.5,
                "font": {"size": 12, "color": "#1a1a1a"}, "bgcolor": "#f2f2f2", "bordercolor": "#555555", "borderwidth": 1,
            })
        if panel.chart in {"scatter", "bar"}:
            for row in table["rows"]:
                if isinstance(row["x"], str) and all(row["values"][s.field] is None for s in panel.series):
                    layout["annotations"].append({
                        "text": "no quantified value reported", "showarrow": False,
                        "xref": "x" + suffix, "yref": "y" + suffix + " domain",
                        "x": _category(row, any(r.get("duration") for r in table["rows"])), "y": 0.5,
                        "font": {"size": 11, "color": "#555555"}, "textangle": -90,
                    })
    figure = {"data": data, "layout": layout}
    _validate_with_plotly(figure)
    return figure


def _validate_with_plotly(figure: Dict[str, Any]) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError as exc:  # pragma: no cover - exercised through status
        raise RuntimeError("Plotly is not installed in this Workbench runtime") from exc
    go.Figure(figure, skip_invalid=False)


def plotly_config(figure_id: str) -> Dict[str, Any]:
    return {
        "displaylogo": False,
        "responsive": True,
        "showLink": False,
        "modeBarButtonsToRemove": ["sendDataToCloud", "lasso2d", "select2d"],
        "toImageButtonOptions": {"format": "svg", "filename": figure_id},
    }


# ---------------------------------------------------------------------------
# Accessible alternatives
# ---------------------------------------------------------------------------

def accessible_table(tables: List[Dict[str, Any]], caption: str) -> Dict[str, Any]:
    out_panels = []
    for table in tables:
        panel: PlotlyPanel = table["panel"]
        unit = _unit_check(table)
        columns = [{"key": "label", "label": "Row"}, {"key": "x", "label": table["xLabel"], "unit": panel.xUnit}]
        if any(r.get("basis") for r in table["rows"]):
            columns.append({"key": "basis", "label": "Measurement basis"})
        if any(r.get("duration") for r in table["rows"]):
            columns.append({"key": "duration", "label": "Duration"})
        for s in panel.series:
            columns.append({"key": s.field, "label": s.label or s.field, "unit": unit})
            if s.uncertainty:
                columns.append({"key": s.field + ".lower", "label": f"{s.label or s.field} lower ({s.uncertainty.semantics})", "unit": unit})
                columns.append({"key": s.field + ".upper", "label": f"{s.label or s.field} upper ({s.uncertainty.semantics})", "unit": unit})
        rows = []
        for r in table["rows"]:
            row = {"label": r["label"], "x": r["x"], "basis": r.get("basis"), "duration": r.get("duration")}
            for s in panel.series:
                row[s.field] = r["values"][s.field]
                unc = r["uncertainty"].get(s.field, {})
                if s.uncertainty:
                    row[s.field + ".lower"] = unc.get("lower")
                    row[s.field + ".upper"] = unc.get("upper")
            rows.append({c["key"]: row.get(c["key"]) for c in columns})
        summary = []
        for s in panel.series:
            vals = [r["values"][s.field] for r in table["rows"] if r["values"][s.field] is not None]
            missing = sum(1 for r in table["rows"] if r["values"][s.field] is None)
            if vals:
                summary.append(f"{s.label or s.field}: {len(vals)} reported values from {min(vals):g} to {max(vals):g} {unit}"
                               + (f"; {missing} not reported" if missing else ""))
            else:
                summary.append(f"{s.label or s.field}: no reported values")
        if panel.chart in UNCERTAINTY_CHARTS:
            rec = table.get("uncertainty")
            if panel.series:
                out_panels.append({"panelId": panel.panelId + ".observations", "title": table["title"] + " — observations",
                                   "chart": "scatter", "columns": columns, "rows": rows, "descriptiveSummary": summary})
            ucols = [{"key": "x", "label": table["xLabel"], "unit": panel.xUnit}] + ue.table_columns(rec, unit)
            urows = [{c["key"]: r.get(c["key"]) for c in ucols} for r in ue.table_rows(rec)]
            out_panels.append({"panelId": panel.panelId, "title": table["title"], "chart": panel.chart,
                               "uncertaintyStatus": "runtime-computed" if rec else "unavailable",
                               "columns": ucols, "rows": urows,
                               "descriptiveSummary": ue.summary(rec, table.get("unavailable", ""))})
            continue
        out_panels.append({"panelId": panel.panelId, "title": table["title"], "chart": panel.chart,
                           "columns": columns, "rows": rows, "descriptiveSummary": summary})
    return {"caption": caption, "panels": out_panels, "html": _table_html(out_panels, caption)}


def _cell(value: Any) -> str:
    if value is None:
        return "not reported"
    return html.escape(f"{value:g}" if isinstance(value, float) else str(value))


def _table_html(panels: List[Dict[str, Any]], caption: str) -> str:
    parts = []
    for p in panels:
        head = "".join(
            f'<th scope="col">{html.escape(c["label"])}{" (" + html.escape(c["unit"]) + ")" if c.get("unit") else ""}</th>'
            for c in p["columns"]
        )
        body = "".join(
            "<tr>" + "".join(
                (f'<th scope="row">{_cell(row[c["key"]])}</th>' if i == 0 else f"<td>{_cell(row[c['key']])}</td>")
                for i, c in enumerate(p["columns"])
            ) + "</tr>"
            for row in p["rows"]
        )
        note = "".join(f"<p>{html.escape(x)}</p>" for x in p["descriptiveSummary"]) if p.get("uncertaintyStatus") else ""
        parts.append(f'<table data-panel-id="{html.escape(p["panelId"])}"><caption>{html.escape(caption)} — '
                     f'{html.escape(p["title"])}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{note}')
    return "".join(parts)


# ---------------------------------------------------------------------------
# Runtime status and isolated static export
# ---------------------------------------------------------------------------

def _installed(package: str) -> Optional[str]:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def _plotly_js_version() -> Optional[str]:
    try:
        from plotly.offline import get_plotlyjs_version
        return get_plotlyjs_version()
    except Exception:  # pragma: no cover - plotly absent
        return None


def runtime_status(probe_export: bool = False) -> Dict[str, Any]:
    installed = {name: _installed(name) for name in PINNED_PACKAGES}
    pinned_match = {name: installed[name] == version for name, version in PINNED_PACKAGES.items()}
    out: Dict[str, Any] = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "buildId": BUILD_ID,
        "adapterId": ADAPTER_ID,
        "adapterEnabled": _flag(ENABLE_ENV),
        "staticExportEnabled": _flag(EXPORT_ENV),
        "pinnedPackages": PINNED_PACKAGES,
        "installedPackages": installed,
        "pinnedPackagesMatch": pinned_match,
        "plotlyJsVersion": _plotly_js_version(),
        "core": {"rendererKey": CORE_RENDERER_KEY, "coreRegistrationStatus": "CONTRACT_ONLY",
                 "coreExecutesPlotly": False, "automaticCoreDispatch": False},
        "staticExportProbe": {"performed": False},
        "observedAt": datetime.now(timezone.utc).isoformat(),
    }
    if probe_export and out["staticExportEnabled"]:
        probe = {"data": [{"type": "scatter", "x": [0, 1], "y": [0, 1]}], "layout": {"width": 320, "height": 240}}
        result = run_static_export(probe, ["svg"], 320, 240)
        out["staticExportProbe"] = {"performed": True, "ok": result["ok"], "error": result.get("error"),
                                    "chromeVersion": result.get("chromeVersion")}
    out["runtimeAvailable"] = bool(installed["plotly"]) and pinned_match["plotly"]
    out["staticExportAvailable"] = bool(out["staticExportProbe"].get("ok"))
    return out


def _worker_env(home: str) -> Dict[str, str]:
    env = {"PATH": os.getenv("PATH", "/usr/bin:/bin"), "HOME": home, "TMPDIR": home, "LANG": "C.UTF-8"}
    if os.getenv("SCWB_PLOTLY_BROWSER_PATH"):
        env["BROWSER_PATH"] = os.environ["SCWB_PLOTLY_BROWSER_PATH"]
    return env


def run_static_export(figure: Dict[str, Any], formats: List[str], width: int, height: int,
                      timeout: int = EXPORT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """Render static images in a separate isolated Python process with no inherited secrets."""
    payload = json.dumps({"figure": figure, "formats": formats, "width": width, "height": height})
    if not _EXPORT_SLOT.acquire(blocking=False):
        return {"ok": False, "error": "export-busy"}
    try:
        with tempfile.TemporaryDirectory(prefix="scwb-plotly-") as home:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", str(WORKER_PATH)], input=payload.encode("utf-8"),
                    capture_output=True, timeout=timeout, env=_worker_env(home), cwd=home, check=False,
                )
            except subprocess.TimeoutExpired:
                return {"ok": False, "error": "export-timeout"}
    finally:
        _EXPORT_SLOT.release()
    try:
        result = json.loads(proc.stdout.decode("utf-8") or "{}")
    except ValueError:
        return {"ok": False, "error": "export-worker-invalid-output", "exitCode": proc.returncode}
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "export-worker-failed"), "exitCode": proc.returncode}
    outputs = {}
    for fmt in formats:
        raw = base64.b64decode(result["outputs"][fmt])
        if not raw or len(raw) > MAX_EXPORT_BYTES:
            return {"ok": False, "error": f"export-{fmt}-size-invalid"}
        if not raw.lstrip()[:8].startswith(STATIC_MAGIC[fmt]) and not (fmt == "svg" and b"<svg" in raw[:400]):
            return {"ok": False, "error": f"export-{fmt}-mime-mismatch"}
        outputs[fmt] = raw
    return {"ok": True, "outputs": outputs, "chromeVersion": result.get("chromeVersion")}


# ---------------------------------------------------------------------------
# Bundle assembly
# ---------------------------------------------------------------------------

def _artifact(fmt: str, sha: str, media: str, width: int, height: int, revision: int) -> Dict[str, Any]:
    return {"format": fmt, "artifactRef": f"sc://workbench/figure-adapters/plotly/{sha}.{fmt}", "sha256": sha,
            "mediaType": media, "width": width, "height": height, "status": "local-review", "revision": revision}


def build_bundle(req: PlotlyCompileRequest, source: Dict[str, Any], figure_sha: str,
                 artifacts: List[Dict[str, Any]], generated_at: str, tables: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    tables = tables or []
    b = req.bundle
    sources = [{k: v for k, v in s.model_dump().items() if v not in ("", None)} for s in b.sourceRefs]
    context: Dict[str, Any] = {"interpretation": b.interpretation, "limitations": b.limitations,
                               "measurementStatus": b.measurementStatus,
                               "units": "; ".join(sorted({s.unit for p in req.panels for s in p.series} | {c.unit for c in req.calculations})),
                               "claimIds": b.claimIds,
                               "doNotInfer": b.doNotInfer}
    semantics = sorted({s.uncertainty.semantics for p in req.panels for s in p.series if s.uncertainty})
    if semantics:
        context["uncertaintyNotation"] = ", ".join(semantics)
    unc = [t for t in tables if t["panel"].chart in UNCERTAINTY_CHARTS]
    if unc:  # SC-FIG-05.3 (proposed v1.1 fields; absent from every other figure)
        drawn = [t["uncertainty"] for t in unc if t.get("uncertainty")]
        notation = sorted({b["semantics"] for r in drawn if r["kind"] == "band" for b in r["bands"]}
                          | {"ensemble-quantile-fan" for r in drawn if r["kind"] == "fan"})
        context["uncertaintyNotation"] = ", ".join(semantics + notation) or "unavailable"
        context["uncertaintyStatus"] = "runtime-computed" if drawn else "unavailable"
        enc = {"table-columns"}
        enc |= {"interval-ribbon" for r in drawn if r["kind"] == "band" and any(b["semantics"] == "confidence-band" for b in r["bands"])}
        enc |= {"prediction-ribbon" for r in drawn if r["kind"] == "band" and any(b["semantics"] == "prediction-band" for b in r["bands"])}
        enc |= {"ensemble-quantile-fan" for r in drawn if r["kind"] == "fan"}
        if len(drawn) < len(unc):
            enc.add("unavailable-notice")
        context["uncertaintyEncodings"] = sorted(enc)
    if b.temporalScope:
        context["temporalScope"] = b.temporalScope
    bundle = {
        "schema": BUNDLE_SCHEMA,
        "figureId": b.figureId,
        "version": b.version,
        "title": b.title,
        "project": {"projectRef": b.projectRef, "ownerScope": b.ownerScope, "environment": b.environment},
        "publication": {"kind": "none", "target": "unassigned",
                        "bindingStatus": "synthetic-test" if b.ownerScope == "isolated-synthetic" else "unbound"},
        "evidenceClass": b.evidenceClass,
        "figureType": b.figureType,
        "sourceRefs": sources,
        "calculationRefs": source["calculationRefs"] + _runtime_calc_refs(req),
        "scientificContext": context,
        "rendering": {"profileId": RENDERING_PROFILE, "renderer": "plotly",
                      "rendererVersion": f"plotly.py {_installed('plotly')}; plotly.js {_plotly_js_version()}",
                      "caption": b.caption, "altText": b.altText, "palette": b.palette,
                      "accessibilityReview": "pending", "visualizationSpecSha256": figure_sha},
        "artifacts": artifacts,
        "provenance": {"authorityOwner": "workbench", "sourceSnapshotIds": source["snapshotIds"],
                       "generationRunId": f"{ADAPTER_ID}:{figure_sha[:24]}", "generatedAt": generated_at,
                       "reproducibility": "synthetic-fixture-tested" if b.ownerScope == "isolated-synthetic" else "not-tested",
                       "scriptSha256": _module_sha256(),
                       "inputManifestSha256": source["inputManifestSha256"],
                       "lineageRefs": [f"{source['kind']}:{source.get('figureSpecHash') or source.get('datasetSha256')}"]},
        "review": {"scientific": "pending", "visual": "pending", "rights": "pending",
                   "sourceIntegrity": "pending", "publication": "pending"},
    }
    if b.labels:
        bundle["labels"] = sorted(set(b.labels))
    return bundle


def _runtime_calc_refs(req: PlotlyCompileRequest) -> List[Dict[str, Any]]:
    refs = []
    for c in req.calculations:
        ref: Dict[str, Any] = {"system": "workspace", "runRef": c.runRef, "method": c.method, "outputSha256": content_hash(c.values),
                               "assumptionRefs": [f"sha256:{content_hash(c.assumptions)}"] if c.assumptions else []}
        if c.bands is not None:
            ref["bandsSha256"] = content_hash(c.bands)
        if c.quantileBands is not None:
            ref["quantileBandsSha256"] = content_hash(c.quantileBands)
        refs.append(ref)
    return refs


def _record(req: PlotlyCompileRequest, table: Dict[str, Any]) -> Any:
    c = req.calculations[table["panel"].calculation]
    return c.bands if table["panel"].chart == "band" else c.quantileBands


def _runtime_source(req: PlotlyCompileRequest) -> Dict[str, Any]:
    ids = [f"workspace-run:{c.runRef}:{content_hash(c.values)}" for c in req.calculations]
    manifest = content_hash([c.model_dump() for c in req.calculations])
    return {"kind": "workspace-runtime-records", "calculationRefs": [], "snapshotIds": ids, "inputManifestSha256": manifest}


def _module_sha256() -> str:
    digest = hashlib.sha256()
    for path in (Path(__file__), WORKER_PATH, Path(ue.__file__)):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def compile_request(req: PlotlyCompileRequest) -> Dict[str, Any]:
    _evidence_gate(req)
    if req.workbenchFigure is not None:
        tables, source = _panels_from_workbench(req)
    elif req.dataset is not None:
        tables, source = _panels_from_dataset(req)
    else:
        tables, source = [_runtime_only_table(p) for p in req.panels], _runtime_source(req)
    if req.calculations:
        try:
            _attach_uncertainty(tables, req)
        except ue.UncertaintyRecordError as exc:
            raise ValueError(str(exc)) from exc
        if req.dataset is not None:
            source = {**source, "snapshotIds": source["snapshotIds"] + _runtime_source(req)["snapshotIds"]}
    figure = compile_plotly(tables, req)
    figure_sha = content_hash(figure)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    artifacts = [_artifact("json", figure_sha, PLOTLY_MEDIA_TYPE, req.width, req.height, req.bundle.version)]
    static: Dict[str, Any] = {"requested": list(req.staticFormats), "performed": False}
    if req.staticFormats:
        if not _flag(EXPORT_ENV):
            static.update({"status": "disabled", "reason": f"{EXPORT_ENV} is not enabled"})
        else:
            result = run_static_export(figure, list(req.staticFormats), req.width, req.height)
            if result.get("error") == "export-busy":
                raise BlockingIOError("static export worker is busy; retry later")
            if not result["ok"]:
                raise RuntimeError("static export failed: " + result["error"])
            static.update({"performed": True, "status": "exported", "chromeVersion": result.get("chromeVersion"),
                           "files": {}})
            for fmt, raw in result["outputs"].items():
                sha = hashlib.sha256(raw).hexdigest()
                artifacts.append(_artifact(fmt, sha, STATIC_MEDIA[fmt], req.width, req.height, req.bundle.version))
                static["files"][fmt] = {"sha256": sha, "bytes": len(raw), "mediaType": STATIC_MEDIA[fmt],
                                        "contentBase64": base64.b64encode(raw).decode("ascii")}
    bundle = build_bundle(req, source, figure_sha, artifacts, generated_at, tables)
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "buildId": BUILD_ID,
        "plotly": {"figure": figure, "config": plotly_config(req.bundle.figureId), "specSha256": figure_sha,
                   "plotlyJsVersion": _plotly_js_version()},
        "accessibleAlternative": accessible_table(tables, req.bundle.caption),
        "staticExport": static,
        "figureBundle": bundle,
        "source": {k: v for k, v in source.items() if k != "calculationRefs"},
        "boundaries": {
            "sourceJobsMutated": False,
            "missingValuesFilled": False,
            "uncertaintySemanticsInferred": False,
            "evidenceClassPromoted": False,
            "reviewDecisionsSetByAdapter": False,
            "remoteAssetsReferenced": False,
            "automaticCoreDispatchPerformed": False,
            "publicationPerformed": False,
        },
    }
    if req.calculations:
        out["boundaries"]["uncertaintyComputedByAdapter"] = False
        out["uncertainty"] = [{
            "panelId": t["panel"].panelId, "chart": t["panel"].chart, "calculation": t["panel"].calculation,
            "status": "runtime-computed" if t.get("uncertainty") else "unavailable",
            **({"consistency": t["uncertainty"]["consistency"], "record": _record(req, t), "recordSha256": content_hash(_record(req, t))}
               if t.get("uncertainty") else {"reason": t["unavailable"]}),
        } for t in tables if t["panel"].chart in UNCERTAINTY_CHARTS]
    out["resultHash"] = content_hash({k: v for k, v in out.items() if k != "staticExport"})
    return out


@router.get("/figure-adapters/plotly/status")
def status_route(probe: bool = False):
    return runtime_status(probe_export=probe)


@router.post("/figure-adapters/plotly/compile")
def compile_route(req: PlotlyCompileRequest):
    if not _flag(ENABLE_ENV):
        raise HTTPException(status_code=503, detail=f"FIG-02A Plotly adapter is disabled ({ENABLE_ENV}).")
    try:
        return compile_request(req)
    except BlockingIOError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
