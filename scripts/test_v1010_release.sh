#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v10.1.0 release validation ==="
TEST_FILES=("$ROOT"/backend/tests/test_*.py)
COUNT=${#TEST_FILES[@]}
MID=$(( (COUNT + 1) / 2 ))
BT1="${TMPDIR:-/tmp}/scwb-v1010-pytest-backend-1"
BT2="${TMPDIR:-/tmp}/scwb-v1010-pytest-backend-2"
BTS="${TMPDIR:-/tmp}/scwb-v1010-pytest-static"
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
        h=c.get('/health').json(); assert h['ok'] and h['version']=='10.1.0' and h['readiness']=='ready',h
        m=c.get('/ai-registry/manifest').json(); assert m['ok'] and m['version']=='10.1.0' and m['capabilities']['modelDatasetRegistry'],m
        s=c.get('/v1010/status').json(); assert s['immutableVersionedRecords'] and s['scientificValidityInferred'] is False,s
        old=c.get('/ai-engineering/manifest').json(); assert old['version']=='10.1.0' and old['capabilities']['scientificAIEngineeringRuntimeFoundation'],old
        caps=c.get('/capabilities').json(); assert caps['version']=='10.1.0' and caps['coreIntegration']['aiRegistryExperimentBindings'] is True,caps
print('PASS: Workbench v10.1.0 Model & Dataset Registry assembled')
print('PASS: immutable versions, integrity, registry search, experiment bindings, retained v10.0 foundation, and Core boundaries are release-gated')
PYLIVE
echo "PASS: Workbench v10.1.0 release checks passed."
