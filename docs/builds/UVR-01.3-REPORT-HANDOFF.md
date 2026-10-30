# UVR-01.3 — Workbench → Research Reporting figure handoff

## Implemented
A pure, integrity-checked, portable SVG figure handoff for a saved Graph Studio render package. Output is a manifest plus SVG bytes. It carries project and report IDs, session, graph/revision, graph and render hashes, view-spec artifact hash, source references, caption, figure number, and SVG SHA-256. Mismatched or unverified destination mapping is rejected. The output never asserts scientific verification or successful persistence.

## Deployment boundary
This build does **not** perform report persistence, change the reporting service, alter Workbench production, or modify a database. It is intentionally an intermediate adapter contract, not an invented report API.

## Next integration requirement
Identify and verify the *actual* Research Reporting Studio report ID, project ownership mapping, authenticated attachment write API or persisted figure-object store, and reopening/read API. Implement a destination-side adapter using its existing authentication and idempotency/transaction semantics; store source graph lineage and SHA-256, reopen the artifact, validate hashes, and test cross-owner denial.

Do not infer that Workbench and Reporting share identity or project IDs. An approved mapping must be issued by the receiving service. Do not send tokens or private scientific data to a new endpoint.

## Validation
Run `node --test standalone-app/tests/uvr-01-3-report-attachment-handoff.test.mjs` from the repository root, alongside existing UVR and SVG-export tests. Tests cover hash integrity, no persistence claim, project/report/session/graph/revision/render-hash mismatch, and corrupted source package.

## Existing contracts reused
- `report-figure-reference.mjs`: saved graph figure metadata
- `report-render-package.mjs`: deterministic view-spec package verification
- `report-svg-export.mjs`: SVG generation
- Core's governance/provenance is separate; no new renderer has been introduced.
