from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)

def test_manifest_and_status_boundaries():
    m=c.get('/production-certification/manifest').json(); assert m['ok'] and m['version']=='9.7.0'
    assert m['capabilities']['retainedMilestoneAudit'] and m['capabilities']['persistentStoreWriteProbe']
    for k in ('scientificCorrectnessCertified','evidenceValidityCertified','causalClaimsCertified','statisticalSignificanceCertified','preferredModelCertified','publicationMeritCertified','automaticRemediationAuthorized','automaticCoreDispatchAuthorized'):
        assert m['boundaries'][k] is False
    s=c.get('/v8120/status').json(); assert s['productionCertification'] and s['automaticRemediation'] is False

def test_production_certification_report_passes(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    r=c.post('/production-certification/run',json={'includeStoreWriteProbe':True,'includeCoreConfiguration':True,'requestedBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['ok'] and d['certificationStatus']=='pass' and d['summary']['failed']==0
    assert d['persistentStore']['writeProbePassed'] is True
    assert d['retainedCapabilities']['allRequiredRetained'] is True
    assert d['retainedCapabilities']['retainedCount']==d['retainedCapabilities']['requiredCount']==12
    assert d['publicationHandoff']['version']=='9.7.0' and d['publicationHandoff']['evidenceManifestGeneration'] is True
    assert d['coreConfiguration']['outboundDispatchEnabled'] is False
    assert len(d['reportHash'])==64

def test_capability_registry_exposes_v8120_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.7.0'
    for key in ('unifiedWorkbenchProductionCertification','productionCertificationReleaseIdentity','productionCertificationPersistenceReadiness','productionCertificationCoreCompatibility','productionCertificationPublicationHandoff','productionCertificationWordPressIntegrity','productionCertificationDeploymentInvariants'):
        assert caps['coreIntegration'][key] is True

def test_health_and_prior_milestone_surfaces_are_retained(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    h=c.get('/health').json(); assert h['version']=='9.7.0' and h['readiness']=='ready'
    for path in ('/v800/status','/v810/status','/v820/status','/v830/status','/v840/status','/v850/status','/v860/status','/v870/status','/v880/status','/v890/status','/v8100/status','/v8110/status'):
        r=c.get(path); assert r.status_code==200,(path,r.text)
