# Workbench v3.1.0 — Persistent Project Workspace

Workbench v3.1.0 turns the unified Workbench project manifest into a practical persistent workspace.

## Persistent project capabilities

- Browser-local project creation, switching, search, pinning, status, and tags
- Debounced autosave and page-exit safety save
- Local revision snapshots with content hashes
- Project import and export bundles
- Shared studio records, evidence IDs, artifact IDs, and metadata
- Active-project events for cross-studio integration
- Storage usage and revision-count reporting
- Private WordPress project storage for authenticated editors
- Private server revision snapshots
- Local/remote synchronization with newest, local, remote, and manual strategies
- Conflict reporting instead of silent overwrite
- Browser-only fallback when the visitor is anonymous or WordPress persistence is unavailable

## WordPress storage model

The plugin registers two private record types:

- `scwb_project`
- `scwb_revision`

Only signed-in users with editing capability can use the project REST routes. Project access is limited to the record owner unless the user can edit other authors' posts.

## New shortcodes

- `[sc_workbench_persistent_workspace]`
- `[sc_workbench_project_manager]`
- `[sc_workbench_project_switcher]`
- `[sc_workbench_project_revisions]`
- `[sc_workbench_project_storage]`
- `[sc_workbench_project_autosave]`

## Compatibility

The persistent workspace becomes the thirteenth unified studio. All v2.x and v3.0.x shortcodes, recovery records, and the v3.0.0 local runner remain compatible.
