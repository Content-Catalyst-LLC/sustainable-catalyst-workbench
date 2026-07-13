# Workbench v3.0.2 — Project Migration, Storage, and Recovery

Workbench v3.0.2 converts the v3.0.0 reset and migration foundations into an operational browser-local recovery system.

## New recovery studio

- Legacy Workbench v1.x/v2.x/v3.x storage discovery
- Non-destructive migration previews
- Canonical `scwb:v3` project manifests
- Target-key collision detection
- Browser quota and storage-health audits
- Duplicate, orphan-dependency, invalid-record, and hash checks
- Signed JSON backups with SHA-256 envelope and record hashes
- Chained backup hashes
- Conflict-aware restore strategies: skip, overwrite, and rename
- Automatic rollback backup before conflicting restores
- Rollback planning with exact confirmation
- Orphan and cleanup planning with exact confirmation
- Source records preserved during migration
- Browser-local operation with no hosted database requirement

## New shortcodes

- `[sc_workbench_migration_recovery]`
- `[sc_workbench_migration_center]`
- `[sc_workbench_storage_health_v302]`
- `[sc_workbench_backup_restore]`
- `[sc_workbench_restore_center]`
- `[sc_workbench_orphan_cleanup]`
- `[sc_workbench_rollback_center]`

## Compatibility

All prior studios and specialist shortcodes remain available. The v3.0.0 local Workbench Runner remains compatible; this release does not change the runner protocol.
