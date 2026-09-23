# Linked Scientific Views & Cross-Filtering

Workbench v8.7.0 provides synchronized projections over the v8.6 canvas and its underlying authoritative v8 research stores.

## API

- `GET /linked-scientific-views/manifest`
- `POST /linked-scientific-views/query`
- `POST /linked-scientific-views/selection/resolve`
- `POST /integration/core/linked-scientific-views/plan`
- `GET /v870/status`

## Cross-filter request

The query accepts a project key, declarative filter specification, selected node IDs, source view, and timeline limit. Filtering operates over projected node metadata and explicit relationships only.

## Selection propagation

Selections are translated into row/node IDs for each synchronized view. Selection is not persisted as scientific state and does not change source records.

## Platform Core

Core integration remains two-phase. v8.7 may prepare an explicit `workbench.linked-scientific-view-state` binding plan when a Core session ID is supplied. The Workbench does not dispatch the request automatically.
