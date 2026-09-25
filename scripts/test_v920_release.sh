#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v9.2.0 release validation ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q backend/tests
PYTHONPATH="$ROOT:$ROOT/backend" "$PY" -m pytest -q tests
PYTHONPATH="$ROOT/backend" "$PY" - <<'PYLIVE'
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    h=c.get('/health').json(); assert h['ok'] and h['version']=='9.2.0' and h['readiness']=='ready',h
    m=c.get('/campaign-manager/manifest').json(); assert m['ok'] and m['version']=='9.2.0' and m['capabilities']['deterministicCartesianParameterSweeps'],m
    s=c.get('/v920/status').json(); assert s['batchExperimentComputationalCampaignManager'] and s['automaticJobExecution'] is False,s
    caps=c.get('/capabilities').json(); assert caps['version']=='9.2.0' and caps['coreIntegration']['computationalCampaignCorePlanning'] is True,caps
print('PASS: Workbench v9.2.0 batch experiment and computational campaign manager manifest assembled')
print('PASS: deterministic sweeps, resumable state, explicit job materialization, and neutral handoff planning are release-gated')
PYLIVE
echo "PASS: Workbench v9.2.0 release checks passed."
