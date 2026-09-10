# Workbench v6.0.1 — Unified Experience, Runtime Identity & Interface Hardening

v6.0.1 is a patch release focused on the public and in-product Workbench experience rather than adding another specialist computation engine.

## Runtime identity

- promotes the FastAPI application, Docker image, WordPress plugin, canonical studio router, unified computational-project interface, and public experience to v6.0.1;
- adds `GET /v601/status` as the patch-line release identity endpoint;
- points WordPress connection diagnostics at `/v601/status` while retaining the existing bounded `/v600/*` computational-project routes;
- removes v5.9/v6.0.0 public-experience promotion logic from the canonical v6.0.1 page surface.

## Unified interface

- groups all 39 studios into Project, Math, Model, Engineer, Data, and Record views;
- adds studio search, browser-local favorites, and browser-local recents;
- constrains the 39-studio navigator to internal scrolling on desktop instead of allowing it to create a very tall page column;
- preserves every specialist studio; no capability is removed or hidden behind a reduced catalog;
- makes `[sc_workbench_experience]` a native v6.0.1 experience that does not include the homepage showcase widget.

## Graph hardening

- adds ResizeObserver-based redraw to Advanced Graph Mathematics;
- redraws after studio activation, panel visibility changes, fullscreen changes, document visibility changes, and viewport resize;
- keeps the public graph in normal document flow and removes sticky/clipping assumptions from the v6.0.1 experience shell.

## Unified computational project density

- removes the v6.0.0 fixed 720px layout minimum;
- constrains the project-control column to internal scrolling while leaving the project graph/workspace in natural document flow.

## Boundary

This release changes interface orchestration and release identity. It does not authorize arbitrary code execution, remote shell access, autonomous publication, automatic certification, or automatic device programming.
