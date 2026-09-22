# Workbench v6.13.0 — Core-Aware Workbench Experience

v6.13.0 adds a read/plan experience layer over the Platform Core integrations delivered in v6.4–v6.12. It does not create a second Core client or an automatic orchestration engine.

## Experience goals

- show one coherent Core-aware context for the active Workbench project;
- expose which Core-issued identifiers are present and which are still missing;
- summarize readiness across connectivity, runtime contract, research session, execution lineage, scenario/uncertainty, visual reasoning, predictive intelligence, forensic quantitative reconstruction, and research state;
- evaluate declared compatibility without auto-repair;
- generate explicit next-action plans that point to existing Workbench integration endpoints;
- preserve manual review before any Core write, state restore, execution replay, or cross-product transition.

## New API surface

- `GET /integration/core/experience/manifest`
- `POST /integration/core/experience/context/assemble`
- `POST /integration/core/experience/compatibility/evaluate`
- `POST /integration/core/experience/actions/plan`
- `GET /v6130/status`

## WordPress

- REST: `/wp-json/sc-workbench/v1/core-aware/status`
- Shortcode: `[sc_workbench_core_aware_status]`

## Boundaries

The experience layer does not execute specialist computation, dispatch Core writes, persist Core state, restore snapshots, replay executions, fabricate Core identifiers, or determine research truth.
