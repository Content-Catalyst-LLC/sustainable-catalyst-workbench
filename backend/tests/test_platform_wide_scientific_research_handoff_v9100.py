from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)


def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='p9100'; env='env-'+p
    e=c.post('/research-environment/build',json={'environment':{'environmentKey':env,'title':'Handoff environment','projectEntityId':p,'components':[]}}); assert e.status_code==200,e.text
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':e.json(),'expectedCurrentRevision':0,'reason':'v9100-test'}); assert s.status_code==200,s.text
    b=c.post('/research-projects/build',json={'project':{'projectKey':p,'title':'Platform-wide handoff project','researchQuestion':'Can this research package be handed off explicitly?','objectives':['prepare cross-product handoff'],'activeEnvironmentKey':env,'activeEnvironmentRevision':1}}); assert b.status_code==200,b.text
    sp=c.post('/research-projects/save',json={'workspace':b.json(),'expectedProjectRevision':0,'reason':'v9100-test'}); assert sp.status_code==200,sp.text
    return p


def seed_package(p):
    r=c.post('/research-package-exchange/packages',json={'projectKey':p,'packageKey':'handoff-package','title':'Platform handoff package','includeProjectWorkspace':True,'selections':[],'createdBy':'tester'})
    assert r.status_code==200,r.text
    return r.json()


def handoff_body(p,package_hash,destinations=None):
    return {'projectKey':p,'handoffKey':'handoff-1','title':'Scientific research handoff','portablePackageHash':package_hash,'destinations':destinations or ['platform-core','archive'],'createdBy':'tester'}


def test_manifest_and_status():
    m=c.get('/scientific-research-handoff/manifest').json(); assert m['ok'] and m['version']=='9.11.0'
    assert m['capabilities']['destinationSpecificContracts'] and m['boundaries']['automaticDestinationDispatch'] is False
    s=c.get('/v9100/status').json(); assert s['platformWideScientificResearchHandoff'] and s['governedCoreObjectCreated'] is False


def test_compose_handoff_is_content_addressed(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=seed_package(p); body=handoff_body(p,pkg['packageHash'])
    a=c.post('/scientific-research-handoff/compose',json=body); b=c.post('/scientific-research-handoff/compose',json=body)
    assert a.status_code==200 and b.status_code==200
    x=a.json(); y=b.json(); assert x['handoffHash']==y['handoffHash'] and len(x['handoffHash'])==64
    assert x['readiness']['allRequestedDestinationsReady'] is True
    assert x['lifecycle']['dispatchState']=='not-dispatched'


def test_save_and_list_are_idempotent(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=seed_package(p); body=handoff_body(p,pkg['packageHash'])
    a=c.post('/scientific-research-handoff/handoffs',json=body).json(); b=c.post('/scientific-research-handoff/handoffs',json=body).json()
    assert a['handoffHash']==b['handoffHash'] and b['idempotent'] is True
    ls=c.get(f'/scientific-research-handoff/handoffs/{p}').json(); assert ls['handoffCount']==1
    got=c.get(f"/scientific-research-handoff/handoffs/{p}/{a['handoffHash']}").json(); assert got['portablePackageHash']==pkg['packageHash']


def test_destination_readiness_reports_missing_requirements(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=seed_package(p); body=handoff_body(p,pkg['packageHash'],['knowledge-library','archive'])
    x=c.post('/scientific-research-handoff/compose',json=body).json()
    assert x['readiness']['readyDestinationCount']==1 and x['readiness']['unresolvedDestinationCount']==1
    k=next(z for z in x['destinationPlans'] if z['destination']=='knowledge-library'); assert not k['readyForExplicitDispatchPlanning'] and 'results-synthesis' in k['missingRequirements']
    body['requireAllDestinationsReady']=True
    assert c.post('/scientific-research-handoff/compose',json=body).status_code==409


def test_destination_plan_is_plan_only(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=seed_package(p); h=c.post('/scientific-research-handoff/handoffs',json=handoff_body(p,pkg['packageHash'])).json()
    r=c.post('/scientific-research-handoff/destination-plan',json={'projectKey':p,'handoffHash':h['handoffHash'],'destination':'archive','requestedBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['destinationPlan']['readyForExplicitDispatchPlanning'] and d['boundaries']['automaticDispatch'] is False and d['boundaries']['destinationStateMutated'] is False


def test_core_plan_is_governance_plan_only(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=seed_package(p); h=c.post('/scientific-research-handoff/handoffs',json=handoff_body(p,pkg['packageHash'])).json()
    r=c.post('/integration/core/scientific-research-handoff/plan',json={'projectKey':p,'handoffHash':h['handoffHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.scientific-research-handoff' and d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False


def test_source_catalog_exposes_packages_and_handoffs(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=seed_package(p); c.post('/scientific-research-handoff/handoffs',json=handoff_body(p,pkg['packageHash']))
    x=c.get(f'/scientific-research-handoff/source-catalog/{p}').json(); assert x['portablePackageCount']==1 and x['handoffCount']==1 and 'crossStudyMetaAnalyses' in x['upstreamCatalogs']


def test_missing_package_is_404(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path)
    r=c.post('/scientific-research-handoff/compose',json=handoff_body(p,'0'*64)); assert r.status_code==404


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0'
    for k in ('platformWideScientificResearchHandoff','scientificResearchPortableTransportBinding','scientificResearchDestinationContracts','scientificResearchDestinationReadiness','scientificResearchRequirementReporting','scientificResearchContentAddressedHandoffs','scientificResearchCrossProductPlanning','scientificResearchCoreGovernancePlanning'):
        assert caps['coreIntegration'][k] is True
