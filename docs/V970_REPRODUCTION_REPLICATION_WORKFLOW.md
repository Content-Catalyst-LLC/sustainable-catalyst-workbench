# Workbench v9.7.0 — Reproduction & Replication Workflow

v9.7 introduces a persistent, content-addressed workflow for reproducing a prior Workbench scientific results synthesis or planning an explicit replication variant. The workflow captures target synthesis lineage, environment/runtime details, input references and hashes, invariants, planned replication changes, preregistration references, and researcher-defined comparison criteria.

Execution remains two-phase: Workbench prepares an execution specification but does not silently queue or run jobs. Comparison evaluates supplied observed metrics against explicit target/tolerance rules and records discrepancies, but intentionally returns no automatic replication verdict or scientific-validity judgment. Platform Core integration is plan-only and preserves Core governance authority.
