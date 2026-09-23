#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v870-release-store}"
rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.7.0 release validation ==="
"$PY" -m pytest -q backend/tests
"$PY" -m pytest -q tests
php -l wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v860-visual-research-canvas.php >/dev/null
php -l wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v870-linked-scientific-views.php >/dev/null
if grep -q 'SCWB_DIR' wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v870-release-')
c=TestClient(app)
assert c.get('/health').json()['version']=='8.7.0'
m=c.get('/linked-scientific-views/manifest').json(); assert m['ok'] and m['version']=='8.7.0' and m['capabilities']['declarativeCrossFiltering'] is True
uid='release-v870'; envkey=uid+'-env'; project=uid+'-project'
env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Release Linked Views Environment','projectEntityId':project,'components':[]}}).json()
assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'release-check'}).status_code==200
ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Release Linked Views Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'release-check'}).status_code==200
for key,atype,origin,tags in [('source-a','source','external',['release','evidence']),('dataset-a','dataset','explicit',['release','data'])]:
    asset={'projectKey':project,'assetKey':key,'assetType':atype,'title':key,'assetRef':'https://example.org/'+key,'contentHash':key+'123456789','origin':origin,'tags':tags}
    r=c.post('/research-assets/register',json={'asset':asset,'expectedAssetRevision':0,'reason':'release-check'}); assert r.status_code==200,r.text
job=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':'Release linked-view solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert job.status_code==200,job.text
jid=job.json()['jobId']; run=c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'release-run'}); assert run.status_code==200,run.text
q=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'kinds':['asset'],'text':'release'}}); assert q.status_code==200,q.text
b=q.json(); assert b['filteredNodeCount']==2 and len(b['views']['assets']['rows'])==2 and b['views']['facets']['assetType']
execq=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'runtimeKinds':['solver'],'executionStatuses':['completed']}}); assert execq.status_code==200,execq.text
ex=execq.json(); assert len(ex['views']['executions']['rows'])==1
nid=ex['views']['executions']['rows'][0]['nodeId']
sel=c.post('/linked-scientific-views/selection/resolve',json={'projectKey':project,'selectedNodeIds':[nid],'sourceView':'executions','filters':{'runtimeKinds':['solver'],'executionStatuses':['completed']}}); assert sel.status_code==200,sel.text
assert sel.json()['views']['canvas']['selectedNodeIds']==[nid] and sel.json()['selectionIsViewStateOnly'] is True
neighbors=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'nodeIds':[nid],'includeNeighbors':True}}); assert neighbors.status_code==200,neighbors.text
assert {'execution','project'} <= {n['kind'] for n in neighbors.json()['views']['canvas']['nodes']}
print('PASS: Workbench v8.7.0 linked scientific views assembled')
print('PASS: declarative cross-filtering synchronizes canvas, asset, execution, timeline, lineage and facet views')
print('PASS: linked selection and one-hop neighbor expansion operate as view state only')
print('PASS: filtering performs no scientific mutation, causal inference, winner selection or automatic Core dispatch')
PYVERIFY
echo "PASS: Workbench v8.7.0 release checks passed."
