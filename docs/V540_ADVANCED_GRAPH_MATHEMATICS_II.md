# Workbench v5.4.0 — Advanced Graph Mathematics II

## Computational model

The v5.4 graph object is an inspectable, content-hashed record containing:

1. an expression stack;
2. per-expression domain restrictions;
3. parameters and viewport;
4. sampled function and derivative series;
5. analysis markers;
6. optional tangent/normal constructions;
7. optional inequality-region intervals;
8. a reproducible graph-object hash.

## Piecewise construction

v5.4 does not introduce a free-form executable piecewise language. Instead, users compose piecewise views by stacking restricted expressions with explicit domain bounds. This keeps parsing bounded and makes each piece independently inspectable.

## Analysis

The v5.4 backend can report roots, extrema, pairwise intersections, discontinuities, and asymptotes inside the requested viewport. Tangent and normal lines are constructed from the first visible series at a user-selected x-coordinate.

## Interaction

The WordPress renderer supports direct trace inspection, wheel zoom, pointer-based panning, reset, fullscreen, and a value-table view. Mathematical computation remains server-side; browser interaction changes only view state and presentation.
