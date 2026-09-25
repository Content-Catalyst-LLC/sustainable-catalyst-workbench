from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)

def _seed(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='project-v8110'; envkey='env-v8110'
    env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Publication Handoff Environment','projectEntityId':project,'components':[]}}).json()
    assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v8110-seed'}).status_code==200
    ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Publication Handoff Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
    assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'v8110-seed'}).status_code==200
    r=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':'Evidence run','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert r.status_code==200,r.text
    jid=r.json()['jobId']; assert c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'v8110-seed'}).status_code==200
    ar=c.post('/research-assets/register',json={'asset':{'projectKey':project,'assetKey':'source-a','assetType':'dataset','title':'Source A','contentHash':'0123456789abcdef','origin':'explicit'},'expectedAssetRevision':0,'reason':'v8110-seed'}); assert ar.status_code==200,ar.text
    snap=c.post('/analysis-board/snapshots',json={'projectKey':project,'title':'Publication analysis','jobIds':[jid],'assetKeys':['source-a'],'narrative':[{'itemId':'m1','kind':'method','text':'Root solver method.'},{'itemId':'f1','kind':'finding','title':'Observed root','text':'A researcher-authored finding.','evidenceRefs':[jid],'state':'final'}],'snapshotLabel':'Publication-ready analysis','createdBy':'tester'}); assert snap.status_code==200,snap.text
    return project,jid,snap.json()['snapshotHash']

def test_manifest_status_capabilities():
    m=c.get('/publication-handoff/manifest').json(); assert m['ok'] and m['version']=='9.1.0'
    assert m['capabilities']['evidenceManifestGeneration'] and m['capabilities']['multiDestinationHandoffPlanning']
    assert m['boundaries']['automaticPublicationAuthorized'] is False
    s=c.get('/v8110/status').json(); assert s['contentAddressedHandoffPackages'] and s['automaticPublication'] is False
    caps=c.get('/capabilities').json(); assert caps['version']=='9.1.0'
    for key in ('researchPublicationEvidenceHandoff','publicationHandoffEvidenceManifest','publicationHandoffImmutablePackages','publicationHandoffMultiDestinationPlanning','publicationHandoffCorePlanning','publicationHandoffKnowledgeLibraryPlanning','publicationHandoffResearchLabPlanning'):
        assert caps['coreIntegration'][key] is True

def test_handoff_preserves_snapshot_narrative_and_evidence(monkeypatch,tmp_path):
    project,jid,snapshot=_seed(monkeypatch,tmp_path)
    r=c.post('/publication-handoff/build',json={'projectKey':project,'snapshotHash':snapshot,'title':'Research report','authors':[{'name':'Researcher'}],'keywords':['reproducibility'],'destinations':['platform-core','knowledge-library','research-lab','external-publication']}); assert r.status_code==200,r.text
    p=r.json(); assert p['version']=='9.1.0' and p['snapshotHash']==snapshot and p['packageHash']
    assert p['publication']['findings'][0]['text']=='A researcher-authored finding.'
    assert p['evidenceManifest']['summary']['findingCount']==1 and p['evidenceManifest']['summary']['unresolvedEvidenceRefCount']==0
    assert p['provenance']['analysisSnapshotImmutable'] is True and p['provenance']['researcherAuthoredNarrativePreserved'] is True
    assert len(p['destinationPlans'])==4 and all(x['dispatchPerformed'] is False for x in p['destinationPlans'])
    assert p['boundaries']['publicationPerformed'] is False and p['boundaries']['scientificValidityInferred'] is False

def test_package_is_immutable_content_addressed_and_idempotent(monkeypatch,tmp_path):
    project,jid,snapshot=_seed(monkeypatch,tmp_path)
    body={'projectKey':project,'snapshotHash':snapshot,'packageLabel':'Publication package','createdBy':'tester','destinations':['knowledge-library']}
    one=c.post('/publication-handoff/packages',json=body); assert one.status_code==200,one.text
    a=one.json(); assert a['immutable'] is True and a['packageHash'] and a['recordHash']
    two=c.post('/publication-handoff/packages',json=body); assert two.status_code==200,two.text
    assert two.json()['packageHash']==a['packageHash'] and two.json()['idempotent'] is True
    ls=c.get(f'/publication-handoff/packages/{project}').json(); assert ls['packageCount']==1
    load=c.get(f"/publication-handoff/packages/{project}/{a['packageHash']}"); assert load.status_code==200 and load.json()['recordHash']==a['recordHash']

def test_unresolved_evidence_is_exposed_not_resolved(monkeypatch,tmp_path):
    project,jid,snapshot=_seed(monkeypatch,tmp_path)
    # Build a second snapshot with an explicit unresolved researcher evidence reference.
    snap=c.post('/analysis-board/snapshots',json={'projectKey':project,'title':'Unresolved evidence analysis','jobIds':[jid],'narrative':[{'itemId':'f2','kind':'finding','text':'Finding with unresolved reference.','evidenceRefs':['external-evidence-ref'],'state':'working'}],'snapshotLabel':'Unresolved evidence'}); assert snap.status_code==200
    r=c.post('/publication-handoff/build',json={'projectKey':project,'snapshotHash':snap.json()['snapshotHash'],'destinations':['knowledge-library']}); assert r.status_code==200
    e=r.json()['evidenceManifest']; assert e['summary']['unresolvedEvidenceRefCount']==1 and e['boundaries']['unresolvedEvidenceAutomaticallyRejected'] is False

def test_core_plan_is_two_phase_and_non_publishing(monkeypatch,tmp_path):
    project,jid,snapshot=_seed(monkeypatch,tmp_path)
    r=c.post('/integration/core/publication-handoff/plan',json={'projectKey':project,'snapshotHash':snapshot,'coreSessionId':'core-v8110','destinations':['platform-core']}); assert r.status_code==200,r.text
    p=r.json(); assert p['version']=='9.1.0' and p['publicationHandoffIsGovernedDerivedObjectOnly'] is True
    assert p['automaticCoreDispatchAuthorized'] is False and p['publicationAuthorized'] is False
    assert any(x.get('phase')=='research-publication-evidence-handoff-bind' for x in p['coreRequests'])
