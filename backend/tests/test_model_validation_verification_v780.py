from fastapi.testclient import TestClient
from app.main import app
from app.v780 import SCHEMA, REPORT_SCHEMA, CORE_COMPUTATION_LINEAGE_CONTRACT


def c(): return TestClient(app)


def test_manifest_status_capabilities():
    cl=c(); m=cl.get('/validation/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='8.12.0' and d['capabilities']['referenceBenchmarkEvaluation']
    s=cl.get('/v780/status').json(); assert s['ok'] and s['datasetComparison'] and s['automaticModelAcceptance'] is False
    caps=cl.get('/capabilities').json(); assert caps['version']=='8.12.0' and caps['coreIntegration']['modelValidationVerificationFramework'] is True


def test_scalar_benchmark_pass_fail_and_path_resolution():
    target={'result':{'value':1.0005,'nested':[{'x':3.0}]}}
    payload={'targetResult':target,'cases':[{'caseKey':'value','actualPath':'result.value','expected':1.0,'absoluteTolerance':0.001,'relativeTolerance':0},{'caseKey':'nested','actualPath':'result.nested.0.x','expected':3.0,'absoluteTolerance':0,'relativeTolerance':0}]}
    r=c().post('/validation/benchmark/evaluate',json=payload); assert r.status_code==200,r.text
    d=r.json(); assert d['outcome']=='pass' and d['passedCaseCount']==2 and d['evidenceHash']
    payload['cases'][0]['absoluteTolerance']=1e-5
    assert c().post('/validation/benchmark/evaluate',json=payload).json()['outcome']=='fail'


def test_dataset_comparison_metrics_and_thresholds():
    r=c().post('/validation/dataset-compare',json={'comparisonKey':'calibration','observed':[1,2,3,4],'predicted':[1.0,2.1,2.9,4.0],'maxRMSE':0.1,'maxMAE':0.1,'minR2':0.99}); assert r.status_code==200,r.text
    d=r.json(); assert d['outcome']=='pass' and d['metrics']['rmse']>0 and d['metrics']['r2']>0.99
    r2=c().post('/validation/dataset-compare',json={'observed':[1,2,3],'predicted':[5,5,5]}); assert r2.status_code==200 and r2.json()['outcome']=='incomplete'


def test_convergence_evaluation_consumes_v740_study():
    cl=c(); study=cl.post('/solvers/convergence-study',json={'problemKind':'integration','problem':{'expression':'x**2','variable':'x','lowerBound':0,'upperBound':1},'solverKey':'integration.simpson','levels':4,'refinementFactor':2}).json()
    r=cl.post('/validation/convergence/evaluate',json={'study':study,'requireMonotoneRefinement':True,'finalChangeTolerance':1e-8}); assert r.status_code==200,r.text
    d=r.json(); assert d['evidenceKind']=='numerical-convergence' and d['outcome'] in {'pass','fail'} and d['scientificConvergenceCertified'] is False


def test_report_build_integrity_and_no_truth_claims():
    cl=c(); ev=cl.post('/validation/dataset-compare',json={'observed':[1,2,3],'predicted':[1,2,3],'maxRMSE':0}).json()
    target=cl.post('/engineering/analyze',json={'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.01,'length_m':1,'elastic_modulus_pa':200000000000}}).json()
    r=cl.post('/validation/report/build',json={'reportKey':'axial-vv','targetKind':'engineering','targetResult':target,'evidence':[ev],'assumptions':['linear elastic model'],'limitations':['single load case']}); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==REPORT_SCHEMA and d['overallStatus']=='pass' and d['declaredChecksPassed'] is True and d['scientificValidityCertified'] is False and d['reportHash']
    assert cl.post('/validation/report/validate',json={'report':d}).json()['valid'] is True
    d['limitations'].append('tampered')
    bad=cl.post('/validation/report/validate',json={'report':d}).json(); assert bad['valid'] is False and 'report-hash-mismatch' in bad['reasons']


def test_core_verification_lineage_plan_is_two_phase(monkeypatch):
    cl=c(); ev=cl.post('/validation/dataset-compare',json={'observed':[1,2,3],'predicted':[1,2,3],'maxRMSE':0}).json()
    report=cl.post('/validation/report/build',json={'targetKind':'model','targetResult':{'model':'demo'},'evidence':[ev]}).json()
    p=cl.post('/integration/core/validation-lineage/plan',json={'report':report}); assert p.status_code==200,p.text
    d=p.json(); assert d['coreComputationLineageContract']==CORE_COMPUTATION_LINEAGE_CONTRACT and d['coreExecutionIdMustComeFromCore'] and d['verificationRegistrations']==[]
    q=cl.post('/integration/core/validation-lineage/plan',json={'report':report,'coreExecutionId':'core-exec-780'}); assert q.status_code==200,q.text
    qq=q.json(); assert qq['verificationRegistrations'][0]['path'].endswith('/verifications') and qq['automaticCoreDispatchAuthorized'] is False
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret780')
    assert cl.post('/integration/core/validation-lineage/plan',json={'report':report}).status_code==401
    assert cl.post('/integration/core/validation-lineage/plan',headers={'X-SC-Service-Token':'secret780'},json={'report':report}).status_code==200


def test_dataset_length_and_nonfinite_guards():
    assert c().post('/validation/dataset-compare',json={'observed':[1,2],'predicted':[1]}).status_code==422
    assert c().post('/validation/benchmark/evaluate',json={'targetResult':{'x':'not-number'},'cases':[{'caseKey':'x','actualPath':'x','expected':1}]}).status_code==422
