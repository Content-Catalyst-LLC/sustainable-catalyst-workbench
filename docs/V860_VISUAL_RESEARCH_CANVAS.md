# Visual Research Canvas API — v8.6.0

The v8.6 canvas is a visual composition layer over authoritative Workbench research objects.

## Endpoints

- `GET /research-canvas/manifest`
- `GET /research-canvas/{project_key}`
- `GET /research-canvas/{project_key}/layout`
- `POST /research-canvas/{project_key}/layout/save`
- `GET /research-canvas/{project_key}/lineage-overlay`
- `POST /research-canvas/selection/resolve`
- `POST /integration/core/research-canvas/plan`
- `GET /v860/status`

## Layout concurrency

Layout saves support `expectedLayoutRevision`. A stale expected revision returns HTTP 409 instead of overwriting a newer visual arrangement.

## WordPress

Use `[sc_workbench_visual_research_canvas project="PROJECT_KEY"]` for the interactive visual workspace and `[sc_workbench_visual_research_canvas_status]` for a lightweight backend status display.
