from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)


def _seed(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='project-v870'; envkey='env-v870'
    env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Linked Views Environment','projectEntityId':project,'components':[]}}).json()
    assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v870-seed'}).status_code==200
    ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Linked Views Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
    assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'v870-seed'}).status_code==200
    for key,atype,origin,tags in [('paper-a','source','external',['climate','evidence']),('dataset-a','dataset','explicit',['climate','model'])]:
        asset={'projectKey':project,'assetKey':key,'assetType':atype,'title':key.replace('-',' ').title(),'assetRef':'https://example.org/'+key,'contentHash':key+'123456789','origin':origin,'tags':tags}
        assert c.post('/research-assets/register',json={'asset':asset,'expectedAssetRevision':0,'reason':'v870-seed'}).status_code==200
    for label in ('Primary solver','Secondary solver'):
        job=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':label,'tags':['linked-view'],'request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert job.status_code==200,job.text
        assert c.post(f"/execution-console/jobs/{job.json()['jobId']}/run",json={'expectedJobRevision':1,'reason':'v870-seed'}).status_code==200
    return project


def test_manifest_status_capabilities():
    m=c.get('/linked-scientific-views/manifest').json(); assert m['ok'] and m['version']=='10.0.0'
    assert m['capabilities']['declarativeCrossFiltering'] and m['boundaries']['filtersMutateScientificObjects'] is False
    s=c.get('/v870/status').json(); assert s['linkedScientificViews'] and s['crossFiltering']
    caps=c.get('/capabilities').json(); assert caps['version']=='10.0.0'
    for key in ('linkedScientificViews','linkedScientificCrossFiltering','linkedScientificSelectionPropagation','linkedScientificFacetCounts','linkedScientificCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_cross_filter_kinds_text_and_facets(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    r=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'kinds':['asset'],'text':'climate'}}); assert r.status_code==200,r.text
    b=r.json(); assert b['filteredNodeCount']==2 and not b['views']['executions']['rows']
    assert {x['assetType'] for x in b['views']['assets']['rows']}=={'source','dataset'}
    facets=b['views']['facets']; assert {x['value'] for x in facets['assetType']}=={'source','dataset'}
    assert b['boundaries']['filtersMutateScientificObjects'] is False


def test_execution_filter_and_linked_selection(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    q=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'runtimeKinds':['solver'],'executionStatuses':['completed']}}); assert q.status_code==200,q.text
    b=q.json(); assert len(b['views']['executions']['rows'])==2 and b['filteredNodeCount']==2
    node=b['views']['executions']['rows'][0]['nodeId']
    s=c.post('/linked-scientific-views/selection/resolve',json={'projectKey':project,'selectedNodeIds':[node],'sourceView':'executions','filters':{'runtimeKinds':['solver'],'executionStatuses':['completed']}}); assert s.status_code==200,s.text
    out=s.json(); assert out['views']['executions']['selectedRowNodeIds']==[node] and out['views']['canvas']['selectedNodeIds']==[node]
    assert out['selectionIsViewStateOnly'] is True


def test_neighbor_expansion_and_unknown_selection(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    assets=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'kinds':['asset']}}).json()['views']['assets']['rows']
    node=assets[0]['nodeId']
    q=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'nodeIds':[node],'includeNeighbors':True}}); assert q.status_code==200,q.text
    kinds={n['kind'] for n in q.json()['views']['canvas']['nodes']}; assert 'asset' in kinds and 'project' in kinds
    bad=c.post('/linked-scientific-views/query',json={'projectKey':project,'selectedNodeIds':['not-a-node']}); assert bad.status_code==404


def test_timeline_range_validation(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    bad=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'timelineStart':'not-a-date'}}); assert bad.status_code==422
    q=c.post('/linked-scientific-views/query',json={'projectKey':project,'filters':{'kinds':['timeline']}}); assert q.status_code==200 and q.json()['views']['timeline']['rows']


def test_core_plan_is_two_phase_and_view_only(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    p=c.post('/integration/core/linked-scientific-views/plan',json={'projectKey':project,'filters':{'kinds':['asset']},'coreSessionId':'core-session-v870'}); assert p.status_code==200,p.text
    b=p.json(); assert b['version']=='10.0.0' and b['linkedViewBindingIsViewStateOnly'] is True
    assert b['automaticCoreDispatchAuthorized'] is False and b['coreRequests']
    assert any(x.get('phase')=='linked-scientific-views-bind' for x in b['coreRequests'])
