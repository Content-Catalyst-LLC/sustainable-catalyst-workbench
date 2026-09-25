#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PY="${SCWB_TEST_PYTHON:-python3}"; cd "$ROOT"; export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"; export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v910-release-store}"; rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
find "$ROOT/backend" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find "$ROOT/backend" -type f -name '*.pyc' -delete 2>/dev/null || true
echo "=== Workbench v9.1.0 release validation ==="
"$PY" - <<'PYIDENT'
import app.release as r
assert r.APP_VERSION == '9.1.0', (r.__file__,r.APP_VERSION)
print('PASS: canonical Workbench runtime identity =', r.APP_VERSION, 'from', r.__file__)
PYIDENT
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v910-experimental-design-research-protocol-builder.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
if grep -q '127.0.0.1:8000' deploy/contabo/upgrade_workbench_backend_v9_1_0_contabo.sh; then echo 'ERROR: stale Workbench verification port 8000 detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from app.v910 import manifest
m=manifest(); assert m['version']=='9.1.0'; assert m['capabilities']['formalResearchProtocolObject']; assert m['boundaries']['protocolCompletenessIsScientificValidity'] is False
print('PASS: Workbench v9.1.0 experimental design and research protocol manifest assembled')
print('PASS: formal protocols, preregistration metadata, execution planning, and Core boundaries are release-gated')
PYVERIFY
echo "PASS: Workbench v9.1.0 release checks passed."
