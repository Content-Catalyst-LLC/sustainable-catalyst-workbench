from fastapi.testclient import TestClient

from app.main import app
from app.v700 import OPERATIONS, RESULT_SCHEMA, SCHEMA


def client():
    return TestClient(app)


def test_manifest_catalog_and_status():
    c = client()
    m = c.get('/execution/runtime/manifest')
    assert m.status_code == 200
    d = m.json()
    assert d['ok'] is True
    assert d['schema'] == SCHEMA
    assert d['version'] == '9.8.0'
    assert d['operationCount'] == len(OPERATIONS) >= 60
    assert 'numerical-scientific' in d['categories']
    assert 'electronics-embedded' in d['categories']
    assert 'predictive' in d['categories']
    assert d['boundaries']['arbitraryPythonExecutionAuthorized'] is False
    assert d['boundaries']['automaticCorePersistenceAuthorized'] is False

    cat = c.get('/execution/runtime/catalog').json()
    assert cat['operationCount'] == len(OPERATIONS)
    keys = {x['key'] for x in cat['operations']}
    for key in ('math.compute', 'numerical.integrate', 'simulation.dynamic', 'controls.pid',
                'electronics.resistor-network', 'digital.truth-table', 'uncertainty.ensemble',
                'predictive.forecast', 'forensics.trajectory', 'energy.execute-handoff'):
        assert key in keys

    status = c.get('/v700/status').json()
    assert status['ok'] and status['version'] == '9.8.0'
    assert status['canonicalExecutionEnvelope'] is True
    assert status['workflowExecution'] is True
    assert status['coreLineagePlanning'] is True
    assert status['arbitraryCodeExecution'] is False


def test_symbolic_math_execution_has_canonical_envelope_and_hashes():
    c = client()
    payload = {'operation': 'math.compute', 'payload': {'expression': '2+3*4'}}
    a = c.post('/execution/runtime/execute', json=payload)
    b = c.post('/execution/runtime/execute', json=payload)
    assert a.status_code == b.status_code == 200
    x, y = a.json(), b.json()
    assert x['schema'] == RESULT_SCHEMA and x['version'] == '9.8.0'
    assert x['operation'] == 'math.compute'
    assert x['executionId'] == y['executionId']
    assert x['requestHash'] == y['requestHash']
    assert x['resultHash'] == y['resultHash']
    assert x['result']['result']['exactText'] == '14'
    assert x['boundaries']['automaticCorePersistencePerformed'] is False


def test_numerical_integration_and_electronics_dispatch():
    c = client()
    r = c.post('/execution/runtime/execute', json={
        'operation': 'numerical.integrate',
        'payload': {'expression': 'x**2', 'variable': 'x', 'lower': 0, 'upper': 1, 'samples': 101},
    })
    assert r.status_code == 200
    d = r.json()
    assert abs(d['result']['result']['value'] - 1/3) < 1e-10
    assert d['executionType'] == 'engineering_calculation'

    e = c.post('/execution/runtime/execute', json={
        'operation': 'electronics.resistor-network',
        'payload': {'topology': 'series', 'resistancesOhm': [100, 220], 'sourceVoltageV': 5},
    })
    assert e.status_code == 200
    ed = e.json()
    assert ed['result']['result']['equivalentResistanceOhm'] == 320.0
    assert ed['category'] == 'electronics-embedded'


def test_simulation_uncertainty_predictive_and_forensic_dispatch():
    c = client()
    sim = c.post('/execution/runtime/execute', json={
        'operation': 'simulation.dynamic',
        'payload': {'model_type': 'first_order', 'solver': 'rk4', 'initial_state': 0, 'input_value': 10, 'gain': 1, 'time_constant': 2, 'duration': 1, 'time_step': .1},
    })
    assert sim.status_code == 200 and sim.json()['executionType'] == 'simulation'

    ens = c.post('/execution/runtime/execute', json={
        'operation': 'uncertainty.ensemble',
        'payload': {'values': [1, 2, 3, 4], 'weightPolicy': 'equal'},
    })
    assert ens.status_code == 200
    assert ens.json()['result']['mean'] == 2.5

    forecast = c.post('/execution/runtime/execute', json={
        'operation': 'predictive.forecast',
        'payload': {'projectEntityId': 'project-1', 'modelKey': 'linear', 'modelName': 'Linear trend', 'history': [1, 2, 3, 4, 5, 6], 'horizon': 2, 'method': 'linear-trend'},
    })
    assert forecast.status_code == 200
    assert forecast.json()['result']['pointForecast'] == [7.0, 8.0]
    assert forecast.json()['executionType'] == 'forecasting'

    forensic = c.post('/execution/runtime/execute', json={
        'operation': 'forensics.trajectory',
        'payload': {
            'reconstructionKey': 'traj-1',
            'points': [
                {'pointKey': 'a', 'timeSeconds': 0, 'x': 0, 'y': 0},
                {'pointKey': 'b', 'timeSeconds': 2, 'x': 6, 'y': 8},
            ],
        },
    })
    assert forensic.status_code == 200
    fd = forensic.json()
    assert fd['result']['summary']['totalDistance'] == 10.0
    assert fd['executionType'] == 'forensic_reconstruction'
    assert fd['boundaries']['truthDetermined'] is False


def test_invalid_operation_and_invalid_payload_are_rejected():
    c = client()
    bad = c.post('/execution/runtime/execute', json={'operation': 'python.exec', 'payload': {'code': 'print(1)'}})
    assert bad.status_code == 422
    bad2 = c.post('/execution/runtime/execute', json={'operation': 'numerical.root', 'payload': {'expression': 'x**2+1', 'bracket': [-1, 1]}})
    assert bad2.status_code == 422


def test_dependency_ordered_workflow_runs_without_hidden_substitution():
    c = client()
    r = c.post('/execution/runtime/workflow/run', json={
        'workflowKey': 'demo-flow',
        'projectRef': 'project:demo',
        'steps': [
            {'stepId': 'b', 'operation': 'electronics.resistor-network', 'dependsOn': ['a'], 'payload': {'topology': 'series', 'resistancesOhm': [10, 20], 'sourceVoltageV': 3}},
            {'stepId': 'a', 'operation': 'math.compute', 'payload': {'expression': '6*7'}},
        ],
    })
    assert r.status_code == 200
    d = r.json()
    assert d['ok'] is True
    assert d['dependencyOrder'] == ['a', 'b']
    assert d['completedStepCount'] == 2
    assert d['automaticOutputSubstitutionPerformed'] is False
    assert d['automaticCorePersistencePerformed'] is False
    assert d['results'][1]['dependencyResultRefs'] == [d['resultRefs']['a']]


def test_workflow_cycle_is_rejected():
    c = client()
    r = c.post('/execution/runtime/workflow/run', json={
        'steps': [
            {'stepId': 'a', 'operation': 'math.compute', 'payload': {'expression': '1'}, 'dependsOn': ['b']},
            {'stepId': 'b', 'operation': 'math.compute', 'payload': {'expression': '2'}, 'dependsOn': ['a']},
        ]
    })
    assert r.status_code == 422


def test_core_lineage_plan_is_two_phase_and_non_dispatching():
    c = client()
    executed = c.post('/execution/runtime/execute', json={
        'operation': 'numerical.root',
        'payload': {'expression': 'x**2-4', 'variable': 'x', 'bracket': [0, 3]},
        'projectRef': 'project:demo',
        'coreSessionId': 'session-1',
    }).json()

    first = c.post('/integration/core/unified-execution/lineage/plan', json={
        'executionResult': executed,
        'coreSessionId': 'session-1',
        'projectRef': 'project:demo',
    })
    assert first.status_code == 200
    d = first.json()
    assert d['coreExecutionIdMustComeFromCore'] is True
    assert d['lineageComponents'] is None
    assert d['automaticCoreDispatchAuthorized'] is False
    assert d['executionRegistration']['coreRequest']['path'] == '/v1/research/computation-lineage/executions'

    second = c.post('/integration/core/unified-execution/lineage/plan', json={
        'executionResult': executed,
        'coreExecutionId': 'core-exec-1',
        'coreSessionId': 'session-1',
        'projectRef': 'project:demo',
    })
    assert second.status_code == 200
    p = second.json()
    assert p['coreExecutionIdProvided'] is True
    assert p['lineageComponents']['coreExecutionId'] == 'core-exec-1'
    assert p['lineageComponents']['componentCounts']['outputs'] == 1
    assert p['lineageComponents']['automaticCorePersistenceAuthorized'] is False


def test_core_route_token_boundary(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN', 'true')
    monkeypatch.setenv('SCWB_SERVICE_TOKEN', 'secret700')
    c = client()
    result = c.post('/execution/runtime/execute', json={'operation': 'math.compute', 'payload': {'expression': '1+1'}}).json()
    assert c.post('/integration/core/unified-execution/lineage/plan', json={'executionResult': result}).status_code == 401
    ok = c.post('/integration/core/unified-execution/lineage/plan', headers={'X-SC-Service-Token': 'secret700'}, json={'executionResult': result})
    assert ok.status_code == 200 and ok.json()['version'] == '9.8.0'
