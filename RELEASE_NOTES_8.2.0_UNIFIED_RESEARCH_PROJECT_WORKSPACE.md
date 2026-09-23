# Sustainable Catalyst Workbench v8.2.0 — Unified Research Project Workspace

v8.2.0 adds a durable project-centric workspace above v8.0 unified research environments and v8.1 persistence/recovery.

## Highlights
- Project workspace with research question, objectives, tags, status and active environment reference.
- Dashboard summaries across data, notebook, workflow, visual, validation, solver, simulation, engineering, design-space and package surfaces.
- Atomic project persistence with optimistic project-revision checks.
- Project activity history without duplicating v8.1 environment revision history.
- Explicit project surface navigation plans; no scientific execution or hidden replay.
- Two-phase Platform Core project/session planning using the existing unified research runtime contract.

## Boundary
v8.1 remains authoritative for research-environment revisions, checkpoints and recovery. v8.2 stores project metadata and the pointer to the active environment/revision; it does not rewrite environment history.
