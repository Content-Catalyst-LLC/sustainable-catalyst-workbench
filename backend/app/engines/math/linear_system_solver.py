from __future__ import annotations

from typing import Any
import numpy as np


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    matrix = np.array(inputs.get("matrix", []), dtype=float)
    vector = np.array(inputs.get("vector", []), dtype=float)

    if matrix.ndim != 2 or matrix.size == 0:
        raise ValueError("matrix must be a non-empty 2D array")
    if vector.ndim != 1 or vector.shape[0] != matrix.shape[0]:
        raise ValueError("vector must be a 1D array with one entry per matrix row")

    rows, cols = matrix.shape
    rank_a = int(np.linalg.matrix_rank(matrix))
    augmented = np.column_stack([matrix, vector])
    rank_aug = int(np.linalg.matrix_rank(augmented))
    consistent = rank_a == rank_aug

    determinant = None
    condition_number = None
    solution = None
    residual_norm = None
    method = None

    if rows == cols:
        determinant = float(np.linalg.det(matrix))
        try:
            condition_number = float(np.linalg.cond(matrix))
            if condition_number > 1e8:
                warnings.append("The matrix is ill-conditioned; small input changes may cause large solution changes.")
        except np.linalg.LinAlgError:
            warnings.append("Could not compute a reliable condition number.")

    if not consistent:
        method = "least_squares_inconsistent_system"
        solution_arr, residuals, _, _ = np.linalg.lstsq(matrix, vector, rcond=None)
        solution = solution_arr.tolist()
        residual_norm = float(np.linalg.norm(matrix @ solution_arr - vector))
        warnings.append("The system is inconsistent; returned least-squares approximation instead of an exact solution.")
    elif rows == cols and rank_a == cols:
        method = "direct_solve"
        solution_arr = np.linalg.solve(matrix, vector)
        solution = solution_arr.tolist()
        residual_norm = float(np.linalg.norm(matrix @ solution_arr - vector))
    else:
        method = "least_squares_or_underdetermined"
        solution_arr, residuals, _, _ = np.linalg.lstsq(matrix, vector, rcond=None)
        solution = solution_arr.tolist()
        residual_norm = float(np.linalg.norm(matrix @ solution_arr - vector))
        if rank_a < cols:
            warnings.append("The system is rank-deficient or underdetermined; returned one least-norm/least-squares solution.")

    result = {
        "shape": {"rows": rows, "cols": cols},
        "rank_A": rank_a,
        "rank_augmented": rank_aug,
        "consistent": consistent,
        "determinant": determinant,
        "condition_number": condition_number,
        "method": method,
        "solution": solution,
        "residual_norm": residual_norm,
    }

    interpretation = (
        "The solver diagnoses structural solvability before returning a result. "
        "Rank equality indicates consistency; rank deficiency or a high condition number should be interpreted as a model-structure warning, not only a numerical detail."
    )
    return {"result": result, "warnings": warnings, "interpretation": interpretation}
