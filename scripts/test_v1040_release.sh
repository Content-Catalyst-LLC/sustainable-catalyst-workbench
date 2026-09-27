#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v10.4.0 release validation ==="
TEST_FILES=("$ROOT"/backend/tests/test_*.py)
COUNT=${#TEST_FILES[@]}
MID=$(( (COUNT + 1) / 2 ))
BT1="${TMPDIR:-/tmp}/scwb-v1040-pytest-backend-1"
BT2="${TMPDIR:-/tmp}/scwb-v1040-pytest-backend-2"
BTS="${TMPDIR:-/tmp}/scwb-v1040-pytest-static"
rm -rf "$BT1" "$BT2" "$BTS"
echo "=== Backend regression group 1/2 ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q --basetemp="$BT1" "${TEST_FILES[@]:0:$MID}"
echo "=== Backend regression group 2/2 ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q --basetemp="$BT2" "${TEST_FILES[@]:$MID}"
echo "=== Static/release regression ==="
PYTHONPATH="$ROOT:$ROOT/backend" "$PY" -m pytest -q --basetemp="$BTS" tests
PYTHONPATH="$ROOT/backend" "$PY" - <<'PYLIVE'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
with tempfile.TemporaryDirectory() as td:
    os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=td
    with TestClient(app) as c:
        h=c.get('/health').json(); assert h['ok'] and h['version']=='10.4.0' and h['readiness']=='ready',h
        m=c.get('/ai-optimization/manifest').json(); assert m['ok'] and m['version']=='10.4.0' and m['capabilities']['hyperparameterOptimizationSearchEngine'],m
        s=c.get('/v1040/status').json(); assert s['gridSearch'] and s['latinHypercubeSearch'] and s['automaticWinnerSelection'] is False,s
        old3=c.get('/ai-evaluation/manifest').json(); assert old3['version']=='10.4.0' and old3['capabilities']['aiEvaluationBenchmarkWorkspace'],old3
        old2=c.get('/ai-training/manifest').json(); assert old2['version']=='10.4.0' and old2['capabilities']['trainingFineTuningExperimentRuntime'],old2
        old1=c.get('/ai-registry/manifest').json(); assert old1['version']=='10.4.0' and old1['capabilities']['modelDatasetRegistry'],old1
        old0=c.get('/ai-engineering/manifest').json(); assert old0['version']=='10.4.0' and old0['capabilities']['scientificAIEngineeringRuntimeFoundation'],old0
        caps=c.get('/capabilities').json(); assert caps['version']=='10.4.0' and caps['coreIntegration']['aiOptimizationSearchEngine'] is True,caps
print('PASS: Workbench v10.4.0 Hyperparameter Optimization & Search Engine assembled')
print('PASS: typed search spaces, deterministic grid/random/Latin-hypercube trials, external optimizer contracts, immutable results, objective diagnostics, retained v10.0–v10.3 surfaces, and Core boundaries are release-gated')
PYLIVE
echo "PASS: Workbench v10.4.0 release checks passed."
