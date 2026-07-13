# Workbench v4.0.0 Connected Extension Contract

Contract name: `sc-workbench-connected-environment`

Contract version: `1.0`

Compatibility floor: Workbench 4.0.0

## Stable browser events

- `scwb:connected-record-built`
- `scwb:project-changed`
- `scwb:active-project-updated`
- `scwb:studio-activated`
- `scwb:panel-visible`

## Stable REST surfaces

- `/wp-json/scwb/v1/connected-workbench-status`
- `/wp-json/scwb/v1/connected-integration-health`
- `/wp-json/scwb/v1/connected-projects`
- `/wp-json/scwb/v1/connected-workflows`
- `/wp-json/scwb/v1/connected-manifests`
- `/v400/status`
- `/v400/capabilities/registry`
- `/v400/project/build`
- `/v400/graph/build`
- `/v400/workflow/plan`
- `/v400/context/build`
- `/v400/integration/health`
- `/v400/traceability/build`
- `/v400/sync/plan`
- `/v400/dossier/build`
- `/v400/release/manifest`
- `/v400/extension/validate`

## Stable schemas

All v4.0.0 records use the prefix:

`sc-workbench-connected-environment-*/1.0`

Breaking changes require a new schema version and an explicit migration path.
