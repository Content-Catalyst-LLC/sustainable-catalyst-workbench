# Workbench v5.5.0 — Dynamic Geometry & Interactive Mathematics

## Interaction model

v5.5 introduces geometry as a first-class Workbench mathematical representation. A construction is no longer a static drawing: points can move while linked objects, constraints, equations, and measurements are recomputed as one inspectable record.

The primary interaction chain is:

`move point → solve constraints → rebuild geometry → recompute measurements → update algebra → preserve geometry object`

## Supported geometry

The initial governed construction model includes points, segments, lines, circles, polygons, vectors, ellipses, parabolas, and hyperbolas. Conic families are sampled deterministically for browser rendering while their center/radius/rotation parameters remain explicit in the object record.

## Constraints

The bounded projection solver supports:

- horizontal alignment;
- vertical alignment;
- coincident points;
- midpoint relationships;
- fixed distances;
- point-on-circle constraints.

Each solve records convergence state, iteration count, maximum residual, and tolerance. The solver has a hard iteration ceiling and does not invoke an unconstrained optimizer or arbitrary executable expression.

## Transformations

Affine transformations use an explicit 2×2 matrix, translation vector, and origin. Results record the determinant, orientation preservation, and area scale so that geometric transformation is also mathematical analysis rather than only visual movement.

## Algebra ↔ geometry

Line/segment/vector constructions expose the corresponding linear equation when defined. Circles expose a center-radius equation. Geometry measurements remain attached to the canonical geometry object and update when points move.

## Expression-linked loci

Parametric loci use `x(t)` and `y(t)` expressions parsed by the v5.1 restricted AST → SymPy engine. Locus generation does not introduce a browser or server `eval` path.
