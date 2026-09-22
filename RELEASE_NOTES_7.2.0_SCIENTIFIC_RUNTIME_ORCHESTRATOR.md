# Workbench v7.2.0 — Scientific Runtime Orchestrator

## Purpose

v7.2.0 adds the routing/orchestration layer above v7.0 execution and v7.1 execution objects. A declared scientific or engineering operation is mapped deterministically to a bounded runtime adapter; local adapters execute only already-allowlisted Workbench operations, while uninstalled R, Julia and generic ML runtimes remain explicit handoff plans.

## Runtime adapters

- Workbench Symbolic Mathematics
- Workbench Numerical Scientific Computing
- Workbench Simulation & Systems
- Workbench Controls & Signals
- Workbench Measurement & Instrumentation
- Workbench Electronics & Digital Hardware
- Workbench Uncertainty & Sensitivity
- Workbench Predictive Runtime
- Workbench Forensic Quantitative Runtime
- Workbench Energy Runtime
- External R (plan-only)
- External Julia (plan-only)
- External ML (plan-only)

## Canonical endpoints

- `GET /execution/orchestrator/manifest`
- `GET /execution/orchestrator/runtimes`
- `POST /execution/orchestrator/route`
- `POST /execution/orchestrator/execute`
- `POST /execution/orchestrator/workflow/run`
- `POST /execution/orchestrator/external/plan`
- `POST /integration/core/runtime-orchestrator/workflow/plan`
- `GET /v720/status`

## Platform Core

The Core planner targets the exact Platform Core v2.90 contract `sc.research.workflow-orchestration.v1` and its `/v1/research/workflows` surfaces. Core records declared workflow/stage/context/event state; it does not infer stage completion or execute specialist computation. Core workflow IDs must be issued by Core before dependent stage/context/event plans are built.

## Safety boundaries

No arbitrary Python/R/Julia, shell commands, dynamic imports, automatic external runtime dispatch, automatic Core persistence, scientific-validity certification, ranking, or truth determination.

## Database

No database migration.
