# Sustainable Catalyst Workbench v0.9.6: Equation-Derived Calculator Backlog

v0.9.6 turns the equation-registry analysis into an admin-visible calculator feature map.

## What it adds

- Bundled calculator suggestion CSV derived from the WordPress equation registry.
- `SC Workbench -> Calculator Backlog` admin page.
- Import bundled suggestions.
- Upload a revised calculator-suggestion CSV.
- Export the current calculator backlog as CSV.
- Custom WordPress database table: `wp_sc_workbench_calculator_backlog`.
- REST endpoint: `/wp-json/sc-workbench/v1/calculator-backlog` for admin use.

## Purpose

The backlog turns article equations into a development roadmap for article-aware calculators, graphing tools, model routers, predictive analytics, systems modeling, economics, environmental monitoring, engineering tools, lab-science tools, and human-systems analyzers.

## Expected CSV columns

```text
priority
calculator_id
calculator_name
category
estimated_matching_equations
example_equations_from_registry
why_build_it
recommended_inputs
recommended_outputs
implementation_notes
```

## Recommended workflow

1. Scan equations with `SC Workbench -> Equation Registry`.
2. Export the equation registry CSV.
3. Analyze it into a calculator-suggestion CSV.
4. Import the suggestion CSV into `SC Workbench -> Calculator Backlog`.
5. Use the backlog as the feature plan for future Workbench calculator builds.
