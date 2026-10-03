"""Workbench v11.4.0 — Linear Algebra, Matrix & Tensor Engine.

Adds exact symbolic matrix algebra and numerical matrix/tensor computation to
the unified v11 CalculationObject architecture.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-linear-algebra-matrix-tensor-status/1.0"
LINEAR_SCHEMA = "sc-workbench-linear-algebra-result/1.0"

router = APIRouter(tags=["workbench-v1140-linear-algebra-matrix-tensor"])


class LinearAlgebraRequest(BaseModel):
    operation: Literal[
        "determinant",
        "inverse",
        "rank",
        "trace",
        "transpose",
        "rref",
        "nullspace",
        "columnspace",
        "eigenvalues",
        "eigenvectors",
        "characteristic-polynomial",
        "solve-linear-system",
        "matrix-multiply",
        "kronecker-product",
        "outer-product",
        "tensor-contract",
        "tensor-transpose",
        "tensor-reshape",
        "tensor-norm",
    ]
    matrix: Optional[List[List[Any]]] = None
    matrixB: Optional[List[List[Any]]] = None
    vector: Optional[List[Any]] = None
    tensor: Optional[Any] = None
    tensorB: Optional[Any] = None
    axes: Optional[Any] = None
    permutation: Optional[List[int]] = None
    shape: Optional[List[int]] = None
    exact: bool = True
    tolerance: float = Field(default=1e-12, gt=0)


class LinearCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    linearAlgebra: LinearAlgebraRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _sympify_nested(value: Any) -> Any:
    if isinstance(value, list):
        return [_sympify_nested(v) for v in value]
    return sp.sympify(value)


def _sympy_matrix(matrix: Optional[List[List[Any]]]) -> sp.Matrix:
    if matrix is None:
        raise ValueError("matrix is required")
    return sp.Matrix(_sympify_nested(matrix))


def _numpy_array(value: Any) -> np.ndarray:
    if value is None:
        raise ValueError("tensor or matrix input is required")
    return np.asarray(value, dtype=float)


def _serialize(value: Any) -> Any:
    if isinstance(value, sp.MatrixBase):
        return [[str(v) for v in row] for row in value.tolist()]
    if isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    return value


def execute_linear_algebra(req: LinearAlgebraRequest) -> Dict[str, Any]:
    op = req.operation
    details: Dict[str, Any] = {}
    verification: Dict[str, Any] = {}

    exact_ops = {
        "determinant", "inverse", "rank", "trace", "transpose", "rref",
        "nullspace", "columnspace", "eigenvalues", "eigenvectors",
        "characteristic-polynomial", "solve-linear-system", "matrix-multiply",
        "kronecker-product", "outer-product",
    }

    use_exact = bool(req.exact and op in exact_ops)
    engine = "sympy" if use_exact else "numpy"
    method = op

    if op == "determinant":
        if use_exact:
            A = _sympy_matrix(req.matrix)
            result = sp.factor(A.det())
            details["shape"] = list(A.shape)
        else:
            A = _numpy_array(req.matrix)
            result = float(np.linalg.det(A))
            details["shape"] = list(A.shape)

    elif op == "inverse":
        if use_exact:
            A = _sympy_matrix(req.matrix)
            result = A.inv()
            residual = sp.simplify(A * result - sp.eye(A.rows))
            verification["identityResidualZero"] = residual == sp.zeros(A.rows)
        else:
            A = _numpy_array(req.matrix)
            result = np.linalg.inv(A)
            verification["identityResidualMaxAbs"] = float(np.max(np.abs(A @ result - np.eye(A.shape[0]))))

    elif op == "rank":
        if use_exact:
            A = _sympy_matrix(req.matrix)
            result = int(A.rank())
        else:
            A = _numpy_array(req.matrix)
            result = int(np.linalg.matrix_rank(A, tol=req.tolerance))

    elif op == "trace":
        if use_exact:
            A = _sympy_matrix(req.matrix)
            result = A.trace()
        else:
            A = _numpy_array(req.matrix)
            result = float(np.trace(A))

    elif op == "transpose":
        if use_exact:
            result = _sympy_matrix(req.matrix).T
        else:
            result = _numpy_array(req.matrix).T

    elif op == "rref":
        A = _sympy_matrix(req.matrix)
        rref, pivots = A.rref()
        result = rref
        details["pivots"] = [int(p) for p in pivots]
        engine = "sympy"

    elif op == "nullspace":
        A = _sympy_matrix(req.matrix)
        basis = A.nullspace()
        result = [v for v in basis]
        details["dimension"] = len(basis)
        engine = "sympy"

    elif op == "columnspace":
        A = _sympy_matrix(req.matrix)
        basis = A.columnspace()
        result = [v for v in basis]
        details["dimension"] = len(basis)
        engine = "sympy"

    elif op == "eigenvalues":
        if use_exact:
            A = _sympy_matrix(req.matrix)
            eigs = A.eigenvals()
            result = [{"value": str(k), "multiplicity": int(v)} for k, v in eigs.items()]
        else:
            A = _numpy_array(req.matrix)
            vals = np.linalg.eigvals(A)
            result = [complex(v) if np.iscomplexobj(v) else float(v) for v in vals]

    elif op == "eigenvectors":
        if use_exact:
            A = _sympy_matrix(req.matrix)
            raw = A.eigenvects()
            result = [
                {
                    "value": str(value),
                    "algebraicMultiplicity": int(mult),
                    "vectors": [_serialize(v) for v in vectors],
                }
                for value, mult, vectors in raw
            ]
        else:
            A = _numpy_array(req.matrix)
            vals, vecs = np.linalg.eig(A)
            result = {
                "values": [complex(v) if np.iscomplexobj(v) else float(v) for v in vals],
                "vectors": vecs.tolist(),
            }

    elif op == "characteristic-polynomial":
        A = _sympy_matrix(req.matrix)
        lam = sp.Symbol("lambda")
        result = sp.expand(A.charpoly(lam).as_expr())
        engine = "sympy"

    elif op == "solve-linear-system":
        if req.vector is None:
            raise ValueError("solve-linear-system requires vector")
        if use_exact:
            A = _sympy_matrix(req.matrix)
            b = sp.Matrix(_sympify_nested(req.vector))
            solution = A.gauss_jordan_solve(b)[0]
            result = solution
            verification["residualZero"] = sp.simplify(A * solution - b) == sp.zeros(A.rows, 1)
        else:
            A = _numpy_array(req.matrix)
            b = _numpy_array(req.vector)
            solution = np.linalg.solve(A, b)
            result = solution
            verification["residualMaxAbs"] = float(np.max(np.abs(A @ solution - b)))

    elif op == "matrix-multiply":
        if req.matrixB is None:
            raise ValueError("matrix-multiply requires matrixB")
        if use_exact:
            A = _sympy_matrix(req.matrix)
            B = _sympy_matrix(req.matrixB)
            result = A * B
        else:
            result = _numpy_array(req.matrix) @ _numpy_array(req.matrixB)

    elif op == "kronecker-product":
        if req.matrixB is None:
            raise ValueError("kronecker-product requires matrixB")
        if use_exact:
            result = sp.kronecker_product(_sympy_matrix(req.matrix), _sympy_matrix(req.matrixB))
        else:
            result = np.kron(_numpy_array(req.matrix), _numpy_array(req.matrixB))

    elif op == "outer-product":
        if req.vector is None:
            raise ValueError("outer-product requires vector")
        left = req.matrix[0] if req.matrix and len(req.matrix) == 1 else None
        if left is None:
            raise ValueError("outer-product uses first vector in matrix as left operand")
        if use_exact:
            a = sp.Matrix(_sympify_nested(left))
            b = sp.Matrix(_sympify_nested(req.vector))
            result = a * b.T
        else:
            result = np.outer(np.asarray(left, dtype=float), np.asarray(req.vector, dtype=float))

    elif op == "tensor-contract":
        if req.tensor is None or req.tensorB is None:
            raise ValueError("tensor-contract requires tensor and tensorB")
        a = _numpy_array(req.tensor)
        b = _numpy_array(req.tensorB)
        axes = req.axes if req.axes is not None else 1
        result = np.tensordot(a, b, axes=axes)
        details["axes"] = axes
        engine = "numpy"

    elif op == "tensor-transpose":
        a = _numpy_array(req.tensor)
        permutation = req.permutation if req.permutation is not None else list(reversed(range(a.ndim)))
        result = np.transpose(a, axes=permutation)
        details["permutation"] = permutation
        engine = "numpy"

    elif op == "tensor-reshape":
        if not req.shape:
            raise ValueError("tensor-reshape requires shape")
        a = _numpy_array(req.tensor)
        result = np.reshape(a, req.shape)
        details["shape"] = req.shape
        engine = "numpy"

    elif op == "tensor-norm":
        a = _numpy_array(req.tensor)
        result = float(np.linalg.norm(a))
        details["shape"] = list(a.shape)
        engine = "numpy"

    else:
        raise ValueError(f"Unsupported linear algebra operation: {op}")

    body = {
        "ok": True,
        "schema": LINEAR_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": engine,
        "method": method,
        "exact": engine == "sympy",
        "result": _serialize(result),
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
    linear: LinearAlgebraRequest,
) -> Dict[str, Any]:
    obj = build_calculation_object(req)
    linear_result = execute_linear_algebra(linear)

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["linearAlgebra"] = linear_result
    obj["result"]["linearAlgebra"] = linear_result["result"]
    obj["executionPlan"]["linearAlgebra"] = {
        "engine": linear_result["engine"],
        "method": linear_result["method"],
        "operation": linear.operation,
        "exact": linear_result["exact"],
    }
    obj["verification"]["linearAlgebra"] = linear_result["verification"]
    obj["provenance"]["linearAlgebraResultHash"] = linear_result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Linear Algebra, Matrix & Tensor Engine",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "engines": {
            "symbolicExact": "sympy",
            "numericalTensor": "numpy",
        },
        "capabilities": {
            "determinant": True,
            "inverse": True,
            "rank": True,
            "trace": True,
            "transpose": True,
            "rref": True,
            "nullspace": True,
            "columnspace": True,
            "eigenAnalysis": True,
            "characteristicPolynomial": True,
            "linearSystems": True,
            "matrixMultiplication": True,
            "kroneckerProduct": True,
            "outerProduct": True,
            "tensorContraction": True,
            "tensorTranspose": True,
            "tensorReshape": True,
            "tensorNorm": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v1140/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/linear-algebra")
def linear_algebra_route(req: LinearAlgebraRequest):
    return execute_linear_algebra(req)


@router.post("/calculation-engine/v1/linear-algebra/calculation-object")
def linear_algebra_calculation_object_route(req: LinearCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.linearAlgebra,
    )
