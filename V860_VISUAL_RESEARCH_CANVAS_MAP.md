# Workbench v8.6.0 — Visual Research Canvas Map

## Research object flow

`v8.2 Project Workspace` → `v8.1 Active Environment` → `v8.3 Assets` → `v8.4 Executions` → `v8.5 Timeline / Lineage` → **`v8.6 Visual Research Canvas`**

## Canvas layers

- **Project layer** — active project identity and revision.
- **Environment layer** — active persisted research-environment revision.
- **Asset layer** — latest project-scoped research asset/artifact records.
- **Execution layer** — durable execution-console jobs and result references.
- **Timeline layer** — content-addressed v8.5 chronological events.
- **Lineage overlay** — v8.5 revision/transition relationships projected as visual edges.
- **Researcher link layer** — explicit user-created visual relationships; these are not inferred scientific claims.

## Persistence model

v8.6 persists only visual composition state: node geometry, visibility, pinned state, viewport, layer toggles, and explicit researcher-authored visual links. Every scientific node continues to point to its owning subsystem through `sourceRef`, `sourceHash`, and `sourceAuthority`.

## Platform Core boundary

Workbench prepares a two-phase binding plan for the visual canvas layout after a Core session exists. The binding identifies the canvas as `workbench.visual-research-canvas-layout` with role `view-composition`; it does not promote the visual arrangement into a scientific truth claim or authorize automatic Core dispatch.
