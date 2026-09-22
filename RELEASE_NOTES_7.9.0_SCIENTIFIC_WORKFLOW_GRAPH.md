# Sustainable Catalyst Workbench v7.9.0 — Scientific Workflow Graph

Workbench v7.9.0 introduces a content-addressed scientific workflow DAG over the bounded v7 execution stack. Graphs use typed nodes, explicit dependencies, deterministic topological ordering, and declared source-path → target-path bindings. Workbench does not perform hidden output substitution.

Supported node families are unified operations, numerical solvers, simulations, engineering analyses, design-space operations, and model-validation/verification steps. Graph executions preserve existing v7.1 execution objects where available, record deterministic result hashes for every node, and produce an integrity-checkable graph-run hash.

The Platform Core handoff targets `sc.research.workflow-orchestration.v1`. Workbench can prepare workflow, stage, context-binding, and event registrations, but it does not invent a Core workflow ID, automatically dispatch to Core, or ask Core to execute specialist scientific work.

A graph pass or completed workflow does not certify scientific validity, truth, safety, code compliance, or fitness for purpose.
