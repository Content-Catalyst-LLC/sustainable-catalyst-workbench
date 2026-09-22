# Workbench 6.4.0 — Platform Core Connectivity Foundation

Workbench 6.4.0 establishes the first native Platform Core integration boundary while preserving the existing specialist computation surface.

## Added

- `GET /health` — Core-compatible product health and release identity.
- `GET /runtime` — explicit Workbench/Core execution-role boundary.
- `GET /capabilities` — machine-readable capability manifest and integration-stage flags.
- `GET /integration/core/status` — non-secret Core configuration and incoming gateway-request diagnostics.
- `GET /v640/status` — release-specific status surface.
- Optional `X-SC-Service-Token` validation for `/integration/core/*` through `SCWB_REQUIRE_SERVICE_TOKEN` + `SCWB_SERVICE_TOKEN`.
- `X-Request-ID` preservation and `X-SC-Workbench-Version` response identity.
- Core connectivity environment contract and example environment file.
- Docker healthcheck pinned to Workbench 6.4.0.
- WordPress Core-connectivity status bridge and `[sc_workbench_core_connectivity_status]` shortcode.

## Preserved boundaries

- Platform Core does not execute Workbench code directly.
- Workbench does not automatically dispatch work to Core in v6.4.0.
- No Core state is automatically persisted by Workbench.
- Existing Workbench scientific, engineering, Energy Systems, project, and handoff endpoints retain their prior access and computation semantics.
- Secrets are never returned by the connectivity status endpoints.

## Next integration build

Workbench v6.5.0 — Unified Runtime Contract Adapter, targeting `sc.research.unified-runtime-contract.v1`.
## Release packaging compatibility note

The v6.4.0 dependency contract explicitly includes `httpx2>=2,<3`. Current Starlette TestClient releases prefer HTTPX2 and can fail test collection when only the legacy HTTPX package is present. The macOS release installer validates this dependency inside its isolated release-test environment.

