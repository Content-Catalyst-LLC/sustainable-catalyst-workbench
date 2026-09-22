# Workbench v7.4.0 — Numerical Methods & Solver Runtime

v7.4 promotes Workbench numerical methods into a canonical, bounded solver runtime above the v7.0 unified execution runtime, v7.1 execution objects, v7.2 runtime orchestration, and v7.3 data workspace.

## Major capabilities
- Canonical problem specifications for root finding, quadrature, differentiation, interpolation, ODE/IVP solving, linear algebra, and bounded optimization.
- Explicit solver catalog with deterministic selection and no silent fallback.
- Normalized convergence, residual, conditioning, function-evaluation, and error diagnostics.
- Refinement-based convergence studies for roots, integration, differentiation, and ODE problems.
- v7.3 workspace-to-solver binding plans with content-addressed input references.
- v7.1 execution-object projection through the v7.2 numerical runtime adapter.
- Two-phase Platform Core computation-lineage output registration using Core-issued execution IDs.

## Boundaries
- No arbitrary Python, shell, dynamic imports, or `eval`/`exec`.
- No automatic solver fallback.
- No automatic Platform Core dispatch or persistence.
- Solver convergence diagnostics are numerical evidence, not scientific-validity certification or mathematical proof.

No database migration is required.
