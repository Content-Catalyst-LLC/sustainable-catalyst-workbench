# Sustainable Catalyst Workbench v0.9.7 — Feature Builder from Equation Registry

v0.9.7 uses the exported Equation Registry CSV and Calculator Backlog CSV to create a richer feature-development layer for the Workbench.

## New admin page

`SC Workbench → Feature Builder`

This page imports a bundled feature queue derived from the equation registry and calculator backlog. It also links to bundled analysis files:

- `workbench_feature_build_queue_v0.9.7.csv`
- `article_tool_profiles_v0.9.7.csv`
- `equation_domain_summary_v0.9.7.csv`
- `equation_feature_clusters_v0.9.7.csv`

## Purpose

The feature builder turns article equations into an implementation roadmap:

- calculator/module candidates
- feature priorities
- source equation evidence
- article coverage counts
- recommended inputs and outputs
- recommended backend path
- first MVP scope
- dependencies

## How to use

1. Install the v0.9.7 plugin.
2. Open `SC Workbench → Feature Builder`.
3. Click `Import Bundled Feature Queue`.
4. Review P0/P1/P2 priorities.
5. Export the feature queue CSV if you want to edit or plan externally.
6. Upload a revised feature CSV as the roadmap changes.

## How this fits the Workbench roadmap

v0.9.5 created the Equation Registry and CSV export.  
v0.9.6 created the Calculator Backlog.  
v0.9.7 connects both into a feature-building system that can guide v1.0 implementation.
