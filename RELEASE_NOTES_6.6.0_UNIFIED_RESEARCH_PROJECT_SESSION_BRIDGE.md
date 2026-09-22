# Workbench v6.6.0 — Unified Research Project & Session Bridge

## Purpose

Workbench v6.6.0 turns the v6.5 runtime-contract adapter into a Core 3.0 research-session participant. It maps Workbench computational projects into Platform Core's unified research/scientific/investigation runtime without moving numerical execution or project authority into Core.

## Added

- `GET /integration/core/unified-runtime/manifest`
- `POST /integration/core/unified-runtime/sessions/build`
- `POST /integration/core/unified-runtime/projects/bind`
- `POST /integration/core/unified-runtime/executions/bind`
- `POST /integration/core/unified-runtime/visuals/bind`
- `POST /integration/core/unified-runtime/validations/bind`
- `POST /integration/core/unified-runtime/packages/bind`
- `POST /integration/core/unified-runtime/handoffs/bind`
- `POST /integration/core/unified-runtime/bundles/consume`
- `GET /v660/status`
- WordPress `[sc_workbench_core_session_status]` bridge

## Core 3.0 compatibility

The release targets `sc.research.unified-research-scientific-investigation-runtime.v1` and preserves `sc.research.unified-runtime-contract.v1` as the underlying runtime contract reference. The request fields match the Core 3.0 session, product, object, execution, visual, validation, package, and handoff binding services.

## Two-phase session lifecycle

1. Workbench prepares a session request.
2. Platform Core persists it and returns the canonical Core session ID.
3. Workbench requires that Core-issued ID before it will build phase-two bindings.
4. Workbench emits deterministic Core request envelopes; it does not dispatch or persist them automatically.

## Security and authority boundary

- Workbench does not fabricate Core session IDs.
- Core does not execute Workbench specialist computation.
- Workbench project objects remain authoritative in Workbench.
- Core stores reference-first research session bindings.
- No automatic remote action, publication, scientific certification, or determination of research truth is authorized by this bridge.

## Validation

- Focused backend + compatibility tests: 35 passed.
- Release/static tests: 9 passed.
- Repository-wide suite: 534 passed.
- No database migration is required for Workbench v6.6.0.
