# Workbench v6.9.0 — Core Visual Reasoning Runtime Adapter

Workbench v6.9.0 adapts specialist numerical and analytical results into renderer-neutral visual research manifests for Platform Core.

## Execution boundary

Workbench owns numerical computation and may derive bounded descriptive statistics needed to describe results. Platform Core owns visual object identity, scene and grammar registries, unified visual workspaces, cross-product visual bindings, and research semantics. Neither side automatically renders, infers truth, or persists the other side's state.

## Integration flow

1. Workbench adapts an execution/scenario/uncertainty result into `sc-workbench-visual-research-result-manifest/1.0`.
2. Workbench builds a Core Visual Reasoning Object registration request.
3. Core returns the canonical visual entity ID.
4. Workbench builds semantic-element and scene-registration requests.
5. Core returns scene/view/composition/grammar IDs as applicable.
6. Workbench prepares unified visual workspace and cross-product bindings using only Core-issued IDs.

## Supported result families

- time/series and scatter results
- distributions and uncertainty ensembles
- Sobol/Morris-style sensitivity outputs
- matrices
- scenario/model-run outputs
- tables and networks

## Safety and reproducibility

All handoffs are deterministic manifests and request plans. `automaticCoreDispatchAuthorized`, `automaticCorePersistenceAuthorized`, renderer execution, automatic layout, automatic visual inference, and truth promotion remain false.
