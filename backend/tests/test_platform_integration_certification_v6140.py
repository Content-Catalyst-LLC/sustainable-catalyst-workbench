from fastapi.testclient import TestClient
from app.main import app
from app.v6140 import CORE_CERTIFICATION_CONTRACT, CASE_CATALOG

c = TestClient(app)


def test_status_manifest_and_local_report():
    s = c.get('/v6140/status')
    assert s.status_code == 200
    d = s.json()
    assert d['version'] == '7.11.0'
    assert d['declaredConformance'] is True
    assert d['scientificValidityCertification'] is False
    m = c.get('/integration/core/certification/manifest')
    assert m.status_code == 200
    body = m.json()
    assert body['coreCertificationContract'] == CORE_CERTIFICATION_CONTRACT
    assert len(body['defaultCaseKeys']) == len(CASE_CATALOG)
    assert body['boundaries']['automaticCoreDispatchAuthorized'] is False
    r = c.get('/integration/core/certification/report/local')
    assert r.status_code == 200
    report = r.json()
    assert report['declaredConformance'] is True
    assert not report['missingRequiredCaseKeys']
    assert not report['nonpassingRequiredCaseKeys']
    assert len(report['reportHash']) == 64


def test_suite_product_cases_and_run_plans_match_core_shapes():
    suite = c.post('/integration/core/certification/suite/prepare', json={}).json()
    assert suite['contract'] == CORE_CERTIFICATION_CONTRACT
    assert suite['request']['path'].endswith('/suites')
    assert suite['request']['data']['contract_ref'] == 'sc.research.unified-runtime-contract.v1'
    assert suite['automaticCoreDispatchAuthorized'] is False

    product = c.post('/integration/core/certification/product/prepare', json={'coreSuiteId':'suite-1'}).json()
    assert product['request']['data']['suite_id'] == 'suite-1'
    assert product['request']['data']['product_version'] == '7.11.0'
    assert 'workbench.computational-project' in product['request']['data']['declared_object_types']

    cases = c.post('/integration/core/certification/cases/prepare', json={'coreSuiteId':'suite-1'}).json()
    assert cases['caseCount'] == len(CASE_CATALOG)
    assert all(x['request']['data']['suite_id'] == 'suite-1' for x in cases['coreRequests'])

    run = c.post('/integration/core/certification/run/prepare', json={'coreSuiteId':'suite-1','coreProductId':'product-1'}).json()
    assert run['request']['data']['suite_id'] == 'suite-1'
    assert run['request']['data']['product_id'] == 'product-1'
    assert run['request']['data']['environment_ref'] == 'sc://workbench/runtime/7.11.0'


def test_result_plan_requires_core_case_ids_and_builds_after_ids_exist():
    partial = c.post('/integration/core/certification/results/prepare', json={
        'coreRunId':'run-1',
        'coreCaseIds': {'workbench-connectivity-foundation':'case-1'},
    }).json()
    assert partial['ready'] is False
    assert partial['missingCoreCaseIds']
    assert len(partial['coreRequests']) == 1

    case_ids = {x['case_key']: f"core-{i}" for i,x in enumerate(CASE_CATALOG)}
    full = c.post('/integration/core/certification/results/prepare', json={'coreRunId':'run-1','coreCaseIds':case_ids}).json()
    assert full['ready'] is True
    assert not full['missingCoreCaseIds']
    assert len(full['coreRequests']) == len(CASE_CATALOG)
    assert all(x['request']['data']['run_id']=='run-1' for x in full['coreRequests'])


def test_exchange_trace_reproduction_and_evidence_plans_are_non_dispatching():
    checks = c.post('/integration/core/certification/checks/prepare', json={
        'coreRunId':'run-1', 'projectRef':'sc://workbench/project/p1',
        'expectedTraceRefs':['a','b'], 'observedTraceRefs':['a','b'],
        'stateVersionRef':'state:v1','reconstructionPlanRef':'reconstruct:1',
    }).json()
    assert len(checks['coreRequests']) == 3
    assert checks['coreRequests'][1]['request']['data']['status'] == 'pass'
    assert checks['coreRequests'][2]['request']['data']['status'] == 'pass'
    assert checks['reproducibilityInferred'] is False
    ev = c.post('/integration/core/certification/evidence/prepare', json={'coreRunId':'run-1'}).json()
    assert ev['request']['data']['content_hash']
    assert ev['request']['data']['evidence_type'] == 'workbench-local-conformance-report'


def test_finalize_plans_revision_and_snapshot_without_persistence():
    d = c.post('/integration/core/certification/finalize/prepare', json={'coreSuiteId':'suite-1'}).json()
    assert len(d['coreRequests']) == 2
    assert d['coreRequests'][0]['request']['path'].endswith('/revisions')
    assert d['coreRequests'][1]['request']['path'].endswith('/snapshots')
    assert d['automaticCorePersistenceAuthorized'] is False


def test_consume_core_report_and_bundle_read_only():
    report = {
        'release':'2.97.0','contract':CORE_CERTIFICATION_CONTRACT,
        'run':{'id':'run-1'},'case_results':[{'id':'r1'}],
        'exchange_checks':[{}],'trace_checks':[{}],'reproduction_checks':[{}],
        'evidence':[{}],'findings':[], 'declared_conformance':True,
        'missing_required_case_ids':[], 'nonpassing_required_case_ids':[],
        'conformance_is_runtime_contract_evidence_not_scientific_or_quality_certification':True,
    }
    d = c.post('/integration/core/certification/run-report/consume', json={'report':report}).json()
    assert d['declaredConformance'] is True
    assert d['scientificValidityCertified'] is False
    assert d['readOnlyConsumption'] is True

    bundle = {'release':'2.97.0','contract':CORE_CERTIFICATION_CONTRACT,'suite':{'id':'suite-1','suite_key':'wb'},'products':[{}],'cases':[{}],'runs':[{}],'revisions':[{}],'snapshots':[{}],'certification_scope':'platform_runtime_contract_conformance_only'}
    b = c.post('/integration/core/certification/suite-bundle/consume', json={'bundle':bundle}).json()
    assert b['coreSuiteId'] == 'suite-1'
    assert b['snapshotCount'] == 1
    assert b['automaticCoreMutationAuthorized'] is False


def test_service_token_guard(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true')
    monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret6140')
    assert c.get('/integration/core/certification/manifest').status_code == 401
    ok = c.get('/integration/core/certification/manifest', headers={'X-SC-Service-Token':'secret6140'})
    assert ok.status_code == 200 and ok.json()['version'] == '7.11.0'
