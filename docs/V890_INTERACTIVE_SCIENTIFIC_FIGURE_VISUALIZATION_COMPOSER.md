# v8.9 Interactive Scientific Figure & Visualization Composer

The v8.9 composer turns completed Workbench computational outputs into explicit, inspectable figure specifications.

A figure request selects one or more completed execution jobs and one or more panels. Each panel declares its mark type, metric scope (`request` or `result`), y metrics, and—when required—an x metric. The backend resolves only metrics that actually exist in the selected authoritative jobs. It preserves missing values and rejects unknown metric references.

The resulting specification includes panel rows, explicit encodings, layout metadata, linked-selection state, renderer capabilities, export planning, source job hashes, and a deterministic figure hash. The specification is suitable for a WordPress SVG preview or another renderer without turning the visualization layer into the source record.

## Publication workflow

1. Select a research project.
2. Load completed Workbench runs.
3. Select source runs.
4. Add one or more panels.
5. Choose mark and metric scope.
6. Select y metrics and, for scatter plots, an explicit x metric.
7. Compose the figure.
8. Review provenance and missing-value flags.
9. Export JSON or the client-side SVG preview.
10. Optionally create a Platform Core binding plan for the figure analytical view.

## Non-goals

v8.9 does not automatically choose the scientifically appropriate chart type, axis, transformation, uncertainty representation, preferred run, or interpretation. It does not certify publication readiness or statistical validity.
