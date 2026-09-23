# Workbench v8.10.0 — Reproducible Analysis Board Map

## Flow
Project (v8.2) → assets (v8.3) + executions (v8.4) → timeline/lineage (v8.5) → comparison (v8.8) + figures (v8.9) → Reproducible Analysis Board (v8.10) → immutable snapshot → explicit Platform Core binding plan.

## Board object
A board contains project identity/revision, selected source references, deterministic analytical views, researcher-authored narrative, provenance hashes, reproducibility metadata, timeline context, and lineage context.

## Snapshot object
Snapshots are immutable content-addressed records under the existing Workbench persistence root. Saving the same board twice is idempotent.

## Authority separation
The board remains an analytical assembly. Projects, assets, jobs/results, timeline events, comparisons, and figures retain their existing authorities.
