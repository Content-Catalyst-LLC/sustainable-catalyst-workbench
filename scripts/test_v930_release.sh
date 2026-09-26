#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v9.3.0 release validation ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q backend/tests
PYTHONPATH="$ROOT:$ROOT/backend" "$PY" -m pytest -q tests
PYTHONPATH="$ROOT/backend" "$PY" - <<'PYLIVE'
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    h=c.get('/health').json(); assert h['ok'] and h['version']=='9.3.0' and h['readiness']=='ready',h
    m=c.get('/statistical-workspace/manifest').json(); assert m['ok'] and m['version']=='9.3.0' and m['capabilities']['linearRegressionDiagnostics'],m
    s=c.get('/v930/status').json(); assert s['statisticalAnalysisDiagnosticWorkspace'] and s['automaticSignificanceDecision'] is False,s
    caps=c.get('/capabilities').json(); assert caps['version']=='9.3.0' and caps['coreIntegration']['statisticalAnalysisCorePlanning'] is True,caps
print('PASS: Workbench v9.3.0 statistical analysis and diagnostic workspace manifest assembled')
print('PASS: explicit methods, statistical diagnostics, provenance, content addressing, and Core planning are release-gated')
PYLIVE
echo "PASS: Workbench v9.3.0 release checks passed."
