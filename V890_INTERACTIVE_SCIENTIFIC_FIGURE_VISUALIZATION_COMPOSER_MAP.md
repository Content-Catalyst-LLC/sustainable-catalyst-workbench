# Workbench v8.9.0 — Interactive Scientific Figure & Visualization Composer Map

## Flow

`Unified Research Project (v8.2)`
→ `Completed execution jobs/results (v8.4)`
→ `Linked scientific views (v8.7)`
→ `Comparative metric model (v8.8)`
→ **`Interactive Scientific Figure & Visualization Composer (v8.9)`**
→ renderer-neutral figure specification + provenance + export plan

## API surfaces

- `GET /figure-composer/manifest`
- `GET /figure-composer/source-catalog/{project_key}`
- `POST /figure-composer/compose`
- `POST /integration/core/figure-composer/plan`
- `GET /v890/status`

## WordPress surfaces

- `[sc_workbench_scientific_figure_composer project="PROJECT_KEY"]`
- `[sc_workbench_scientific_figure_composer_status]`

## Supported marks

- line
- scatter
- bar
- point
- table

## Authority boundary

The v8.9 figure specification is not a competing scientific source of truth. Project state remains authoritative in v8.2; execution requests/results and hashes remain authoritative in v8.4; linked-view state remains owned by v8.7; comparative metric extraction remains owned by v8.8.
