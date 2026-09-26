from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)


def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='p970'; env='env-'+p
    e=c.post('/research-environment/build',json={'environment':{'environmentKey':env,'title':'Replication environment','projectEntityId':p,'components':[]}}); assert e.status_code==200,e.text
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':e.json(),'expectedCurrentRevision':0,'reason':'v970-test'}); assert s.status_code==200,s.text
    b=c.post('/research-projects/build',json={'project':{'projectKey':p,'title':'Replication Study','researchQuestion':'Can the result be reproduced?','objectives':['reproduce'],'activeEnvironmentKey':env,'activeEnvironmentRevision':1}}); assert b.status_code==200,b.text
    sp=c.post('/research-projects/save',json={'workspace':b.json(),'expectedProjectRevision':0,'reason':'v970-test'}); assert sp.status_code==200,sp.text
    syn=c.post('/results-synthesis/syntheses',json={'projectKey':p,'synthesisKey':'syn','title':'Target synthesis','resultsNarrative':'Observed result narrative.','statements':[{'statementKey':'r1','kind':'result','statement':'Observed response was 10.0.','sourceRefs':[]}],'createdBy':'test'}); assert syn.status_code==200,syn.text
    return p,syn.json()['synthesisHash']


def payload(p,h,mode='reproduction'):
    x={'projectKey':p,'workflowKey':'rr-1','title':'Reproduction workflow','mode':mode,'targetSynthesisHash':h,'researchQuestion':'Can this result be reproduced?','environment':{'runtime':'python','runtimeVersion':'3.12','containerImage':'workbench:9.9.0'},'inputs':[{'inputKey':'dataset','role':'dataset','objectRef':'asset:data','contentHash':'abc'}],'comparisonCriteria':[{'criterionKey':'metric-y','metric':'metrics.y','comparator':'absolute','targetValue':10.0,'tolerance':0.5,'unit':'unit'}],'invariants':['same dataset']}
    if mode=='replication': x['plannedChanges']=['independent dataset']
    return x


def test_manifest_and_status():
    m=c.get('/reproduction-replication/manifest').json(); assert m['ok'] and m['version']=='9.9.0'
    assert m['capabilities']['environmentCapture'] and m['boundaries']['automaticReplicationVerdict'] is False
    s=c.get('/v970/status').json(); assert s['reproductionReplicationWorkflow'] and s['automaticExecution'] is False


def test_compose_reproduction(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); d=c.post('/reproduction-replication/compose',json=payload(p,h)).json()
    assert d['ok'] and d['mode']=='reproduction' and d['target']['synthesisHash']==h
    assert d['completeness']['readyForExecutionPlanning'] and d['boundaries']['automaticScientificValidityInference'] is False


def test_reproduction_rejects_planned_changes(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); x=payload(p,h); x['plannedChanges']=['changed sample']; assert c.post('/reproduction-replication/compose',json=x).status_code==422


def test_replication_requires_explicit_change_for_readiness(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); x=payload(p,h,'replication'); d=c.post('/reproduction-replication/compose',json=x).json(); assert d['completeness']['replicationChangesDeclared'] is True


def test_content_address_deterministic(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); x=payload(p,h); a=c.post('/reproduction-replication/compose',json=x).json(); b=c.post('/reproduction-replication/compose',json=x).json(); assert a['workflowHash']==b['workflowHash']


def test_save_list_load_idempotent(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); x={**payload(p,h),'createdBy':'tester'}; a=c.post('/reproduction-replication/workflows',json=x).json(); b=c.post('/reproduction-replication/workflows',json=x).json(); assert not a['idempotent'] and b['idempotent']
    ls=c.get(f'/reproduction-replication/workflows/{p}').json(); assert ls['workflowCount']==1
    got=c.get(f"/reproduction-replication/workflows/{p}/{a['workflowHash']}").json(); assert got['recordHash']==a['recordHash']


def test_execution_plan_is_plan_only(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); a=c.post('/reproduction-replication/workflows',json={**payload(p,h),'createdBy':'tester'}).json(); d=c.post('/reproduction-replication/execution-plan',json={'projectKey':p,'workflowHash':a['workflowHash'],'executionRuntime':'python','executionEntryPoint':'run.py'}).json(); assert d['boundaries']['automaticExecution'] is False and d['boundaries']['jobQueued'] is False


def test_comparison_reports_tolerance_without_verdict(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); a=c.post('/reproduction-replication/workflows',json={**payload(p,h),'createdBy':'tester'}).json(); d=c.post('/reproduction-replication/compare',json={'projectKey':p,'workflowHash':a['workflowHash'],'observedMetrics':[{'criterionKey':'metric-y','observedValue':10.3}]}).json(); assert d['summary']['withinToleranceCount']==1 and d['boundaries']['replicationVerdictInferred'] is False


def test_comparison_outside_tolerance(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); a=c.post('/reproduction-replication/workflows',json={**payload(p,h),'createdBy':'tester'}).json(); d=c.post('/reproduction-replication/compare',json={'projectKey':p,'workflowHash':a['workflowHash'],'observedMetrics':[{'criterionKey':'metric-y','observedValue':11.0}],'discrepancyNotes':['difference observed']}).json(); assert d['summary']['outsideToleranceCount']==1 and d['discrepancyNotes']


def test_source_catalog(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); d=c.get(f'/reproduction-replication/source-catalog/{p}').json(); assert d['synthesisCount']==1 and d['boundaries']['catalogInfersReplicability'] is False


def test_core_plan_preserves_governance(monkeypatch,tmp_path):
    p,h=seed_project(monkeypatch,tmp_path); a=c.post('/reproduction-replication/workflows',json={**payload(p,h),'createdBy':'tester'}).json(); d=c.post('/integration/core/reproduction-replication/plan',json={'projectKey':p,'workflowHash':a['workflowHash'],'createdBy':'tester'}).json(); assert d['bindingPlan']['objectType']=='workbench.reproduction-replication-workflow' and d['boundaries']['governedReplicationClaimCreated'] is False


def test_missing_target_returns_404(monkeypatch,tmp_path):
    p,_=seed_project(monkeypatch,tmp_path); x=payload(p,'f'*64); assert c.post('/reproduction-replication/compose',json=x).status_code==404


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.9.0'
    for k in ('reproductionReplicationWorkflow','reproductionReplicationTargetBinding','reproductionReplicationEnvironmentCapture','reproductionReplicationComparisonCriteria','reproductionReplicationResultComparison','reproductionReplicationContentAddressedRecords','reproductionReplicationCorePlanning'): assert caps['coreIntegration'][k] is True
