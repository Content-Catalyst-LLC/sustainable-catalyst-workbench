# Workbench v8.7.0 — Linked Scientific Views & Cross-Filtering

Workbench v8.7.0 turns the v8.6 Visual Research Canvas into a coordinated scientific inspection environment. A single declarative filter or explicit selection can now be projected across canvas, asset table, execution table, timeline, lineage, and facet views while the underlying project, environment, asset, execution, timeline, and scientific result records remain authoritative in their owning subsystems.

## Highlights

- Six synchronized views: canvas, assets, executions, timeline, lineage, and facets.
- Declarative cross-filtering by node kind, source authority, asset type/origin/tag, runtime kind, execution status, timeline event type, text, and ISO-8601 timeline range.
- Optional one-hop neighbor expansion using explicit canvas relationships.
- Cross-view selection propagation without persistent mutation of scientific objects.
- Deterministic facet counts for rapid research navigation.
- View-state hashes for reproducible linked-view inspection states.
- Two-phase Platform Core planning for view-state bindings through the existing unified research-session contract.

## Scientific boundaries

Linked views are inspection and composition state only. Filters do not delete, rewrite, grade, or reinterpret research objects. Selection does not establish importance, causality, truth, or preference. The release performs no automatic winner selection, no automatic scientific interpretation, and no automatic Platform Core dispatch or persistence.

## Persistence

No new database migration is required. v8.7 reuses the persistent Workbench research stores and the v8.6 canvas projection. Cross-filter and linked-selection state is computed on demand and is not silently persisted.
