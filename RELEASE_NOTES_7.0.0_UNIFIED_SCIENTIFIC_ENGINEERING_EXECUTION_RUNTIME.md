# Sustainable Catalyst Workbench v7.0.0
## Unified Scientific & Engineering Execution Runtime

v7.0.0 is the architectural consolidation release that follows the completed v6.x Platform Core integration sequence. It introduces one canonical execution contract across Workbench's bounded specialist scientific and engineering engines while preserving each specialist implementation and its safety boundary.

### What changes

- Adds `sc-workbench-unified-scientific-engineering-execution-runtime/1.0`.
- Adds a single allow-listed operation catalog spanning symbolic mathematics, numerical scientific computing, simulation and systems, robotics/controls/mechatronics, measurement/instrumentation, signals/controls, electronics/embedded systems, digital logic/FPGA, uncertainty/sensitivity, predictive intelligence, forensic quantitative reconstruction, and explicit-input energy analysis.
- Adds canonical deterministic Workbench execution identities and stable input/result content hashes.
- Adds a common result/provenance envelope: `sc-workbench-unified-execution-result/1.0`.
- Adds dependency-ordered workflows with explicit declared dependencies and no hidden output injection.
- Adds a two-phase Platform Core computation-lineage planner that reuses the certified v6.7 computation-lineage and v6.6 unified-session contracts.
- Adds WordPress runtime status through `[sc_workbench_unified_execution_status]` and `/wp-json/sc-workbench/v1/unified-execution/status`.

### HTTP surfaces

- `GET /execution/runtime/manifest`
- `GET /execution/runtime/catalog`
- `POST /execution/runtime/execute`
- `POST /execution/runtime/workflow/run`
- `POST /integration/core/unified-execution/lineage/plan`
- `GET /v700/status`

### Safety and ownership boundaries

v7.0.0 does not accept arbitrary Python, shell commands, arbitrary callables, dynamic imports, or remote execution directives. Workflow steps do not automatically inject prior outputs into later payloads. Platform Core remains the reference/provenance/orchestration authority and does not directly execute Workbench specialist computation. Workbench does not automatically persist or dispatch to Core and does not certify scientific validity, infer reproducibility, rank conclusions, or determine truth.

### Database migration

None.
