# Workbench v8.6.0 — Visual Research Canvas

Workbench v8.6.0 adds a project-scoped visual composition surface over the authoritative Workbench v8 research environment. Projects, active environments, registered research assets, execution jobs, and v8.5 timeline events can be viewed together as linked canvas objects without copying or rewriting their scientific records.

## Highlights

- Deterministic visual nodes for v8.1–v8.5 authoritative research objects.
- Persistent drag/layout state with optimistic layout revisions and integrity hashes.
- Researcher-authored visual links stored separately from derived provenance/lineage relationships.
- v8.5 timeline nodes and lineage overlays inside the visual workspace.
- Linked node selection for downstream inspection and handoff planning.
- Two-phase Platform Core canvas-layout binding plans through the existing unified research session contract.
- WordPress interactive canvas shortcode: `[sc_workbench_visual_research_canvas project="PROJECT_KEY"]`.
- WordPress status shortcode: `[sc_workbench_visual_research_canvas_status]`.

## Authority boundary

The canvas is a view-composition layer, not a scientific source of truth. It stores positions, dimensions, visibility, viewport state, layer choices, and explicit researcher-authored visual links. Project state remains owned by v8.2, research-environment state by v8.1, asset records by v8.3, execution jobs/results by v8.4, and timeline/lineage projections by v8.5.

The canvas does not automatically execute scientific workloads, infer causality, grade evidence, select winners, alter scientific results, or dispatch/persist to Platform Core.

## Persistence

No database migration is required. Canvas layout state is stored under the existing Workbench `/data` persistence mount alongside—but separate from—the authoritative research stores.
