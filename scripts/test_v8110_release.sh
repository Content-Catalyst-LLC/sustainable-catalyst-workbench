#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PY="${SCWB_TEST_PYTHON:-python3}"; cd "$ROOT"; export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"; export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v8110-release-store}"; rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.11.0 release validation ==="
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v8110-research-publication-evidence-handoff.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
if grep -q '127.0.0.1:8000' deploy/contabo/upgrade_workbench_backend_v8_11_0_contabo.sh; then echo 'ERROR: stale Workbench verification port 8000 detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from app.v8110 import manifest
m=manifest()
assert m['version']=='8.11.0'
assert m['capabilities']['evidenceManifestGeneration'] is True
assert m['capabilities']['multiDestinationHandoffPlanning'] is True
assert m['boundaries']['automaticPublicationAuthorized'] is False
print('PASS: Workbench v8.11.0 research publication and evidence handoff manifest assembled')
print('PASS: immutable snapshot handoff, evidence manifests, and explicit destination planning are release-gated')
PYVERIFY
echo "PASS: Workbench v8.11.0 release checks passed."
