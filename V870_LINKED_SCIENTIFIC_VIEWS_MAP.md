# Workbench v8.7.0 — Linked Scientific Views Map

## Input authorities

- v8.1 Research Environment Persistence & Recovery
- v8.2 Unified Research Project Workspace
- v8.3 Research Asset & Artifact Registry
- v8.4 Interactive Execution Console
- v8.5 Research Timeline & Run History
- v8.6 Visual Research Canvas

## Linked-view pipeline

`authoritative stores -> v8.6 canvas projection -> declarative filter -> matched node set -> relationship closure (optional) -> synchronized scientific views -> explicit selection propagation`

## Views

1. **Canvas** — filtered visual nodes and explicit edges with v8.6 persisted layout retained.
2. **Assets** — source/dataset/artifact table projection.
3. **Executions** — runtime/status/result-lineage table projection.
4. **Timeline** — chronologically ordered event projection.
5. **Lineage** — filtered node/edge projection with linked-degree diagnostics.
6. **Facets** — deterministic counts for kinds, authorities, asset metadata, runtime/status, and event types.

## Filter vocabulary

- node kinds
- source authorities
- asset types
- asset origins
- asset tags
- runtime kinds
- execution statuses
- timeline event types
- text
- ISO-8601 timeline start/end
- explicit node IDs
- one-hop neighbor expansion

## Boundaries

The linked-view engine does not mutate authoritative research objects, execute scientific workloads, infer causality, certify scientific validity, rank hypotheses, choose a winner, or automatically persist/dispatch to Platform Core.
