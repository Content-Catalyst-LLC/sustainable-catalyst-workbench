# Workbench v7.11.0 — Visual Scientific Computing Workspace

v7.11.0 adds a renderer-neutral scientific visualization workspace over the v7 computation stack. It supports linked scientific views, explicit selection/filter/cursor state, bounded parameter-control recomputation plans, notebook-result projection, and two-phase Platform Core visual-reasoning registration plans.

Supported scientific views include line/scatter, trajectories, uncertainty bands and distributions, matrices/heatmaps, numerical convergence, Pareto/design-space views, tables, and scalar metrics.

## Boundaries

- Workbench owns scientific computation and preparation of renderer-neutral view specifications.
- Controls prepare explicit runtime-request mutations; they do not execute automatically.
- Cross-view state is explicit and content-addressed; hidden dataflow is not authorized.
- Platform Core remains the semantic visual-object, scene, grammar, linked-view, query, and unified-workspace authority.
- Workbench never automatically dispatches or persists visual objects to Platform Core.
- Visual presentation does not certify scientific validity, truth, safety, or fitness for purpose.
