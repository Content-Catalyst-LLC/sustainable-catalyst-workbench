"""Workbench v11.12.0 — Geometry, Trigonometry & Coordinate Mathematics.

Adds Euclidean, triangle, circle, coordinate, vector, intersection, and
trigonometric reasoning to the unified v11 CalculationObject.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sympy.geometry import Circle, Line, Point, Polygon, Segment, Triangle

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-geometry-trigonometry-coordinate-status/1.0"
RESULT_SCHEMA = "sc-workbench-geometry-trigonometry-coordinate-result/1.0"

router = APIRouter(tags=["workbench-v11120-geometry-trigonometry-coordinate-mathematics"])


class GeometryRequest(BaseModel):
    operation: Literal[
        "distance",
        "midpoint",
        "slope",
        "line-equation",
        "line-intersection",
        "circle-properties",
        "circle-line-intersection",
        "triangle-properties",
        "polygon-area",
        "vector-angle",
        "vector-projection",
        "trig-evaluate",
        "trig-solve-right-triangle",
        "coordinate-transform",
    ]
    pointA: Optional[List[float]] = Field(default=None, min_length=2, max_length=3)
    pointB: Optional[List[float]] = Field(default=None, min_length=2, max_length=3)
    pointC: Optional[List[float]] = Field(default=None, min_length=2, max_length=3)
    points: List[List[float]] = Field(default_factory=list, max_length=1000)
    lineA: Optional[List[List[float]]] = Field(default=None, min_length=2, max_length=2)
    lineB: Optional[List[List[float]]] = Field(default=None, min_length=2, max_length=2)
    center: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    radius: Optional[float] = Field(default=None, gt=0)
    vectorA: Optional[List[float]] = None
    vectorB: Optional[List[float]] = None
    angle: Optional[float] = None
    angleUnit: Literal["degrees", "radians"] = "degrees"
    trigFunction: Optional[Literal["sin", "cos", "tan", "asin", "acos", "atan"]] = None
    sideA: Optional[float] = Field(default=None, gt=0)
    sideB: Optional[float] = Field(default=None, gt=0)
    hypotenuse: Optional[float] = Field(default=None, gt=0)
    transform: Optional[Literal["translate", "rotate", "scale"]] = None
    translate: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    scale: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)


class GeometryCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    geometry: GeometryRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _require_point(value, name):
    if value is None:
        raise ValueError(f"{name} is required")
    return np.asarray(value, dtype=float)


def _point2(value, name):
    p = _require_point(value, name)
    if p.size != 2:
        raise ValueError(f"{name} must be two-dimensional")
    return Point(sp.nsimplify(p[0]), sp.nsimplify(p[1]))


def _serialize_sympy(value):
    if isinstance(value, Point):
        return {"type": "Point", "coordinates": [str(v) for v in value.args],
                "approximate": [float(sp.N(v)) for v in value.args]}
    if isinstance(value, Segment):
        return {"type": "Segment", "p1": _serialize_sympy(value.p1), "p2": _serialize_sympy(value.p2)}
    return str(value)


def _angle_to_radians(value: float, unit: str) -> float:
    return math.radians(value) if unit == "degrees" else float(value)


def execute_geometry(req: GeometryRequest) -> Dict[str, Any]:
    op = req.operation
    verification: Dict[str, Any] = {}
    details: Dict[str, Any] = {}
    method = op

    if op == "distance":
        a = _require_point(req.pointA, "pointA")
        b = _require_point(req.pointB, "pointB")
        if a.size != b.size:
            raise ValueError("point dimensions must match")
        d = float(np.linalg.norm(b-a))
        result: Any = {"distance": d, "dimension": int(a.size)}
        verification["nonnegative"] = d >= 0

    elif op == "midpoint":
        a = _require_point(req.pointA, "pointA")
        b = _require_point(req.pointB, "pointB")
        if a.size != b.size:
            raise ValueError("point dimensions must match")
        result = {"midpoint": ((a+b)/2).tolist()}

    elif op == "slope":
        a = _require_point(req.pointA, "pointA")
        b = _require_point(req.pointB, "pointB")
        if a.size != 2 or b.size != 2:
            raise ValueError("slope requires 2D points")
        dx = b[0]-a[0]
        if abs(dx) < 1e-15:
            result = {"slope": None, "vertical": True}
        else:
            result = {"slope": float((b[1]-a[1])/dx), "vertical": False}

    elif op == "line-equation":
        p1 = _point2(req.pointA, "pointA")
        p2 = _point2(req.pointB, "pointB")
        line = Line(p1, p2)
        x, y = sp.symbols("x y", real=True)
        expr = sp.expand(line.coefficients[0]*x + line.coefficients[1]*y + line.coefficients[2])
        result = {
            "standardForm": str(sp.Eq(expr, 0)),
            "coefficients": [str(v) for v in line.coefficients],
        }
        method = "sympy-line"

    elif op == "line-intersection":
        if req.lineA is None or req.lineB is None:
            raise ValueError("line-intersection requires lineA and lineB")
        l1 = Line(_point2(req.lineA[0], "lineA[0]"), _point2(req.lineA[1], "lineA[1]"))
        l2 = Line(_point2(req.lineB[0], "lineB[0]"), _point2(req.lineB[1], "lineB[1]"))
        intersections = l1.intersection(l2)
        result = {"intersections": [_serialize_sympy(v) for v in intersections]}
        verification["intersects"] = bool(intersections)
        method = "sympy-line-intersection"

    elif op == "circle-properties":
        c = _point2(req.center, "center")
        if req.radius is None:
            raise ValueError("circle-properties requires radius")
        r = sp.nsimplify(req.radius)
        circle = Circle(c, r)
        result = {
            "center": _serialize_sympy(circle.center),
            "radius": str(circle.radius),
            "diameter": str(2*circle.radius),
            "circumferenceExact": str(circle.circumference),
            "circumferenceApproximate": float(sp.N(circle.circumference)),
            "areaExact": str(circle.area),
            "areaApproximate": float(sp.N(circle.area)),
        }
        method = "sympy-circle"

    elif op == "circle-line-intersection":
        if req.center is None or req.radius is None or req.lineA is None:
            raise ValueError("circle-line-intersection requires center, radius, and lineA")
        circle = Circle(_point2(req.center, "center"), sp.nsimplify(req.radius))
        line = Line(_point2(req.lineA[0], "lineA[0]"), _point2(req.lineA[1], "lineA[1]"))
        intersections = circle.intersection(line)
        result = {"intersections": [_serialize_sympy(v) for v in intersections]}
        verification["intersectionCount"] = len(intersections)
        method = "sympy-circle-line-intersection"

    elif op == "triangle-properties":
        p1 = _point2(req.pointA, "pointA")
        p2 = _point2(req.pointB, "pointB")
        p3 = _point2(req.pointC, "pointC")
        tri = Triangle(p1, p2, p3)
        result = {
            "areaExact": str(tri.area),
            "areaApproximate": float(sp.N(tri.area)),
            "perimeterExact": str(tri.perimeter),
            "perimeterApproximate": float(sp.N(tri.perimeter)),
            "centroid": _serialize_sympy(tri.centroid),
            "circumcenter": _serialize_sympy(tri.circumcircle.center),
            "incenter": _serialize_sympy(tri.incircle.center),
            "anglesRadians": {str(k): str(v) for k, v in tri.angles.items()},
            "isRight": bool(tri.is_right()),
            "isIsosceles": bool(tri.is_isosceles()),
            "isEquilateral": bool(tri.is_equilateral()),
        }
        verification["positiveArea"] = float(sp.N(tri.area)) > 0
        method = "sympy-triangle"

    elif op == "polygon-area":
        if len(req.points) < 3:
            raise ValueError("polygon-area requires at least 3 points")
        pts = [_point2(p, f"points[{i}]") for i, p in enumerate(req.points)]
        poly = Polygon(*pts)
        result = {
            "areaExact": str(poly.area),
            "areaApproximate": float(sp.N(abs(poly.area))),
            "perimeterExact": str(poly.perimeter),
            "centroid": _serialize_sympy(poly.centroid),
        }
        verification["nonzeroArea"] = abs(float(sp.N(poly.area))) > 0
        method = "sympy-polygon"

    elif op == "vector-angle":
        a = _require_point(req.vectorA, "vectorA")
        b = _require_point(req.vectorB, "vectorB")
        if a.size != b.size:
            raise ValueError("vector dimensions must match")
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            raise ValueError("vector-angle requires nonzero vectors")
        cosine = float(np.clip(np.dot(a,b)/(na*nb), -1, 1))
        radians = math.acos(cosine)
        result = {
            "dotProduct": float(np.dot(a,b)),
            "cosine": cosine,
            "angleRadians": radians,
            "angleDegrees": math.degrees(radians),
        }
        verification["cosineInRange"] = -1 <= cosine <= 1

    elif op == "vector-projection":
        a = _require_point(req.vectorA, "vectorA")
        b = _require_point(req.vectorB, "vectorB")
        if a.size != b.size:
            raise ValueError("vector dimensions must match")
        denom = float(np.dot(b,b))
        if denom == 0:
            raise ValueError("cannot project onto zero vector")
        scale = float(np.dot(a,b)/denom)
        projection = scale*b
        result = {
            "projection": projection.tolist(),
            "scalarCoefficient": scale,
            "residual": (a-projection).tolist(),
        }
        verification["residualOrthogonalToTarget"] = abs(float(np.dot(a-projection,b))) < 1e-10

    elif op == "trig-evaluate":
        if req.trigFunction is None or req.angle is None:
            raise ValueError("trig-evaluate requires trigFunction and angle")
        fn = req.trigFunction
        if fn in {"sin","cos","tan"}:
            radians = _angle_to_radians(req.angle, req.angleUnit)
            value = getattr(math, fn)(radians)
            result = {"value": value, "inputRadians": radians}
        else:
            inv = getattr(math, fn)
            radians = inv(req.angle)
            result = {
                "angleRadians": radians,
                "angleDegrees": math.degrees(radians),
            }
        method = "python-math-trigonometry"

    elif op == "trig-solve-right-triangle":
        a, b, h = req.sideA, req.sideB, req.hypotenuse
        provided = sum(v is not None for v in (a,b,h))
        if provided < 2:
            raise ValueError("provide any two of sideA, sideB, hypotenuse")
        if h is None:
            h = math.hypot(a,b)
        elif a is None:
            if h <= b:
                raise ValueError("hypotenuse must exceed leg")
            a = math.sqrt(h*h-b*b)
        elif b is None:
            if h <= a:
                raise ValueError("hypotenuse must exceed leg")
            b = math.sqrt(h*h-a*a)
        if abs(a*a+b*b-h*h) > 1e-8*max(1.0,h*h):
            raise ValueError("provided sides do not satisfy the Pythagorean theorem")
        alpha = math.degrees(math.atan2(a,b))
        beta = 90.0-alpha
        result = {
            "sideA": a, "sideB": b, "hypotenuse": h,
            "angleA_degrees": alpha, "angleB_degrees": beta,
            "area": 0.5*a*b,
            "perimeter": a+b+h,
        }
        verification["pythagoreanResidual"] = a*a+b*b-h*h
        method = "right-triangle-trigonometry"

    elif op == "coordinate-transform":
        if not req.points:
            raise ValueError("coordinate-transform requires points")
        if req.transform is None:
            raise ValueError("coordinate-transform requires transform")
        pts = np.asarray(req.points, dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError("coordinate-transform requires 2D points")
        if req.transform == "translate":
            if req.translate is None:
                raise ValueError("translate transform requires translate")
            out = pts + np.asarray(req.translate, dtype=float)
        elif req.transform == "scale":
            if req.scale is None:
                raise ValueError("scale transform requires scale")
            out = pts * np.asarray(req.scale, dtype=float)
        else:
            if req.angle is None:
                raise ValueError("rotate transform requires angle")
            theta = _angle_to_radians(req.angle, req.angleUnit)
            matrix = np.array([[math.cos(theta),-math.sin(theta)],
                               [math.sin(theta), math.cos(theta)]])
            out = pts @ matrix.T
            details["rotationMatrix"] = matrix.tolist()
        result = {"points": out.tolist()}
        method = f"coordinate-{req.transform}"

    else:
        raise ValueError(f"Unsupported geometry operation: {op}")

    body = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy-geometry-numpy",
        "runtime": "python",
        "method": method,
        "result": result,
        "details": details,
        "verification": verification,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok","resultHash"}}
    )
    return body


def calculation_object_extension(req: UnifiedCalculationRequest, geometry_req: GeometryRequest):
    obj = build_calculation_object(req)
    result = execute_geometry(geometry_req)
    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["geometry"] = result
    obj["result"]["geometry"] = result["result"]
    obj["executionPlan"]["geometry"] = {
        "runtime": "python",
        "engine": "sympy-geometry-numpy",
        "operation": geometry_req.operation,
        "method": result["method"],
    }
    obj["verification"]["geometry"] = result["verification"]
    obj["provenance"]["geometryResultHash"] = result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k:v for k,v in obj.items() if k not in {"ok","calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Geometry, Trigonometry & Coordinate Mathematics",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy-geometry-numpy",
        "wordpressRequired": False,
        "capabilities": {
            "euclideanDistanceMidpointSlope": True,
            "analyticLineGeometry": True,
            "lineIntersections": True,
            "circleGeometry": True,
            "circleLineIntersections": True,
            "triangleGeometry": True,
            "polygonAreaCentroid": True,
            "vectorAngles": True,
            "vectorProjection": True,
            "trigonometricEvaluation": True,
            "rightTriangleSolving": True,
            "coordinateTransforms": True,
            "exactAndApproximateGeometry": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v11120/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/geometry")
def geometry_route(req: GeometryRequest):
    return execute_geometry(req)


@router.post("/calculation-engine/v1/geometry/calculation-object")
def geometry_calculation_object_route(req: GeometryCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.geometry)
