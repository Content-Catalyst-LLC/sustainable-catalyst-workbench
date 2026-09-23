# Sustainable Catalyst Workbench v8.7.0

Current release: **Workbench v8.7.0 — Linked Scientific Views & Cross-Filtering**.

v8.7.0 coordinates the v8.6 Visual Research Canvas with synchronized asset, execution, timeline, lineage, and facet views. A declarative filter or explicit node selection propagates across those views while project, environment, asset, execution, timeline, provenance, and scientific-result records remain authoritative in their owning Workbench subsystems.

The linked-view engine supports bounded filtering by object kind, authority, asset type/origin/tag, runtime/status, event type, text, ISO-8601 timeline range, and explicit node IDs, plus optional one-hop relationship expansion. Filters and selections are view state only: they do not rewrite scientific records, infer causality, grade evidence, or select a preferred result.

See `RELEASE_NOTES_8.7.0_LINKED_SCIENTIFIC_VIEWS_CROSS_FILTERING.md`, `V870_LINKED_SCIENTIFIC_VIEWS_MAP.md`, and `docs/V870_LINKED_SCIENTIFIC_VIEWS_CROSS_FILTERING.md` for the release contract and API map.
