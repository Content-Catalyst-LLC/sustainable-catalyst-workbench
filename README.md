# Sustainable Catalyst Workbench

Sustainable Catalyst Workbench is the scientific computing, engineering analysis, technical prototyping, simulation, visualization, and scientific-AI execution environment of the Sustainable Catalyst platform.

**Current release:** v10.4.0 — Hyperparameter Optimization & Search Engine

## Architecture

Workbench provides governed computational and engineering capabilities while preserving explicit boundaries between calculation, scientific interpretation, and platform governance.

- **Scientific computing** — numerical methods, symbolic work, statistical analysis, uncertainty, sensitivity, optimization, and reproducible execution.
- **Engineering analysis** — electronics, embedded systems, FPGA, robotics, controls, instrumentation, mechanical/thermal, civil/infrastructure, electrical, and energy workflows.
- **Simulation and modeling** — dynamical systems, digital twins, scenario analysis, predictive workflows, and parameter exploration.
- **Scientific visualization** — plots, engineering dashboards, linked views, scientific figures, and visual research outputs.
- **Scientific AI engineering** — model/dataset registries, training and fine-tuning contracts, benchmark/evaluation workflows, and hyperparameter-search studies.
- **Backend runtime** — FastAPI services and governed computational APIs.
- **Go runner / offline components** — bounded local execution and portability support.
- **WordPress interface** — public and research-facing Workbench UI.
- **Platform Core integration** — governed research-object, provenance, evidence, visual, and handoff contracts.

Workbench executes explicit analytical and engineering work. It does not silently substitute assumptions, infer scientific validity, or replace Platform Core governance.

## Repository layout

- `backend/` — Python/FastAPI computation and research runtime.
- `deploy/` — deployment configuration and production helpers.
- `docs/` — current architecture and operational documentation.
- `examples/` — example payloads and workflows.
- `installers/` — maintained installation tooling.
- `offline/` — offline/local execution support.
- `runner-go/` — Go runner.
- `scripts/` — active build, validation, migration, release, and operational tooling.
- `tests/` — active regression and release validation.
- `wordpress-plugin/` — Sustainable Catalyst Workbench WordPress plugin.
- `compose.yml` — container orchestration definition.

## Release history

Historical release notes, validation reports, installer dry runs, terminal-command files, per-version environment examples, field maps, and other generated release artifacts are intentionally not retained at the root of `main`.

The exact repository state immediately before the September 29, 2026 cleanup is preserved on:

`archive/pre-root-cleanup-2026-09-29-workbench`

Git history continues to preserve prior source and release artifacts. Generated release material should live in release bundles or ignored staging directories rather than accumulating in the source-tree root.
