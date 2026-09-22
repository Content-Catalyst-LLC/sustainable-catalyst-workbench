# Workbench v6.7.0 — Computation, Analysis & Execution Lineage Bridge

v6.7.0 targets Platform Core's `sc.research.computation-analysis-execution-lineage.v1` contract directly. Workbench first prepares an execution registration, Core returns the authoritative execution ID, and Workbench then prepares deterministic lineage requests for inputs, parameters, assumptions, software environments, ordered steps, outputs, research bindings, dependencies, verification evidence, revisions, and immutable snapshots.

If a Core 3.0 unified research session ID is supplied, the bridge also prepares an execution binding that links the Core computation-lineage execution into that session. Specialist computation remains Workbench-owned; Core remains reference-first provenance, lineage, and research-session infrastructure.
