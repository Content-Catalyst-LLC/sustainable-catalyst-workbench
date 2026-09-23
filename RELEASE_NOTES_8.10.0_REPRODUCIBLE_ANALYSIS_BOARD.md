# Workbench v8.10.0 — Reproducible Analysis Board

Workbench v8.10.0 adds a content-addressed analysis-board layer that assembles authoritative Workbench research objects into one reproducible analytical surface.

## Highlights
- Binds v8.2 project state, v8.3 research assets, v8.4 executions, v8.5 timeline/lineage context, v8.8 comparisons, and v8.9 scientific figures.
- Preserves source hashes instead of copying source-of-truth semantics into the board.
- Supports explicit researcher-authored assumptions, methods, findings, and notes.
- Produces deterministic `boardHash` values for reproducibility and comparison.
- Persists immutable, content-addressed analysis-board snapshots under the existing v8.1 Workbench data root.
- Exposes snapshot listing and integrity-validated snapshot retrieval.
- Adds explicit, plan-only Platform Core binding for reproducible analytical views.

## Boundaries
The board does not generate findings, select winners, infer causality, infer statistical significance, certify scientific validity, mutate source objects, or automatically dispatch/persist to Platform Core.

## Database
No database migration is required. Snapshot persistence uses the existing Workbench `/data` persistence mount.
