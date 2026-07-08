# Sustainable Catalyst Workbench v0.7.0

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


## v0.7.0 Pattern Cluster

Adds Pattern, Geometry, Design, Music, and AI tools: music frequency and chord/scale analysis, color contrast and palette harmony, vector geometry, embedding similarity, PCA, Fourier analysis, classification metrics, and multimodal pattern comparison.


## v0.7.0 Expansion

Adds serious global-impact and public-systems tools: environmental monitoring QA/QC, global impact assessment, climate scenarios, earth hazards, marine/ocean health, astronomy, materials science, public-health analytics, international law issue mapping, legal-traditions comparison, and metaphysics frameworks.
