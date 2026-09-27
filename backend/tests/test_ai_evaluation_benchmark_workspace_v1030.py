from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)

def model_req(project,key='model-a',artifact='a'):
    return {'projectKey':project,'modelKey':key,'versionLabel':'1.0','title':key,'provider':'local','modelId':f'sc/{key}','task':'classification','artifactHash':artifact*64,'license':'Apache-2.0','compatibility':{'runtimeKinds':['ai-engineering']},'createdBy':'tester'}

def dataset_req(project,key='eval-data',h='b'):
    return {'projectKey':project,'datasetKey':key,'versionLabel':'1.0','title':key,'datasetHash':h*64,'datasetRef':f'sc://dataset/{key}','format':'parquet','license':'CC-BY-4.0','compatibility':{'runtimeKinds':['ai-engineering'],'dataFormats':['parquet']},'createdBy':'tester'}

def setup_sources(monkeypatch,tmp_path,p='eval-project'):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    m1=c.post('/ai-registry/models',json=model_req(p,'model-a','a')); assert m1.status_code==200,m1.text
    m2=c.post('/ai-registry/models',json=model_req(p,'model-b','c')); assert m2.status_code==200,m2.text
    d=c.post('/ai-registry/datasets',json=dataset_req(p)); assert d.status_code==200,d.text
    return m1.json(),m2.json(),d.json()

def bench_req(p,d,baseline=''):
    return {'projectKey':p,'benchmarkKey':'bench-1','title':'Classification benchmark','task':'classification','datasetRecordHashes':[d['recordHash']],
            'metrics':[{'metricKey':'accuracy','title':'Accuracy','kind':'accuracy','direction':'higher-is-better','regressionTolerance':0.01},{'metricKey':'latency','title':'Latency','kind':'latency-ms','direction':'lower-is-better','unit':'ms','regressionTolerance':5.0},{'metricKey':'notescore','title':'Reported score','kind':'custom','direction':'report-only'}],
            'slices':[{'sliceKey':'region-west','title':'West region','field':'region','operator':'eq','value':'west'}],
            'baselineModelRecordHash':baseline,'reproducibility':{'seed':42,'repeats':3,'dependencyLockHash':'d'*64,'deterministicRequested':True},'createdBy':'tester'}

def test_manifest_status_and_boundaries():
    m=c.get('/ai-evaluation/manifest').json(); assert m['ok'] and m['version']=='10.3.0'
    for k in ('aiEvaluationBenchmarkWorkspace','registryBackedBenchmarkSuites','researcherDefinedMetrics','evaluationDatasetBinding','diagnosticSlices','deterministicEvaluationManifests','immutableEvaluationResults','baselineRelativeRegressionDiagnostics','datasetAndSliceDiagnostics','multiModelComparison','platformCoreEvaluationPlanning'): assert m['capabilities'][k] is True
    for k in ('automaticInferenceExecution','automaticModelDownload','automaticDatasetDownload','automaticExternalProviderCall','automaticCompositeRanking','automaticWinnerSelection','automaticPreferredModelPromotion','automaticProductionApproval','scientificValidityInferred','automaticCoreDispatch'): assert m['boundaries'][k] is False
    s=c.get('/v1030/status').json(); assert s['aiEvaluationBenchmarkWorkspace'] and s['automaticWinnerSelection'] is False

def test_benchmark_is_registry_backed_content_addressed_and_idempotent(monkeypatch,tmp_path):
    p='bench-project'; m1,m2,d=setup_sources(monkeypatch,tmp_path,p); req=bench_req(p,d,m1['recordHash'])
    comp=c.post('/ai-evaluation/benchmarks/compose',json=req); assert comp.status_code==200,comp.text; x=comp.json(); assert x['benchmarkReady'] and x['issues']==[] and len(x['benchmarkHash'])==64
    a=c.post('/ai-evaluation/benchmarks',json=req); assert a.status_code==200,a.text
    b=c.post('/ai-evaluation/benchmarks',json=req); assert b.status_code==200,b.text
    assert a.json()['idempotent'] is False and b.json()['idempotent'] is True and a.json()['benchmarkHash']==b.json()['benchmarkHash']
    listing=c.get(f'/ai-evaluation/benchmarks/{p}').json(); assert listing['benchmarkCount']==1

def test_unresolved_dataset_is_reported_not_repaired(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store')); p='missing'; req={'projectKey':p,'benchmarkKey':'b','title':'B','task':'classification','datasetRecordHashes':['a'*64],'metrics':[{'metricKey':'accuracy','title':'Accuracy','kind':'accuracy','direction':'higher-is-better'}]}
    comp=c.post('/ai-evaluation/benchmarks/compose',json=req); assert comp.status_code==200; assert comp.json()['benchmarkReady'] is False
    saved=c.post('/ai-evaluation/benchmarks',json=req); assert saved.status_code==409

def test_execution_plan_is_explicit_and_not_authorized(monkeypatch,tmp_path):
    p='plan-project'; m1,m2,d=setup_sources(monkeypatch,tmp_path,p); b=c.post('/ai-evaluation/benchmarks',json=bench_req(p,d,m1['recordHash'])).json()
    r=c.post('/ai-evaluation/execution-plan',json={'projectKey':p,'benchmarkHash':b['benchmarkHash'],'modelRecordHashes':[m1['recordHash'],m2['recordHash']],'requestedBy':'tester'}); assert r.status_code==200,r.text
    x=r.json(); assert x['ready'] and x['authorized'] is False and len(x['models'])==2 and x['boundaries']['executionRequiresExplicitAuthorization'] is True

def test_evaluation_results_are_immutable_and_validate_metric_slice_dataset_contract(monkeypatch,tmp_path):
    p='result-project'; m1,m2,d=setup_sources(monkeypatch,tmp_path,p); b=c.post('/ai-evaluation/benchmarks',json=bench_req(p,d,m1['recordHash'])).json(); h=b['benchmarkHash']
    req={'projectKey':p,'benchmarkHash':h,'evaluationKey':'eval-a','modelRecordHash':m1['recordHash'],'metrics':{'accuracy':0.91,'latency':50.0,'notescore':1.0},'datasetMetrics':{d['recordHash']:{'accuracy':0.91}},'sliceMetrics':{'region-west':{'accuracy':0.88}},'sampleCount':100,'recordedBy':'tester'}
    a=c.post('/ai-evaluation/results',json=req); assert a.status_code==200,a.text
    same=c.post('/ai-evaluation/results',json=req); assert same.status_code==200 and same.json()['idempotent'] is True
    bad=c.post('/ai-evaluation/results',json={**req,'evaluationKey':'bad','metrics':{'unknown':1.0}}); assert bad.status_code==409
    rows=c.get(f'/ai-evaluation/results/{p}/{h}').json(); assert rows['evaluationCount']==1

def test_comparison_reports_metric_regression_without_winner(monkeypatch,tmp_path):
    p='compare-project'; m1,m2,d=setup_sources(monkeypatch,tmp_path,p); b=c.post('/ai-evaluation/benchmarks',json=bench_req(p,d,m1['recordHash'])).json(); h=b['benchmarkHash']
    r1=c.post('/ai-evaluation/results',json={'projectKey':p,'benchmarkHash':h,'evaluationKey':'base','modelRecordHash':m1['recordHash'],'metrics':{'accuracy':0.90,'latency':50.0,'notescore':1.0}}).json()
    r2=c.post('/ai-evaluation/results',json={'projectKey':p,'benchmarkHash':h,'evaluationKey':'candidate','modelRecordHash':m2['recordHash'],'metrics':{'accuracy':0.87,'latency':60.0,'notescore':9.0}}).json()
    out=c.post('/ai-evaluation/compare',json={'projectKey':p,'benchmarkHash':h,'evaluationHashes':[r1['evaluationHash'],r2['evaluationHash']],'baselineEvaluationHash':r1['evaluationHash']}); assert out.status_code==200,out.text
    x=out.json(); assert x['regressionCount']==2 and x['boundaries']['automaticWinnerSelection'] is False and x['boundaries']['automaticCompositeRanking'] is False
    assert {r['metricKey'] for r in x['regressions']}=={'accuracy','latency'}

def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    p='core-eval'; m1,m2,d=setup_sources(monkeypatch,tmp_path,p); b=c.post('/ai-evaluation/benchmarks',json=bench_req(p,d)).json()
    r=c.post('/integration/core/ai-evaluation/plan',json={'projectKey':p,'kind':'benchmark-suite','sourceHash':b['benchmarkHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    x=r.json(); assert x['bindingPlan']['objectType']=='workbench.ai-benchmark-suite' and x['boundaries']['automaticCoreDispatch'] is False and x['boundaries']['scientificValidityInferred'] is False

def test_capability_registry_and_retained_v10_surfaces():
    caps=c.get('/capabilities').json(); assert caps['version']=='10.3.0'
    for k in ('aiEvaluationBenchmarkWorkspace','aiEvaluationRegistryBackedBenchmarks','aiEvaluationResearcherDefinedMetrics','aiEvaluationDatasetBindings','aiEvaluationDiagnosticSlices','aiEvaluationDeterministicManifests','aiEvaluationImmutableResults','aiEvaluationRegressionDiagnostics','aiEvaluationMultiModelComparison','aiEvaluationCorePlanning'): assert caps['coreIntegration'][k] is True
    assert c.get('/ai-training/manifest').json()['version']=='10.3.0'
    assert c.get('/ai-registry/manifest').json()['version']=='10.3.0'
    assert c.get('/ai-engineering/manifest').json()['version']=='10.3.0'
