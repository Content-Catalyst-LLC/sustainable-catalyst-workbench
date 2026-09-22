# Workbench v6.12.0 — Research State, Reproduction & Snapshot Integration

Workbench v6.12.0 connects declared Workbench project/computation state to Platform Core's project-state versioning, reproducible research package, and cross-product context/snapshot registries.

## What ships

- deterministic Workbench research-state snapshots with SHA-256 content identity;
- Platform Core project-state creation and version plans;
- versioned object bindings, dependency graphs, and runtime-environment bindings;
- explicit Core freeze, named checkpoint, and reconstruction-plan requests;
- reproducible package creation plus components, artifacts, environments, replay plans, and immutable package snapshots;
- cross-product research context, state-marker, handoff protocol, package, and snapshot plans;
- Core historical-manifest/reproducible-package/context bundle consumption into explicit Workbench resume plans;
- reference/hash comparison evidence without reproducibility certification;
- WordPress backend status shortcode and REST status surface.

## Core contracts

- `sc.research.project-state-versioning-reproducibility.v1` (Platform Core v2.92)
- `sc.research.reproducible-package.v1` (Platform Core v2.75)
- `sc.research.cross-product-context-handoff.v1` (Platform Core v2.91)

## Execution boundary

v6.12 is plan-only for Core mutation. It does not dispatch to Core, restore historical Workbench state automatically, replay executions automatically, fetch missing external objects, infer missing versions, infer or certify reproducibility, validate scientific results, choose canonical historical state, or determine truth.

## WordPress bootstrap hardening

The v6.10 production bootstrap regression remains permanently covered: the v6.12 static release gate requires the main plugin bootstrap to use `__DIR__` includes and rejects any `SCWB_DIR` reference.

## Database

No Workbench database migration is required.
