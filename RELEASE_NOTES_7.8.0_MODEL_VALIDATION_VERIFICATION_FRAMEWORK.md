# Workbench v7.8.0 — Model Validation & Verification Framework

v7.8.0 introduces a reproducible validation and verification layer over Sustainable Catalyst Workbench scientific and engineering outputs.

## Added
- Scalar/reference benchmark evaluation with explicit absolute/relative tolerance policies.
- Observed-versus-predicted dataset comparison with MAE, RMSE, maximum absolute error, bias, and R² diagnostics.
- Numerical convergence verification that consumes v7.4 convergence-study evidence.
- Content-addressed V&V reports with assumptions, limitations, dataset/method references, evidence hashes, integrity validation, and explicit pass/fail/incomplete status.
- Platform Core computation-lineage verification planning using the existing `sc.research.computation-analysis-execution-lineage.v1` contract and Core-issued execution IDs.
- WordPress runtime status bridge and shortcode.

## Boundaries
A passing report means only that declared checks satisfied declared tolerances. v7.8.0 does not certify scientific truth, fitness for purpose, engineering safety, building/code compliance, regulatory acceptance, or automatic model acceptance. No endpoint automatically dispatches or persists data to Platform Core.
