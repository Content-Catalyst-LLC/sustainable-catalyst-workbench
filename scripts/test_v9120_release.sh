#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v9.12.0 release validation ==="
TEST_FILES=("$ROOT"/backend/tests/test_*.py)
COUNT=${#TEST_FILES[@]}
MID=$(( (COUNT + 1) / 2 ))
BT1="${TMPDIR:-/tmp}/scwb-v9120-pytest-backend-1"
BT2="${TMPDIR:-/tmp}/scwb-v9120-pytest-backend-2"
BTS="${TMPDIR:-/tmp}/scwb-v9120-pytest-static"
rm -rf "$BT1" "$BT2" "$BTS"
echo "=== Backend regression group 1/2 ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q --basetemp="$BT1" "${TEST_FILES[@]:0:$MID}"
echo "=== Backend regression group 2/2 ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q --basetemp="$BT2" "${TEST_FILES[@]:$MID}"
echo "=== Static/release regression ==="
PYTHONPATH="$ROOT:$ROOT/backend" "$PY" -m pytest -q --basetemp="$BTS" tests
PYTHONPATH="$ROOT/backend" "$PY" - <<'PYLIVE'
import tempfile, os
from fastapi.testclient import TestClient
from app.main import app
with tempfile.TemporaryDirectory() as td:
    os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=td
    with TestClient(app) as c:
        h=c.get('/health').json(); assert h['ok'] and h['version']=='9.12.0' and h['readiness']=='ready',h
        m=c.get('/v9-production-certification/manifest').json(); assert m['ok'] and m['version']=='9.12.0' and m['capabilities']['retainedV9MilestoneAudit'],m
        r=c.post('/v9-production-certification/run',json={'requestedBy':'release-gate'}).json(); assert r['ok'] and r['productionReady'] and r['retainedV9Milestones']['allRequiredRetained'],r
        s=c.get('/v9120/status').json(); assert s['workbenchV9ProductionCertification'] and s['productionCertificationIsScientificValidity'] is False,s
        caps=c.get('/capabilities').json(); assert caps['version']=='9.12.0' and caps['coreIntegration']['v9ProductionCertificationCorePlanning'] is True,caps
print('PASS: Workbench v9.12.0 production certification assembled')
print('PASS: runtime, persistence, retained v9 milestones, portability/handoff, certification, and governance boundaries are release-gated')
PYLIVE
echo "PASS: Workbench v9.12.0 release checks passed."
