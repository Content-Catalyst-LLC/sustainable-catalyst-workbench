# Sustainable Catalyst Prototyping Workbench v2.5.0

A compact AI-enabled research and analytics workbench for modeling, calculating, visualizing, and interpreting complex systems across science, sustainability, engineering, architecture, psychology, economics, governance, and meaning.

Workbench now combines three layers: WordPress provides the public interface, FastAPI/Python performs the established analytical work, and Browser Code Studio provides an editor-first local coding lab with persistent project files, direct Run controls, output, charts, and an optional advanced console. R, Julia, Haskell, and C++ extension bridges remain included for deeper statistical, simulation, formal logic, and performance workflows.

## Packages

- `wordpress-plugin/sustainable-catalyst-workbench/` — WordPress plugin.
- `backend/` — FastAPI analytics and AI backend.
- `extensions/` — optional R, Julia, Haskell, and C++ companion examples.
- `research-library/` — compact Research Library insertion block.
- `scripts/` — setup, run, and GitHub publishing scripts.

## Core shortcodes

```text
[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
[sc_workbench mode="auto"]
[sc_workbench article="article-slug"]
```

## v0.9.7 Equation and Article-Aware Layer

Adds a WordPress database scanner for LaTeX equations in published posts/pages, a custom equation registry table, article-aware Workbench panels, current-article equation lookup, equation-to-tool recommendations, and a FastAPI `/equations/analyze` endpoint for richer equation interpretation. The scanner detects `\(...\)`, `\[...\]`, `$$...$$`, and `[latex]...[/latex]` patterns in `wp_posts.post_content`.

## Local backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8088
```

Then set WordPress:

```text
SC Workbench → Settings
Backend URL: http://127.0.0.1:8088
Enable AI: enabled
Scope gate: enabled
```

## Production note

For the public site, deploy the backend to a real HTTPS endpoint such as `https://api.sustainablecatalyst.com`. Localhost only works on the same machine/server.

## Safety

All calculators are educational and analytical support tools. They are not substitutes for licensed engineering, architectural, legal, medical, psychological, financial, or safety-critical professional judgment.


## v0.7.x Pattern Cluster

Adds Pattern, Geometry, Design, Music, and AI tools: music frequency and chord/scale analysis, color contrast and palette harmony, vector geometry, embedding similarity, PCA, Fourier analysis, classification metrics, and multimodal pattern comparison.


## v0.7.x Expansion

Adds serious global-impact and public-systems tools: environmental monitoring QA/QC, global impact assessment, climate scenarios, earth hazards, marine/ocean health, astronomy, materials science, public-health analytics, international law issue mapping, legal-traditions comparison, and metaphysics frameworks.


## v0.8.1 AI Provider Stack

Keeps AI provider support intentionally simple and production-manageable:

- `disabled` — registry-only answers and calculators.
- `gemini` — recommended free/low-cost first provider.
- `deepseek` — low-cost OpenAI-compatible alternate provider.
- `openai` — optional premium provider.

No Groq provider is included in this release to avoid provider sprawl, extra settings, and unnecessary debugging complexity.

## Production Deployment

For the live Sustainable Catalyst site, deploy the FastAPI backend to a public HTTPS URL and use that URL in the WordPress plugin settings. Localhost (`127.0.0.1:8088`) only works for local testing.

Recommended Render deployment files are included:

- `render.yaml`
- `backend/start.sh`
- `backend/Dockerfile`
- `docs/DEPLOY_FASTAPI_RENDER.md`


## v0.8.1 Final Expansion: Advanced Engineering, Lab Science, and Export Graphics

Adds nuclear physics, particle physics, neurophysics, rocket/orbital mechanics, electronics engineering, RF/antenna systems, full-stack engineering risk/reliability, lab-science analytics, clinical-research metrics, and frontend export controls for SVG/PNG graph images plus PDF-ready reports.


## v0.8.1 Professional Systems Layer

Adds predictive analytics and economics as major modules, plus FPGA/digital systems, electrical power, mechanical, structural, civil infrastructure, urban planning, architecture/building science, and astrophysics tools. The layer is backend-first, export/report-ready, and safety-scoped for professional review.


## Psychology, Thinking, Meaning, and Limits to Growth

Adds psychology, behavioral science, moral psychology, thinking tools, meaning/aesthetics tools, systems modeling, predictive modeling readiness, and a simplified Limits to Growth system-dynamics simulator.


## v0.9.7 Calculator Backlog

v0.9.7 adds an equation-derived calculator backlog admin page, bundled calculator suggestion CSV, CSV upload/export, and a custom WordPress table for turning equation-registry analysis into future Workbench feature planning.


## v0.9.7 Feature Builder

Adds a WordPress admin Feature Builder page using the latest Equation Registry CSV and Calculator Backlog CSV to generate a feature implementation queue, article tool profiles, equation-domain summaries, and feature clusters for future Workbench calculator development.


## v0.9.9 — Built Feature Tools from Feature Builder CSV

Version 0.9.8 promotes the Feature Builder CSV into executable Workbench tools. All 59 rows from `sustainable-catalyst-feature-builder-20260708-121706.csv` are represented as backend tool specs, WordPress local calculator specs, and deterministic MVP engines. The release includes equation-derived calculators for weighted indices, forecasting, stock-flow systems, recurrence dynamics, ODE stability, environmental QA/QC, risk matrices, economics/policy systems, planetary pressure, climate balance, population ecology, chemistry/lab science, optimization, linear algebra diagnostics, causal inference, Bayesian updating, networks, complexity, RF/electrical/power, materials, structural screening, clinical epidemiology, lab calibration, rocket/orbital calculations, content profiles, behavioral systems, and meaning matrices.

These tools remain educational and analytical. Engineering, clinical, structural, RF/power, chemical, lab, aerospace, and safety-critical outputs require professional review.


## v0.9.9 Validation and Routing Upgrade

Adds **SC Workbench → Embed Shortcodes**, which analyzes indexed equations by page/article and generates calculator-specific shortcodes such as `[sc_workbench mode="tool" tool="systems-modeling-tool" article="article-slug"]`. Use this to embed calculators next to articles that contain mathematical formulas.


## v1.0.0 Stable Workbench Core

v1.0.0 adds stable shortcode display modes, an Article Calculator Placement Assistant, a Validation Dashboard, and a Tool Catalog. Use `display="inline"`, `display="compact"`, `display="full"`, or `display="drawer"` to embed calculators near formulas without overwhelming long pages.

## v1.1.0 — Chalkboard Translator + Symbolic Math + Units

Workbench v1.1.0 adds Phase 1 of the advanced symbolic calculator layer:

- `POST /symbolic/analyze` FastAPI endpoint.
- WordPress `/wp-json/sc-workbench/v1/symbolic` proxy.
- Chalkboard tab inside `[sc_workbench]`.
- Standalone shortcode: `[sc_workbench_chalkboard title="Chalkboard Translator"]`.
- Keyboard math translation to chalkboard preview, LaTeX, SymPy code, symbolic operations, optional SVG graphs, and unit-aware engineering notes.

See `docs/V110_CHALKBOARD_SYMBOLIC_MATH_UNITS.md`.


## v1.4.0 Graph Studio

This package adds Phase 2 of the Workbench symbolic interface: Graph Studio with parameter sliders. Use `[sc_workbench_graph_studio title="Graph Studio"]` for a standalone page or the main `[sc_workbench]` shortcode to expose the Graph Studio tab alongside Ask, Chalkboard, Calculate, Models, Equations, and Pathways.

Backend endpoint: `POST /graph/studio`. WordPress REST proxy: `/wp-json/sc-workbench/v1/graph`.


## v1.4.0 Core Engineering Calculators

Adds a core engineering calculator library for mechanics, stress/strain, beam deflection, circuits, RC response, heat transfer, pump power, energy emissions, and FMEA-style risk screening. Outputs include calculation notes, assumptions, validation checks, warnings, and sensitivity graphs.


## v1.5.0 Exportable Calculation Reports

Phase 5 adds backend-generated calculation reports for Workbench results. Engineering Calculator and Engineering Mode outputs can now be exported as structured Markdown and HTML calculation notes with purpose, formula, inputs, units, computed results, graphs, assumptions, validation checks, methods, warnings, and professional-review boundaries.

Backend endpoint:

```text
POST /reports/calculation
```

WordPress proxy endpoint:

```text
/wp-json/sc-workbench/v1/calculation-report
```

Report export buttons now appear in Workbench result panels: Print/PDF, Markdown Report, HTML Report, Copy Report, and Download JSON.


## v1.6.0 Article-Embedded Calculators Near Formulas
- Added backend formula embed planner: POST /articles/formula-embed.
- Added WordPress REST proxy /wp-json/sc-workbench/v1/formula-embed.
- Added [sc_workbench_formula_calculator] and [sc_formula_calculator] shortcodes.
- Added Article Embeds tab to the Workbench.
- Added near-formula shortcode generation to Embed Shortcodes and Placement Assistant admin pages.
- Added frontend formula cards with Recommend, Symbolic, Graph, and Engineering Note actions.
- Added tests and documentation for Phase 6.


## Version 1.7.0 — Advanced Domain Calculators

Adds deterministic calculator families for econometrics, psychometrics, computational biology, computational chemistry, computational physics, architecture, infrastructure, pattern recognition, and astrophysics. The existing engineering calculator UI is upgraded into an Advanced Calculator Library while preserving the prior shortcode.

## Version 1.8.0 — Browser Code Studio Foundation

Adds a browser-native Code Studio to the main Workbench and two standalone shortcodes. The release includes a black-and-green command-line interface, IndexedDB project persistence with localStorage fallback, a virtual filesystem, editor, file browser, event log, chart workspace contract, documentation panel, project export, a WordPress/FastAPI manifest, and a draft structured-job contract for the future downloadable Go runner. Arbitrary code execution is intentionally disabled until the browser runtime release.

```text
[sc_workbench_code_studio title="Browser Code Studio" project="default"]
[sc_workbench_terminal title="Workbench Terminal" project="default"]
```

See `docs/V180_BROWSER_CODE_STUDIO_FOUNDATION.md`.



## Version 1.9.0 — Browser Python, R, JavaScript, and SQL

Adds lazy-loaded browser execution for JavaScript, Python through Pyodide, R through webR, and analytical SQL through DuckDB-Wasm. Code runs on the visitor device in controlled browser workers or WebAssembly runtimes. The release adds runtime selection, load/run/stop controls, command aliases, approved package manifests, structured table and chart rendering, local artifacts, runtime timeouts, and static browser safety checks. WordPress and FastAPI remain non-execution layers.

```text
run /src/main.js
python /src/analysis.py
Rscript /src/analysis.R
duckdb /src/query.sql
```

See `docs/V190_BROWSER_PYTHON_R_JAVASCRIPT_SQL.md`.


## Version 1.9.1 — Editor-First Browser Code Lab

This interface correction makes Code Studio work like a browser coding exercise rather than requiring terminal commands. The Code panel opens by default, users select a language and file, type or paste code, click **Run**, and read output beside the editor. Runtimes still execute entirely on the visitor device.

Highlights:

- Editor-first default view
- Direct Run and Stop controls
- Automatic save before execution
- Automatic runtime loading on first run
- Dedicated stdout and error pane
- Line-number gutter
- Runnable-file selector
- Ctrl/Command + Enter execution shortcut
- Tables and charts retained in a separate results panel
- Command-line interface retained as an optional Advanced Console

See `docs/V191_EDITOR_FIRST_BROWSER_CODE_LAB.md`.

## Version 2.0.0 — Go Runner, Research Lab, and Hardware Studio Foundation

Adds an optional loopback-only Go runner, one-time browser pairing, origin-bound tokens, allowlisted native runtime discovery and execution, a Research Lab Canvas, structured Research and Lab Notebook, Technical Documentation Studio, Arduino Studio, conceptual schematic and PCB generators, synchronized BOM workflows, an Assembly Translator foundation, and an FPGA Studio foundation.

Native execution is disabled by default and is not a hostile-code sandbox. It runs only on the local visitor machine when the runner is explicitly started with `--enable-native-exec`. Generated code, electronics, PCB, and FPGA outputs require technical review and validation.

## Version 2.1.0 — Raspberry Pi, TinyML, and Embedded Device Studio

Adds a Raspberry Pi project generator, structured embedded-device discovery through the loopback Go Runner, TinyML dataset validation and browser baselines, INT8 and Float16 deployment previews, sensor calibration with residual and uncertainty records, device observation logs, an expanded embedded board catalog, and project-bundle exports.

The local runner remains loopback-only and origin-paired. It exposes no arbitrary shell endpoint. The new device-task endpoint accepts only named allowlisted tasks; Arduino CLI board discovery additionally requires `--enable-native-exec`. Generated models, code, wiring assumptions, and deployment scaffolds require hardware-in-the-loop validation.

## Version 2.2.0 — FPGA, Electronics Design, and Hardware Validation Studio

Adds FPGA project generation and implementation-report review, HDL and board-constraint records, electronics architecture checks, structured schematic and netlist validation, BOM lifecycle/cost/substitution review, preliminary PCB planning and design-rule checks, hardware test-plan evaluation, validation dossiers, and expanded local hardware-tool discovery.

The local runner remains loopback-only and origin-paired. It exposes no arbitrary shell endpoint. Named hardware-version tasks require explicit consent and `--enable-native-exec`. Generated HDL, constraints, schematics, netlists, BOMs, PCB plans, test records, and validation results require qualified engineering review and hardware-in-the-loop verification.

## Version 2.3.0 — Robotics, Controls, and Mechatronics Studio

Adds differential-drive kinematics, PID baseline simulation, mechatronics architecture review, actuator sizing, robot state-machine validation, hardware-in-the-loop telemetry checks, and paired local robotics-tool discovery.

## Version 2.4.0 — Instrumentation, Data Acquisition, and Signal Analysis Studio

Adds instrumentation range and resolution review, data-acquisition sizing, time-domain statistics, browser-local spectrum analysis, calibration and uncertainty budgets, measurement-campaign validation, and paired local instrumentation-tool discovery.

## Version 2.5.0 — Simulation, Digital Twin, and Systems Modeling Studio

Adds dynamic simulation, bounded digital-twin calibration, coupled systems models, scenario sweeps, seeded Monte Carlo uncertainty, model validation, and paired local simulation-tool discovery.
