# Sustainable Catalyst Workbench

Version: 0.1.0

Sustainable Catalyst Workbench is a site-scoped analytical layer for the Sustainable Catalyst Research Library. It connects topic-scoped AI assistance, deterministic calculators, qualitative diagnostics, quantitative models, article-map routing, and reproducible backend engines.

This starter package includes:

- A WordPress plugin with shortcodes and admin settings.
- A FastAPI backend with scope gating, topic registry, tool registry, and starter engines.
- Initial Workbench tools for quantitative, qualitative, governance, sustainability, and decision-support use cases.
- Docker Compose scaffolding for local backend development.
- A GitHub push helper script.

## Architecture

```text
WordPress / Sustainable Catalyst Site
  ↓
Sustainable Catalyst Workbench Plugin
  ↓
FastAPI Backend
  ↓
Scope Gate + Topic Registry + Tool Registry
  ↓
Deterministic Engines + AI/Retrieval Orchestration Stubs
  ↓
PostgreSQL/pgvector + Redis/Celery-ready expansion
```

## Included starter tools

- Linear Algebra Systems Solver
- Decision Matrix
- Risk & Resilience Scorecard
- AI Governance Audit
- Sustainability Tradeoff Matrix
- Qualitative Interpretation Matrix
- Research Library Assistant
- Workbench Tool Finder

## WordPress shortcodes

```text
[sc_workbench]
[sc_workbench_tools]
[sc_workbench tool="linear-system-solver"]
[sc_workbench_ai mode="library-guide"]
[sc_workbench_ai mode="article-copilot" topic="systems-modeling"]
```

## Backend local run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8088
```

Then set the WordPress plugin backend URL to:

```text
http://127.0.0.1:8088
```

## Docker run

```bash
cd backend
docker compose up --build
```

## WordPress install

Zip the folder:

```text
wordpress-plugin/sustainable-catalyst-workbench
```

Upload it in WordPress under Plugins → Add New → Upload Plugin.

## Current limitation

This v0.1.0 package intentionally includes deterministic engines and AI/retrieval stubs, but it does not include production OpenAI credentials, embeddings, or live Research Library indexing. Those should be added after the plugin shell is tested safely on staging.
