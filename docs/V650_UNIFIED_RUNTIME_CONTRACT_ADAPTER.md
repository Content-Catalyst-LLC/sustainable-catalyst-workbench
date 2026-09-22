# Workbench v6.5.0 — Unified Runtime Contract Adapter

Workbench v6.5.0 implements a deterministic adapter for Platform Core's `sc.research.unified-runtime-contract.v1` contract. It builds on the v6.4 connectivity foundation and keeps specialist computation owned by Workbench.

## Runtime contract endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /integration/core/runtime-contract/manifest` | Declares Workbench product identity, supported operations, capabilities, object types, Core paths, and security boundaries. |
| `POST /integration/core/runtime-contract/validate` | Validates a Core contract bundle against Workbench's declared capabilities without inferring semantics. |
| `POST /integration/core/runtime-contract/product-binding` | Builds a Core-compatible product-binding request for Workbench. |
| `POST /integration/core/runtime-contract/project/map` | Maps a Workbench v6 canonical computational project and objects into stable Core references. |
| `POST /integration/core/runtime-contract/exchanges/consume` | Consumes a Core exchange envelope and turns it into a bounded Workbench import plan. |
| `POST /integration/core/runtime-contract/exchanges/build` | Builds a Core-compatible exchange record with Workbench as the source product. |
| `POST /integration/core/runtime-contract/invocations/build` | Builds Core invocation-lineage records for Workbench activity. |
| `POST /integration/core/runtime-contract/results/build` | Builds Core result-binding records with content hashes. |
| `GET /v650/status` | Public release status and declared adapter surface. |

## Declared Core capabilities

Workbench v6.5 declares:

- `object:create`
- `object:read`
- `object:link`
- `object:version`
- `object:snapshot`
- `provenance:trace`
- `context:handoff`
- `package:export`
- `validation:record`

It does **not** declare `object:update` or `workflow:state` in v6.5 because the adapter is non-persistent. A caller can rebuild a Workbench project, but the adapter does not claim to mutate a Core-owned object or workflow state.

## Supported runtime operations

`create`, `read`, `link`, `version`, `snapshot`, `trace`, `handoff`, `package`, `validate_external`, and `list` are supported at the adapter layer. Core's `update` operation is recognized as part of the vocabulary but is not declared as implemented by Workbench v6.5.

## Core-compatible request shapes

The adapter emits payloads matching Core 2.96's `/v1/research/runtime-contract/*` service fields, including `contract_id`, `product_ref`, `project_ref`, `source_product_ref`, `target_product_ref`, `exchange_id`, `invocation_id`, `object_ref`, `object_version_ref`, `content_hash`, and provenance references.

The returned `coreRequest` blocks are instructions for caller-led persistence. `automaticDispatchAuthorized` remains false in this release.

## Project mapping

A canonical Workbench project is mapped to references such as:

- `sc://workbench/project/{projectId}`
- `sc://workbench/object/{projectId}/{objectId}`
- `sc://workbench/variables/{projectId}/{projectHashPrefix}`

Workbench project and object content hashes are preserved so later Core lineage/reproduction layers can refer to exact computational state.

## Security and execution boundary

Receiving a Core exchange envelope never authorizes computation on its own. The adapter requires a separate explicit specialist operation request before execution. It also does not certify scientific validity, infer missing schemas, mutate Core data, or automatically persist lineage to Core.
