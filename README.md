# Sustainable Catalyst Workbench v1.4.0

A compact AI-enabled research and analytics workbench for modeling, calculating, visualizing, and interpreting complex systems across science, sustainability, engineering, architecture, psychology, economics, governance, and meaning.

This release is backend-first: WordPress provides the compact interface, while FastAPI/Python performs the analytical work and returns structured results plus SVG graphs. R, Julia, Haskell, and C++ extension bridges are included for deeper statistical, simulation, formal logic, and performance workflows.

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
