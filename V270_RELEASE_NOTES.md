# Workbench v2.7.0 — Scientific Visualization and Engineering Dashboard Studio

## Release purpose

Workbench v2.7.0 turns saved measurements, simulation outputs, validation records, and runtime results into auditable scientific figures and engineering dashboards. The release keeps browser-local calculations as the default and adds optional paired discovery of local visualization tools.

## New WordPress modules

- `[sc_workbench_scientific_visualization project="default"]`
- `[sc_workbench_engineering_dashboard project="default"]`
- `[sc_workbench_interactive_chart_studio project="default"]`
- `[sc_workbench_validation_overlay project="default"]`
- `[sc_workbench_system_state_view project="default"]`
- `[sc_workbench_visual_export_accessibility project="default"]`

## Major capabilities

- Time-series, scatter, bar, histogram, frequency-spectrum, and spatial x/y visualization
- Threshold-aware engineering metric dashboards
- Interactive parameter controls for first-order, sine, linear, and quadratic models
- Observed-versus-predicted overlays with configurable uncertainty bands
- RMSE, MAE, bias, coverage, distribution, and series-summary records
- Directed engineering system-state views with structural checks
- SVG, PNG, JSON, and tabular export support
- Programmatic SVG titles/descriptions, text narratives, and data tables
- Paired local discovery for Gnuplot, Graphviz, ImageMagick, Inkscape, FFmpeg, Chromium, and Python visualization libraries

## Compatibility

The release preserves the existing v2.0.0–v2.6.0 WordPress modules, backend routes, saved browser records, runner pairing boundary, and structured local execution model.

## Boundaries

Charts do not establish the validity of source data, experimental design, transformations, thresholds, uncertainty assumptions, or causal claims. Users must review units, scales, sampling, missing data, transformations, visual encodings, color contrast, accessibility narratives, and exported artifacts.
