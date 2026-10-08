from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def step(id, expression, depends=None):
    return {
        "id": id,
        "title": id,
        "dependsOn": depends or [],
        "calculationRequest": {
            "calculation": {"operation": "evaluate", "expression": expression},
            "requestedResultType": "numeric",
            "requireVerification": True,
            "requireProvenance": True,
        },
    }


def test_status():
    d=client.get('/v1400/status').json()
    assert d['version']=='14.0.0'
    assert d['computationalWorkflowComposerReady'] is True
    assert all(d['checks'].values())


def test_compose_and_validate_dag():
    body={"title":"Two step","steps":[step('a','2+3'),step('b','${a.result}*4',['a'])]}
    r=client.post('/standalone/v1/workflows/compose',json=body)
    assert r.status_code==200
    w=r.json()['workflow']
    assert w['validation']['valid'] is True
    assert w['validation']['topologicalOrder']==['a','b']
    assert w['workflowHash']


def test_cycle_and_unknown_dependency_are_blocked():
    cyc={"title":"Cycle","steps":[step('a','${b.result}+1',['b']),step('b','${a.result}+1',['a'])]}
    w=client.post('/standalone/v1/workflows/compose',json=cyc).json()['workflow']
    assert w['validation']['valid'] is False
    assert 'workflow-cycle-detected' in w['validation']['blockers']

    unk={"title":"Unknown","steps":[step('a','${missing.result}+1',['missing'])]}
    w=client.post('/standalone/v1/workflows/compose',json=unk).json()['workflow']
    assert w['validation']['valid'] is False
    assert any('unknown-dependency:missing' in x for x in w['validation']['blockers'])


def test_execution_chains_canonical_calculation_objects():
    body={"title":"Two step","steps":[step('a','2+3'),step('b','${a.result}*4',['a'])]}
    w=client.post('/standalone/v1/workflows/compose',json=body).json()['workflow']
    r=client.post('/standalone/v1/workflows/execute',json={'workflow':w})
    assert r.status_code==200
    x=r.json()['execution']
    assert x['topologicalOrder']==['a','b']
    assert x['stepCount']==2
    assert x['steps'][0]['calculationObject']
    assert x['steps'][1]['calculationObject']
    assert x['policy']['workflowOrchestratorMutatesResults'] is False
    assert x['executionHash']
