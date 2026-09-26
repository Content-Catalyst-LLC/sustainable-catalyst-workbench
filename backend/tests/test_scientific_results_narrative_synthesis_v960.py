import json
from fastapi.testclient import TestClient
from app.main import app
from app.v510 import content_hash
from app.v810 import _atomic_json_write
from app.v930 import _analysis_path
from app.v940 import _study_path
from app.v950 import _calibration_path
c=TestClient(app)


def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='p960'; env_key='env-'+p
    e=c.post('/research-environment/build',json={'environment':{'environmentKey':env_key,'title':'Synthesis environment','projectEntityId':p,'components':[]}}); assert e.status_code==200,e.text
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':e.json(),'expectedCurrentRevision':0,'reason':'v960-test'}); assert s.status_code==200,s.text
    b=c.post('/research-projects/build',json={'project':{'projectKey':p,'title':'Synthesis Study','researchQuestion':'What do the results support?','objectives':['synthesize results'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert b.status_code==200,b.text
    sp=c.post('/research-projects/save',json={'workspace':b.json(),'expectedProjectRevision':0,'reason':'v960-test'}); assert sp.status_code==200,sp.text
    return p


def seed_sources(project):
    ah='a'*64
    analysis={'ok':True,'schema':'sc-workbench-statistical-analysis/1.0','version':'9.6.0','projectKey':project,'analysisHash':ah,'analysisRef':f'sc://workbench/statistical-analyses/{project}/{ah}','analysisKey':'a1','title':'Analysis','campaignHash':'c'*64,'resultMetricPath':'metrics.y','methods':['descriptive'],'observationCount':10,'createdBy':'test','createdAt':'2026-09-26T00:00:00Z'}
    analysis['recordHash']=content_hash({k:v for k,v in analysis.items() if k not in {'createdAt','recordHash','idempotent'}}); _analysis_path(project,ah).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_analysis_path(project,ah),analysis)
    uh='u'*64
    study={'ok':True,'schema':'sc-workbench-uncertainty-sensitivity-study/1.0','version':'9.6.0','projectKey':project,'studyHash':uh,'studyRef':f'sc://workbench/uncertainty-sensitivity/{project}/{uh}','studyKey':'u1','title':'Uncertainty','campaignHash':'c'*64,'samplingMethod':'monte-carlo','sampleCount':100,'createdBy':'test','createdAt':'2026-09-26T00:00:00Z'}
    study['recordHash']=content_hash({k:v for k,v in study.items() if k not in {'createdAt','recordHash','idempotent'}}); _study_path(project,uh).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_study_path(project,uh),study)
    kh='k'*64
    cal={'ok':True,'schema':'sc-workbench-model-calibration/1.0','version':'9.6.0','projectKey':project,'calibrationHash':kh,'calibrationRef':f'sc://workbench/model-calibration/{project}/{kh}','calibrationKey':'k1','title':'Calibration','campaignHash':'c'*64,'problemHash':'p'*64,'createdBy':'test','createdAt':'2026-09-26T00:00:00Z'}
    cal['recordHash']=content_hash({k:v for k,v in cal.items() if k not in {'createdAt','recordHash','idempotent'}}); _calibration_path(project,kh).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_calibration_path(project,kh),cal)
    return ah,uh,kh


def payload(project,ah,uh,kh):
    return {'projectKey':project,'synthesisKey':'syn-1','title':'Scientific synthesis','statisticalAnalysisHashes':[ah],'uncertaintyStudyHashes':[uh],'calibrationHashes':[kh],'statements':[{'statementKey':'r1','kind':'result','statement':'The measured response increased in the analyzed runs.','sourceRefs':[f'analysis:{ah}'],'evidenceRefs':['evidence:result-table']},{'statementKey':'i1','kind':'interpretation','statement':'The pattern may be practically important.','sourceRefs':[f'calibration:{kh}'],'qualification':'Researcher interpretation.'}], 'abstract':'Researcher-written abstract.','methodsNarrative':'Researcher-written methods.','resultsNarrative':'Researcher-written results narrative.','interpretation':'Researcher interpretation.','limitations':['Limited campaign scope.'],'conclusion':'Researcher-written conclusion.'}


def test_manifest_and_status():
    m=c.get('/results-synthesis/manifest').json(); assert m['ok'] and m['version']=='9.6.0'
    assert m['capabilities']['statementSourceTraceability'] and m['boundaries']['automaticNarrativeGeneration'] is False
    s=c.get('/v960/status').json(); assert s['scientificResultsNarrativeSynthesis'] and s['automaticScientificValidityInference'] is False


def test_compose_binds_sources_and_traceability(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); d=c.post('/results-synthesis/compose',json=payload(p,ah,uh,kh)).json()
    assert d['ok'] and len(d['sources'])==3 and d['readiness']['traceabilityCoverage']==1.0
    assert d['researcherAuthored'] is True and d['boundaries']['automaticFindingGeneration'] is False


def test_unresolved_source_refs_are_surfaced_not_silently_fixed(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); x=payload(p,ah,uh,kh); x['statements'][0]['sourceRefs']=['analysis:'+'f'*64]
    d=c.post('/results-synthesis/compose',json=x).json(); assert d['readiness']['unresolvedSourceReferenceCount']==1 and d['readiness']['unsupportedStatementCount']==1


def test_content_address_is_deterministic(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); x=payload(p,ah,uh,kh)
    a=c.post('/results-synthesis/compose',json=x).json(); b=c.post('/results-synthesis/compose',json=x).json(); assert a['synthesisHash']==b['synthesisHash'] and len(a['synthesisHash'])==64


def test_save_is_idempotent(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); x={**payload(p,ah,uh,kh),'createdBy':'tester'}
    a=c.post('/results-synthesis/syntheses',json=x).json(); b=c.post('/results-synthesis/syntheses',json=x).json(); assert a['idempotent'] is False and b['idempotent'] is True


def test_list_and_load(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); a=c.post('/results-synthesis/syntheses',json={**payload(p,ah,uh,kh),'createdBy':'tester'}).json()
    ls=c.get(f'/results-synthesis/syntheses/{p}').json(); assert ls['synthesisCount']==1
    got=c.get(f"/results-synthesis/syntheses/{p}/{a['synthesisHash']}").json(); assert got['recordHash']==a['recordHash']


def test_source_catalog_lists_inputs(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); d=c.get(f'/results-synthesis/source-catalog/{p}').json(); assert d['statisticalAnalysisCount']==1 and d['uncertaintyStudyCount']==1 and d['calibrationCount']==1
    assert d['boundaries']['catalogGeneratesNarrative'] is False


def test_publication_plan_is_plan_only(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); a=c.post('/results-synthesis/syntheses',json={**payload(p,ah,uh,kh),'createdBy':'tester'}).json()
    d=c.post('/results-synthesis/publication-plan',json={'projectKey':p,'synthesisHash':a['synthesisHash'],'createdBy':'tester'}).json(); assert len(d['plannedHandoffs'])==2 and d['boundaries']['automaticPublication'] is False


def test_core_plan_preserves_governance(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); a=c.post('/results-synthesis/syntheses',json={**payload(p,ah,uh,kh),'createdBy':'tester'}).json()
    d=c.post('/integration/core/results-synthesis/plan',json={'projectKey':p,'synthesisHash':a['synthesisHash'],'createdBy':'tester'}).json(); assert d['bindingPlan']['objectType']=='workbench.scientific-results-synthesis' and d['boundaries']['automaticCoreDispatchAuthorized'] is False


def test_duplicate_statement_keys_rejected(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ah,uh,kh=seed_sources(p); x=payload(p,ah,uh,kh); x['statements'].append(dict(x['statements'][0])); assert c.post('/results-synthesis/compose',json=x).status_code==422


def test_missing_bound_source_returns_404(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x={'projectKey':p,'synthesisKey':'x','title':'x','statisticalAnalysisHashes':['f'*64],'resultsNarrative':'x'}; assert c.post('/results-synthesis/compose',json=x).status_code==404


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.6.0'
    for k in ('scientificResultsNarrativeSynthesis','scientificResultsResearcherAuthoredNarrative','scientificResultsSourceBinding','scientificResultsStatementTraceability','scientificResultsContentAddressedRecords','scientificResultsPublicationPlanning','scientificResultsCorePlanning'): assert caps['coreIntegration'][k] is True
