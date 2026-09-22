# v6.12 Platform Core Research-State Field Map

## Project state — `sc.research.project-state-versioning-reproducibility.v1`

Workbench maps snapshots into Core `states`, `versions`, `bindings`, `dependencies`, `environments`, `freeze`, `checkpoints`, `reconstruction-plans`, and `snapshots` routes.

- Workbench `bindingKey` -> Core `binding_key`
- `objectType` -> `object_type`
- `objectRef` -> `object_ref`
- `versionRef` -> `object_version_ref`
- `contentHash` -> `content_hash`
- environment `environmentKey` -> `environment_key`
- environment `environmentType` -> `environment_type`
- dependency endpoints -> `from_binding_key` / `to_binding_key`

Core's state ID is authoritative and must be returned by Core before v6.12 builds version-specific requests.

## Reproducible research — `sc.research.reproducible-package.v1`

Workbench maps captured bindings to Core components, explicit artifacts to artifact records, environments to runtime/dependency manifests, and the Workbench resume contract to a declarative replay plan. Core does not execute the replay plan.

## Cross-product context — `sc.research.cross-product-context-handoff.v1`

Workbench maps captured bindings to context object bindings, records the snapshot hash as a state marker, declares a snapshot-mode handoff protocol, then prepares a context package and immutable Core context snapshot.

## Guardrails

All Core request envelopes set `automaticDispatchAuthorized=false`. Workbench does not certify reproducibility or scientific validity and does not authorize automatic state restoration or execution replay.
