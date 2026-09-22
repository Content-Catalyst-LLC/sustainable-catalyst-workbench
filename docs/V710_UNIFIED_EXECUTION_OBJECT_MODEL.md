# Workbench v7.1.0 — Unified Execution Object Model

v7.1.0 builds directly on the v7.0 unified scientific and engineering execution runtime. It introduces one canonical, reference-first execution object that can represent a single specialist execution or an ordered multi-step workflow without introducing a second execution engine.

## Added

- `sc-workbench-execution-object/1.0` canonical object schema.
- Deterministic execution-object identity and content-addressed object hashes.
- Single-execution and workflow-execution object projection.
- Declared input, dataset, parameter, environment, dependency, output, lineage, provenance, tag, and metadata sections.
- Full-fidelity execute-and-project mode plus reference/hash-only projection for pre-existing v7.0 results.
- Workflow child objects and explicit dependency edges.
- Integrity validation that detects object tampering and inline-result/content-hash mismatches.
- Explicit metadata-only object revisions with `previousObjectHash`; underlying scientific result content is immutable across revisions.
- Two-phase Platform Core binding plans for the v3 unified research runtime and v2.96 runtime-contract invocation/result registries.
- WordPress status surface and REST status route.

## API surfaces

- `GET /execution/objects/manifest`
- `POST /execution/objects/execute`
- `POST /execution/objects/workflow/run`
- `POST /execution/objects/project`
- `POST /execution/objects/validate`
- `POST /execution/objects/revise`
- `POST /integration/core/execution-objects/binding/plan`
- `GET /v710/status`

## Core contracts

- `sc.research.unified-runtime-contract.v1`
- `sc.research.unified-research-scientific-investigation-runtime.v1`
- `sc.research.computation-analysis-execution-lineage.v1`

## Boundaries

Workbench does not automatically persist execution objects, dispatch to Platform Core, replay executions, mutate scientific result content during revisions, certify scientific validity or reproducibility, rank outcomes, or determine truth.

No database migration is required.
