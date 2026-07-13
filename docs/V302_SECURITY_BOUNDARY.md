# Workbench v3.0.2 Security and Recovery Boundary

- Storage operations run in the current browser profile.
- No browser storage is uploaded by the WordPress interface.
- Migration preserves legacy source records by default.
- Restore verifies backup envelope and record hashes before execution.
- Conflicting restore, rollback, cleanup, and reset require a downloaded backup.
- Cleanup requires `CLEAN WORKSPACE`; rollback requires `ROLLBACK WORKBENCH`.
- Imported data must be revalidated before technical or consequential use.
