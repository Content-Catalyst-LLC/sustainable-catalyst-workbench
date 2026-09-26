from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)


def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='p980'; env='env-'+p
    e=c.post('/research-environment/build',json={'environment':{'environmentKey':env,'title':'Meta-analysis environment','projectEntityId':p,'components':[]}}); assert e.status_code==200,e.text
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':e.json(),'expectedCurrentRevision':0,'reason':'v980-test'}); assert s.status_code==200,s.text
    b=c.post('/research-projects/build',json={'project':{'projectKey':p,'title':'Cross-study synthesis','researchQuestion':'What is the pooled effect?','objectives':['compare studies'],'activeEnvironmentKey':env,'activeEnvironmentRevision':1}}); assert b.status_code==200,b.text
    sp=c.post('/research-projects/save',json={'workspace':b.json(),'expectedProjectRevision':0,'reason':'v980-test'}); assert sp.status_code==200,sp.text
    return p


def payload(p):
    return {'projectKey':p,'analysisKey':'meta-1','title':'Cross-study treatment effect','researchQuestion':'What is the pooled treatment effect?','effectMeasure':'generic','confidenceLevel':0.95,'studies':[
        {'studyKey':'s1','label':'Study 1','subgroup':'A','effectValue':0.20,'standardError':0.10,'inputScale':'effect'},
        {'studyKey':'s2','label':'Study 2','subgroup':'A','effectValue':0.40,'standardError':0.12,'inputScale':'effect'},
        {'studyKey':'s3','label':'Study 3','subgroup':'B','effectValue':0.10,'standardError':0.11,'inputScale':'effect'},
    ],'models':['fixed-effect','random-effects'],'subgroupAnalysis':True,'leaveOneOut':True}


def test_manifest_and_status():
    m=c.get('/cross-study-meta/manifest').json(); assert m['ok'] and m['version']=='9.11.0'
    assert m['capabilities']['dersimonianLairdRandomEffects'] and m['boundaries']['automaticPreferredModelSelection'] is False
    s=c.get('/v980/status').json(); assert s['crossStudyMetaAnalysisWorkspace'] and s['automaticScientificValidityInference'] is False


def test_fixed_and_random_meta_analysis(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); d=c.post('/cross-study-meta/analyze',json=payload(p)).json()
    assert d['ok'] and d['studyCount']==3 and set(d['pooledModels'])=={'fixed-effect','random-effects'}
    assert d['pooledModels']['fixed-effect']['studyCount']==3
    assert d['pooledModels']['random-effects']['tauSquared']>=0
    assert d['pooledModels']['fixed-effect']['heterogeneity']['df']==2
    assert d['boundaries']['automaticSignificanceConclusion'] is False


def test_effect_normalization_ratio(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x=payload(p); x['effectMeasure']='log-odds-ratio'; x['models']=['fixed-effect']; x['studies']=[
        {'studyKey':'a','effectValue':2.0,'standardError':0.2,'inputScale':'ratio'},
        {'studyKey':'b','effectValue':1.5,'standardError':0.25,'inputScale':'ratio'}]
    d=c.post('/cross-study-meta/analyze',json=x).json(); assert abs(d['studies'][0]['normalizedEffect']-0.69314718056)<1e-8
    assert d['pooledModels']['fixed-effect']['naturalScaleEstimate']>1


def test_correlation_normalization_derives_se(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x=payload(p); x['effectMeasure']='fisher-z-correlation'; x['models']=['fixed-effect']; x['studies']=[
        {'studyKey':'a','effectValue':0.30,'inputScale':'correlation','sampleSize':40},
        {'studyKey':'b','effectValue':0.20,'inputScale':'correlation','sampleSize':50}]
    d=c.post('/cross-study-meta/analyze',json=x).json(); assert d['studies'][0]['normalizationTransform']=='fisher-z'
    assert 0<d['pooledModels']['fixed-effect']['naturalScaleEstimate']<1


def test_subgroups_and_leave_one_out(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); d=c.post('/cross-study-meta/analyze',json=payload(p)).json()
    assert d['subgroups']['A']['studyCount']==2 and d['subgroups']['B']['studyCount']==1
    assert len(d['leaveOneOut'])==3 and all(x['influenceConclusionInferred'] is False for x in d['leaveOneOut'])


def test_pairwise_comparisons_are_neutral(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); d=c.post('/cross-study-meta/analyze',json=payload(p)).json()
    assert len(d['pairwiseComparisons'])==3 and all(x['scientificDifferenceInferred'] is False for x in d['pairwiseComparisons'])


def test_deterministic_content_hash(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x=payload(p); a=c.post('/cross-study-meta/analyze',json=x).json(); b=c.post('/cross-study-meta/analyze',json=x).json(); assert a['analysisHash']==b['analysisHash'] and len(a['sourceManifestHash'])==64


def test_save_list_load_idempotent(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x={**payload(p),'createdBy':'tester'}; a=c.post('/cross-study-meta/meta-analyses',json=x).json(); b=c.post('/cross-study-meta/meta-analyses',json=x).json(); assert not a['idempotent'] and b['idempotent']
    ls=c.get(f'/cross-study-meta/meta-analyses/{p}').json(); assert ls['analysisCount']==1
    got=c.get(f"/cross-study-meta/meta-analyses/{p}/{a['analysisHash']}").json(); assert got['recordHash']==a['recordHash']


def test_visualization_plan_is_renderer_neutral(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); a=c.post('/cross-study-meta/meta-analyses',json={**payload(p),'createdBy':'tester'}).json(); d=c.post('/cross-study-meta/visualization-plan',json={'projectKey':p,'analysisHash':a['analysisHash']}).json(); assert len(d['views'])>=3 and d['boundaries']['rendererInvoked'] is False


def test_core_plan_preserves_governance(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); a=c.post('/cross-study-meta/meta-analyses',json={**payload(p),'createdBy':'tester'}).json(); d=c.post('/integration/core/cross-study-meta/plan',json={'projectKey':p,'analysisHash':a['analysisHash'],'createdBy':'tester'}).json(); assert d['bindingPlan']['objectType']=='workbench.cross-study-meta-analysis' and d['boundaries']['governedCrossStudyClaimCreated'] is False


def test_source_catalog(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); d=c.get(f'/cross-study-meta/source-catalog/{p}').json(); assert d['explicitExternalStudyRecordsSupported'] and d['boundaries']['catalogInfersStudyComparability'] is False


def test_ratio_measure_mismatch_rejected(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x=payload(p); x['studies'][0]['inputScale']='ratio'; x['studies'][0]['effectValue']=2.0; r=c.post('/cross-study-meta/analyze',json=x); assert r.status_code==422


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0'
    for k in ('crossStudyMetaAnalysisWorkspace','crossStudyEffectNormalization','crossStudyFixedEffectMetaAnalysis','crossStudyRandomEffectsMetaAnalysis','crossStudyHeterogeneityDiagnostics','crossStudySubgroupAnalysis','crossStudyLeaveOneOutSensitivity','crossStudyCorePlanning'): assert caps['coreIntegration'][k] is True
