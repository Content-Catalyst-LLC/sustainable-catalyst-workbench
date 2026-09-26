#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v10.0.0 release validation ==="
TEST_FILES=("$ROOT"/backend/tests/test_*.py)
COUNT=${#TEST_FILES[@]}
MID=$(( (COUNT + 1) / 2 ))
BT1="${TMPDIR:-/tmp}/scwb-v1000-pytest-backend-1"
BT2="${TMPDIR:-/tmp}/scwb-v1000-pytest-backend-2"
BTS="${TMPDIR:-/tmp}/scwb-v1000-pytest-static"
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
        h=c.get('/health').json(); assert h['ok'] and h['version']=='10.0.0' and h['readiness']=='ready',h
        m=c.get('/ai-engineering/manifest').json(); assert m['ok'] and m['version']=='10.0.0' and m['capabilities']['scientificAIEngineeringRuntimeFoundation'],m
        rc=c.get('/ai-engineering/runtime-contracts').json(); assert rc['version']=='10.0.0' and all(x['executionImplemented'] is False for x in rc['contracts']),rc
        s=c.get('/v1000/status').json(); assert s['scientificAIEngineeringRuntimeFoundation'] and s['scientificValidityInferred'] is False,s
        caps=c.get('/capabilities').json(); assert caps['version']=='10.0.0' and caps['coreIntegration']['aiEngineeringCorePlanning'] is True,caps
        old=c.get('/v9-production-certification/manifest').json(); assert old['version']=='10.0.0' and old['capabilities']['retainedV9MilestoneAudit'],old
print('PASS: Workbench v10.0.0 Scientific AI Engineering Runtime Foundation assembled')
print('PASS: AI experiment contracts, provenance, deterministic configuration, neutral execution planning, retained v9 capabilities, and Core boundaries are release-gated')
PYLIVE
echo "PASS: Workbench v10.0.0 release checks passed."
