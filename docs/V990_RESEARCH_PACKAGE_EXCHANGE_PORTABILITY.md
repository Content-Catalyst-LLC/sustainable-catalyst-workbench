# Workbench v9.9.0 — Research Package Exchange & Portability

v9.9.0 adds content-addressed research-package export/import infrastructure for moving reproducible Workbench research state between environments without silently activating or overwriting native records.

## Added
- Portable research package schema and manifest.
- Explicit object selection across v9.0–v9.8 research objects.
- Deterministic ZIP export with canonical JSON payloads.
- Per-object SHA-256 and Workbench content-hash verification.
- Dependency/reference inventory and optional strict closure checks.
- Workbench runtime/package-format compatibility assessment.
- Non-mutating import validation.
- Explicit quarantine/staging workflow for validated imports.
- Source catalog and package registry.
- Platform Core package binding plan.
- WordPress Research Package Exchange & Portability interface.

## Guardrails
Staging never activates imported objects or overwrites native Workbench research stores. Package validation does not infer scientific validity, evidence quality, compatibility of scientific methods, or truth. No imported archive is executed. No automatic Platform Core dispatch occurs.
