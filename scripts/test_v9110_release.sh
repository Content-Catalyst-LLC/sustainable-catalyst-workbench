#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
echo "=== Workbench v9.11.0 release validation ==="
TEST_FILES=("$ROOT"/backend/tests/test_*.py)
COUNT=${#TEST_FILES[@]}
MID=$(( (COUNT + 1) / 2 ))
BT1="${TMPDIR:-/tmp}/scwb-v9110-pytest-backend-1"
BT2="${TMPDIR:-/tmp}/scwb-v9110-pytest-backend-2"
BTS="${TMPDIR:-/tmp}/scwb-v9110-pytest-static"
rm -rf "$BT1" "$BT2" "$BTS"
echo "=== Backend regression group 1/2 ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q --basetemp="$BT1" "${TEST_FILES[@]:0:$MID}"
echo "=== Backend regression group 2/2 ==="
PYTHONPATH="$ROOT/backend" "$PY" -m pytest -q --basetemp="$BT2" "${TEST_FILES[@]:$MID}"
echo "=== Static/release regression ==="
PYTHONPATH="$ROOT:$ROOT/backend" "$PY" -m pytest -q --basetemp="$BTS" tests
PYTHONPATH="$ROOT/backend" "$PY" - <<'PYLIVE'
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    h=c.get('/health').json(); assert h['ok'] and h['version']=='9.11.0' and h['readiness']=='ready',h
    m=c.get('/research-study-certification/manifest').json(); assert m['ok'] and m['version']=='9.11.0' and m['capabilities']['crossStageLineageCoherence'],m
    s=c.get('/v9110/status').json(); assert s['endToEndResearchStudyCertification'] and s['certificationIsScientificValidity'] is False,s
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0' and caps['coreIntegration']['researchStudyCertificationCorePlanning'] is True,caps
print('PASS: Workbench v9.11.0 end-to-end research study certification manifest assembled')
print('PASS: structural completeness, lineage, integrity, readiness, and non-validity boundaries are release-gated')
PYLIVE
echo "PASS: Workbench v9.11.0 release checks passed."
