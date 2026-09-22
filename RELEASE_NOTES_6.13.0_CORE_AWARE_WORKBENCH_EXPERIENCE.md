# Workbench v6.13.0 — Core-Aware Workbench Experience

## Summary

v6.13.0 turns the Platform Core integration work from v6.4–v6.12 into a coherent Workbench-facing experience. It adds a single context model, compatibility/readiness evaluation, Core-ID gap detection, and explicit next-action planning across the full integration stack.

## Added

- Core-aware context assembly across project/session/execution/visual/predictive/forensic/state/package/context references.
- Present/missing Core-ID detection.
- Compatibility/readiness evaluation for declared Core connectivity, version prefix, service-token state, and runtime contracts.
- Explicit next-action plans targeting existing Workbench integration endpoints.
- Cross-bridge manifest covering v6.4–v6.12.
- WordPress status shortcode and REST status route.
- Continued release-time guard against the historical `SCWB_DIR` bootstrap regression.

## Boundaries

v6.13.0 is a read/plan experience layer. It does not auto-dispatch to Core, auto-persist Core state, restore historical state, replay executions, fabricate Core IDs, execute specialist computation, or determine truth.

## Database

No database migration.
