# Workbench v3.8.0 security boundary

- Local service host defaults to `127.0.0.1`.
- The launcher refuses non-loopback host values.
- No remote shell, arbitrary command endpoint, or public listener is included.
- Local projects are not uploaded automatically.
- Synchronization requires an explicit export and import action.
- Bundle integrity is checked before import planning.
- Conflicts can be held for manual review.
- Updates require a trusted package hash and a restorable backup.
- Uninstallation preserves project data by default.
- Installer scripts create isolated Python environments.
