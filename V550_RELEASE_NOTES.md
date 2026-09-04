# Workbench v5.5.0 — Dynamic Geometry & Interactive Mathematics

Workbench v5.5.0 extends the mathematics line from symbolic computation and advanced graphing into directly manipulable geometry.

## Highlights

- Draggable mathematical points with immediate construction updates.
- Segments, infinite lines, circles, polygons, vectors, ellipses, parabolas, and hyperbolas.
- Deterministic bounded constraints for horizontal, vertical, coincident, midpoint, fixed-distance, and point-on-circle relationships.
- Live measurements including distance, slope, angle, radius, circumference, perimeter, and area.
- Algebra ↔ geometry linkage for line and circle equations.
- Affine/matrix transformations with determinant, orientation, and area-scale metadata.
- Expression-linked loci generated through the restricted v5.1 AST → SymPy parser.
- Canonical content-hashed geometry objects for reproducibility and export.
- WordPress studio: `[sc_workbench_dynamic_geometry]` with aliases `[sc_workbench_geometry]` and `[sc_workbench_geometry_studio]`.
- Workbench studio router adds a dedicated Dynamic Geometry entry.
- Workbench Settings now certifies the `/v550/status` backend capability.
- Public Workbench experience advances visible release identity to v5.5.0 and adds Dynamic Geometry to the advanced navigator.

## Runtime

This is a backend + WordPress release. Deploy the v5.5.0 backend to Contabo after pushing GitHub, then upload the v5.5.0 WordPress plugin.

## Security boundary

Geometry constraint solving is bounded and deterministic. Expression-linked loci use the existing restricted mathematics parser. Arbitrary Python `eval` / `exec`, remote shell access, arbitrary command execution, and automatic physical-device execution remain unauthorized.
