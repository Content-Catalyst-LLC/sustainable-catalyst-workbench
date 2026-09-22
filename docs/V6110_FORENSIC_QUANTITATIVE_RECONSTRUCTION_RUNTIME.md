# Workbench v6.11.0 — Forensic Quantitative Reconstruction Runtime

Workbench v6.11.0 is the specialist numerical execution plane for Platform Core Open Forensics quantitative reconstructions.

## Runtime boundary

Platform Core owns investigations, evidence, source provenance, chain of custody, claims, hypotheses, timeline/spatial evidence, quantitative reconstruction records, and reproduction packages. Workbench executes explicit numerical operations and returns hashed result manifests plus Core-compatible persistence plans.

The runtime does **not** rank hypotheses, assign posterior/probability values to hypotheses, select a winner, determine truth, guilt, responsibility, authenticity, or evidentiary admissibility.

## Supported operations

- Planar or geodetic trajectory reconstruction with segment distance, elapsed time, speed, and segment-to-segment acceleration.
- Pairwise temporal-window overlap, gap, and ordering calculations.
- First-order uncertainty propagation for sums, differences, products, ratios, and weighted sums under an explicit independent-input assumption.
- Descriptive residual/error metrics for multiple declared hypotheses without sorting or ranking them.
- Consumption of `sc.forensic-quantitative-handoff.v1` manifests.
- Result-binding plans to Platform Core Open Forensics.
- Quantitative reproduction-package plans.
- v6.7 computation-lineage handoff plans.

## Core contracts

- `sc.open-forensics.quantitative-reconstruction.v1`
- `sc.forensic-quantitative-handoff.v1`
- `sc.open-forensics.quantitative-reproduction-package.v1`
- `sc.open-forensics.forensic-timeline.v1`
- `sc.open-forensics.spatial-temporal-evidence.v1`
- `sc.open-forensics.competing-hypothesis-matrix.v1`
