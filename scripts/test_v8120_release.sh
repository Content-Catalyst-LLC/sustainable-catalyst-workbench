#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PY="${SCWB_TEST_PYTHON:-python3}"; cd "$ROOT"; export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"; export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v8120-release-store}"; rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.12.0 release validation ==="
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v8120-unified-production-certification.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
if grep -q '127.0.0.1:8000' deploy/contabo/upgrade_workbench_backend_v8_12_0_contabo.sh; then echo 'ERROR: stale Workbench verification port 8000 detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from app.v8120 import manifest,run_certification,CertificationRequest
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v8120-cert-')
m=manifest(); assert m['version']=='8.12.0'; assert m['capabilities']['retainedMilestoneAudit'] is True; assert m['boundaries']['scientificCorrectnessCertified'] is False
r=run_certification(CertificationRequest(requestedBy='release-gate')); assert r['ok'] and r['certificationStatus']=='pass' and r['summary']['failed']==0
print('PASS: Workbench v8.12.0 unified production certification assembled')
print('PASS: release identity, persistence, retained capabilities, Core boundaries and publication handoff are certification-gated')
PYVERIFY
echo "PASS: Workbench v8.12.0 release checks passed."
