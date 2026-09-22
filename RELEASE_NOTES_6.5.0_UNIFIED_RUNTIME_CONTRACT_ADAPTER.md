# Sustainable Catalyst Workbench v6.5.0 — Unified Runtime Contract Adapter

v6.5.0 advances the Platform Core integration roadmap from connectivity to contract interoperability.

## Added

- Deterministic adapter for `sc.research.unified-runtime-contract.v1`.
- Core runtime-contract manifest with Workbench product, operation, capability, and object-type declarations.
- Core contract-bundle validation against declared Workbench capabilities.
- Core-compatible Workbench product-binding request builder.
- Canonical Workbench project/object → Core reference mapping.
- Inbound Core exchange-envelope consumer with explicit, non-executing import plans.
- Outbound Core exchange request builder.
- Core invocation-lineage request builder.
- Core result-binding builder with optional deterministic result-payload hashing.
- Service-token enforcement inherited from v6.4 for the entire runtime-contract integration surface.
- WordPress runtime-contract status bridge and `[sc_workbench_runtime_contract_status]` shortcode.

## Boundaries retained

- Platform Core does not directly execute Workbench specialist code.
- Receiving a Core envelope does not automatically start computation.
- v6.5 does not automatically dispatch writes to Core.
- v6.5 does not persist Core state locally.
- Scientific-result validity is not certified by the adapter.
- Existing Workbench scientific, engineering, Energy Systems, and v6.0 canonical-project endpoints remain backward compatible.

## Validation

- Backend suite: 33 passed.
- Repository-level suite: 481 passed.
- Focused v6.5 adapter/backend tests: 19 passed.
- v6.5 + v6.4 static release tests: 5 passed.

## R2 release-validator repair

The macOS apply/push package now handles FastAPI/Starlette `_IncludedRouter` entries during the post-test route assembly check. This changes release validation only; the v6.5 runtime-contract adapter API and backend behavior are unchanged. The installer also reuses an already-populated isolated v6.5 test environment when available.

### R3 release-validator compatibility repair

The release validator now probes the assembled FastAPI application through
`TestClient` instead of enumerating internal `app.routes` objects. FastAPI
0.141/Starlette 1.6 can retain nested `_IncludedRouter` objects that do not
expose a direct `.path`, even though their child endpoints resolve correctly.
This repair changes validation only; the v6.5 runtime-contract API behavior is
unchanged.
