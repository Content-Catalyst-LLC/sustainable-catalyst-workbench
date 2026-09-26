from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def seed_foundation(monkeypatch, tmp_path, project='p-v9110'):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    env='env-'+project
    e=c.post('/research-environment/build',json={'environment':{'environmentKey':env,'title':'Certification environment','projectEntityId':project,'components':[]}}); assert e.status_code==200,e.text
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':e.json(),'expectedCurrentRevision':0,'reason':'v9110-test'}); assert s.status_code==200,s.text
    b=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Certification project','researchQuestion':'Is this research lifecycle structurally traceable?','objectives':['certify research lineage'],'activeEnvironmentKey':env,'activeEnvironmentRevision':1}}); assert b.status_code==200,b.text
    sp=c.post('/research-projects/save',json={'workspace':b.json(),'expectedProjectRevision':0,'reason':'v9110-test'}); assert sp.status_code==200,sp.text
    st=c.post('/study-composer/studies',json={'projectKey':project,'studyKey':'study-1','title':'Certification study','researchQuestion':'Is this research lifecycle structurally traceable?','objectives':['certify lineage'],'protocol':{'designType':'simulation','methods':['parameter sweep']},'status':'active','createdBy':'tester'}); assert st.status_code==200,st.text
    study=st.json()
    protocol={
      'projectKey':project,'studyHash':study['studyHash'],'protocolKey':'protocol-001','title':'Certification protocol','protocolVersion':'1.0','status':'draft',
      'hypotheses':[{'hypothesisId':'h1','statement':'Output changes as x changes','kind':'primary'}],
      'variables':[{'variableId':'x','label':'X','role':'treatment','dataType':'continuous'},{'variableId':'y','label':'Y','role':'outcome','dataType':'continuous'}],
      'sampling':{'population':'simulated systems','method':'simulation','targetSampleSize':2},
      'measurement':{'primaryOutcomeIds':['y']},
      'analysis':{'primaryEstimand':'response across x','statisticalMethods':['descriptive comparison']},
      'stopping':{'ruleType':'fixed','target':'two planned runs'},'createdBy':'tester'
    }
    pr=c.post('/protocol-builder/protocols',json=protocol); assert pr.status_code==200,pr.text
    campaign={
      'projectKey':project,'protocolHash':pr.json()['protocolHash'],'campaignKey':'campaign-001','title':'Certification campaign','status':'ready','runtimeKind':'unified',
      'requestTemplate':{'operation':'evaluate','parameters':{'x':0}},'parameterAxes':[{'path':'parameters.x','values':[1,2]}],
      'replications':1,'budget':{'maxRuns':4,'maxPreparedJobs':2},'createdBy':'tester'
    }
    ca=c.post('/campaign-manager/campaigns',json=campaign); assert ca.status_code==200,ca.text
    return project, study, pr.json(), ca.json()


def body(project, study, protocol, campaign, profile='study-foundation'):
    return {'projectKey':project,'certificationKey':'cert-001','title':'End-to-end certification','profile':profile,
            'studyHash':study['studyHash'],'protocolHash':protocol['protocolHash'],'campaignHash':campaign['campaignHash'],'reviewer':'tester','createdBy':'tester'}


def test_manifest_and_status():
    m=c.get('/research-study-certification/manifest').json(); assert m['ok'] and m['version']=='9.11.0'
    assert m['capabilities']['crossStageLineageCoherence'] and m['boundaries']['certificationIsScientificValidity'] is False
    assert 'full-v9' in m['profiles'] and 'platform-wide-research-handoff' in m['profiles']['full-v9']
    s=c.get('/v9110/status').json(); assert s['endToEndResearchStudyCertification'] and s['automaticStudyApproval'] is False


def test_foundation_profile_can_complete(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path)
    r=c.post('/research-study-certification/evaluate',json=body(p,st,pr,ca)); assert r.status_code==200,r.text
    d=r.json(); assert d['certificationStatus']=='complete' and d['scientificValidityCertified'] is False
    assert d['dimensions']['profileCompleteness']['complete'] and d['dimensions']['lineageCoherence']['complete']
    checks={x['check']:x for x in d['lineageChecks']}; assert checks['protocol→study']['coherent'] and checks['campaign→protocol']['coherent'] and checks['campaign→study']['coherent']


def test_reproducible_profile_reports_explicit_gaps(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path)
    r=c.post('/research-study-certification/evaluate',json=body(p,st,pr,ca,'reproducible-study')); assert r.status_code==200,r.text
    d=r.json(); assert d['certificationStatus']=='incomplete'
    missing={x['stage'] for x in d['gaps'] if x['code']=='required-object-missing'}
    assert {'statistical-analysis','uncertainty-sensitivity-study','model-calibration','results-synthesis','reproduction-replication-workflow'} <= missing
    assert d['boundaries']['automaticRemediation'] is False


def test_lineage_mismatch_is_reported_without_scientific_verdict(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path)
    # Make a second study/protocol and deliberately combine that protocol with the first study.
    st2=c.post('/study-composer/studies',json={'projectKey':p,'studyKey':'study-2','title':'Other study','researchQuestion':'Other question','objectives':['other'],'protocol':{'designType':'simulation','methods':['other']},'status':'active','createdBy':'tester'}).json()
    payload={'projectKey':p,'studyHash':st2['studyHash'],'protocolKey':'protocol-002','title':'Other protocol','protocolVersion':'1.0','status':'draft','hypotheses':[{'hypothesisId':'h2','statement':'Other','kind':'primary'}],'variables':[{'variableId':'x','label':'X','role':'treatment','dataType':'continuous'},{'variableId':'y','label':'Y','role':'outcome','dataType':'continuous'}],'sampling':{'population':'sim','method':'simulation','targetSampleSize':2},'measurement':{'primaryOutcomeIds':['y']},'analysis':{'primaryEstimand':'other','statisticalMethods':['descriptive']},'stopping':{'ruleType':'fixed','target':'two'},'createdBy':'tester'}
    pr2=c.post('/protocol-builder/protocols',json=payload).json()
    req=body(p,st,pr2,ca); req['profile']='study-foundation'
    d=c.post('/research-study-certification/evaluate',json=req).json(); assert d['certificationStatus']=='incomplete'
    assert any(g.get('code')=='lineage-mismatch' and g.get('check')=='protocol→study' for g in d['gaps'])
    assert d['scientificValidityCertified'] is False


def test_save_is_content_addressed_and_idempotent(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path); req=body(p,st,pr,ca)
    a=c.post('/research-study-certification/certifications',json=req); assert a.status_code==200,a.text
    x=a.json(); assert x['idempotent'] is False and len(x['certificationHash'])==64 and len(x['recordHash'])==64
    y=c.post('/research-study-certification/certifications',json=req).json(); assert y['idempotent'] is True and y['certificationHash']==x['certificationHash']
    got=c.get(f"/research-study-certification/certifications/{p}/{x['certificationHash']}").json(); assert got['recordHash']==x['recordHash']
    ls=c.get(f'/research-study-certification/certifications/{p}').json(); assert ls['certificationCount']==1


def test_optional_portable_package_and_handoff_are_integrity_checked(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path)
    selections=[
      {'objectType':'scientific-study','objectHash':st['studyHash']},
      {'objectType':'research-protocol','objectHash':pr['protocolHash']},
      {'objectType':'computational-campaign','objectHash':ca['campaignHash']},
    ]
    pkg=c.post('/research-package-exchange/packages',json={'projectKey':p,'packageKey':'cert-package','title':'Certification package','includeProjectWorkspace':True,'selections':selections,'createdBy':'tester'}); assert pkg.status_code==200,pkg.text
    h=c.post('/scientific-research-handoff/handoffs',json={'projectKey':p,'handoffKey':'cert-handoff','title':'Certification handoff','portablePackageHash':pkg.json()['packageHash'],'destinations':['platform-core','archive'],'createdBy':'tester'}); assert h.status_code==200,h.text
    req=body(p,st,pr,ca); req['portablePackageHash']=pkg.json()['packageHash']; req['handoffHash']=h.json()['handoffHash']
    d=c.post('/research-study-certification/evaluate',json=req).json(); assert d['certificationStatus']=='complete'
    stage={x['stage']:x for x in d['stageAssessments']}; assert stage['portable-research-package']['integrity']['valid'] is True and stage['platform-wide-research-handoff']['integrity']['valid'] is True
    checks={x['check']:x for x in d['lineageChecks']}; assert checks['handoff→portable-package']['coherent'] and checks['portable-package-includes→scientific-study']['coherent']


def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path); cert=c.post('/research-study-certification/certifications',json=body(p,st,pr,ca)).json()
    r=c.post('/integration/core/research-study-certification/plan',json={'projectKey':p,'certificationHash':cert['certificationHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.research-study-certification' and d['bindingPlan']['scientificValidityCertified'] is False
    assert d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False


def test_source_catalog_and_capability_flags(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path); c.post('/research-study-certification/certifications',json=body(p,st,pr,ca))
    cat=c.get(f'/research-study-certification/source-catalog/{p}').json(); assert cat['ok'] and cat['catalogs']['researchStudyCertifications']['certificationCount']==1
    assert 'platformWideResearchHandoffs' in cat['catalogs']
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0'
    for k in ('endToEndResearchStudyCertification','researchStudyCertificationProfiles','researchStudyCertificationObjectIntegrity','researchStudyCertificationLineageCoherence','researchStudyCertificationReproducibilityReadiness','researchStudyCertificationPortabilityReadiness','researchStudyCertificationHandoffReadiness','researchStudyCertificationContentAddressedRecords','researchStudyCertificationCorePlanning'):
        assert caps['coreIntegration'][k] is True


def test_missing_root_study_is_404(monkeypatch,tmp_path):
    p,st,pr,ca=seed_foundation(monkeypatch,tmp_path)
    req=body(p,st,pr,ca); req['studyHash']='0'*64
    assert c.post('/research-study-certification/evaluate',json=req).status_code==404
