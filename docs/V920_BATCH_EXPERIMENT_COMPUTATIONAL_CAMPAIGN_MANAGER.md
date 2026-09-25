# Workbench v9.2.0 — Batch Experiment & Computational Campaign Manager

## Purpose
v9.2.0 operationalizes a v9.1 research protocol as an explicit computational campaign. It expands researcher-authored parameter axes and replication counts into deterministic planned runs, enforces campaign budgets, preserves resumable campaign state, and binds prepared execution-console jobs and their result hashes back to the campaign.

## Authority boundaries
Workbench owns computational campaign planning and execution-state coordination. Platform Core remains the authority for governed research/evidence objects, provenance, findings, reproducibility, and cross-product exchange. v9.2.0 does not automatically queue or run jobs, select a preferred result, infer significance/causality/validity, mutate a protocol, run analysis, or dispatch to Platform Core.

## Primary routes
- `GET /campaign-manager/manifest`
- `GET /campaign-manager/source-catalog/{project_key}`
- `POST /campaign-manager/compose`
- `POST /campaign-manager/campaigns`
- `GET /campaign-manager/campaigns/{project_key}`
- `GET /campaign-manager/campaigns/{project_key}/{campaign_hash}`
- `GET /campaign-manager/campaigns/{project_key}/{campaign_hash}/state`
- `POST /campaign-manager/materialize`
- `POST /campaign-manager/refresh`
- `POST /campaign-manager/analysis-plan`
- `POST /integration/core/campaign-manager/plan`
- `GET /v920/status`
