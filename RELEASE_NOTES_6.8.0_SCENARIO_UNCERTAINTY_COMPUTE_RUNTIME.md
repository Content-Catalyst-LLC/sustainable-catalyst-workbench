# Workbench v6.8.0 — Scenario & Uncertainty Compute Runtime Integration

Workbench v6.8.0 connects Platform Core's scenario-compute and uncertainty-compute orchestration surfaces to Workbench as the specialist numerical execution plane.

## Added

- Core `scenario-compute-input-manifest-v1` consumption without automatic local execution.
- Deterministic Monte Carlo and Latin-hypercube sampling.
- Sobol design generation and externally supplied-output Sobol index analysis.
- Morris design generation and elementary-effects analysis.
- Ensemble weight normalization and descriptive statistics.
- Empirical exceedance probability with a Wilson 95% confidence interval.
- Deterministic affine scenario execution against Core parameter manifests.
- Core scenario-attempt, model-run-binding, and result-binding callback request planning.
- Direct v6.7 computation-lineage registration/component planning for scenario executions.
- WordPress runtime-status bridge and `[sc_workbench_scenario_uncertainty_status]`.

## Execution boundary

Platform Core remains authoritative for research scenarios, uncertainty definitions, sensitivity-study semantics, ensemble semantics, provenance, and research-session context. Workbench performs specialist numerical computation. Core does not send arbitrary code to Workbench through v6.8, and Workbench does not automatically dispatch or persist data to Core.

## Compatibility

- Platform Core scenario endpoints: `/v1/scenario-compute/*`
- Platform Core uncertainty endpoints: `/v1/uncertainty-compute/*`
- Scenario manifest schema: `scenario-compute-input-manifest-v1`
- Workbench v6.7 lineage contract: `sc.research.computation-analysis-execution-lineage.v1`
- No Workbench database migration.
