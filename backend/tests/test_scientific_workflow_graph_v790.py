from copy import deepcopy

from fastapi.testclient import TestClient
from app.main import app
from app.v790 import SCHEMA, RUN_SCHEMA, CORE_WORKFLOW_CONTRACT


def c(): return TestClient(app)


def axial_graph():
    return {
        "graphKey": "axial-vv-graph",
        "title": "Axial engineering calculation with explicit benchmark",
        "nodes": [
            {
                "nodeId": "engineering",
                "nodeType": "engineering",
                "request": {
                    "analysisKey": "mechanical.axial-member",
                    "inputs": {
                        "force_n": 1000,
                        "area_m2": 0.01,
                        "length_m": 1,
                        "elastic_modulus_pa": 200000000000,
                    },
                },
            },
            {
                "nodeId": "benchmark",
                "nodeType": "validation",
                "action": "benchmark",
                "dependsOn": ["engineering"],
                "bindings": [
                    {"sourceNodeId": "engineering", "sourcePath": "result", "targetPath": "targetResult"}
                ],
                "request": {
                    "cases": [
                        {
                            "caseKey": "stress",
                            "actualPath": "stressPa",
                            "expected": 100000,
                            "absoluteTolerance": 1e-9,
                            "relativeTolerance": 0,
                        }
                    ]
                },
            },
        ],
    }


def test_manifest_status_and_capabilities():
    cl=c(); m=cl.get('/workflow-graph/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='9.8.0' and d['capabilities']['dependencyDirectedAcyclicGraphs']
    s=cl.get('/v790/status').json(); assert s['ok'] and s['typedNodes'] and s['hiddenOutputSubstitution'] is False
    caps=cl.get('/capabilities').json(); assert caps['version']=='9.8.0' and caps['coreIntegration']['scientificWorkflowGraph'] is True


def test_graph_plan_is_deterministic_and_content_addressed():
    cl=c(); graph=axial_graph()
    a=cl.post('/workflow-graph/plan',json=graph); b=cl.post('/workflow-graph/plan',json=graph)
    assert a.status_code==200 and b.status_code==200
    aa=a.json(); bb=b.json(); assert aa['graphHash']==bb['graphHash'] and aa['planHash']==bb['planHash']
    assert aa['dependencyOrder']==['engineering','benchmark'] and aa['executionPerformed'] is False


def test_cycle_rejected_by_validation_and_plan():
    graph={
        'graphKey':'cycle',
        'nodes':[
            {'nodeId':'a','nodeType':'engineering','dependsOn':['b'],'request':{'analysisKey':'thermal.convection','inputs':{'coefficient_w_m2k':10,'area_m2':1,'surface_temp_c':30,'fluid_temp_c':25}}},
            {'nodeId':'b','nodeType':'engineering','dependsOn':['a'],'request':{'analysisKey':'thermal.convection','inputs':{'coefficient_w_m2k':10,'area_m2':1,'surface_temp_c':30,'fluid_temp_c':25}}},
        ],
    }
    cl=c(); v=cl.post('/workflow-graph/validate',json=graph); assert v.status_code==200 and v.json()['acyclic'] is False
    p=cl.post('/workflow-graph/plan',json=graph); assert p.status_code==422


def test_binding_requires_declared_dependency():
    graph=axial_graph(); graph['nodes'][1]['dependsOn']=[]
    r=c().post('/workflow-graph/validate',json=graph)
    assert r.status_code==422


def test_run_explicit_binding_engineering_to_benchmark():
    r=c().post('/workflow-graph/run',json={'graph':axial_graph()}); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==RUN_SCHEMA and d['ok'] is True and d['completedNodeCount']==2
    eng,bench=d['nodeRuns']; assert eng['executionObject']['objectRef'].startswith('sc://workbench/execution-object/')
    assert bench['result']['outcome']=='pass'
    assert bench['appliedBindings'][0]['sourcePath']=='result' and bench['appliedBindings'][0]['targetPath']=='targetResult'
    assert d['automaticOutputSubstitutionPerformed'] is False and d['explicitDeclaredBindingsApplied'] is True


def test_run_hash_tamper_detection():
    cl=c(); d=cl.post('/workflow-graph/run',json={'graph':axial_graph()}).json()
    good=cl.post('/workflow-graph/run/validate',json={'graphRun':d}); assert good.status_code==200 and good.json()['valid'] is True
    tampered=deepcopy(d); tampered['nodeRuns'][0]['result']['result']['stress_pa']=123
    bad=cl.post('/workflow-graph/run/validate',json={'graphRun':tampered}).json(); assert bad['valid'] is False
    assert any(x.startswith('node-result-hash-mismatch') for x in bad['reasons'])


def test_solver_node_runs_through_existing_bounded_solver():
    graph={
        'graphKey':'solver-graph',
        'nodes':[{
            'nodeId':'root','nodeType':'solver',
            'request':{'problemKind':'root','solverKey':'root.brentq','problem':{'expression':'x**2 - 2','variable':'x','bracket':[0,2]}}
        }]
    }
    r=c().post('/workflow-graph/run',json={'graph':graph}); assert r.status_code==200,r.text
    run=r.json()['nodeRuns'][0]; assert run['result']['solverKey']=='root.brentq' and run['executionObject']['objectHash']


def test_validation_report_can_bind_prior_result_explicitly():
    graph={
        'graphKey':'vv-report-graph',
        'nodes':[
            {'nodeId':'eng','nodeType':'engineering','request':{'analysisKey':'thermal.convection','inputs':{'coefficient_w_m2k':10,'area_m2':2,'surface_temp_c':30,'fluid_temp_c':25}}},
            {'nodeId':'report','nodeType':'validation','action':'report','dependsOn':['eng'],
             'bindings':[{'sourceNodeId':'eng','sourcePath':'result','targetPath':'targetResult'}],
             'request':{'reportKey':'thermal-report','targetKind':'engineering','evidence':[], 'limitations':['no validation evidence declared']}}
        ]
    }
    r=c().post('/workflow-graph/run',json={'graph':graph}); assert r.status_code==200,r.text
    report=r.json()['nodeRuns'][1]['result']; assert report['overallStatus']=='incomplete' and report['scientificValidityCertified'] is False


def test_core_workflow_plan_is_two_phase(monkeypatch):
    cl=c(); run=cl.post('/workflow-graph/run',json={'graph':axial_graph()}).json()
    p=cl.post('/integration/core/workflow-graph/plan',json={'graphRun':run}); assert p.status_code==200,p.text
    d=p.json(); assert d['coreWorkflowContract']==CORE_WORKFLOW_CONTRACT and d['coreWorkflowIdMustComeFromCore'] and d['stageRegistrations']==[]
    q=cl.post('/integration/core/workflow-graph/plan',json={'graphRun':run,'coreWorkflowId':'core-wf-790'}); assert q.status_code==200,q.text
    qq=q.json(); assert len(qq['stageRegistrations'])==2 and qq['stageRegistrations'][0]['path'].endswith('/stages') and qq['automaticCoreDispatchAuthorized'] is False
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret790')
    assert cl.post('/integration/core/workflow-graph/plan',json={'graphRun':run}).status_code==401
    assert cl.post('/integration/core/workflow-graph/plan',headers={'X-SC-Service-Token':'secret790'},json={'graphRun':run}).status_code==200


def test_missing_required_binding_path_causes_node_failure():
    graph=axial_graph(); graph['nodes'][1]['bindings'][0]['sourcePath']='result.not_there'
    r=c().post('/workflow-graph/run',json={'graph':graph}); assert r.status_code==200,r.text
    d=r.json(); assert d['ok'] is False and d['failedNodeId']=='benchmark' and d['nodeRuns'][1]['status']=='failed'


def test_no_arbitrary_code_or_hidden_substitution_boundaries():
    m=c().get('/workflow-graph/manifest').json()
    assert m['boundaries']['arbitraryCodeExecution'] is False
    assert m['boundaries']['hiddenOutputSubstitution'] is False
    assert m['boundaries']['automaticCoreDispatch'] is False
