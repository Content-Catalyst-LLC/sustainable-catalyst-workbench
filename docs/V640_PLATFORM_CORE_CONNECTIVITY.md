# Workbench v6.4.0 — Platform Core Connectivity Contract

## Product roles

Platform Core is the orchestration, research-context, provenance, and visual-reasoning backbone. Workbench remains the specialist scientific and engineering computation plane.

## Core-facing endpoints

| Endpoint | Purpose | Authentication in v6.4.0 |
|---|---|---|
| `/health` | Core gateway health/version probe | Public operational metadata |
| `/runtime` | Execution-role and safety boundary | Public operational metadata |
| `/capabilities` | Capability discovery | Public operational metadata |
| `/integration/core/status` | Core configuration/request-context diagnostics | Optional shared service token |
| `/v640/status` | Release status | Public operational metadata |

## Platform Core registry pairing

Recommended Platform Core environment configuration:

```text
SC_CORE_WORKBENCH_URL=http://sc-workbench:8088
SC_CORE_WORKBENCH_ENABLED=true
SC_CORE_WORKBENCH_REQUIRED=true
SC_CORE_WORKBENCH_HEALTH_PATH=/health
SC_CORE_WORKBENCH_EXPECTED_VERSION_PREFIX=6.4.
SC_CORE_WORKBENCH_TOKEN_REQUIRED=true
SC_CORE_WORKBENCH_SERVICE_TOKEN=<same secret as Workbench SCWB_SERVICE_TOKEN>
```

Workbench pairing:

```text
SCWB_CORE_URL=http://sc-core:8090
SCWB_CORE_ENABLED=true
SCWB_CORE_REQUIRED=true
SCWB_CORE_EXPECTED_VERSION_PREFIX=3.
SCWB_REQUIRE_SERVICE_TOKEN=true
SCWB_SERVICE_TOKEN=<shared secret>
```

`SCWB_CORE_API_KEY` is reserved for outbound authenticated Core calls in later integration builds. v6.4.0 does not perform automatic outbound Core dispatch.
