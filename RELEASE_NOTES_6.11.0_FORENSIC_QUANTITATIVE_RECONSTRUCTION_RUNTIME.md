# Workbench v6.11.0 — Forensic Quantitative Reconstruction Runtime

Adds the specialist numerical execution layer for Platform Core Open Forensics quantitative reconstruction and reproduction handoffs.

## Added
- Core `sc.forensic-quantitative-handoff.v1` consumer.
- Planar/geodetic trajectory reconstruction.
- Temporal overlap/gap comparison.
- First-order independent uncertainty propagation.
- Descriptive hypothesis residual metrics with no ranking/probability/verdict.
- Core quantitative result-binding and reproduction-package plans.
- v6.7 computation-lineage handoff plan.
- WordPress runtime status integration.

## Boundaries
Workbench computes explicit quantitative results. Platform Core remains authoritative for evidence, provenance, chain of custody, claims, hypotheses, investigation state, and research semantics. Neither layer is authorized by this release to turn numerical fit into truth, guilt, responsibility, a ranked hypothesis list, or a forensic verdict.

No Workbench database migration is required.
