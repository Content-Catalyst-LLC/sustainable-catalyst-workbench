# Sustainable Catalyst Workbench v3.1.0

Persistent Project Workspace for the Unified Prototyping Workbench.

Version 3.1.0 adds local-first projects, active-project switching, autosave, private WordPress persistence, revision snapshots, project import/export, synchronization planning, and conflict-aware recovery while retaining the full v2.x and v3.0.x studio system.

## Primary shortcode

```text
[sc_workbench topic="workbench" title="Sustainable Catalyst Workbench" display="full"]
```

## Persistent workspace shortcode

```text
[sc_workbench_persistent_workspace project="default"]
```

## Storage modes

- **Browser:** local browser storage only
- **Hybrid:** browser storage plus optional private WordPress synchronization
- **WordPress:** private authenticated WordPress project storage with browser working copy

No paid external database is required for the baseline persistent workspace.

See `V310_RELEASE_NOTES.md` and `docs/V310_SECURITY_BOUNDARY.md`.
