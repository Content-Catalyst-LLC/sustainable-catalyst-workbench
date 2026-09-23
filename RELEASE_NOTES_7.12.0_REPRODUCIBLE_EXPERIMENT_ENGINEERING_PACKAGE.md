# Workbench v7.12.0 — Reproducible Experiment & Engineering Package

v7.12.0 closes the Workbench v7 architecture with a content-addressed research-package layer over the scientific and engineering runtime stack.

## Capabilities

- Build experiment, engineering, or mixed packages from declared Workbench state.
- Embed bounded JSON components or preserve external/reference-first components with required content hashes.
- Package v7.3 data workspaces, v7.9 workflow graph runs, v7.10 notebook runs, v7.11 visual workspaces, v7.8 V&V reports, v7.1 execution objects, artifacts, environments, assumptions, limitations, and lineage references.
- Generate deterministic integrity manifests and package hashes.
- Validate package tampering before replay/export/Core planning.
- Prepare explicit replay plans without automatic execution or hidden-state restoration.
- Prepare export/archive manifests without writing files automatically.
- Reuse Platform Core `sc.research.reproducible-package.v1` through two-phase package registration.

## Boundaries

A package does not certify reproducibility, scientific validity, engineering safety, code compliance, regulatory approval, or truth. Replay and Core persistence require explicit caller/operator action.
