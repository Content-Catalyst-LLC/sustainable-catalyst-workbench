# v7.9.0 Scientific Workflow Graph Map

## Canonical schema

- Graph runtime: `sc-workbench-scientific-workflow-graph/1.0`
- Graph plan: `sc-workbench-scientific-workflow-graph-plan/1.0`
- Graph run: `sc-workbench-scientific-workflow-graph-run/1.0`
- Core workflow contract: `sc.research.workflow-orchestration.v1`

## Node families

1. `unified-operation` → v7.0 bounded execution registry
2. `solver` → v7.4 Numerical Methods & Solver Runtime
3. `simulation` → v7.5 Simulation & Dynamical Systems Runtime
4. `engineering` → v7.6 Engineering Systems Runtime
5. `design-space` → v7.7 Optimization & Design Space Exploration
6. `validation` → v7.8 Model Validation & Verification Framework

## Dataflow rules

Every cross-node value transfer must declare:

- `sourceNodeId`
- `sourcePath`
- `targetPath`
- the source node in the target node's `dependsOn`

Bindings are applied only after the source node has completed. No undeclared result substitution occurs.

## Core boundary

Workbench prepares `/v1/research/workflows` registrations and, only after Core supplies a workflow ID, stage/context/event registration plans. No automatic Core dispatch or persistence is performed.
