#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PY="${SCWB_TEST_PYTHON:-python3}"; cd "$ROOT"; export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"; export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v880-release-store}"; rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.8.0 release validation ==="
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v880-comparative-experiment-model-analysis.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v880-release-'); c=TestClient(app)
assert c.get('/health').json()['version']=='8.8.0'; assert c.get('/comparative-analysis/manifest').json()['version']=='8.8.0'
project='release-v880-project'; envkey='release-v880-env'
env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Release Comparison Environment','projectEntityId':project,'components':[]}}).json(); assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'release'}).status_code==200
ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Release Comparison Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json(); assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'release'}).status_code==200
jobs=[]
for bracket in ([0,3],[1,4]):
 r=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':bracket},'solverKey':'root.brentq'}}); assert r.status_code==200,r.text; jid=r.json()['jobId']; assert c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'release'}).status_code==200; jobs.append(jid)
r=c.post('/comparative-analysis/compare',json={'projectKey':project,'jobIds':jobs}); assert r.status_code==200,r.text; b=r.json(); assert b['jobCount']==2 and len(b['pairwiseComparisons'])==1 and b['boundaries']['automaticWinnerSelectionPerformed'] is False
print('PASS: Workbench v8.8.0 comparative experiment & model analysis assembled')
print('PASS: provenance-preserving metric matrices and transparent pairwise deltas operate without ranking')
PYVERIFY
echo "PASS: Workbench v8.8.0 release checks passed."
