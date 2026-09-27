from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)


def model_req(project,key='m'):
    return {'projectKey':project,'modelKey':key,'versionLabel':'1.0','title':key,'provider':'local','modelId':f'sc/{key}','task':'classification','artifactHash':'a'*64,'license':'Apache-2.0','compatibility':{'runtimeKinds':['ai-engineering']},'createdBy':'tester'}


def dataset_req(project,key,rolehash):
    return {'projectKey':project,'datasetKey':key,'versionLabel':'1.0','title':key,'datasetHash':rolehash*64,'datasetRef':f'sc://dataset/{key}','format':'parquet','license':'CC-BY-4.0','compatibility':{'runtimeKinds':['ai-engineering'],'dataFormats':['parquet']},'createdBy':'tester'}


def setup(monkeypatch,tmp_path,p='opt-project'):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    model=c.post('/ai-registry/models',json=model_req(p)).json()
    train=c.post('/ai-registry/datasets',json=dataset_req(p,'train','b')).json()
    val=c.post('/ai-registry/datasets',json=dataset_req(p,'val','c')).json()
    exp_req={'projectKey':p,'experimentKey':'exp','title':'Experiment','mode':'training','model':{'modelKey':'m','provider':'local','modelId':'sc/m','modelVersion':'1.0','task':'classification','artifactHash':'a'*64},'datasets':[{'role':'train','datasetRef':'sc://dataset/train','datasetHash':'b'*64},{'role':'validation','datasetRef':'sc://dataset/val','datasetHash':'c'*64}],'training':{'enabled':True,'seed':7,'epochs':2,'batchSize':8,'learningRate':0.001},'inference':{'enabled':False},'createdBy':'tester'}
    er=c.post('/ai-engineering/experiments',json=exp_req); assert er.status_code==200,er.text; exp=er.json()
    bind_req={'projectKey':p,'experimentHash':exp['experimentHash'],'modelRecordHash':model['recordHash'],'datasets':[{'role':'train','datasetRecordHash':train['recordHash']},{'role':'validation','datasetRecordHash':val['recordHash']}],'createdBy':'tester'}
    br=c.post('/ai-registry/experiment-bindings',json=bind_req); assert br.status_code==200,br.text; bind=br.json()
    run_req={'projectKey':p,'trainingKey':'base-train','title':'Base training','experimentHash':exp['experimentHash'],'registryBindingHash':bind['recordHash'],'baseModelRecordHash':model['recordHash'],'fineTuning':{'method':'supervised-finetuning'},'hyperparameters':{'seed':7,'epochs':2,'batchSize':8,'learningRate':0.001},'outputModelKey':'derived','outputVersionLabel':'1.0','createdBy':'tester'}
    run=c.post('/ai-training/runs',json=run_req); assert run.status_code==200,run.text; run=run.json()
    bench_req={'projectKey':p,'benchmarkKey':'bench','title':'Benchmark','task':'classification','datasetRecordHashes':[val['recordHash']],'metrics':[{'metricKey':'accuracy','title':'Accuracy','kind':'accuracy','direction':'higher-is-better'}],'createdBy':'tester'}
    bench=c.post('/ai-evaluation/benchmarks',json=bench_req); assert bench.status_code==200,bench.text; bench=bench.json()
    return model,train,val,exp,bind,run,bench


def search_req(p,run,bench,strategy='grid'):
    return {'projectKey':p,'searchKey':'search-1','title':'HP search','baseTrainingRunHash':run['runHash'],'benchmarkHash':bench['benchmarkHash'],'objective':{'metricKey':'accuracy','direction':'maximize'},'parameters':[{'parameterKey':'lr','path':'hyperparameters.learningRate','kind':'float','minimum':0.0001,'maximum':0.001,'gridValues':[0.0001,0.001]},{'parameterKey':'batch','path':'hyperparameters.batchSize','kind':'int','minimum':8,'maximum':16,'gridValues':[8,16]}],'strategy':strategy,'seed':42,'budget':{'maxTrials':4,'maxConcurrentTrials':2},'createdBy':'tester'}


def test_manifest_status_boundaries():
    m=c.get('/ai-optimization/manifest').json(); assert m['ok'] and m['version']=='10.4.0'
    for k in ('hyperparameterOptimizationSearchEngine','trainingRunTemplateBinding','benchmarkObjectiveBinding','typedSearchSpaces','gridSearch','seededRandomSearch','latinHypercubeSearch','externalBayesianOptimizerContract','deterministicTrialManifests','searchBudgets','resumableTrialState','immutableTrialResults','objectiveDiagnostics','platformCoreSearchPlanning'): assert m['capabilities'][k] is True
    for k in ('automaticTrainingExecution','automaticExternalOptimizerCall','automaticPreferredModelPromotion','automaticProductionApproval','scientificValidityInferred','automaticCoreDispatch'): assert m['boundaries'][k] is False
    s=c.get('/v1040/status').json(); assert s['hyperparameterOptimizationSearchEngine'] and s['automaticWinnerSelection'] is False


def test_search_is_training_and_benchmark_backed(monkeypatch,tmp_path):
    p='compose'; *_,run,bench=setup(monkeypatch,tmp_path,p); req=search_req(p,run,bench)
    comp=c.post('/ai-optimization/searches/compose',json=req); assert comp.status_code==200,comp.text; assert comp.json()['searchReady']
    a=c.post('/ai-optimization/searches',json=req); assert a.status_code==200,a.text
    b=c.post('/ai-optimization/searches',json=req); assert b.status_code==200 and b.json()['idempotent'] is True
    assert c.get(f'/ai-optimization/searches/{p}').json()['searchCount']==1


def test_objective_must_exist_in_benchmark(monkeypatch,tmp_path):
    p='bad-objective'; *_,run,bench=setup(monkeypatch,tmp_path,p); req=search_req(p,run,bench); req['objective']['metricKey']='not-declared'
    comp=c.post('/ai-optimization/searches/compose',json=req); assert comp.status_code==200 and comp.json()['searchReady'] is False
    assert c.post('/ai-optimization/searches',json=req).status_code==409


def test_grid_trials_are_deterministic(monkeypatch,tmp_path):
    p='grid'; *_,run,bench=setup(monkeypatch,tmp_path,p); s=c.post('/ai-optimization/searches',json=search_req(p,run,bench)).json()
    a=c.post('/ai-optimization/trials/generate',json={'projectKey':p,'searchHash':s['searchHash']}); b=c.post('/ai-optimization/trials/generate',json={'projectKey':p,'searchHash':s['searchHash']})
    assert a.status_code==200,a.text; assert a.json()['generatedTrialCount']==4 and a.json()['trials']==b.json()['trials']
    vals={tuple(sorted(x['parameters'].items())) for x in a.json()['trials']}; assert len(vals)==4


def test_seeded_random_and_latin_hypercube_are_reproducible(monkeypatch,tmp_path):
    for strategy in ('random','latin-hypercube'):
        p='strat-'+strategy; *_,run,bench=setup(monkeypatch,tmp_path,p); req=search_req(p,run,bench,strategy); req['budget']['maxTrials']=3
        s=c.post('/ai-optimization/searches',json=req).json()
        a=c.post('/ai-optimization/trials/generate',json={'projectKey':p,'searchHash':s['searchHash']}).json(); b=c.post('/ai-optimization/trials/generate',json={'projectKey':p,'searchHash':s['searchHash']}).json()
        assert a['generatedTrialCount']==3 and a['trials']==b['trials']


def test_external_optimizer_contract_does_not_call_optimizer(monkeypatch,tmp_path):
    p='bayes'; *_,run,bench=setup(monkeypatch,tmp_path,p); req=search_req(p,run,bench,'bayesian-contract'); req['externalOptimizerRef']='optimizer://bayes/1'
    s=c.post('/ai-optimization/searches',json=req).json(); m=c.post('/ai-optimization/trials/generate',json={'projectKey':p,'searchHash':s['searchHash']}).json()
    assert m['externalOptimizerRequired'] is True and m['generatedTrialCount']==0 and m['boundaries']['automaticExternalOptimizerCall'] is False


def test_execution_plan_not_authorized(monkeypatch,tmp_path):
    p='plan'; *_,run,bench=setup(monkeypatch,tmp_path,p); s=c.post('/ai-optimization/searches',json=search_req(p,run,bench)).json()
    x=c.post('/ai-optimization/execution-plan',json={'projectKey':p,'searchHash':s['searchHash'],'trialCount':2,'requestedBy':'tester'}).json()
    assert x['authorized'] is False and len(x['trials'])==2 and x['boundaries']['executionRequiresExplicitAuthorization'] is True


def test_trial_results_are_immutable_and_analysis_is_not_preference(monkeypatch,tmp_path):
    p='results'; *_,run,bench=setup(monkeypatch,tmp_path,p); s=c.post('/ai-optimization/searches',json=search_req(p,run,bench)).json(); trials=c.post('/ai-optimization/trials/generate',json={'projectKey':p,'searchHash':s['searchHash']}).json()['trials']
    vals=[0.80,0.91]
    for t,v in zip(trials[:2],vals):
        req={'projectKey':p,'searchHash':s['searchHash'],'trialHash':t['trialHash'],'status':'completed','objectiveValue':v,'metrics':{'accuracy':v},'recordedBy':'tester'}
        r=c.post('/ai-optimization/trial-results',json=req); assert r.status_code==200,r.text
        assert c.post('/ai-optimization/trial-results',json=req).json()['idempotent'] is True
    conflict={'projectKey':p,'searchHash':s['searchHash'],'trialHash':trials[0]['trialHash'],'status':'completed','objectiveValue':0.7}
    assert c.post('/ai-optimization/trial-results',json=conflict).status_code==409
    a=c.post('/ai-optimization/analyze',json={'projectKey':p,'searchHash':s['searchHash']}).json()
    assert a['objectiveOrdering'][0]['objectiveValue']==0.91 and a['observedMaximum']==0.91
    assert a['boundaries']['automaticWinnerSelection'] is False and a['boundaries']['automaticPreferredModelPromotion'] is False


def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    p='core'; *_,run,bench=setup(monkeypatch,tmp_path,p); s=c.post('/ai-optimization/searches',json=search_req(p,run,bench)).json()
    x=c.post('/integration/core/ai-optimization/plan',json={'projectKey':p,'kind':'search-study','sourceHash':s['searchHash'],'createdBy':'tester'}); assert x.status_code==200,x.text
    j=x.json(); assert j['bindingPlan']['objectType']=='workbench.ai-hyperparameter-search' and j['boundaries']['automaticCoreDispatch'] is False


def test_capability_registry_and_retained_v10_surfaces():
    caps=c.get('/capabilities').json(); assert caps['version']=='10.4.0'
    for k in ('aiOptimizationSearchEngine','aiOptimizationTrainingRunBinding','aiOptimizationBenchmarkObjectiveBinding','aiOptimizationTypedSearchSpaces','aiOptimizationDeterministicTrials','aiOptimizationSearchBudgets','aiOptimizationImmutableTrialResults','aiOptimizationObjectiveDiagnostics','aiOptimizationCorePlanning'): assert caps['coreIntegration'][k] is True
    assert c.get('/ai-evaluation/manifest').json()['version']=='10.4.0'
    assert c.get('/ai-training/manifest').json()['version']=='10.4.0'
    assert c.get('/ai-registry/manifest').json()['version']=='10.4.0'
    assert c.get('/ai-engineering/manifest').json()['version']=='10.4.0'
