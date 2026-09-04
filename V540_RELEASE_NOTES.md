# Workbench v5.4.0 — Advanced Graph Mathematics II

Workbench v5.4.0 advances the graphing line from single-expression visualization to a multi-expression mathematical analysis environment.

## Highlights

- Up to 8 linked Cartesian expressions in one graph object.
- Per-series domain restrictions for piecewise-style graph construction.
- First- and second-derivative overlays per series.
- Roots, extrema, and pairwise intersections across visible series.
- Tangent and normal-line construction at a selected x-coordinate.
- Discontinuity inspection plus vertical and horizontal asymptote analysis.
- Optional inequality-region sampling and shading.
- Synchronized value-table representation.
- High-DPI trace, wheel zoom, pointer pan, reset, and fullscreen controls.
- Existing vector-field, polar, parametric, implicit, and 3D v5.2 routes remain available for compatibility.
- WordPress Workbench settings now certify the v5.4 advanced graph backend.

## Runtime

This is a backend + WordPress release. Deploy the v5.4.0 backend to Contabo after pushing GitHub, then upload the v5.4.0 WordPress plugin.

## Security boundary

All expressions continue through the restricted v5.1 AST-to-SymPy allow-list. Arbitrary Python `eval` / `exec`, remote shell access, and arbitrary command execution remain unauthorized.
