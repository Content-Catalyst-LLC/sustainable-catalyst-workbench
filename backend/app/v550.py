"""Workbench v5.5.0 — Dynamic Geometry & Interactive Mathematics.

This module adds deterministic geometry construction records, bounded constraint
projection, affine transformations, conic sampling, measurements, and
expression-linked loci. Mathematical expressions continue to pass through the
v5.1 restricted AST -> SymPy allow-list; no Python eval/exec is used.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.v510 import RestrictedSympyParser, content_hash
from app.v520 import _linspace, _safe_real

VERSION = "5.5.0"
SCHEMA = "sc-workbench-dynamic-geometry-object/1.0"
MAX_POINTS = 64
MAX_OBJECTS = 96
MAX_CONSTRAINTS = 96
MAX_LOCUS_SAMPLES = 1001
MAX_SOLVER_ITERATIONS = 60

router = APIRouter(prefix="/v550", tags=["workbench-v550-dynamic-geometry"])


def _finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite.")
    return value


def _pt(x: float, y: float) -> Dict[str, float]:
    return {"x": round(float(x), 12), "y": round(float(y), 12)}


def _distance(a: Dict[str, float], b: Dict[str, float]) -> float:
    return math.hypot(b["x"] - a["x"], b["y"] - a["y"])


def _record(kind: str, source: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "kind": kind,
        "source": source,
        **payload,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
    }
    value["geometryObjectHash"] = content_hash(value)
    return value


class PointSpec(BaseModel):
    id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    x: float
    y: float
    label: str = ""
    draggable: bool = True
    fixed: bool = False

    @model_validator(mode="after")
    def validate_point(self):
        _finite(self.x, "point x")
        _finite(self.y, "point y")
        return self


class ObjectSpec(BaseModel):
    id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    type: Literal["segment", "line", "circle", "polygon", "vector", "ellipse", "parabola", "hyperbola"]
    pointIds: List[str] = Field(default_factory=list, max_length=32)
    centerId: Optional[str] = None
    throughId: Optional[str] = None
    radius: Optional[float] = None
    radiusX: Optional[float] = None
    radiusY: Optional[float] = None
    rotationDegrees: float = 0.0
    label: str = ""
    visible: bool = True

    @model_validator(mode="after")
    def validate_object(self):
        if self.radius is not None and self.radius <= 0:
            raise ValueError("radius must be positive.")
        if self.radiusX is not None and self.radiusX <= 0:
            raise ValueError("radiusX must be positive.")
        if self.radiusY is not None and self.radiusY <= 0:
            raise ValueError("radiusY must be positive.")
        _finite(self.rotationDegrees, "rotationDegrees")
        return self


class ConstraintSpec(BaseModel):
    type: Literal["horizontal", "vertical", "coincident", "midpoint", "distance", "point-on-circle"]
    pointIds: List[str] = Field(min_length=2, max_length=3)
    value: Optional[float] = None

    @model_validator(mode="after")
    def validate_constraint(self):
        if self.type == "distance":
            if self.value is None or self.value <= 0 or not math.isfinite(float(self.value)):
                raise ValueError("distance constraint requires a positive finite value.")
        if self.type == "point-on-circle":
            if len(self.pointIds) != 2 or self.value is None or self.value <= 0:
                raise ValueError("point-on-circle requires [point, center] and a positive radius value.")
        if self.type == "midpoint" and len(self.pointIds) != 3:
            raise ValueError("midpoint requires [midpoint, endpointA, endpointB].")
        return self


class ConstructionInput(BaseModel):
    points: List[PointSpec] = Field(min_length=1, max_length=MAX_POINTS)
    objects: List[ObjectSpec] = Field(default_factory=list, max_length=MAX_OBJECTS)
    constraints: List[ConstraintSpec] = Field(default_factory=list, max_length=MAX_CONSTRAINTS)
    solveConstraints: bool = True
    tolerance: float = Field(default=1e-7, gt=0, le=1e-2)
    iterations: int = Field(default=30, ge=1, le=MAX_SOLVER_ITERATIONS)

    @model_validator(mode="after")
    def validate_construction(self):
        point_ids = [p.id for p in self.points]
        object_ids = [o.id for o in self.objects]
        if len(set(point_ids)) != len(point_ids):
            raise ValueError("Point IDs must be unique.")
        if len(set(object_ids)) != len(object_ids):
            raise ValueError("Object IDs must be unique.")
        known = set(point_ids)
        for obj in self.objects:
            refs = list(obj.pointIds)
            if obj.centerId:
                refs.append(obj.centerId)
            if obj.throughId:
                refs.append(obj.throughId)
            missing = [r for r in refs if r not in known]
            if missing:
                raise ValueError(f"Object {obj.id} references unknown point(s): {', '.join(missing)}")
        for constraint in self.constraints:
            missing = [r for r in constraint.pointIds if r not in known]
            if missing:
                raise ValueError(f"Constraint references unknown point(s): {', '.join(missing)}")
        return self


class TransformInput(BaseModel):
    points: List[PointSpec] = Field(min_length=1, max_length=MAX_POINTS)
    pointIds: List[str] = Field(default_factory=list, max_length=MAX_POINTS)
    matrix: List[List[float]] = Field(default_factory=lambda: [[1.0, 0.0], [0.0, 1.0]])
    translation: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    origin: List[float] = Field(default_factory=lambda: [0.0, 0.0])

    @model_validator(mode="after")
    def validate_transform(self):
        if len(self.matrix) != 2 or any(len(row) != 2 for row in self.matrix):
            raise ValueError("matrix must be 2x2.")
        if len(self.translation) != 2 or len(self.origin) != 2:
            raise ValueError("translation and origin must contain two values.")
        for row in self.matrix:
            for value in row:
                _finite(value, "matrix value")
        for value in self.translation + self.origin:
            _finite(value, "transform value")
        known = {p.id for p in self.points}
        if self.pointIds and any(pid not in known for pid in self.pointIds):
            raise ValueError("Transform references unknown point ID.")
        return self


class LocusInput(BaseModel):
    xExpression: str
    yExpression: str
    parameter: str = Field(default="t", pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    tMin: float = 0.0
    tMax: float = 2 * math.pi
    samples: int = Field(default=361, ge=25, le=MAX_LOCUS_SAMPLES)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_locus(self):
        if not math.isfinite(self.tMin) or not math.isfinite(self.tMax) or self.tMin >= self.tMax:
            raise ValueError("locus parameter range must be finite and increasing.")
        if len(self.parameters) > 8:
            raise ValueError("At most 8 locus parameters are supported.")
        return self


def _point_map(points: List[PointSpec]) -> Dict[str, Dict[str, Any]]:
    return {
        p.id: {
            "id": p.id,
            "x": float(p.x),
            "y": float(p.y),
            "label": p.label or p.id,
            "draggable": bool(p.draggable),
            "fixed": bool(p.fixed),
        }
        for p in points
    }


def _movable(point: Dict[str, Any]) -> bool:
    return not bool(point.get("fixed"))


def _pair_adjust(a: Dict[str, Any], b: Dict[str, Any], dx: float, dy: float) -> None:
    ma, mb = _movable(a), _movable(b)
    if ma and mb:
        a["x"] += dx / 2.0
        a["y"] += dy / 2.0
        b["x"] -= dx / 2.0
        b["y"] -= dy / 2.0
    elif ma:
        a["x"] += dx
        a["y"] += dy
    elif mb:
        b["x"] -= dx
        b["y"] -= dy


def _apply_constraint(points: Dict[str, Dict[str, Any]], c: ConstraintSpec) -> float:
    ids = c.pointIds
    if c.type == "horizontal":
        a, b = points[ids[0]], points[ids[1]]
        error = a["y"] - b["y"]
        _pair_adjust(a, b, 0.0, -error)
        return abs(error)
    if c.type == "vertical":
        a, b = points[ids[0]], points[ids[1]]
        error = a["x"] - b["x"]
        _pair_adjust(a, b, -error, 0.0)
        return abs(error)
    if c.type == "coincident":
        a, b = points[ids[0]], points[ids[1]]
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        _pair_adjust(a, b, dx, dy)
        return math.hypot(dx, dy)
    if c.type == "midpoint":
        m, a, b = points[ids[0]], points[ids[1]], points[ids[2]]
        tx, ty = (a["x"] + b["x"]) / 2.0, (a["y"] + b["y"]) / 2.0
        dx, dy = tx - m["x"], ty - m["y"]
        if _movable(m):
            m["x"], m["y"] = tx, ty
        return math.hypot(dx, dy)
    if c.type == "distance":
        a, b = points[ids[0]], points[ids[1]]
        target = float(c.value)
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        current = math.hypot(dx, dy)
        if current < 1e-12:
            if _movable(b):
                b["x"] = a["x"] + target
                return target
            return target
        error = current - target
        ux, uy = dx / current, dy / current
        ma, mb = _movable(a), _movable(b)
        if ma and mb:
            a["x"] += ux * error / 2.0
            a["y"] += uy * error / 2.0
            b["x"] -= ux * error / 2.0
            b["y"] -= uy * error / 2.0
        elif ma:
            a["x"] += ux * error
            a["y"] += uy * error
        elif mb:
            b["x"] -= ux * error
            b["y"] -= uy * error
        return abs(error)
    if c.type == "point-on-circle":
        p, center = points[ids[0]], points[ids[1]]
        radius = float(c.value)
        dx, dy = p["x"] - center["x"], p["y"] - center["y"]
        current = math.hypot(dx, dy)
        if current < 1e-12:
            if _movable(p):
                p["x"] = center["x"] + radius
            return radius
        error = current - radius
        if _movable(p):
            p["x"] = center["x"] + dx / current * radius
            p["y"] = center["y"] + dy / current * radius
        return abs(error)
    return 0.0


def _solve(points: Dict[str, Dict[str, Any]], constraints: List[ConstraintSpec], tolerance: float, iterations: int) -> Dict[str, Any]:
    max_error = 0.0
    used = 0
    for idx in range(iterations):
        max_error = 0.0
        for constraint in constraints:
            max_error = max(max_error, _apply_constraint(points, constraint))
        used = idx + 1
        if max_error <= tolerance:
            break
    return {
        "converged": max_error <= tolerance,
        "iterations": used,
        "maxResidual": round(max_error, 12),
        "tolerance": tolerance,
    }


def _rotate(x: float, y: float, degrees: float) -> Tuple[float, float]:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return x * c - y * s, x * s + y * c


def _conic_points(obj: ObjectSpec, points: Dict[str, Dict[str, Any]]) -> List[Dict[str, float]]:
    center = points.get(obj.centerId or "", {"x": 0.0, "y": 0.0})
    cx, cy = center["x"], center["y"]
    rx = float(obj.radiusX or obj.radius or 3.0)
    ry = float(obj.radiusY or obj.radius or 2.0)
    out: List[Dict[str, float]] = []
    if obj.type == "ellipse":
        for t in _linspace(0.0, 2 * math.pi, 181):
            x, y = _rotate(rx * math.cos(t), ry * math.sin(t), obj.rotationDegrees)
            out.append(_pt(cx + x, cy + y))
    elif obj.type == "parabola":
        # local y = x^2/(4p); radiusX acts as horizontal extent, radiusY as focal parameter scale.
        p = max(0.05, ry)
        for xlocal in _linspace(-rx, rx, 161):
            ylocal = (xlocal * xlocal) / (4.0 * p)
            x, y = _rotate(xlocal, ylocal, obj.rotationDegrees)
            out.append(_pt(cx + x, cy + y))
    elif obj.type == "hyperbola":
        a, b = max(0.05, rx), max(0.05, ry)
        for branch in (-1.0, 1.0):
            for u in _linspace(-1.7, 1.7, 91):
                xlocal = branch * a * math.cosh(u)
                ylocal = b * math.sinh(u)
                x, y = _rotate(xlocal, ylocal, obj.rotationDegrees)
                out.append(_pt(cx + x, cy + y))
            out.append({"x": float("nan"), "y": float("nan")})
    return out


def _equation(obj: ObjectSpec, points: Dict[str, Dict[str, Any]]) -> Optional[str]:
    if obj.type in ("segment", "line", "vector") and len(obj.pointIds) >= 2:
        a, b = points[obj.pointIds[0]], points[obj.pointIds[1]]
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        if abs(dx) < 1e-12:
            return f"x = {a['x']:.6g}"
        slope = dy / dx
        intercept = a["y"] - slope * a["x"]
        return f"y = {slope:.6g}x {intercept:+.6g}"
    if obj.type == "circle" and obj.centerId:
        center = points[obj.centerId]
        if obj.throughId:
            radius = _distance(center, points[obj.throughId])
        else:
            radius = float(obj.radius or 1.0)
        return f"(x {(-center['x']):+.6g})² + (y {(-center['y']):+.6g})² = {radius * radius:.6g}"
    return None


def _measure_object(obj: ObjectSpec, points: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"objectId": obj.id, "type": obj.type, "label": obj.label or obj.id}
    equation = _equation(obj, points)
    if equation:
        result["equation"] = equation
    if obj.type in ("segment", "line", "vector") and len(obj.pointIds) >= 2:
        a, b = points[obj.pointIds[0]], points[obj.pointIds[1]]
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        result.update({
            "length": round(math.hypot(dx, dy), 12),
            "dx": round(dx, 12),
            "dy": round(dy, 12),
            "slope": None if abs(dx) < 1e-12 else round(dy / dx, 12),
            "angleDegrees": round(math.degrees(math.atan2(dy, dx)), 12),
        })
    elif obj.type == "circle" and obj.centerId:
        center = points[obj.centerId]
        radius = _distance(center, points[obj.throughId]) if obj.throughId else float(obj.radius or 1.0)
        result.update({
            "radius": round(radius, 12),
            "diameter": round(2 * radius, 12),
            "circumference": round(2 * math.pi * radius, 12),
            "area": round(math.pi * radius * radius, 12),
        })
    elif obj.type == "polygon" and len(obj.pointIds) >= 3:
        poly = [points[pid] for pid in obj.pointIds]
        perimeter = sum(_distance(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
        signed = sum(poly[i]["x"] * poly[(i + 1) % len(poly)]["y"] - poly[(i + 1) % len(poly)]["x"] * poly[i]["y"] for i in range(len(poly))) / 2.0
        result.update({"perimeter": round(perimeter, 12), "signedArea": round(signed, 12), "area": round(abs(signed), 12)})
    elif obj.type in ("ellipse", "parabola", "hyperbola"):
        result.update({
            "center": obj.centerId,
            "radiusX": obj.radiusX,
            "radiusY": obj.radiusY,
            "rotationDegrees": obj.rotationDegrees,
        })
    return result


def construction_object(payload: ConstructionInput) -> Dict[str, Any]:
    points = _point_map(payload.points)
    solver = {"converged": True, "iterations": 0, "maxResidual": 0.0, "tolerance": payload.tolerance}
    if payload.solveConstraints and payload.constraints:
        solver = _solve(points, payload.constraints, payload.tolerance, payload.iterations)

    rendered_objects: List[Dict[str, Any]] = []
    measurements: List[Dict[str, Any]] = []
    for obj in payload.objects:
        record = obj.model_dump()
        if obj.type == "circle" and obj.centerId:
            center = points[obj.centerId]
            radius = _distance(center, points[obj.throughId]) if obj.throughId else float(obj.radius or 1.0)
            record["center"] = _pt(center["x"], center["y"])
            record["resolvedRadius"] = round(radius, 12)
        if obj.type in ("ellipse", "parabola", "hyperbola"):
            record["sampledPoints"] = _conic_points(obj, points)
        record["equation"] = _equation(obj, points)
        rendered_objects.append(record)
        measurements.append(_measure_object(obj, points))

    result = _record(
        "dynamic-geometry-construction",
        {
            "points": [p.model_dump() for p in payload.points],
            "objects": [o.model_dump() for o in payload.objects],
            "constraints": [c.model_dump() for c in payload.constraints],
        },
        {
            "points": [_pt(p["x"], p["y"]) | {"id": p["id"], "label": p["label"], "draggable": p["draggable"], "fixed": p["fixed"]} for p in points.values()],
            "objects": rendered_objects,
            "constraints": [c.model_dump() for c in payload.constraints],
            "solver": solver,
            "measurements": measurements,
            "objectCount": len(rendered_objects),
            "pointCount": len(points),
        },
    )
    return {"ok": True, "result": result}


def transform_object(payload: TransformInput) -> Dict[str, Any]:
    selected = set(payload.pointIds or [p.id for p in payload.points])
    a, b = payload.matrix[0]
    c, d = payload.matrix[1]
    tx, ty = payload.translation
    ox, oy = payload.origin
    transformed: List[Dict[str, Any]] = []
    for p in payload.points:
        x, y = float(p.x), float(p.y)
        if p.id in selected:
            lx, ly = x - ox, y - oy
            x = a * lx + b * ly + ox + tx
            y = c * lx + d * ly + oy + ty
        transformed.append(_pt(x, y) | {"id": p.id, "label": p.label or p.id, "draggable": p.draggable, "fixed": p.fixed})
    determinant = a * d - b * c
    result = _record(
        "affine-transformation",
        payload.model_dump(),
        {
            "points": transformed,
            "matrix": [[round(a, 12), round(b, 12)], [round(c, 12), round(d, 12)]],
            "translation": [round(tx, 12), round(ty, 12)],
            "origin": [round(ox, 12), round(oy, 12)],
            "determinant": round(determinant, 12),
            "orientationPreserved": determinant > 0,
            "areaScale": round(abs(determinant), 12),
        },
    )
    return {"ok": True, "result": result}


def locus_object(payload: LocusInput) -> Dict[str, Any]:
    symbols = [payload.parameter] + list(payload.parameters.keys())
    parser = RestrictedSympyParser(symbols)
    try:
        x_expr = parser.parse(payload.xExpression)
        y_expr = parser.parse(payload.yExpression)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    t = parser.symbol(payload.parameter)
    substitutions = {parser.symbol(name): float(value) for name, value in payload.parameters.items()}
    points: List[Optional[Dict[str, float]]] = []
    finite_count = 0
    for tv in _linspace(payload.tMin, payload.tMax, payload.samples):
        xv = _safe_real(x_expr, {t: tv, **substitutions})
        yv = _safe_real(y_expr, {t: tv, **substitutions})
        if xv is None or yv is None:
            points.append(None)
        else:
            points.append(_pt(xv, yv))
            finite_count += 1
    result = _record(
        "expression-linked-locus",
        payload.model_dump(),
        {
            "parameter": payload.parameter,
            "points": points,
            "finitePointCount": finite_count,
            "xExpression": str(x_expr),
            "yExpression": str(y_expr),
            "freeSymbols": sorted(str(s) for s in (x_expr.free_symbols | y_expr.free_symbols)),
        },
    )
    return {"ok": True, "result": result}


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-dynamic-geometry-status/1.0",
        "version": VERSION,
        "foundation": "v5.1 restricted SymPy CAS + v5.4 advanced graph mathematics",
        "capabilities": [
            "draggable-points",
            "segments-and-lines",
            "circles",
            "polygons",
            "vectors",
            "ellipses",
            "parabolas",
            "hyperbolas",
            "horizontal-vertical-constraints",
            "coincident-points",
            "midpoint-constraints",
            "fixed-distance-constraints",
            "point-on-circle-constraints",
            "dynamic-measurements",
            "algebra-geometry-linkage",
            "affine-transformations",
            "matrix-transformations",
            "expression-linked-loci",
            "canonical-geometry-objects",
        ],
        "limits": {
            "maxPoints": MAX_POINTS,
            "maxObjects": MAX_OBJECTS,
            "maxConstraints": MAX_CONSTRAINTS,
            "maxLocusSamples": MAX_LOCUS_SAMPLES,
            "maxConstraintIterations": MAX_SOLVER_ITERATIONS,
        },
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/construction")
def construction(payload: ConstructionInput) -> Dict[str, Any]:
    try:
        return construction_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/transform")
def transform(payload: TransformInput) -> Dict[str, Any]:
    try:
        return transform_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/locus")
def locus(payload: LocusInput) -> Dict[str, Any]:
    return locus_object(payload)
