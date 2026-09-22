# Workbench v7.3.0 — Dataset, Variable & Parameter Workspace

## Purpose

v7.3.0 establishes the canonical research-input layer used by later Workbench solvers, simulations, optimization, notebooks, and reusable workflows. Datasets, variables, parameter sets and assumptions are represented as deterministic content-addressed objects rather than ad-hoc request fields.

## Capabilities

- bounded inline or reference-first datasets
- typed variables with dataset-column bindings
- unit validation and conversion through Pint
- parameter sets with bounds and sensitivity roles
- declared assumptions with evidence/protocol references
- restricted SymPy-derived scalar values without Python eval/exec
- explicit workspace-to-execution binding plans
- Platform Core computation-lineage input/parameter/assumption plans

## Canonical endpoints

- `GET /data-workspace/manifest`
- `POST /data-workspace/build`
- `POST /data-workspace/units/convert`
- `POST /data-workspace/derive`
- `POST /data-workspace/execution-binding/plan`
- `POST /integration/core/data-workspace/lineage/plan`
- `GET /v730/status`

## Platform Core

Core integration uses `sc.research.computation-analysis-execution-lineage.v1`. Dataset inputs, parameters and assumptions are only planned against a Core-issued execution id. Workbench does not invent Core execution ids and does not dispatch or persist the plans automatically.

## Boundaries

No arbitrary Python, shell, R, or Julia execution; no hidden data fetching; no automatic persistence or execution; no automatic Core dispatch; no scientific-validity, reproducibility, ranking, or truth certification.

## Database

No database migration.
