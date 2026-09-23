#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v8100-release-store}"
rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.10.0 release validation ==="
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v8100-reproducible-analysis-board.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
if grep -q '127.0.0.1:8000' deploy/contabo/upgrade_workbench_backend_v8_10_0_contabo.sh; then echo 'ERROR: stale Workbench verification port 8000 detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v8100-release-')
c=TestClient(app)
assert c.get('/health').json()['version']=='8.10.0'
assert c.get('/analysis-board/manifest').json()['version']=='8.10.0'
project='release-v8100-project'; envkey='release-v8100-env'
env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Release Board Environment','projectEntityId':project,'components':[]}}).json()
assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'release'}).status_code==200
ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Release Board Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'release'}).status_code==200
r=c.post('/analysis-board/build',json={'projectKey':project,'title':'Release board','narrative':[{'itemId':'n1','kind':'note','text':'Explicit release note.'}]}); assert r.status_code==200,r.text
b=r.json(); assert b['boardHash'] and b['provenance']['sourceHashesPreserved'] is True and b['boundaries']['findingsAutomaticallyGenerated'] is False
s=c.post('/analysis-board/snapshots',json={'projectKey':project,'title':'Release board','snapshotLabel':'Release snapshot'}); assert s.status_code==200,s.text
snap=s.json(); assert snap['immutable'] is True and snap['snapshotHash']
print('PASS: Workbench v8.10.0 reproducible analysis board assembled')
print('PASS: content-addressed immutable snapshot persistence and provenance preservation operate without scientific reinterpretation')
PYVERIFY
echo "PASS: Workbench v8.10.0 release checks passed."
