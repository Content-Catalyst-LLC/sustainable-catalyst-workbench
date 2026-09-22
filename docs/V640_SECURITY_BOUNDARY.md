# Workbench v6.4.0 Security Boundary

- `/health`, `/runtime`, `/capabilities`, and `/v640/status` expose operational metadata only.
- `/integration/core/status` never returns `SCWB_SERVICE_TOKEN` or `SCWB_CORE_API_KEY` values.
- When `SCWB_REQUIRE_SERVICE_TOKEN=true`, Core integration routes validate `X-SC-Service-Token` using constant-time comparison.
- v6.4.0 does not change authentication semantics of legacy Workbench calculation routes.
- v6.4.0 does not execute arbitrary code received from Platform Core.
- v6.4.0 does not automatically call Platform Core or persist Core state.
- Production service tokens must be injected through deployment secrets/environment and must never be committed to source control.
