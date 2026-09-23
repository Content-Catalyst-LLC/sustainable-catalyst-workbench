# Workbench v8.5.0 — Research Timeline & Run History

Workbench v8.5.0 adds a project-wide chronological view over the authoritative v8 research stores. It derives project activity from v8.2, environment revision/checkpoint/recovery history from v8.1, asset revision history from v8.3, and execution lifecycle/run history from v8.4 without creating a competing source of truth.

## Highlights
- Content-addressed timeline events with explicit timestamp provenance.
- Project-wide source filtering and text filtering.
- Durable execution run-history inspection using v8.4 job records.
- Revision and transition lineage graph across project, environment, checkpoint, asset and execution events.
- Neutral event comparison with no automatic winner, scientific interpretation or causal inference.
- Two-phase Platform Core event binding plans through the existing unified research session contract.
- v8.3 asset records created under v8.5 include `registeredAt`; older v8.3 records remain valid and are explicitly marked as undated when projected into the timeline.

## Boundaries
The timeline is a derived projection. It does not rewrite project/environment/asset/job history, does not use filesystem mtime as authoritative chronology, does not execute scientific workloads, and does not automatically dispatch or persist to Platform Core.

No database migration is required. Persistent state remains under the Workbench `/data` mount established in v8.1.
