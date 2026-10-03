"""Workbench v11.7.0 — Units, Dimensions & Physical Quantities.

Promotes physical quantities to first-class calculation objects with unit
conversion, dimensional analysis, unit-aware arithmetic, derived quantities,
compatibility checks, and provenance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import pint
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-units-dimensions-physical-quantities-status/1.0"
QUANTITY_SCHEMA = "sc-workbench-physical-quantity-result/1.0"

router = APIRouter(tags=["workbench-v1170-units-dimensions-physical-quantities"])

ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
Q_ = ureg.Quantity


class QuantityOperand(BaseModel):
    magnitude: float
    unit: str = Field(max_length=300)


class PhysicalQuantityRequest(BaseModel):
    operation: Literal[
        "parse",
        "convert",
        "dimensionality",
        "compatible",
        "add",
        "subtract",
        "multiply",
        "divide",
        "power",
        "to-base-units",
        "derive",
        "consistency-check",
    ]
    expression: Optional[str] = Field(default=None, max_length=2000)
    targetUnit: Optional[str] = Field(default=None, max_length=300)
    left: Optional[QuantityOperand] = None
    right: Optional[QuantityOperand] = None
    exponent: Optional[float] = None
    operands: List[QuantityOperand] = Field(default_factory=list, max_length=100)
    formula: Optional[str] = Field(default=None, max_length=2000)


class QuantityCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    quantity: PhysicalQuantityRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _quantity_from_operand(op: QuantityOperand):
    return Q_(op.magnitude, op.unit)


def _dimension_map(quantity) -> Dict[str, float]:
    return {str(k): float(v) for k, v in quantity.dimensionality.items()}


def _serialize_quantity(quantity) -> Dict[str, Any]:
    base = quantity.to_base_units()
    return {
        "magnitude": float(quantity.magnitude),
        "unit": str(quantity.units),
        "text": str(quantity),
        "dimensionality": _dimension_map(quantity),
        "baseUnits": {
            "magnitude": float(base.magnitude),
            "unit": str(base.units),
            "text": str(base),
        },
    }


def _require_left(req: PhysicalQuantityRequest):
    if req.left is None:
        raise ValueError(f"{req.operation} requires left")
    return _quantity_from_operand(req.left)


def _require_right(req: PhysicalQuantityRequest):
    if req.right is None:
        raise ValueError(f"{req.operation} requires right")
    return _quantity_from_operand(req.right)


def execute_quantity(req: PhysicalQuantityRequest) -> Dict[str, Any]:
    details: Dict[str, Any] = {}
    verification: Dict[str, Any] = {}
    op = req.operation

    if op == "parse":
        if not req.expression:
            raise ValueError("parse requires expression")
        q = ureg(req.expression)
        result: Any = _serialize_quantity(q)

    elif op == "convert":
        if not req.expression or not req.targetUnit:
            raise ValueError("convert requires expression and targetUnit")
        source = ureg(req.expression)
        q = source.to(req.targetUnit)
        result = _serialize_quantity(q)
        details["source"] = _serialize_quantity(source)
        verification["dimensionPreserved"] = source.dimensionality == q.dimensionality

    elif op == "dimensionality":
        if not req.expression:
            raise ValueError("dimensionality requires expression")
        q = ureg(req.expression)
        result = {
            "dimensionality": _dimension_map(q),
            "baseUnits": _serialize_quantity(q)["baseUnits"],
        }

    elif op == "compatible":
        left = _require_left(req)
        right = _require_right(req)
        compatible = left.dimensionality == right.dimensionality
        result = compatible
        verification["leftDimensionality"] = _dimension_map(left)
        verification["rightDimensionality"] = _dimension_map(right)

    elif op == "add":
        left = _require_left(req)
        right = _require_right(req)
        q = left + right
        result = _serialize_quantity(q.to(left.units))
        verification["dimensionallyCompatible"] = left.dimensionality == right.dimensionality

    elif op == "subtract":
        left = _require_left(req)
        right = _require_right(req)
        q = left - right
        result = _serialize_quantity(q.to(left.units))
        verification["dimensionallyCompatible"] = left.dimensionality == right.dimensionality

    elif op == "multiply":
        left = _require_left(req)
        right = _require_right(req)
        result = _serialize_quantity(left * right)

    elif op == "divide":
        left = _require_left(req)
        right = _require_right(req)
        result = _serialize_quantity(left / right)

    elif op == "power":
        left = _require_left(req)
        if req.exponent is None:
            raise ValueError("power requires exponent")
        result = _serialize_quantity(left ** req.exponent)
        details["exponent"] = req.exponent

    elif op == "to-base-units":
        if not req.expression:
            raise ValueError("to-base-units requires expression")
        q = ureg(req.expression).to_base_units()
        result = _serialize_quantity(q)

    elif op == "derive":
        if not req.formula or not req.operands:
            raise ValueError("derive requires formula and operands")
        namespace = {
            f"q{i+1}": _quantity_from_operand(operand)
            for i, operand in enumerate(req.operands)
        }
        allowed = set(namespace.keys())
        tokens = (
            req.formula.replace("(", " ").replace(")", " ")
            .replace("*", " ").replace("/", " ").replace("+", " ")
            .replace("-", " ").replace("**", " ").split()
        )
        for token in tokens:
            if token.startswith("q") and token not in allowed:
                raise ValueError(f"Unknown quantity token: {token}")
        q = eval(req.formula, {"__builtins__": {}}, namespace)
        result = _serialize_quantity(q)
        details["formula"] = req.formula
        details["operands"] = {
            name: _serialize_quantity(quantity)
            for name, quantity in namespace.items()
        }

    elif op == "consistency-check":
        if not req.operands:
            raise ValueError("consistency-check requires operands")
        quantities = [_quantity_from_operand(x) for x in req.operands]
        first_dim = quantities[0].dimensionality
        consistent = all(q.dimensionality == first_dim for q in quantities)
        result = consistent
        verification["dimensions"] = [_dimension_map(q) for q in quantities]
        verification["allSameDimension"] = consistent

    else:
        raise ValueError(f"Unsupported physical quantity operation: {op}")

    body = {
        "ok": True,
        "schema": QUANTITY_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "pint",
        "runtime": "python",
        "result": result,
        "details": details,
        "verification": verification,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "resultHash"}}
    )
    return body


def calculation_object_extension(
    req: UnifiedCalculationRequest,
    quantity: PhysicalQuantityRequest,
):
    obj = build_calculation_object(req)
    result = execute_quantity(quantity)

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["physicalQuantity"] = result
    obj["result"]["physicalQuantity"] = result["result"]
    obj["units"] = {
        "engine": "pint",
        "operation": quantity.operation,
        "result": result["result"],
    }
    obj["executionPlan"]["physicalQuantity"] = {
        "runtime": "python",
        "engine": "pint",
        "operation": quantity.operation,
    }
    obj["verification"]["physicalQuantity"] = result["verification"]
    obj["provenance"]["physicalQuantityResultHash"] = result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Units, Dimensions & Physical Quantities",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "pint",
        "wordpressRequired": False,
        "capabilities": {
            "quantityParsing": True,
            "unitConversion": True,
            "dimensionality": True,
            "compatibilityChecking": True,
            "unitAwareAddition": True,
            "unitAwareSubtraction": True,
            "unitAwareMultiplication": True,
            "unitAwareDivision": True,
            "quantityPowers": True,
            "baseUnitNormalization": True,
            "derivedQuantities": True,
            "dimensionConsistencyChecks": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v1170/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/quantities")
def quantities_route(req: PhysicalQuantityRequest):
    return execute_quantity(req)


@router.post("/calculation-engine/v1/quantities/calculation-object")
def quantity_calculation_object_route(req: QuantityCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.quantity,
    )
