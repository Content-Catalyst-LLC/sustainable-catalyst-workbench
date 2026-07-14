# Workbench v4.0.2 Security Boundary

- Synchronization plans are previews until a human explicitly executes them.
- Idempotency keys prevent repeated operations from being treated as new writes.
- Destructive overwrite, deletion, tombstone purge, and rollback require a verified backup.
- Rollback additionally requires the exact confirmation phrase `ROLLBACK CONNECTED PROJECT`.
- The module exposes no remote shell, arbitrary command execution, public network binding, automatic publication, or safety bypass.
- Private WordPress sync transactions and checkpoints are not publicly searchable.
