from fastapi.testclient import TestClient
from app.main import app
from app.v680 import (
    CORE_SCENARIO_MANIFEST_SCHEMA,
    SamplingDesignRequest, FactorSpec, SobolAnalysisRequest, MorrisAnalysisRequest,
    EnsembleStatisticsRequest, ExceedanceRequest, ScenarioRequestConsumeRequest,
    ScenarioAffineExecuteRequest, AffineOutputSpec, ScenarioCallbackBuildRequest,
    scenario_uncertainty_manifest, run_sampling_design, run_sobol_analysis,
    run_morris_analysis, run_ensemble_statistics, run_exceedance,
    consume_scenario_request, execute_affine_scenario, build_scenario_callbacks,
)

def client(): return TestClient(app)

def factors():
    return [
        FactorSpec(key='x', distribution='uniform', lowerBound=0, upperBound=10),
        FactorSpec(key='y', distribution='triangular', lowerBound=0, upperBound=4, parameters={'mode':2}),
    ]

def core_manifest(**overrides):
    d={
        'schema':CORE_SCENARIO_MANIFEST_SCHEMA,
        'plan_id':'plan-1','case_id':'case-1','project_entity_id':'project-1',
        'model_entity_id':'model-1','model_version_entity_id':'model-v1','scenario_entity_id':'scenario-1',
        'execution_product':'workbench','parameter_values':{'x':2.0,'y':3.0},
        'scenario_parameter_values':{'x':2.0},'parameter_overrides':{'y':3.0},
        'expected_outputs':['z'],'execution_contract':{},'output_contract':{},'case_hash':'casehash','core_execution':False,
    }
    d.update(overrides); return d

def test_manifest_declares_exact_core_surfaces_and_boundaries():
    m=scenario_uncertainty_manifest()
    assert m['version']=='9.5.0'
    assert m['coreScenarioInputManifestSchema']=='scenario-compute-input-manifest-v1'
    assert m['corePaths']['scenarioAttempts']=='/v1/scenario-compute/requests/{request_id}/attempts'
    assert m['corePaths']['uncertaintySampling']=='/v1/uncertainty-compute/sampling/design'
    assert m['boundaries']['workbenchExecutesUncertaintyNumerics'] is True
    assert m['boundaries']['arbitraryCodeFromCoreAuthorized'] is False

def test_monte_carlo_is_deterministic_and_workbench_owned():
    req=SamplingDesignRequest(method='monte-carlo',sampleCount=8,seed=7,factors=factors())
    a=run_sampling_design(req); b=run_sampling_design(req)
    assert a['samples']==b['samples']
    assert a['manifest_sha256']==b['manifest_sha256']
    assert a['total_evaluations']==8
    assert a['calculated_by_workbench'] is True and a['calculated_by_core'] is False

def test_latin_hypercube_produces_requested_samples():
    x=run_sampling_design(SamplingDesignRequest(method='latin-hypercube',sampleCount=12,seed=12,factors=factors()))
    assert len(x['samples'])==12 and x['total_evaluations']==12
    assert all(0 <= row['x'] <= 10 for row in x['samples'])

def test_sobol_design_has_core_compatible_a_b_ab_shape():
    x=run_sampling_design(SamplingDesignRequest(method='sobol-design',sampleCount=5,seed=2,factors=factors()))
    assert len(x['A'])==5 and len(x['B'])==5
    assert set(x['AB'])=={'x','y'}
    assert x['total_evaluations']==20

def test_morris_design_tracks_trajectories():
    x=run_sampling_design(SamplingDesignRequest(method='morris-design',sampleCount=3,seed=3,levels=6,factors=factors()))
    assert len(x['trajectories'])==3
    assert len(x['samples'])==9
    assert x['total_evaluations']==9

def test_factor_validation_rejects_missing_bounds():
    r=client().post('/integration/core/scenario-uncertainty/sampling/design/run',json={'method':'monte-carlo','sampleCount':2,'factors':[{'key':'x','distribution':'uniform'}]})
    assert r.status_code==500 or r.status_code==422

def test_sobol_analysis_matches_core_shape_and_ranking():
    x=run_sobol_analysis(SobolAnalysisRequest(A=[1,2,3,4],B=[2,3,4,5],AB={'x':[1.5,2.5,3.5,4.5],'y':[1.1,2.1,3.1,4.1]}))
    assert x['method']=='sobol' and x['sample_count']==4
    assert {r['factor_key'] for r in x['factors']}=={'x','y'}
    assert x['factors'][0]['rank_position']==1
    assert x['calculated_by_core'] is False

def test_morris_analysis_computes_elementary_effects():
    samples=[{'x':0,'y':0},{'x':1,'y':0},{'x':1,'y':1}]
    x=run_morris_analysis(MorrisAnalysisRequest(samples=samples,outputs=[0,2,5],trajectories=[{'start_index':0,'order':['x','y']}]))
    rows={r['factor_key']:r for r in x['factors']}
    assert rows['x']['mu_star']==2 and rows['y']['mu_star']==3

def test_ensemble_statistics_normalizes_weights():
    x=run_ensemble_statistics(EnsembleStatisticsRequest(values=[0,10],weights=[1,3]))
    assert x['mean']==7.5
    assert abs(sum(x['normalized_weights'])-1)<1e-12
    assert x['aggregation_performed_by_workbench'] is True

def test_equal_weight_policy_overrides_raw_weights():
    x=run_ensemble_statistics(EnsembleStatisticsRequest(values=[0,10],weights=[1,99],weightPolicy='equal'))
    assert x['mean']==5

def test_exceedance_returns_empirical_probability_and_interval():
    x=run_exceedance(ExceedanceRequest(values=[1,2,3,4],threshold=2,operator='>'))
    assert x['exceedances']==2 and x['probability']==0.5
    assert len(x['confidence_interval_95'])==2
    assert x['probability_estimation_performed_by_core'] is False

def test_consume_core_scenario_request_preserves_exact_manifest_fields():
    record={'id':'req-1','requested_product':'workbench','request_hash':'rh','input_manifest_json':core_manifest()}
    x=consume_scenario_request(ScenarioRequestConsumeRequest(coreRequest=record))
    c=x['context']; assert x['ok'] is True
    assert c['coreRequestId']=='req-1' and c['scenarioEntityId']=='scenario-1'
    assert c['parameterValues']=={'x':2.0,'y':3.0}
    assert c['automaticWorkbenchExecutionAuthorized'] is False

def test_consumer_rejects_non_workbench_request():
    x=consume_scenario_request(ScenarioRequestConsumeRequest(coreRequest={'requested_product':'lab','input_manifest_json':core_manifest(execution_product='lab')}))
    assert x['ok'] is False and x['requestedProduct']=='lab'

def test_affine_scenario_execution_is_deterministic_and_builds_v670_registration():
    req=ScenarioAffineExecuteRequest(coreRequestId='req-2',inputManifest=core_manifest(),outputs={'z':AffineOutputSpec(intercept=1,coefficients={'x':2,'y':3})})
    x=execute_affine_scenario(req)
    assert x['outputs'][0]['value']==14
    assert x['numerical_computation_performed_by_workbench'] is True
    assert x['executionRegistrationPlan']['coreRequest']['path']=='/v1/research/computation-lineage/executions'
    assert x['lineageComponentsPlan'] is None

def test_affine_scenario_can_build_v670_components_when_core_execution_id_exists():
    req=ScenarioAffineExecuteRequest(coreRequestId='req-3',coreExecutionId='core-exec-3',coreSessionId='core-session-3',inputManifest=core_manifest(),outputs={'z':AffineOutputSpec(coefficients={'x':1})})
    x=execute_affine_scenario(req)
    p=x['lineageComponentsPlan']
    assert p['coreExecutionId']=='core-exec-3'
    assert p['componentCounts']['parameters']==2
    assert p['componentCounts']['outputs']==1
    assert p['unifiedSessionExecutionBinding']['binding']['session_id']=='core-session-3'

def test_affine_scenario_rejects_missing_numeric_parameter():
    r=client().post('/integration/core/scenario-uncertainty/scenario/affine/run',json={'coreRequestId':'r','inputManifest':core_manifest(parameter_values={'x':'abc'}),'outputs':{'z':{'coefficients':{'x':1}}}})
    assert r.status_code in (422,500)

def test_callback_plan_uses_exact_core_attempt_shape_and_never_dispatches():
    x=build_scenario_callbacks(ScenarioCallbackBuildRequest(coreRequestId='req-4',externalExecutionId='sc://workbench/execution/4',runtimeMetadata={'seed':42}))
    assert x['requestCount']==1
    r=x['coreRequests'][0]
    assert r['path']=='/v1/scenario-compute/requests/req-4/attempts'
    assert r['data']['executor_product']=='workbench' and r['data']['executed_by_core'] is False
    assert x['automaticCoreDispatchAuthorized'] is False

def test_callback_plan_can_bind_model_run_and_result_entities():
    x=build_scenario_callbacks(ScenarioCallbackBuildRequest(coreRequestId='req-5',externalExecutionId='e5',coreModelRunEntityId='run-5',resultBindings=[{'result_entity_id':'result-5','output_key':'z','binding_role':'primary'}]))
    paths=[r['path'] for r in x['coreRequests']]
    assert '/v1/scenario-compute/requests/req-5/bind-run' in paths
    assert '/v1/scenario-compute/requests/req-5/results' in paths

def test_service_token_policy_applies_to_v680(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret-680')
    c=client(); assert c.get('/integration/core/scenario-uncertainty/manifest').status_code==401
    ok=c.get('/integration/core/scenario-uncertainty/manifest',headers={'X-SC-Service-Token':'secret-680'})
    assert ok.status_code==200 and ok.json()['version']=='9.5.0'

def test_v680_status_and_capabilities():
    c=client(); s=c.get('/v680/status').json(); assert s['ok'] is True and s['version']=='9.5.0' and s['sobol'] is True
    caps=c.get('/capabilities').json(); assert caps['version']=='9.5.0'; assert caps['coreIntegration']['scenarioUncertaintyRuntime'] is True
    assert 'platform-core-scenario-uncertainty-compute-runtime' in caps['capabilities']
