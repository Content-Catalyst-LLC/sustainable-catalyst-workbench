# Workbench v6.5.0 — Core Runtime Adapter Security Boundary

- Existing v6.4 optional `X-SC-Service-Token` protection applies to all new `/integration/core/runtime-contract/*` routes.
- `/v650/status` remains public operational metadata.
- Runtime contract payloads never cause automatic specialist computation.
- Core exchange envelopes are converted into explicit import plans; `automaticExecutionAuthorized` is always false.
- Generated Core write requests are returned to the caller; Workbench v6.5 does not automatically dispatch or persist them.
- Workbench does not infer contract semantics, determine truth, certify scientific results, or authorize another product.
- The adapter preserves caller-supplied project/provenance references and Workbench content hashes.
