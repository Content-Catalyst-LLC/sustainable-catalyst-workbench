import os
from fastapi.testclient import TestClient
from app.main import app
from app.v810 import _store_root

c=TestClient(app)

def _environment(monkeypatch,tmp_path,key='env-v820'):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    spec={'environmentKey':key,'title':'Project Environment','projectEntityId':'project-v820','components':[
        {'componentKey':'data','componentType':'data-workspace','payload':{'workspaceHash':'data-hash'}},
        {'componentKey':'notebook','componentType':'notebook-run','payload':{'notebookRunHash':'nb-hash','cellRuns':[]}},
        {'componentKey':'visual','componentType':'visual-workspace','payload':{'visualWorkspaceHash':'vis-hash','views':[]}},
    ]}
    env=c.post('/research-environment/build',json={'environment':spec}).json()
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v820-test'})
    assert saved.status_code==200,saved.text
    return env

def _workspace(monkeypatch,tmp_path):
    env=_environment(monkeypatch,tmp_path)
    r=c.post('/research-projects/build',json={'project':{
        'projectKey':'project-v820','title':'Unified Research Project','description':'Project workspace test',
        'researchQuestion':'How do the project assets fit together?','objectives':['integrate','reproduce'],
        'tags':['test','v820'],'activeEnvironmentKey':'env-v820','activeEnvironmentRevision':1
    }})
    assert r.status_code==200,r.text
    return r.json()

def test_manifest_and_status():
    m=c.get('/research-projects/manifest').json(); assert m['ok'] and m['version']=='8.9.0' and m['capabilities']['projectCentricWorkspace'] is True
    s=c.get('/v820/status').json(); assert s['ok'] and s['version']=='8.9.0' and s['environmentHistoryAuthority']=='v8.1'

def test_build_dashboard_from_persisted_environment(monkeypatch,tmp_path):
    ws=_workspace(monkeypatch,tmp_path)
    assert ws['activeEnvironmentRevision']==1
    assert ws['dashboard']['countsBySurface']['data']==1
    assert ws['dashboard']['countsBySurface']['notebook']==1
    assert ws['dashboard']['countsBySurface']['visual']==1
    assert ws['scientificExecutionPerformed'] is False

def test_save_load_list_activity_and_conflict(monkeypatch,tmp_path):
    ws=_workspace(monkeypatch,tmp_path)
    save=c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'create-project'})
    assert save.status_code==200,save.text
    assert save.json()['projectRevision']==1
    loaded=c.get('/research-projects/project-v820'); assert loaded.status_code==200 and loaded.json()['workspace']['workspaceHash']==ws['workspaceHash']
    listing=c.get('/research-projects').json(); assert listing['projectCount']==1 and listing['projects'][0]['projectKey']=='project-v820'
    activity=c.get('/research-projects/project-v820/activity').json(); assert activity['activityCount']==1 and activity['activity'][0]['type']=='project-workspace-saved'
    conflict=c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0})
    assert conflict.status_code==409

def test_surface_plan_uses_active_environment(monkeypatch,tmp_path):
    ws=_workspace(monkeypatch,tmp_path)
    c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0})
    r=c.post('/research-projects/surface/plan',json={'projectKey':'project-v820','surface':'notebook','action':'prepare-run','payload':{'notebookKey':'n1'}})
    assert r.status_code==200,r.text
    body=r.json(); assert body['surface']=='notebook' and body['scientificExecutionPerformed'] is False
    assert body['surfacePlan']['automaticDispatchAuthorized'] is False

def test_core_plan_two_phase(monkeypatch,tmp_path):
    ws=_workspace(monkeypatch,tmp_path)
    c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0})
    p1=c.post('/integration/core/research-project-workspace/plan',json={'projectKey':'project-v820','coreProjectEntityId':'core-project-v820'})
    assert p1.status_code==200,p1.text
    b1=p1.json(); assert b1['phase']=='prepare-session' and b1['coreSessionId'] is None and b1['automaticCoreDispatchAuthorized'] is False
    p2=c.post('/integration/core/research-project-workspace/plan',json={'projectKey':'project-v820','coreProjectEntityId':'core-project-v820','coreSessionId':'core-session-1'})
    assert p2.status_code==200,p2.text
    b2=p2.json(); assert b2['phase']=='bind-environment' and b2['coreSessionId']=='core-session-1'
    assert any(x.get('data',{}).get('object_type')=='workbench.research-project-workspace' for x in b2['coreRequests'])

def test_project_record_tamper_rejected(monkeypatch,tmp_path):
    import json
    ws=_workspace(monkeypatch,tmp_path)
    c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0})
    files=list((_store_root()/'projects').glob('*/project.json')); assert len(files)==1
    data=json.loads(files[0].read_text()); data['reason']='tampered'; files[0].write_text(json.dumps(data))
    r=c.get('/research-projects/project-v820'); assert r.status_code==422 and 'integrity' in r.text

def test_capabilities_advertise_v820():
    caps=c.get('/capabilities').json(); assert caps['version']=='8.9.0'
    ci=caps['coreIntegration']
    for key in ('unifiedResearchProjectWorkspace','researchProjectDashboardSummaries','researchProjectSurfaceNavigation','researchProjectActivityHistory','researchProjectCoreSessionPlanning'):
        assert ci[key] is True
