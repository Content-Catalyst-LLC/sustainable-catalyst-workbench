"""SC-FIG-04 — default-disabled MapLibre adapter for governed geospatial figures.

Compiles a hash-declared Workspace dataset that carries a sealed Site Intelligence reproducible spatial
package (``siPackage``) and rows derived from its evidence objects into:

* a Lab map view ``sc-lab-maplibre-view/1.1`` (``application/vnd.sc.maplibre-view.v1+json``) holding the
  SI evidence objects unchanged, with graduated classes, heat maps, time steps, uncertainty, a two-step
  comparison and Workspace calculation results,
* an accessible table (one row per object),
* an ``sc.figure-bundle.v1`` record (``spatial-map``, EPSG:4326) with source, calculation, spatial
  provenance and artifact hashes.

Before anything is compiled the adapter verifies, in order: the dataset bytes against the declared
SHA-256; the SI package and manifest digests; every evidence object's SI content digest and its entry in
the package manifest; that every row names an object in the package and repeats its digest, time and
values exactly; the evidence classes (never promoted to observed); and the declared licence of every SI
source (restricted refused; pending only for local review). Publication rights are never inferred from
the dataset, the package or the licence string inside an object: the owner declares each source's
licence status, and Research holds release.

No basemap, tile, imagery or URL is emitted. Earth-observation layers are not compiled here: Lab's gate
refuses every provider until one is approved. Review decisions are always emitted as pending.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash

VERSION = APP_VERSION
SCHEMA = "sc-workbench-maplibre-figure-adapter/1.0"
BUILD_ID = "FIG-04"
ADAPTER_ID = "workbench.maplibre-figure-adapter"
BUNDLE_SCHEMA = "sc.figure-bundle.v1"
RENDERING_PROFILE = "sc-institutional-research-v1"
VIEW_MEDIA_TYPE = "application/vnd.sc.maplibre-view.v1+json"
VIEW_SCHEMA = "sc-lab-maplibre-view/1.1"
DATASET_SCHEMA = "sc-fig04-si-derived-dataset/1"
SI_OBJECT = "sc-site-intelligence-spatial-evidence-object/2.0"
SI_PACKAGE = "sc-site-intelligence-reproducible-spatial-intelligence-package/1.0"
SI_MANIFEST = "sc-site-intelligence-reproducible-spatial-package-manifest/1.0"
SI_PACKAGE_UNSEALED = {"package_id", "package_digest", "sealed", "delivery_attempted", "execution_attempted"}
MAPLIBRE_VERSION = "5.24.0"
CRS = "EPSG:4326"
ENABLE_ENV = "SCWB_MAPLIBRE_ADAPTER_ENABLED"
MAX_DATASET_BYTES = 8 * 1024 * 1024
MAX_OBJECTS = 5000
MAX_TEXT = 400
EVIDENCE_FIELD = "evidence_class"
router = APIRouter(tags=["workbench-fig-04-maplibre-figure-adapter"])

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
UncertaintyKind = Literal["standard-error", "standard-deviation", "ci95-half-width"]
GEOMETRY = {"point": ("Point", "MultiPoint"), "line": ("LineString", "MultiLineString"),
            "polygon": ("Polygon", "MultiPolygon"), "heatmap": ("Point", "MultiPoint")}
RAMPS = ("viridis", "cividis", "magma")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_URLISH = re.compile(r"(?:^|[^a-z])(?:https?|ftp|file|data|blob|javascript|mapbox|pmtiles):|\{[xyz]\}|//", re.I)
_FIELD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_ID = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_SI_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _plain(value: str, where: str, limit: int = MAX_TEXT) -> str:
    """Figure text is stored as data and drawn with textContent; refuse control characters and URLs."""
    value = str(value or "").strip()
    if _CONTROL.search(value):
        raise ValueError(f"{where}: control characters are not permitted")
    if _URLISH.search(value):
        raise ValueError(f"{where}: URLs and tile templates are not permitted in figure text")
    return value[:limit]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SpatialDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    datasetId: str = Field(min_length=3, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contentBase64: str = Field(min_length=4, max_length=MAX_DATASET_BYTES * 4 // 3 + 8)
    evidenceClass: EvidenceClass


class FieldSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=120)
    unit: str = Field(min_length=1, max_length=40)
    uncertainty: str = Field(default="", max_length=64)
    uncertaintyKind: Optional[UncertaintyKind] = None

    @model_validator(mode="after")
    def validate_uncertainty(self):
        if bool(self.uncertainty) != (self.uncertaintyKind is not None):
            raise ValueError("uncertainty needs both a property name and an uncertaintyKind")
        if self.uncertainty and not _FIELD.fullmatch(self.uncertainty):
            raise ValueError(f"invalid uncertainty property name: {self.uncertainty!r}")
        return self


class Classify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    breaks: List[float] = Field(min_length=1, max_length=8)
    colors: List[str] = Field(min_length=2, max_length=9)

    @model_validator(mode="after")
    def validate_classes(self):
        if any(not math.isfinite(b) for b in self.breaks) or any(b <= a for a, b in zip(self.breaks, self.breaks[1:])):
            raise ValueError("classify.breaks must be ascending finite numbers")
        if len(self.colors) != len(self.breaks) + 1 or not all(_COLOR.fullmatch(c) for c in self.colors):
            raise ValueError(f"classify.colors must be {len(self.breaks) + 1} #rrggbb constants")
        return self


class Weight(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    max: float = Field(gt=0, le=1e12)


class LayerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,47}$")
    geometry: Literal["point", "line", "polygon", "heatmap"]
    evidenceClass: Optional[EvidenceClass] = None
    legend: str = Field(min_length=4, max_length=200)
    style: Dict[str, Any] = Field(default_factory=dict)
    classify: Optional[Classify] = None
    weight: Optional[Weight] = None
    ramp: Optional[Literal["viridis", "cividis", "magma"]] = None

    @model_validator(mode="after")
    def validate_layer(self):
        if self.geometry == "heatmap":
            if self.weight is None or self.ramp is None or self.classify is not None:
                raise ValueError(f"heatmap layer {self.id} needs weight and ramp (and no classify)")
        elif self.weight is not None or self.ramp is not None:
            raise ValueError(f"layer {self.id}: weight and ramp are for heatmap layers only")
        if self.classify is not None and self.geometry == "line":
            raise ValueError(f"layer {self.id}: classify is for points and polygons only")
        for k, v in self.style.items():
            if k.lower().endswith("color"):
                if not (isinstance(v, str) and _COLOR.fullmatch(v)):
                    raise ValueError(f"layer {self.id} style.{k} must be a #rrggbb constant")
            elif isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"layer {self.id} style.{k} must be a constant number")
        return self


class TimeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=120)
    initial: Literal["first", "last"] = "last"


class ComparisonSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    match: str
    label: str = Field(min_length=4, max_length=200)
    fromStep: str = Field(default="", max_length=40)
    toStep: str = Field(default="", max_length=40)


class ViewSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=5, max_length=220)
    fields: Dict[str, FieldSpec] = Field(min_length=1, max_length=24)
    layers: List[LayerSpec] = Field(min_length=1, max_length=12)
    time: Optional[TimeSpec] = None
    comparison: Optional[ComparisonSpec] = None
    maxZoom: float = Field(default=12, ge=1, le=18)


class CalculationInput(BaseModel):
    """A result of a verified Workspace run. Research binds the run itself; this records which value is shown."""
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=3, max_length=200)
    unit: str = Field(min_length=1, max_length=40)
    method: str = Field(min_length=3, max_length=300)
    runRef: str = Field(min_length=3, max_length=200)
    values: Dict[str, Any] = Field(min_length=1, max_length=200)
    valueKey: str = Field(min_length=1, max_length=120)
    uncertaintyKey: str = Field(default="", max_length=120)
    uncertaintyKind: Optional[UncertaintyKind] = None

    @model_validator(mode="after")
    def validate_keys(self):
        if bool(self.uncertaintyKey) != (self.uncertaintyKind is not None):
            raise ValueError("calculation uncertainty needs both uncertaintyKey and uncertaintyKind")
        return self


class SpatialSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceId: str = Field(min_length=1, max_length=240)
    provider: str = Field(min_length=1, max_length=240)
    identityStatus: Literal["unverified", "source-identified", "source-hash-verified"]
    qualityStatus: Literal["pending", "qualified", "rejected", "not-applicable"]
    licenceStatus: Literal["pending", "verified-for-use", "restricted"]
    notes: str = Field(default="", max_length=1000)


class SpatialBundleMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    figureId: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{2,100}$")
    version: int = Field(default=1, ge=1)
    title: str = Field(min_length=5, max_length=220)
    projectRef: str = Field(min_length=1, max_length=200)
    ownerScope: Literal["isolated-synthetic", "unbound-local"]
    environment: Literal["staging", "local-review"]
    evidenceClass: EvidenceClass
    interpretation: str = Field(min_length=8, max_length=2000)
    limitations: List[str] = Field(min_length=1, max_length=20)
    measurementStatus: MeasurementStatus
    doNotInfer: List[str] = Field(default_factory=list, max_length=20)
    caption: str = Field(min_length=15, max_length=2000)
    altText: str = Field(min_length=15, max_length=2000)
    geometryStatus: Literal["illustrative", "source-verified"] = "illustrative"
    extentStatus: str = Field(default="regional-rectangle", max_length=60)
    sourceRefs: List[SpatialSource] = Field(min_length=1, max_length=50)
    labels: List[str] = Field(default_factory=list, max_length=20)


class MapLibreCompileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset: SpatialDataset
    view: ViewSpec
    calculations: List[CalculationInput] = Field(default_factory=list, max_length=8)
    bundle: SpatialBundleMetadata


# ---------------------------------------------------------------------------
# Site Intelligence verification (SI's own canonical form: sorted keys, compact, UTF-8)
# ---------------------------------------------------------------------------

def _si_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _decode_dataset(ds: SpatialDataset) -> Dict[str, Any]:
    try:
        raw = base64.b64decode(ds.contentBase64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("dataset contentBase64 is not valid base64") from exc
    if not raw or len(raw) > MAX_DATASET_BYTES:
        raise ValueError(f"dataset must be 1 byte to {MAX_DATASET_BYTES} bytes")
    if hashlib.sha256(raw).hexdigest() != ds.sha256:
        raise PermissionError("dataset bytes do not match the declared (Workspace-pinned) SHA-256")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("dataset is not UTF-8 JSON") from exc
    if not isinstance(doc, dict) or doc.get("schema") != DATASET_SCHEMA:
        raise ValueError(f"dataset is not a {DATASET_SCHEMA} document")
    return doc


def verify_si_package(pkg: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Verifies a sealed SI package and its evidence objects; returns (objects, package reference)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != SI_PACKAGE or pkg.get("sealed") is not True:
        raise ValueError("siPackage is not a sealed Site Intelligence reproducible spatial package")
    manifest = pkg.get("manifest") if isinstance(pkg.get("manifest"), dict) else {}
    if manifest.get("schema") != SI_MANIFEST:
        raise ValueError("siPackage manifest schema mismatch")
    if manifest.get("manifest_digest") != _si_digest({k: v for k, v in manifest.items() if k != "manifest_digest"}):
        raise PermissionError("siPackage manifest digest does not match its content")
    if pkg.get("package_digest") != _si_digest({k: v for k, v in pkg.items() if k not in SI_PACKAGE_UNSEALED}):
        raise PermissionError("siPackage digest does not match its content")
    objects = ((pkg.get("components") or {}).get("evidence_objects")) or []
    if not isinstance(objects, list) or not objects or len(objects) > MAX_OBJECTS:
        raise ValueError(f"siPackage must hold 1 to {MAX_OBJECTS} evidence objects")
    listed = sorted(e.get("digest") for e in manifest.get("entries") or [] if e.get("group") == "evidence_objects")
    seen = set()
    for i, o in enumerate(objects):
        at = f"siPackage evidence object {i}"
        if not isinstance(o, dict) or o.get("schema") != SI_OBJECT:
            raise ValueError(f"{at} is not a {SI_OBJECT}")
        if not _SI_HASH.fullmatch(str(o.get("content_digest"))) or \
                o["content_digest"] != _si_digest({k: v for k, v in o.items() if k != "content_digest"}):
            raise PermissionError(f"{at} ({o.get('object_id')}) does not match its Site Intelligence content digest")
        if o.get("crs") != CRS:
            raise ValueError(f"{at} crs must be {CRS} (no reprojection)")
        if o.get("visibility") != "public":
            raise PermissionError(f"{at} visibility {o.get('visibility')} is not public")
        if o.get("object_id") in seen:
            raise ValueError(f"{at} repeats object_id {o.get('object_id')}")
        seen.add(o.get("object_id"))
    if listed != sorted(o["content_digest"] for o in objects):
        raise PermissionError("siPackage manifest does not list exactly its evidence objects")
    ref = {"package_id": pkg.get("package_id"), "package_digest": pkg["package_digest"],
           "manifest_digest": manifest["manifest_digest"]}
    return objects, ref


def verify_rows(rows: Any, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every row must name a package object and repeat its digest, time and property values exactly."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("dataset rows are required")
    by_id = {o["object_id"]: o for o in objects}
    used = set()
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise ValueError(f"dataset row {i} is not an object")
        o = by_id.get(r.get("object_id"))
        if o is None:
            raise PermissionError(f"dataset row {i} names an object that is not in the SI package")
        if r.get("content_digest") != o["content_digest"]:
            raise PermissionError(f"dataset row {i} does not carry its object's SI content digest")
        if "observed_at" in r and r["observed_at"] != o.get("observed_at"):
            raise PermissionError(f"dataset row {i} observed_at differs from its SI object")
        if r["object_id"] in used:
            raise ValueError(f"dataset row {i} repeats object {r['object_id']}")
        used.add(r["object_id"])
        props = o.get("properties") or {}
        for k, v in r.items():
            if k in props and props[k] != v:
                raise PermissionError(f"dataset row {i} value {k} differs from its SI object")
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError(f"dataset row {i} {k} is not finite")
    return rows


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def _evidence_and_rights_gate(req: MapLibreCompileRequest, objects: List[Dict[str, Any]]) -> None:
    b = req.bundle
    if EXPECTED_MEASUREMENT[b.evidenceClass] != b.measurementStatus:
        raise ValueError(f"evidenceClass {b.evidenceClass} requires measurementStatus {EXPECTED_MEASUREMENT[b.evidenceClass]}")
    if req.dataset.evidenceClass != b.evidenceClass:
        raise ValueError(f"dataset evidenceClass {req.dataset.evidenceClass} cannot be relabelled as {b.evidenceClass}")
    for o in objects:
        c = (o.get("properties") or {}).get(EVIDENCE_FIELD)
        if c not in EXPECTED_MEASUREMENT:
            raise ValueError(f"SI object {o['object_id']} has no recognised {EVIDENCE_FIELD}")
        if c == "observed" and b.evidenceClass != "observed":
            raise ValueError(f"SI object {o['object_id']} is observed inside a {b.evidenceClass} figure (no promotion to observed)")
    declared = {s.sourceId: s for s in b.sourceRefs}
    in_package = {((o.get("source") or {}).get("source_id")) for o in objects}
    missing = sorted(x for x in in_package if x not in declared)
    if missing:
        raise PermissionError("SI sources without a declared licence status: " + ", ".join(missing))
    extra = sorted(x for x in declared if x not in in_package)
    if extra:
        raise ValueError("declared sources not used by any SI object: " + ", ".join(extra))
    restricted = [s.sourceId for s in b.sourceRefs if s.licenceStatus == "restricted"]
    if restricted:
        raise PermissionError("restricted sources cannot be rendered: " + ", ".join(restricted))
    pending = [s.sourceId for s in b.sourceRefs if s.licenceStatus == "pending"]
    if pending and b.environment != "local-review":
        raise PermissionError("sources with pending licence review may only render for local-review: " + ", ".join(pending))
    if b.evidenceClass == "observed":
        weak = [s.sourceId for s in b.sourceRefs if s.qualityStatus != "qualified"]
        if weak:
            raise ValueError("observed figures require qualified sources: " + ", ".join(weak))
    if b.geometryStatus == "source-verified" and any(s.identityStatus != "source-hash-verified" for s in b.sourceRefs):
        raise ValueError("geometryStatus source-verified needs source-hash-verified sources")


def _numeric(objects, f, where):
    for o in objects:
        v = (o.get("properties") or {}).get(f)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)):
            raise ValueError(f"{where} field {f} must be numeric (object {o['object_id']})")


# ---------------------------------------------------------------------------
# View, table and bundle
# ---------------------------------------------------------------------------

def compile_view(req: MapLibreCompileRequest, objects: List[Dict[str, Any]], bbox: List[float]) -> Dict[str, Any]:
    v = req.view
    for f in v.fields:
        if not _FIELD.fullmatch(f):
            raise ValueError(f"invalid field name {f!r}")
    fields = {}
    for f, d in v.fields.items():
        fd = {"label": _plain(d.label, f"field {f} label"), "unit": _plain(d.unit, f"field {f} unit")}
        if d.uncertainty:
            fd.update(uncertainty=d.uncertainty, uncertaintyKind=d.uncertaintyKind)
            _numeric(objects, d.uncertainty, f"field {f} uncertainty")
            if any(((o.get("properties") or {}).get(d.uncertainty) or 0) < 0 for o in objects):
                raise ValueError(f"field {f} uncertainty values must be non-negative")
        fields[f] = fd

    def declared_numeric(f, where):
        if f not in fields:
            raise ValueError(f"{where} field {f!r} is not a declared field")
        _numeric(objects, f, where)

    layers, legend, drawn = [], [], set()
    if len({l.id for l in v.layers}) != len(v.layers):
        raise ValueError("layer ids must be unique")
    for l in v.layers:
        out: Dict[str, Any] = {"id": l.id, "geometry": l.geometry}
        if l.evidenceClass:
            out["where"] = {"property": EVIDENCE_FIELD, "equals": l.evidenceClass}
        if l.style:
            out["style"] = dict(l.style)
        if l.classify:
            declared_numeric(l.classify.field, f"layer {l.id} classify")
            out["classify"] = l.classify.model_dump()
        if l.geometry == "heatmap":
            declared_numeric(l.weight.field, f"layer {l.id} weight")
            out["weight"] = l.weight.model_dump()
            out["ramp"] = l.ramp
        layers.append(out)
        legend.append({"layer": l.id, "label": _plain(l.legend, f"layer {l.id} legend")})
        for o in objects:
            if o["geometry"]["type"] in GEOMETRY[l.geometry] and \
                    (not l.evidenceClass or (o.get("properties") or {}).get(EVIDENCE_FIELD) == l.evidenceClass):
                drawn.add(o["object_id"])
    undrawn = [o["object_id"] for o in objects if o["object_id"] not in drawn]
    if undrawn:
        raise ValueError(f"{len(undrawn)} SI object(s) are not drawn by any layer")
    classes = {(o.get("properties") or {}).get(EVIDENCE_FIELD) for o in objects}
    if len(classes) > 1 and not all(any(l.evidenceClass == c for l in v.layers) for c in classes):
        raise ValueError("objects mix evidence classes; each class needs its own layer")

    view: Dict[str, Any] = {
        "schema": VIEW_SCHEMA, "title": _plain(v.title, "view title", 220), "objects": objects,
        "evidenceField": EVIDENCE_FIELD, "fields": fields, "layers": layers, "legend": legend,
        "basemap": None, "camera": {"bbox": bbox, "maxZoom": v.maxZoom},
    }
    steps = sorted({o.get("observed_at") for o in objects if isinstance(o.get("observed_at"), str)})
    if v.time:
        if len(steps) < 2 or any(not isinstance(o.get("observed_at"), str) for o in objects):
            raise ValueError("time steps need every SI object to carry observed_at, with at least two distinct values")
        view["time"] = {"property": "observed_at", "label": _plain(v.time.label, "time label"), "steps": steps,
                        "initial": steps[-1] if v.time.initial == "last" else steps[0]}
    if v.comparison:
        c = v.comparison
        declared_numeric(c.field, "comparison")
        if not _FIELD.fullmatch(c.match):
            raise ValueError("comparison match must be a property name")
        frm, to = c.fromStep or (steps[0] if steps else ""), c.toStep or (steps[-1] if steps else "")
        if frm not in steps or to not in steps or frm >= to:
            raise ValueError("comparison needs two SI observed_at steps, earlier first")
        view["comparison"] = {"field": c.field, "from": frm, "to": to, "match": c.match, "label": _plain(c.label, "comparison label")}
    calcs = []
    for i, c in enumerate(req.calculations):
        value = c.values.get(c.valueKey)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"calculation {i}: {c.valueKey!r} is not a finite number in the run's result values")
        entry = {"label": _plain(c.label, f"calculation {i} label"), "value": value, "unit": _plain(c.unit, f"calculation {i} unit"),
                 "method": _plain(c.method, f"calculation {i} method"), "calculationRef": i}
        if c.uncertaintyKey:
            u = c.values.get(c.uncertaintyKey)
            if isinstance(u, bool) or not isinstance(u, (int, float)) or not math.isfinite(u) or u < 0:
                raise ValueError(f"calculation {i}: {c.uncertaintyKey!r} is not a non-negative number in the run's result values")
            entry.update(uncertainty=u, uncertaintyKind=c.uncertaintyKind)
        calcs.append(entry)
    if calcs:
        view["calculations"] = calcs
    return view


def _bbox(objects: List[Dict[str, Any]]) -> List[float]:
    boxes = [o.get("bbox") for o in objects]
    if any(not (isinstance(b, list) and len(b) == 4 and all(isinstance(x, (int, float)) for x in b)) for b in boxes):
        raise ValueError("every SI object needs its bbox")
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def accessible_table(view: Dict[str, Any], caption: str) -> Dict[str, Any]:
    fields = view["fields"]
    cols = ["Object", "Geometry", "Evidence class"]
    for f, d in fields.items():
        cols.append(d["label"] if d["unit"] in {"1", "category"} else f"{d['label']} ({d['unit']})")
        if d.get("uncertainty"):
            cols.append(f"{d['label']} {d['uncertaintyKind']} ({d['unit']})")
    cols += ["Observed or valid time", "Source", "Licence (as recorded by SI)", "SI digest"]
    rows = []
    for o in view["objects"]:
        p, s, vals = o.get("properties") or {}, o.get("source") or {}, []
        for f, d in fields.items():
            vals.append("not reported" if p.get(f) is None else str(p.get(f)))
            if d.get("uncertainty"):
                u = p.get(d["uncertainty"])
                vals.append("not reported" if u is None else str(u))
        rows.append([o["object_id"], o["geometry"]["type"], str(p.get(EVIDENCE_FIELD))] + vals +
                    [o.get("observed_at") or "not reported", s.get("source_id") or "", s.get("license") or "not recorded",
                     o["content_digest"]])
    return {"caption": caption, "columns": cols, "rows": rows}


def _module_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_bundle(req: MapLibreCompileRequest, view_sha: str, pkg_ref: Dict[str, Any], bbox: List[float],
                 generated_at: str, view: Dict[str, Any]) -> Dict[str, Any]:
    b, ds = req.bundle, req.dataset
    sources = []
    for s in b.sourceRefs:
        # The data this figure was drawn from is the pinned Workspace dataset (which seals the SI package).
        d = {k: v for k, v in s.model_dump().items() if v not in ("", None)}
        d.update(sha256=ds.sha256, crs=CRS)
        sources.append(d)
    units = sorted({d["unit"] for d in view["fields"].values() if d["unit"] not in {"1", "category"}})
    context: Dict[str, Any] = {"interpretation": b.interpretation, "limitations": b.limitations,
                               "measurementStatus": b.measurementStatus, "units": "; ".join(units),
                               "doNotInfer": b.doNotInfer}
    kinds = sorted({d["uncertaintyKind"] for d in view["fields"].values() if d.get("uncertaintyKind")})
    if kinds:
        context["uncertaintyNotation"] = ", ".join(kinds)
    if view.get("time"):
        context["temporalScope"] = f"{view['time']['steps'][0]} to {view['time']['steps'][-1]} ({len(view['time']['steps'])} steps)"
    bundle = {
        "schema": BUNDLE_SCHEMA, "figureId": b.figureId, "version": b.version, "title": b.title,
        "project": {"projectRef": b.projectRef, "ownerScope": b.ownerScope, "environment": b.environment},
        "publication": {"kind": "none", "target": "unassigned",
                        "bindingStatus": "synthetic-test" if b.ownerScope == "isolated-synthetic" else "unbound"},
        "evidenceClass": b.evidenceClass, "figureType": "spatial-map",
        "sourceRefs": sources,
        "calculationRefs": [{"system": "workspace", "runRef": c.runRef, "method": c.method,
                             "outputSha256": content_hash(c.values), "assumptionRefs": []} for c in req.calculations],
        "scientificContext": context,
        "spatial": {"geometryStatus": b.geometryStatus, "crs": CRS, "extentStatus": b.extentStatus, "bbox": bbox,
                    "siPackage": pkg_ref, "objectCount": len(view["objects"])},
        "rendering": {"profileId": RENDERING_PROFILE, "renderer": "maplibre-gl",
                      "rendererVersion": f"maplibre-gl {MAPLIBRE_VERSION} (Lab Graph Studio, SC-FIG-04)",
                      "caption": b.caption, "altText": b.altText, "palette": "colorblind-safe",
                      "accessibilityReview": "pending", "visualizationSpecSha256": view_sha},
        "artifacts": [{"format": "json", "artifactRef": f"sc://workbench/figure-adapters/maplibre/{view_sha}.json",
                       "sha256": view_sha, "mediaType": VIEW_MEDIA_TYPE, "status": "local-review", "revision": b.version}],
        "provenance": {"authorityOwner": "workbench",
                       "sourceSnapshotIds": [f"dataset:{ds.datasetId}:{ds.sha256}", f"site-intelligence-package:{pkg_ref['package_digest']}"],
                       "generationRunId": f"{ADAPTER_ID}:{view_sha[:24]}", "generatedAt": generated_at,
                       "reproducibility": "synthetic-fixture-tested" if b.ownerScope == "isolated-synthetic" else "not-tested",
                       "scriptSha256": _module_sha256(), "inputManifestSha256": ds.sha256,
                       "lineageRefs": [f"authorized-dataset:{ds.sha256}", f"site-intelligence-package:{pkg_ref['package_digest']}"]},
        "review": {"scientific": "pending", "visual": "pending", "rights": "pending",
                   "sourceIntegrity": "pending", "publication": "pending"},
    }
    if b.labels:
        bundle["labels"] = sorted(set(b.labels))
    return bundle


def compile_request(req: MapLibreCompileRequest) -> Dict[str, Any]:
    doc = _decode_dataset(req.dataset)
    objects, pkg_ref = verify_si_package(doc.get("siPackage"))
    rows = verify_rows(doc.get("rows"), objects)
    _evidence_and_rights_gate(req, objects)
    for text, where in ((req.bundle.title, "title"), (req.bundle.caption, "caption"), (req.bundle.altText, "altText"),
                        (req.bundle.interpretation, "interpretation")):
        _plain(text, where, 2000)
    bbox = _bbox(objects)
    view = compile_view(req, objects, bbox)
    view_sha = content_hash(view)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    bundle = build_bundle(req, view_sha, pkg_ref, bbox, generated_at, view)
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION, "buildId": BUILD_ID,
        "maplibre": {"view": view, "specSha256": view_sha, "mediaType": VIEW_MEDIA_TYPE, "maplibreVersion": MAPLIBRE_VERSION},
        "accessibleAlternative": accessible_table(view, req.bundle.caption),
        "figureBundle": bundle,
        "verification": {"datasetSha256": req.dataset.sha256, "siPackage": pkg_ref, "objects": len(objects),
                         "rowsVerified": len(rows), "siDigestsRecomputed": True, "manifestMatched": True,
                         "sources": {s.sourceId: s.licenceStatus for s in req.bundle.sourceRefs}},
        "boundaries": {
            "siObjectsModified": False, "reprojected": False, "evidenceClassPromoted": False,
            "missingValuesFilled": False, "basemapOrTilesReferenced": False, "earthObservationLayers": False,
            "publicationRightsInferred": False, "reviewDecisionsSetByAdapter": False, "publicationPerformed": False,
        },
    }
    out["resultHash"] = content_hash(out)
    return out


def runtime_status() -> Dict[str, Any]:
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "buildId": BUILD_ID, "enabled": _flag(ENABLE_ENV),
            "enableEnv": ENABLE_ENV, "viewSchema": VIEW_SCHEMA, "viewMediaType": VIEW_MEDIA_TYPE,
            "datasetSchema": DATASET_SCHEMA, "siObjectSchema": SI_OBJECT, "siPackageSchema": SI_PACKAGE,
            "maplibreVersion": MAPLIBRE_VERSION, "approvedTileProviders": [],
            "earthObservation": "not compiled here; Lab refuses every provider until one is approved"}


@router.get("/figure-adapters/maplibre/status")
def status_route():
    return runtime_status()


@router.post("/figure-adapters/maplibre/compile")
def compile_route(req: MapLibreCompileRequest):
    if not _flag(ENABLE_ENV):
        raise HTTPException(status_code=503, detail=f"FIG-04 MapLibre adapter is disabled ({ENABLE_ENV}).")
    try:
        return compile_request(req)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
