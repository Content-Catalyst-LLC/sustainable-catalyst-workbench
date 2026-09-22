# Workbench v7.7.0 — Optimization & Design Space Map

## Design-space object
- variables: bounded continuous design variables
- objectives: restricted mathematical expressions, minimize/maximize, explicit weights
- constraints: <=, >=, == with explicit right-hand side and tolerance
- parameters: declared finite scalar constants

## Runtime surfaces
- `POST /design-space/evaluate`
- `POST /design-space/explore`
- `POST /design-space/pareto`
- `POST /design-space/optimize`
- `POST /design-space/validate`
- `POST /design-space/workspace-binding/plan`
- `POST /design-space/candidate-handoff/plan`
- `POST /integration/core/design-space-lineage/plan`

## Exploration
Full-factorial only in v7.7.0, bounded to 4,096 points. No random hidden search.

## Optimization
SLSQP with explicit bounds and constraints. Multiple objectives are combined only through user-declared weights. Objective normalization is not automatic.

## Tradeoffs
Pareto-frontier extraction is descriptive. Workbench does not rank frontier points or select a preferred design.
