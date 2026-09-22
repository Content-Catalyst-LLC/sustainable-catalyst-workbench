# Workbench v7.6.0 — Engineering Systems Runtime

v7.6.0 adds a canonical bounded engineering layer above the unified execution/object/orchestration/data/solver/simulation stack. It covers mechanical axial and simply-supported beam analysis, thermal conduction and convection, Darcy–Weisbach pipe-flow analysis, declared civil axial capacity, DC circuit analysis, existing actuator sizing, and existing explicit-input Energy Systems execution.

Every engineering run receives deterministic hashes and a v7.1 execution object. Cross-domain system bundles execute only explicitly declared analyses and do not silently couple outputs between domains. v7.3 workspaces can prepare explicit bindings into engineering inputs, and Platform Core integration uses `sc.research.computation-analysis-execution-lineage.v1` in a two-phase, non-dispatching plan.

## Safety and authority boundaries

This runtime does not perform licensed engineering certification, code-compliance certification, physical-safety certification, automatic design selection, physical actuation, or automatic Platform Core persistence. Formula results depend on the declared model assumptions and inputs and must be independently reviewed for real-world engineering use.
