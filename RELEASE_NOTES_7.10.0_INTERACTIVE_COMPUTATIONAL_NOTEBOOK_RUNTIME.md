# Workbench v7.10.0 — Interactive Computational Notebook Runtime

Workbench v7.10.0 introduces a content-addressed computational notebook runtime over the bounded scientific and engineering runtimes delivered in v7.0–v7.9.

## Capabilities
- Typed notebook cells: markdown, unified operation, solver, simulation, engineering, design-space, and validation.
- Explicit `dependsOn` relationships and source-path → target-path bindings.
- Deterministic notebook hashes and notebook-run hashes.
- Preserved execution objects for executable cells.
- Notebook-run integrity validation and replay planning.
- Projection into a v7.9 Scientific Workflow Graph.
- Two-phase Platform Core workflow planning via `sc.research.workflow-orchestration.v1`.

## Reproducibility boundary
The notebook runtime does not expose a hidden interpreter namespace. Values move between executable cells only through declared dependency bindings. Markdown cells are descriptive and non-executable. Replay plans do not automatically re-execute cells and do not authorize hidden-state restoration.

## Platform Core boundary
Workbench prepares workflow, stage, context-binding, and event requests. Core must issue the workflow ID. No automatic Core dispatch or persistence occurs.

## Safety / scientific boundary
Successful execution or replayability does not certify scientific validity, truth, engineering safety, fitness for purpose, or regulatory compliance.

## Database
No database migration is required.
