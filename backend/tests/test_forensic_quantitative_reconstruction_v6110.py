from fastapi.testclient import TestClient
from app.main import app
from app.v6110 import TRAJECTORY_SCHEMA, TEMPORAL_SCHEMA, UNCERTAINTY_SCHEMA, HYPOTHESIS_SCHEMA

c=TestClient(app)

def trajectory_payload():
    return {"reconstructionKey":"traj-demo","coordinateMode":"planar","distanceUnit":"m","points":[{"pointKey":"p0","timeSeconds":0,"x":0,"y":0},{"pointKey":"p1","timeSeconds":2,"x":3,"y":4},{"pointKey":"p2","timeSeconds":4,"x":9,"y":12}]}

def test_manifest_status_and_capabilities():
    m=c.get('/integration/core/forensic-quantitative/manifest'); assert m.status_code==200
    d=m.json(); assert d['version']=='8.5.0'; assert d['coreForensicQuantitativeContract']=='sc.open-forensics.quantitative-reconstruction.v1'; assert d['coreForensicHandoffContract']=='sc.forensic-quantitative-handoff.v1'; assert d['boundaries']['truthDeterminationAuthorized'] is False
    s=c.get('/v6110/status').json(); assert s['ok'] and s['version']=='8.5.0' and s['trajectoryReconstruction'] is True and s['hypothesisRanking'] is False
    caps=c.get('/capabilities').json(); assert caps['coreIntegration']['forensicQuantitativeReconstructionRuntime'] is True; assert 'platform-core-forensic-quantitative-reconstruction-runtime' in caps['capabilities']

def test_consumes_core_quantitative_handoff_without_execution():
    handoff={'contract':'sc.forensic-quantitative-handoff.v1','investigation_id':'inv-1','reconstruction_id':'rec-1','target_product':'workbench','model_ref':'model-1','execute_by_core':False,'input_manifest':{'contract':'sc.open-forensics.quantitative-reconstruction.v1','investigation_id':'inv-1','measurements':[],'assumptions':[],'parameters':[],'scenarios':[]}}
    r=c.post('/integration/core/forensic-quantitative/handoff/consume',json={'handoff':handoff}); assert r.status_code==200,r.text
    d=r.json(); assert d['targetProduct']=='workbench'; assert d['executionPlan']['automaticExecutionAuthorized'] is False; assert len(d['handoffHash'])==64

def test_rejects_non_workbench_handoff():
    handoff={'contract':'sc.forensic-quantitative-handoff.v1','target_product':'lab','input_manifest':{'contract':'sc.open-forensics.quantitative-reconstruction.v1'}}
    assert c.post('/integration/core/forensic-quantitative/handoff/consume',json={'handoff':handoff}).status_code==422

def test_planar_trajectory_reconstruction_metrics():
    r=c.post('/forensics/reconstruction/trajectory',json=trajectory_payload()); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==TRAJECTORY_SCHEMA; assert d['segments'][0]['distance']==5.0; assert d['segments'][0]['speed']==2.5; assert d['summary']['totalDistance']==15.0; assert d['summary']['averageSpeed']==3.75; assert d['truth_determination'] is False; assert len(d['resultHash'])==64

def test_geodetic_trajectory_uses_meter_distance():
    p={'reconstructionKey':'geo','coordinateMode':'geodetic-degrees','points':[{'pointKey':'a','timeSeconds':0,'x':0,'y':0},{'pointKey':'b','timeSeconds':10,'x':0.001,'y':0}]}
    d=c.post('/forensics/reconstruction/trajectory',json=p).json(); assert d['distanceUnit']=='m'; assert 110 < d['summary']['totalDistance'] < 112

def test_duplicate_trajectory_times_rejected():
    p=trajectory_payload(); p['points'][1]['timeSeconds']=0
    assert c.post('/forensics/reconstruction/trajectory',json=p).status_code==422

def test_temporal_comparison_overlap_and_gap():
    p={'windows':[{'windowKey':'a','startSeconds':0,'endSeconds':10},{'windowKey':'b','startSeconds':8,'endSeconds':12},{'windowKey':'c','startSeconds':20,'endSeconds':22}]}
    r=c.post('/forensics/reconstruction/temporal-comparison',json=p); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==TEMPORAL_SCHEMA; assert any(x['relation']=='overlaps' and x['overlapSeconds']==2 for x in d['comparisons']); assert any(x['gapSeconds']==8 for x in d['comparisons']); assert d['confirmed_sequence'] is False

def test_first_order_uncertainty_sum_and_ratio():
    p={'operation':'sum','measurements':[{'key':'a','value':3,'stddev':0.3},{'key':'b','value':4,'stddev':0.4}]}
    d=c.post('/forensics/reconstruction/uncertainty',json=p).json(); assert d['schema']==UNCERTAINTY_SCHEMA; assert d['result']==7.0; assert abs(d['stddev']-0.5)<1e-12
    p={'operation':'ratio','measurements':[{'key':'a','value':10,'stddev':1},{'key':'b','value':2,'stddev':0.2}]}
    d=c.post('/forensics/reconstruction/uncertainty',json=p).json(); assert d['result']==5.0; assert d['stddev']>0

def test_descriptive_hypothesis_metrics_are_not_ranked():
    p={'observations':[1,2,3],'hypotheses':[{'hypothesisRef':'hyp-1','predictions':[1,2,3]},{'hypothesisRef':'hyp-2','predictions':[2,3,4]}]}
    r=c.post('/forensics/reconstruction/hypothesis-metrics',json=p); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==HYPOTHESIS_SCHEMA; assert d['metrics'][0]['rmse']==0.0; assert d['ranked'] is False; assert d['probabilities_assigned'] is False; assert d['winner'] is None and d['verdict'] is None

def test_core_result_binding_plan_targets_open_forensics_result_endpoint():
    result=c.post('/forensics/reconstruction/trajectory',json=trajectory_payload()).json()
    p={'investigationId':'inv-1','reconstructionId':'rec-1','handoffId':'handoff-1','result':result,'evidenceItemId':'evidence-1'}
    r=c.post('/integration/core/forensic-quantitative/result/plan',json=p); assert r.status_code==200,r.text
    d=r.json(); assert d['coreRequest']['path']=='/v1/open-forensics/investigations/inv-1/quantitative-handoffs/handoff-1/results'; assert d['coreRequest']['data']['content_hash']==result['resultHash']; assert d['truthPromotionAuthorized'] is False

def test_reproduction_package_plan_targets_core_package_endpoint():
    result=c.post('/forensics/reconstruction/trajectory',json=trajectory_payload()).json()
    r=c.post('/integration/core/forensic-quantitative/reproduction/plan',json={'investigationId':'inv-1','reconstructionId':'rec-1','result':result}); assert r.status_code==200,r.text
    d=r.json(); assert d['coreForensicReproductionPackageContract']=='sc.open-forensics.quantitative-reproduction-package.v1'; assert d['coreRequest']['path'].endswith('/quantitative-reconstructions/rec-1/reproduction-packages'); assert d['reproducibilityEqualsTruth'] is False

def test_lineage_plan_uses_forensic_reconstruction_execution_type():
    result=c.post('/forensics/reconstruction/trajectory',json=trajectory_payload()).json()
    r=c.post('/integration/core/forensic-quantitative/lineage/plan',json={'projectRef':'project:1','reconstructionRef':'core:reconstruction:1','result':result,'evidenceRefs':['evidence:1']}); assert r.status_code==200,r.text
    d=r.json(); assert d['executionCreateRequest']['executionType']=='forensic_reconstruction'; assert d['coreExecutionIdMustComeFromCore'] is True; assert d['postExecutionComponents']['researchBindings'][0]['targetType']=='evidence'

def test_service_token_guard(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret6110')
    assert c.get('/integration/core/forensic-quantitative/manifest').status_code==401
    ok=c.get('/integration/core/forensic-quantitative/manifest',headers={'X-SC-Service-Token':'secret6110'}); assert ok.status_code==200 and ok.json()['version']=='8.5.0'
