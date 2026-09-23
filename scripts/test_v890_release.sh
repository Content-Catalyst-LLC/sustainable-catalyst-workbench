#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v890-release-store}"
rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.9.0 release validation ==="
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v890-interactive-scientific-figure-visualization-composer.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
if grep -q '127.0.0.1:8000' deploy/contabo/upgrade_workbench_backend_v8_9_0_contabo.sh; then echo 'ERROR: stale Workbench verification port 8000 detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v890-release-')
c=TestClient(app)
assert c.get('/health').json()['version']=='8.9.0'
assert c.get('/figure-composer/manifest').json()['version']=='8.9.0'
project='release-v890-project'; envkey='release-v890-env'
env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Release Figure Environment','projectEntityId':project,'components':[]}}).json()
assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'release'}).status_code==200
ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Release Figure Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'release'}).status_code==200
jobs=[]
for bracket in ([0,3],[1,4]):
 r=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':bracket},'solverKey':'root.brentq'}}); assert r.status_code==200,r.text
 jid=r.json()['jobId']; assert c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'release'}).status_code==200; jobs.append(jid)
cat=c.get(f'/figure-composer/source-catalog/{project}').json(); metric=next(x['metric'] for x in cat['resultMetrics'] if x['presentCount']>=2)
r=c.post('/figure-composer/compose',json={'projectKey':project,'jobIds':jobs,'title':'Release figure','panels':[{'panelId':'a','mark':'bar','metricScope':'result','yMetrics':[metric]}]}); assert r.status_code==200,r.text
b=r.json(); assert b['layout']['panelCount']==1 and b['provenance']['sourceHashesPreserved'] is True and b['boundaries']['automaticScientificEncodingSelectionPerformed'] is False
print('PASS: Workbench v8.9.0 interactive scientific figure composer assembled')
print('PASS: explicit figure encodings, provenance, linked selection and export planning operate without scientific reinterpretation')
PYVERIFY
echo "PASS: Workbench v8.9.0 release checks passed."
