# v5.2.0 Interactive Graph Mathematics

## Object model
The graph service returns `sc-workbench-graph-object/1.0` objects. Each object includes the v5.2 version, graph kind, source expression(s), viewport/parameters, sampled or analyzed geometry, governance flags, and a SHA-256 content hash.

## Graph families
- **Cartesian** — y=f(x), discontinuity-aware sampled polylines.
- **Parametric** — x(t), y(t) over a bounded parameter range.
- **Polar** — r(theta) converted to bounded Cartesian points.
- **Implicit / contour** — expression=0 or lhs=rhs contour segments generated from a bounded grid.
- **Vector field** — u(x,y), v(x,y) arrows with optional normalization.
- **3D surface** — z=f(x,y) sampled into a bounded grid for client-side wireframe rendering.

## Linked analysis
Cartesian graph requests can include a symbolic derivative overlay and bounded definite-integral overlay. The analysis endpoint returns roots, extrema, and intersections within the selected x-domain. Parameter values are substituted before analysis.

## Limits
Sampling, implicit grids, vector grids, surface grids, and parameter counts are bounded server-side. The service returns geometry only; it does not return executable code.
