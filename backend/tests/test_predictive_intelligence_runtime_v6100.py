from fastapi.testclient import TestClient
from app.main import app
from app.v6100 import FORECAST_SCHEMA, BACKTEST_SCHEMA, CALIBRATION_SCHEMA

c=TestClient(app)

def forecast_payload(method='linear-trend'):
    return {'projectEntityId':'project-predictive-1','modelKey':'trend-demo','modelName':'Trend Demo','targetKey':'demand','targetLabel':'Demand','history':[10,12,14,16,18,20],'horizon':3,'method':method,'intervalLevel':0.9,'workbenchExecutionRef':'run:predictive-1'}

def test_manifest_status_and_capabilities():
    m=c.get('/integration/core/predictive-intelligence/manifest'); assert m.status_code==200
    d=m.json(); assert d['version']=='8.11.0'; assert d['corePredictiveModelContract']=='sc.predictive.model.v1'; assert d['coreVisualPredictiveContract']=='sc.visual-runtime.predictive-intelligence.v1'; assert d['boundaries']['coreExecutesPredictiveModels'] is False
    s=c.get('/v6100/status').json(); assert s['ok'] and s['version']=='8.11.0' and s['probabilisticIntervals'] is True
    caps=c.get('/capabilities').json(); assert caps['coreIntegration']['predictiveIntelligenceRuntime'] is True; assert 'platform-core-predictive-intelligence-runtime' in caps['capabilities']

def test_linear_trend_forecast_and_interval():
    r=c.post('/predictive/forecast',json=forecast_payload()); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==FORECAST_SCHEMA; assert d['pointForecast']==[22.0,24.0,26.0]; assert len(d['intervalForecast'])==3; assert d['calculated_by_workbench'] is True; assert d['calculated_by_core'] is False; assert len(d['resultHash'])==64

def test_naive_drift_mean_and_moving_average_forecasts():
    for method in ('naive','drift','mean','moving-average'):
        p=forecast_payload(method); p['movingAverageWindow']=3
        r=c.post('/predictive/forecast',json=p); assert r.status_code==200,r.text; assert len(r.json()['pointForecast'])==3
    drift=c.post('/predictive/forecast',json=forecast_payload('drift')).json(); assert drift['pointForecast'][0]==22.0

def test_rolling_origin_backtest_metrics():
    r=c.post('/predictive/backtest',json={'history':[1,2,3,4,5,6,7],'method':'linear-trend','minimumTrainSize':3}); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==BACKTEST_SCHEMA; assert d['foldCount']==4; assert d['metrics']['mae'] < 1e-9; assert d['metrics']['rmse'] < 1e-9

def test_binary_calibration_brier_logloss_and_bins():
    r=c.post('/predictive/calibration',json={'probabilities':[0.1,0.2,0.8,0.9],'outcomes':[0,0,1,1],'bins':4}); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==CALIBRATION_SCHEMA; assert d['metrics']['brier'] < 0.03; assert d['metrics']['logLoss']>0; assert len(d['bins'])>=2; assert d['calculated_by_core'] is False

def test_invalid_probability_rejected():
    r=c.post('/predictive/calibration',json={'probabilities':[0.2,1.2],'outcomes':[0,1]}); assert r.status_code==422

def test_model_plan_targets_core_predictive_registry():
    f=c.post('/predictive/forecast',json=forecast_payload()).json()
    r=c.post('/integration/core/predictive-intelligence/model/plan',json={'forecastResult':f}); assert r.status_code==200,r.text
    d=r.json(); assert d['coreModelIdMustComeFromCore'] is True; assert d['coreRequests'][0]['path']=='/v1/predictive-intelligence/models'; assert d['coreRequests'][0]['data']['runtime_product']=='workbench'; assert d['automaticCorePersistenceAuthorized'] is False

def test_forecast_core_plan_requires_core_ids_and_builds_provenance_requests():
    f=c.post('/predictive/forecast',json=forecast_payload()).json()
    bad=c.post('/integration/core/predictive-intelligence/forecast/plan',json={'forecastResult':f,'coreModelId':'','coreTargetId':'target-1'}); assert bad.status_code==422
    r=c.post('/integration/core/predictive-intelligence/forecast/plan',json={'forecastResult':f,'coreModelId':'model-core-1','coreTargetId':'target-core-1'}); assert r.status_code==200,r.text
    d=r.json(); paths=[x['path'] for x in d['coreRequests']]; assert '/v1/predictive-intelligence/models/model-core-1/forecast-runs' in paths; assert '/v1/predictive-intelligence/models/model-core-1/probabilistic-forecasts' in paths; assert d['coreForecastRunIdMustComeFromCore'] is True; assert d['coreProbabilisticForecastIdMustComeFromCore'] is True

def test_calibration_core_plan_is_two_phase():
    cal=c.post('/predictive/calibration',json={'probabilities':[0.1,0.3,0.7,0.9],'outcomes':[0,0,1,1],'bins':4}).json()
    r=c.post('/integration/core/predictive-intelligence/calibration/plan',json={'calibrationResult':cal,'coreModelId':'model-1','coreTargetId':'target-1'}); assert r.status_code==200,r.text
    d=r.json(); assert d['coreCalibrationStudyIdMustComeFromCore'] is True; assert d['requestCount']==1
    r=c.post('/integration/core/predictive-intelligence/calibration/plan',json={'calibrationResult':cal,'coreModelId':'model-1','coreTargetId':'target-1','coreCalibrationStudyId':'study-1','coreProbabilisticForecastId':'pf-1'}); assert r.status_code==200,r.text
    d=r.json(); assert d['requestCount']>1; assert any('/calibration-studies/study-1/bins' in x['path'] for x in d['coreRequests'])

def test_visual_predictive_plan_waits_for_workspace_id_then_builds_overlays():
    f=c.post('/predictive/forecast',json=forecast_payload()).json()
    r=c.post('/integration/core/predictive-intelligence/visual/plan',json={'forecastResult':f,'coreCompositionId':'composition-1'}); assert r.status_code==200,r.text
    d=r.json(); assert d['coreWorkspaceIdMustComeFromCore'] is True; assert d['requestCount']==1
    r=c.post('/integration/core/predictive-intelligence/visual/plan',json={'forecastResult':f,'coreCompositionId':'composition-1','coreWorkspaceId':'vp-workspace-1','coreForecastRunId':'forecast-run-1','coreProbabilisticForecastId':'pf-1','targetViewIds':['view-1']}); assert r.status_code==200,r.text
    d=r.json(); paths=[x['path'] for x in d['coreRequests']]; assert '/v1/visual-runtime/predictive/workspaces/vp-workspace-1/forecast-overlays' in paths; assert '/v1/visual-runtime/predictive/workspaces/vp-workspace-1/uncertainty-displays' in paths; assert d['visualRenderingByCore'] is False

def test_service_token_guard(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret6100')
    assert c.get('/integration/core/predictive-intelligence/manifest').status_code==401
    ok=c.get('/integration/core/predictive-intelligence/manifest',headers={'X-SC-Service-Token':'secret6100'}); assert ok.status_code==200 and ok.json()['version']=='8.11.0'
