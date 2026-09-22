# Sustainable Catalyst Workbench v7.7.0 — Optimization & Design Space Exploration

v7.7.0 adds a bounded optimization and design-space runtime above the v7.3 data workspace, v7.4 numerical solver, v7.5 simulation runtime and v7.6 engineering systems runtime.

## Added
- canonical design variables with bounds, initial values, units and grid resolution
- explicit single- and multi-objective functions with declared minimize/maximize goals and weights
- explicit inequality/equality constraints and feasibility diagnostics
- deterministic full-factorial design-space exploration with hard point limits
- Pareto-frontier extraction over feasible explored points
- constrained SLSQP weighted-sum optimization with no hidden objective normalization
- v7.3 workspace-to-design-space binding plans
- explicit candidate handoff plans into engineering or simulation requests
- v7.1 execution-object projection and content-addressed run hashes
- two-phase Platform Core computation-lineage output planning

## Boundaries
Workbench does not infer objective preferences, automatically normalize unlike objectives, choose a design winner, certify engineering safety or code compliance, execute arbitrary code, or automatically dispatch/persist records to Platform Core.

No database migration is required.
