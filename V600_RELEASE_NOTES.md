# Workbench v6.0.0 — Unified Computational Workbench

v6.0.0 turns the specialist v5.x mathematics and engineering studios into one canonical computational-project system. A project can carry shared variables, linked computational objects, cross-studio dependencies, provenance, append-only history, portable exports, and explicit handoff packets for Lab, Decision Studio, the Knowledge Library, Research Librarian, Site Intelligence, Workspace, or offline continuation.

The backend advances to v6.0.0 and must be redeployed.

## New backend routes

- `GET /v600/status`
- `POST /v600/project/build`
- `POST /v600/variables/resolve`
- `POST /v600/links/validate`
- `POST /v600/provenance/build`
- `POST /v600/history/build`
- `POST /v600/export/build`
- `POST /v600/handoff/build`

## WordPress

Primary v6 studio shortcode: `[sc_workbench_computational_project]`

Aliases: `[sc_workbench_unified_computational]`, `[sc_workbench_computational_workbench]`, `[sc_workbench_v600]`.

The canonical `[sc_workbench]` router now opens the Unified Computational Project studio by default while retaining all earlier studios.

## Boundary

v6.0.0 composes and transports inspectable computational records. It does not autonomously execute generated code, program physical devices, publish results, certify models, launch remote shells, or perform destructive synchronization.
