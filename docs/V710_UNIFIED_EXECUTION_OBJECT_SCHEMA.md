# v7.1.0 Unified Execution Object Schema

Canonical schema: `sc-workbench-execution-object/1.0`.

## Top-level identity

- `objectId` — deterministic Workbench object identifier.
- `objectRef` — `sc://workbench/execution-object/{objectId}`.
- `objectKey` — caller-supplied or execution/workflow-derived key.
- `objectKind` — `single_execution` or `workflow_execution`.
- `revision` / `previousObjectHash` — explicit metadata revision chain.
- `objectHash` — content-addressed hash of the canonical object excluding the hash field itself.

## Canonical sections

| Section | Purpose |
|---|---|
| `runtime` | Product, runtime kind/ref/version, specialist source release |
| `method` | Operation/category/execution type/method refs |
| `inputs` | Input refs, dataset refs, declared payload/workflow when available, request hash and fidelity |
| `parameters` | Request/workflow parameters and declared metadata |
| `environment` | Runtime environment ref, external environment refs and environment hash |
| `dependencies` | Parent execution refs, workflow dependency edges and order |
| `outputs` | Output refs, types, content hashes, result schemas and inline specialist results |
| `children` | Child execution objects for workflow objects |
| `lineage` | Workbench execution refs, workflow/envelope hashes and Core readiness |
| `provenance` | Source schema/version/ref/hash and projection mode |
| `boundaries` | Explicit non-automation and non-certification guarantees |

## Projection fidelity

`execute-and-project` preserves the declared request/workflow payload. `reference-first-project` can wrap an already-produced v7.0 result using its refs/hashes but reports reduced input fidelity rather than inventing unavailable request content.

## Revision semantics

Revisions preserve `objectId`, `objectRef`, execution outputs, result hashes, and scientific content. Only descriptive label/tags/metadata and the revision record may change. Recomputing a scientific result requires a new execution, not an object revision.

## Platform Core mapping

A v7.1 object can prepare:

- `POST /v1/research/unified-runtime/execution-bindings`
- `POST /v1/research/runtime-contract/invocations`
- `POST /v1/research/runtime-contract/results`

Core-issued session, contract, and invocation IDs remain Core authority; Workbench never invents them and never auto-dispatches the prepared requests.
