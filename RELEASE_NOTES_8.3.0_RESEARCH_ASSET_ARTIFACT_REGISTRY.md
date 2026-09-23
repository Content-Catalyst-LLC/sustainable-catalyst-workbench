# Workbench v8.3.0 — Research Asset & Artifact Registry

Workbench v8.3.0 adds a durable, searchable, project-scoped registry of research assets and artifacts above v8.2 Unified Research Project Workspace and v8.1 Research Environment Persistence & Recovery.

## New capabilities

- Content-addressed research asset metadata with deterministic asset hashes.
- Append-only asset revision history with optimistic revision checks.
- Indexing of the active project's integrity-validated v8.1 environment without duplicating scientific payloads.
- Explicit registration of external sources/artifacts; external assets require both a stable reference and content hash.
- Search/filtering by project, free text, asset type, tag and exact content hash.
- Registry integrity/tamper validation on persisted asset revisions.
- Two-phase Platform Core asset-binding plans under the existing unified research-session contract.

## Asset types

Datasets, parameter sets, models, notebooks, workflows, executions, solver results, simulations, engineering analyses, design spaces, validation reports, figures, visualizations, reports, evidence, sources, reproducible packages, artifacts, external objects and other research assets.

## Authority boundaries

- v8.2 remains authoritative for research project state and the active project workspace.
- v8.1 remains authoritative for environment revisions, checkpoints and recovery.
- v8.3 stores an index of metadata, references, hashes and provenance; it does not copy embedded scientific payloads into a second state store.
- Search/index operations perform no scientific computation, notebook replay, workflow execution or remote retrieval.
- Platform Core planning remains explicit, two-phase and non-dispatching.

## API

- `GET /research-assets/manifest`
- `POST /research-assets/register`
- `POST /research-assets/index/project`
- `GET /research-assets/search`
- `GET /research-assets/{project_key}/{asset_key}`
- `GET /research-assets/{project_key}/{asset_key}/revisions`
- `POST /integration/core/research-assets/plan`
- `GET /v830/status`

No database migration is required. Registry files use the existing persistent Workbench `/data` mount.
