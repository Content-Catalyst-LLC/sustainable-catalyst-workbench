from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

def test_manifest_and_status_boundaries():
    m=c.get('/v9-production-certification/manifest').json(); assert m['ok'] and m['version']=='9.12.0'
    assert len(m['requiredV9Milestones'])==12 and m['capabilities']['retainedV9MilestoneAudit']
    for k in ('productionCertificationIsScientificValidity','scientificCorrectnessCertified','evidenceTruthCertified','causalClaimsCertified','statisticalMeritCertified','peerReviewCertified','publicationMeritCertified','automaticRemediation','automaticCoreDispatch','governedCoreObjectCreated'):
        assert m['boundaries'][k] is False
    s=c.get('/v9120/status').json(); assert s['workbenchV9ProductionCertification'] and s['productionCertificationIsScientificValidity'] is False


def test_runtime_certification_passes(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    r=c.post('/v9-production-certification/run',json={'certificationKey':'prod-cert','requestedBy':'tester','includeStoreWriteProbe':True,'includeCoreConfiguration':True,'includeMilestoneManifestAudit':True}); assert r.status_code==200,r.text
    d=r.json(); assert d['ok'] and d['productionReady'] and d['certificationStatus']=='pass' and d['summary']['failed']==0
    assert d['persistentStore']['writeProbePassed'] is True
    assert d['retainedV9Milestones']['allRequiredRetained'] and d['retainedV9Milestones']['passedCount']==d['retainedV9Milestones']['requiredCount']==12
    assert d['deploymentContract']['localPort']==8088 and d['deploymentContract']['dockerImage']=='sustainable-catalyst-workbench:9.12.0'
    assert d['boundaries']['productionCertificationIsScientificValidity'] is False and len(d['reportHash'])==64


def test_all_v9_milestone_manifests_are_current(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    d=c.post('/v9-production-certification/run',json={'requestedBy':'tester'}).json()
    rows=d['retainedV9Milestones']['milestones']; assert len(rows)==12
    assert all(x['manifestReady'] and x['capabilityRetained'] and x['passed'] for x in rows)
    assert all(x['manifestVersion']=='9.12.0' and len(x['manifestHash'])==64 for x in rows)


def test_save_is_content_addressed_and_idempotent(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    req={'certificationKey':'prod-cert','requestedBy':'tester','notes':'release certification'}
    a=c.post('/v9-production-certification/certifications',json=req); assert a.status_code==200,a.text
    x=a.json(); assert x['idempotent'] is False and len(x['certificationHash'])==64 and len(x['recordHash'])==64
    y=c.post('/v9-production-certification/certifications',json=req).json(); assert y['idempotent'] is True and y['certificationHash']==x['certificationHash']
    got=c.get('/v9-production-certification/certifications/'+x['certificationHash']).json(); assert got['recordHash']==x['recordHash']
    ls=c.get('/v9-production-certification/certifications').json(); assert ls['certificationCount']==1


def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    cert=c.post('/v9-production-certification/certifications',json={'certificationKey':'core-plan','requestedBy':'tester'}).json()
    r=c.post('/integration/core/v9-production-certification/plan',json={'certificationHash':cert['certificationHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.v9-production-certification' and d['bindingPlan']['productionReady'] is True
    assert d['bindingPlan']['scientificValidityCertified'] is False
    assert d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False


def test_capability_registry_exposes_v9120_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.12.0'
    for key in ('workbenchV9ProductionCertification','v9ProductionCertificationReleaseIdentity','v9ProductionCertificationRuntimeReadiness','v9ProductionCertificationPersistenceReadiness','v9ProductionCertificationRetainedMilestones','v9ProductionCertificationPortabilityHandoff','v9ProductionCertificationDeploymentInvariants','v9ProductionCertificationContentAddressedRecords','v9ProductionCertificationCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_health_and_complete_v9_status_surface_retained(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    h=c.get('/health').json(); assert h['version']=='9.12.0' and h['readiness']=='ready'
    for path in ('/v900/status','/v910/status','/v920/status','/v930/status','/v940/status','/v950/status','/v960/status','/v970/status','/v980/status','/v990/status','/v9100/status','/v9110/status','/v9120/status'):
        r=c.get(path); assert r.status_code==200,(path,r.text)
