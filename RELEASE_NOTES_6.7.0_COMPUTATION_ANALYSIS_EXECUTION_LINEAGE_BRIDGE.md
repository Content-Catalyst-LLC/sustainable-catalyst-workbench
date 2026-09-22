# Workbench v6.7.0 — Computation, Analysis & Execution Lineage Bridge

## Purpose

Workbench v6.7.0 turns the v6.6 unified research-session bridge into a reproducible computation-lineage participant. It maps externally executed Workbench runs into Platform Core's `sc.research.computation-analysis-execution-lineage.v1` contract while keeping computation, numerical methods, engineering analysis, and scientific execution owned by Workbench.

## Added

- `GET /integration/core/computation-lineage/manifest`
- `POST /integration/core/computation-lineage/executions/build`
- `POST /integration/core/computation-lineage/executions/components/build`
- `POST /integration/core/computation-lineage/executions/session-binding/build`
- `POST /integration/core/computation-lineage/executions/lifecycle/build`
- `POST /integration/core/computation-lineage/bundles/consume`
- `GET /v670/status`
- WordPress `[sc_workbench_core_execution_lineage_status]` bridge

## Exact Core lineage families

The adapter targets Core v2.87's execution registry and produces exact request shapes for:

- execution registration;
- versioned inputs and content hashes;
- parameter bindings;
- declared assumptions and evidence references;
- software/runtime environment capture;
- ordered execution steps;
- outputs, result references, schemas, and hashes;
- research-object / claim / evidence bindings;
- cross-execution dependencies;
- verification evidence;
- execution revisions; and
- immutable execution snapshots.

## Unified Core 3.0 session integration

When a real Core session ID is supplied, v6.7 also prepares a Core 3.0 unified-runtime `execution-binding` whose `execution_ref` points at the Core computation-lineage execution. This connects a Workbench run to the larger research project/session without duplicating the execution record.

## Two-phase execution lifecycle

1. Workbench prepares a computation execution registration request.
2. Platform Core persists the execution and returns the authoritative Core execution ID.
3. Workbench requires that Core-issued ID before it builds lineage component requests.
4. Workbench optionally binds that Core execution into the v6.6 unified research session.
5. Workbench can prepare lifecycle revisions and immutable snapshot requests.

## Security and authority boundary

- Workbench does not fabricate Core execution IDs.
- Core records externally executed lineage; Core does not execute Workbench code.
- No automatic Core HTTP dispatch or persistence is performed by v6.7.
- Core does not infer findings, claims, scientific validity, reproducibility, or truth from the lineage bridge.
- Consumed Core bundles are read-only context and do not automatically mutate Workbench projects.

## Migration

No Workbench database migration is required.

## Validation

- Focused backend integration/compatibility suite: 50 passed.
- Release/static suite: 14 passed.
- Repository-wide Python suite: 554 passed.
- ASGI endpoint probes: PASS.
- No Workbench database migration is required.
