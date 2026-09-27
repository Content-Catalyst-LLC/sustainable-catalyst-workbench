# Workbench v10.4.0 — Hyperparameter Optimization & Search Engine

v10.4.0 adds content-addressed hyperparameter search studies on top of v10.2 training-run templates and v10.3 benchmark objectives.

## Added
- Typed float, integer, categorical, and boolean search spaces.
- Explicit tunable training/fine-tuning paths.
- Deterministic grid, seeded random, and Latin-hypercube trial manifests.
- Explicit Bayesian/custom external-optimizer contracts without automatic provider calls.
- Search budgets for trials, concurrency, wall time, CPU/GPU use, cost, and failures.
- Explicit, unauthorized-by-default execution plans.
- Immutable per-trial results and resumable search state.
- Objective diagnostics and ordering that do not imply model preference or scientific validity.
- Platform Core plan-only bindings.

## Boundaries
The release does not launch training automatically, call external optimizers, promote a trial or model, approve production deployment, infer scientific validity, or persist governed Platform Core objects automatically.
