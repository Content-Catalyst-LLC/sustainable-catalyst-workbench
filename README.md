# Sustainable Catalyst Workbench v0.8.1

A compact AI-enabled research and analytics workbench for modeling, calculating, visualizing, and interpreting complex systems across science, sustainability, engineering, architecture, psychology, economics, governance, and meaning.

This release is backend-first: WordPress provides the compact interface, while FastAPI/Python performs the analytical work and returns structured results plus SVG graphs. R, Julia, Haskell, and C++ extension bridges are included for deeper statistical, simulation, formal logic, and performance workflows.

## Packages

- `wordpress-plugin/sustainable-catalyst-workbench/` — WordPress plugin.
- `backend/` — FastAPI analytics and AI backend.
- `extensions/` — optional R, Julia, Haskell, and C++ companion examples.
- `research-library/` — compact Research Library insertion block.
- `scripts/` — setup, run, and GitHub publishing scripts.

## Core shortcode

```text
[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
```

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
