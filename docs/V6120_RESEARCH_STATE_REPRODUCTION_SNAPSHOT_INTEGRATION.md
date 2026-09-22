# v6.12 Research State, Reproduction & Snapshot Integration

The v6.12 adapter captures a deterministic, reference-first representation of Workbench state and translates it into exact Platform Core request plans. Core-issued IDs are required for project-state, reproducible-package, and research-context phase-two operations.

## Lifecycle

1. Capture deterministic Workbench state.
2. Prepare Core project-state registration.
3. Receive the authoritative Core state ID.
4. Prepare a draft version with object, dependency, and environment bindings.
5. Freeze the version in Core.
6. Register a named checkpoint and declarative reconstruction plan.
7. Prepare a Core reproducible research package and receive its ID.
8. Bind components, artifacts, environments, and a declarative replay plan.
9. Snapshot the Core reproducible package.
10. Optionally prepare a cross-product research context/handoff snapshot.
11. Consume Core state later into an explicit Workbench resume plan.

## Resume semantics

A resume plan is not a restore. It identifies required object references, environments, and declared instructions. Reference resolution, environment compatibility checks, and any execution request remain explicit caller/operator actions.
