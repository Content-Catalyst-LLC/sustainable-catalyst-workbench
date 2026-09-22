import os
from fastapi.testclient import TestClient
from app.main import app
from app.v710 import OBJECT_SCHEMA, SCHEMA


def client():
    return TestClient(app)


def execute_object(c, expression='6*7'):
    r=c.post('/execution/objects/execute',json={
        'operation':'math.compute',
        'payload':{'expression':expression},
        'projectRef':'project:v710-demo',
        'coreSessionId':'session:v710-demo',
        'requestKey':'math-demo',
        'label':'Math demo',
        'inputRefs':['dataset:alpha'],
        'tags':['demo'],
        'metadata':{'purpose':'test'},
    })
    assert r.status_code==200,r.text
    return r.json()


def test_manifest_status_capabilities_and_current_identity():
    c=client()
    m=c.get('/execution/objects/manifest'); assert m.status_code==200
    d=m.json(); assert d['version']=='7.1.0' and d['schema']==SCHEMA
    assert d['objectSchema']==OBJECT_SCHEMA
    assert d['capabilities']['singleExecutionObjects'] is True
    assert d['capabilities']['workflowExecutionObjects'] is True
    assert d['boundaries']['automaticCorePersistenceAuthorized'] is False
    s=c.get('/v710/status').json(); assert s['ok'] and s['version']=='7.1.0'
    assert s['contentAddressedIntegrity'] is True and s['resultContentImmutableAcrossRevisions'] is True
    caps=c.get('/capabilities').json(); assert caps['version']=='7.1.0'
    assert caps['coreIntegration']['unifiedExecutionObjectModel'] is True
    assert 'unified-execution-object-model' in caps['capabilities']


def test_single_execution_object_preserves_declared_request_result_and_integrity():
    c=client(); payload=execute_object(c)
    obj=payload['executionObject']; result=payload['executionResult']
    assert obj['schema']==OBJECT_SCHEMA and obj['objectKind']=='single_execution'
    assert obj['status']=='completed' and obj['terminal'] is True
    assert obj['method']['operation']=='math.compute'
    assert obj['inputs']['declaredPayload']=={'expression':'6*7'}
    assert obj['inputs']['fidelity']=='declared_payload_and_references'
    assert obj['outputs'][0]['contentHash']==result['resultHash']
    assert obj['outputs'][0]['inlineResult']['result']['exactText']=='42'
    assert obj['lineage']['workbenchExecutionRefs']==[result['executionRef']]
    assert obj['boundaries']['resultContentImmutable'] is True
    v=c.post('/execution/objects/validate',json={'executionObject':obj})
    assert v.status_code==200 and v.json()['valid'] is True


def test_deterministic_object_identity_and_hash_for_same_declared_execution():
    c=client(); a=execute_object(c)['executionObject']; b=execute_object(c)['executionObject']
    assert a['objectId']==b['objectId']
    assert a['objectRef']==b['objectRef']
    assert a['objectHash']==b['objectHash']


def test_reference_first_projection_marks_reduced_input_fidelity():
    c=client()
    raw=c.post('/execution/runtime/execute',json={'operation':'math.compute','payload':{'expression':'10+5'},'projectRef':'project:projection'}).json()
    r=c.post('/execution/objects/project',json={'source':raw,'datasetRefs':['dataset:projection'],'environmentRefs':['env:python-3.12']})
    assert r.status_code==200,r.text
    obj=r.json(); assert obj['inputs']['declaredPayload'] is None
    assert obj['inputs']['fidelity']=='reference_hash_only'
    assert obj['inputs']['datasetRefs']==['dataset:projection']
    assert obj['environment']['environmentRefs']==['env:python-3.12']


def test_workflow_object_preserves_children_dependency_graph_and_results():
    c=client()
    r=c.post('/execution/objects/workflow/run',json={
        'workflowKey':'object-flow',
        'projectRef':'project:flow',
        'steps':[
            {'stepId':'a','operation':'math.compute','payload':{'expression':'2+3'}},
            {'stepId':'b','operation':'electronics.resistor-network','dependsOn':['a'],'payload':{'topology':'series','resistancesOhm':[10,20],'sourceVoltageV':3}},
        ],
    })
    assert r.status_code==200,r.text
    d=r.json(); obj=d['executionObject']
    assert obj['objectKind']=='workflow_execution'
    assert len(obj['children'])==2 and len(obj['outputs'])==2
    assert obj['dependencies']['dependencyOrder']==['a','b']
    assert len(obj['dependencies']['edges'])==1
    edge=obj['dependencies']['edges'][0]
    assert edge['relation']=='depends_on' and edge['from']==obj['children'][0]['objectRef'] and edge['to']==obj['children'][1]['objectRef']
    assert obj['boundaries']['hiddenOutputSubstitutionPerformed'] is False
    assert c.post('/execution/objects/validate',json={'executionObject':obj}).json()['valid'] is True


def test_integrity_validation_detects_tampered_result_and_object_hash():
    c=client(); obj=execute_object(c)['executionObject']
    obj['outputs'][0]['inlineResult']['result']['exactText']='43'
    v=c.post('/execution/objects/validate',json={'executionObject':obj}).json()
    assert v['valid'] is False
    assert v['resultContentMutationDetected'] is True
    assert any('objectHash' in x for x in v['issues'])
    assert any('inline result hash mismatch' in x for x in v['issues'])


def test_revision_is_metadata_only_and_preserves_result_content():
    c=client(); obj=execute_object(c)['executionObject']; old_output=obj['outputs']
    r=c.post('/execution/objects/revise',json={
        'executionObject':obj,
        'reason':'Add review metadata',
        'label':'Reviewed math demo',
        'addTags':['reviewed'],
        'metadataPatch':{'reviewState':'reviewed'},
    })
    assert r.status_code==200,r.text
    revised=r.json(); assert revised['revision']==2 and revised['previousObjectHash']==obj['objectHash']
    assert revised['objectId']==obj['objectId'] and revised['objectRef']==obj['objectRef']
    assert revised['outputs']==old_output
    assert revised['revisionRecord']['resultContentChanged'] is False
    assert revised['objectHash']!=obj['objectHash']
    assert c.post('/execution/objects/validate',json={'executionObject':revised}).json()['valid'] is True


def test_core_binding_plan_is_two_phase_reference_first_and_non_dispatching():
    c=client(); obj=execute_object(c)['executionObject']
    first=c.post('/integration/core/execution-objects/binding/plan',json={'executionObject':obj})
    assert first.status_code==200,first.text
    d=first.json(); assert d['coreRuntimeSessionIdMustComeFromCore'] is True
    assert d['scientificRuntimeExecutionBinding'] is None and d['runtimeInvocationRegistration'] is None
    assert d['automaticCoreDispatchAuthorized'] is False and d['automaticCorePersistenceAuthorized'] is False

    second=c.post('/integration/core/execution-objects/binding/plan',json={
        'executionObject':obj,
        'coreRuntimeSessionId':'core-session-1',
        'coreRuntimeContractId':'core-contract-1',
    })
    assert second.status_code==200,second.text
    p=second.json()
    assert p['scientificRuntimeExecutionBinding']['path']=='/v1/research/unified-runtime/execution-bindings'
    assert p['scientificRuntimeExecutionBinding']['data']['session_id']=='core-session-1'
    assert p['runtimeInvocationRegistration']['path']=='/v1/research/runtime-contract/invocations'
    assert p['coreInvocationIdMustComeFromCoreBeforeResultBinding'] is True
    assert p['runtimeResultBinding'] is None

    third=c.post('/integration/core/execution-objects/binding/plan',json={
        'executionObject':obj,
        'coreRuntimeSessionId':'core-session-1',
        'coreRuntimeContractId':'core-contract-1',
        'coreInvocationId':'core-invocation-1',
    }).json()
    assert third['runtimeResultBinding']['path']=='/v1/research/runtime-contract/results'
    assert third['runtimeResultBinding']['data']['object_ref']==obj['objectRef']
    assert third['runtimeResultBinding']['data']['content_hash']==obj['objectHash']


def test_core_route_token_boundary(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true')
    monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret710')
    c=client(); obj=execute_object(c)['executionObject']
    denied=c.post('/integration/core/execution-objects/binding/plan',json={'executionObject':obj})
    assert denied.status_code==401
    ok=c.post('/integration/core/execution-objects/binding/plan',headers={'X-SC-Service-Token':'secret710'},json={'executionObject':obj})
    assert ok.status_code==200 and ok.json()['version']=='7.1.0'
