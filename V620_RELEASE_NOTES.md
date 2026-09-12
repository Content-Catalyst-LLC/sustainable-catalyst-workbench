# Workbench v6.2.0 — Energy Workbench Runtime

Workbench v6.2.0 turns the Energy Systems v1.2 handoff contract into an explicit-input execution runtime for Energy Systems Intelligence v1.3.0.

The release adds four backend routes under `/v1/energy-runtime`: `execution-framework`, `plan`, `execute`, and `validate-result`. Fourteen calculations are supported across source-bound unit conversion, energy balances and generation, scenario economics, and bioenergy/carbon arithmetic.

The existing `/consumer` and `/consume` routes remain non-executing. Calculations occur only when `/execute` is called explicitly. The runtime does not infer missing inputs, fetch market values, persist studies, rank options, select winners, issue recommendations, or turn stoichiometric carbon equivalence into a carbon-credit claim.

Result packets preserve caller inputs, formulas, method-contract references, source refs, assumptions, provenance, review context, and deterministic result identifiers.
