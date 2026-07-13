# Workbench v3.8.0 — Offline and Installable Workbench

Version 3.8.0 turns the unified Workbench into a locally installable,
offline-capable environment for macOS, Linux, and Raspberry Pi OS.

## Included

- Browser-local project operation without a hosted backend
- Loopback-only FastAPI launcher on `127.0.0.1:8787`
- Install scripts for macOS, Linux, and Raspberry Pi OS
- Progressive web application shell and service-worker cache
- Optional platform-specific Python wheelhouse
- Versioned local application directories and preserved project data
- Runtime and dependency readiness plans
- Portable synchronization bundles with integrity and conflict checks
- Update planning with mandatory backups and package hashes
- Recovery plans that preserve data before repairing application files
- Private WordPress offline-node and synchronization-bundle records

## Security and operational boundaries

The local launcher refuses public network binds. The WordPress interface does
not execute arbitrary shell commands, expose remote shells, or upload projects
automatically. Automatic update installation is not authorized by generated
plans; packages must be verified and a rollback point must exist.
