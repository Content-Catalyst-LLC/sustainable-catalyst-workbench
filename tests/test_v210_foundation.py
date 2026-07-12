"""Lightweight regression tests for Workbench v2.1.0 pure calculations."""
from app.v210 import linear_fit


def test_linear_fit_exact_relationship() -> None:
    result = linear_fit([0.0, 1.0, 2.0], [1.0, 3.0, 5.0])
    assert result["slope"] == 2.0
    assert result["intercept"] == 1.0
    assert result["rmse"] == 0.0
    assert result["r2"] == 1.0
