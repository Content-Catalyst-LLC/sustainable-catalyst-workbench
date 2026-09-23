#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v860-release-store}"
rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.6.0 release validation ==="
"$PY" -m pytest -q "$ROOT/backend/tests"
"$PY" -m pytest -q "$ROOT/tests"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v850-research-timeline-run-history.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v860-visual-research-canvas.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v860-release-')
c=TestClient(app)
assert c.get('/health').json()['version']=='8.6.0'
m=c.get('/research-canvas/manifest').json(); assert m['ok'] and m['version']=='8.6.0' and m['capabilities']['projectVisualCanvas'] is True
uid='release-v860'; envkey=uid+'-env'; project=uid+'-project'
env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Release Canvas Environment','projectEntityId':project,'components':[]}}).json()
assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'release-check'}).status_code==200
ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Release Canvas Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'release-check'}).status_code==200
asset={'projectKey':project,'assetKey':'release-source','assetType':'source','title':'Release Source','assetRef':'https://example.org/release','contentHash':'abcdef123456','origin':'external'}
assert c.post('/research-assets/register',json={'asset':asset,'expectedAssetRevision':0,'reason':'release-check'}).status_code==200
job=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':'Release solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert job.status_code==200,job.text
jid=job.json()['jobId']; assert c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'release-run'}).status_code==200
canvas=c.get('/research-canvas/'+project); assert canvas.status_code==200,canvas.text
b=canvas.json(); assert {'project','environment','asset','execution','timeline'} <= {n['kind'] for n in b['nodes']}
node=b['nodes'][0]
saved=c.post('/research-canvas/'+project+'/layout/save',json={'expectedLayoutRevision':0,'nodes':[{'nodeId':node['nodeId'],'x':111,'y':222,'pinned':True}]}); assert saved.status_code==200,saved.text
assert saved.json()['layoutRevision']==1 and saved.json()['scientificPayloadsPersisted'] is False
projected=c.get('/research-canvas/'+project).json(); current=next(n for n in projected['nodes'] if n['nodeId']==node['nodeId']); assert current['x']==111 and current['y']==222
sel=c.post('/research-canvas/selection/resolve',json={'projectKey':project,'nodeIds':[node['nodeId']]}); assert sel.status_code==200 and sel.json()['selectionIsViewStateOnly'] is True
lin=c.get('/research-canvas/'+project+'/lineage-overlay'); assert lin.status_code==200 and lin.json()['automaticCausalInferencePerformed'] is False
print('PASS: Workbench v8.6.0 visual research canvas assembled')
print('PASS: authoritative v8 research objects project into linked visual nodes without scientific payload duplication')
print('PASS: layout persistence, optimistic revisions, linked selection, timeline and lineage overlays are active')
print('PASS: canvas remains view composition only and performs no automatic scientific interpretation or Core dispatch')
PYVERIFY
echo "PASS: Workbench v8.6.0 release checks passed."
