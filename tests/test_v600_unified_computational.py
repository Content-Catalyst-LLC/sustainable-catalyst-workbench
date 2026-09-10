import pytest

from backend.app.v600 import (
    ComputationalObject,
    ExportRequest,
    HandoffRequest,
    HistoryEvent,
    HistoryRequest,
    LinkGraphRequest,
    ObjectLink,
    ProjectBuildRequest,
    ProjectInput,
    ProvenanceOperation,
    ProvenanceRequest,
    SharedVariable,
    VariableSetRequest,
    build_export,
    build_handoff,
    build_history,
    build_link_graph,
    build_project,
    build_provenance,
    resolve_variables,
    status_record,
)


def sample_project():
    return ProjectInput(
        projectId='study-one',
        title='Study One',
        variables=[
            SharedVariable(name='a', value=2, valueType='number'),
            SharedVariable(name='frequency_hz', value=1000, valueType='number', units='Hz'),
        ],
        objects=[
            ComputationalObject(objectId='math-model', kind='symbolic-expression', studio='mathematics', variableInputs=['a'], payload={'expression': 'a*x^2'}),
            ComputationalObject(objectId='graph-view', kind='graph', studio='graph-mathematics', variableInputs=['a'], dependencyObjectIds=['math-model'], payload={'expression': 'a*x^2'}),
        ],
    )


def test_status_reports_unified_project_capabilities_and_boundaries():
    s = status_record()
    assert s['ok'] is True and s['version'] == '6.0.0'
    for capability in ['canonical-computational-projects','shared-project-variables','linked-computational-objects','computational-provenance','append-only-project-history','portable-computational-exports','cross-platform-handoff-packets']:
        assert capability in s['capabilities']
    assert s['automaticExecutionAuthorized'] is False
    assert s['automaticDeviceProgrammingAuthorized'] is False
    assert s['remoteShellAuthorized'] is False


def test_project_build_links_shared_variables_and_objects():
    r = build_project(ProjectBuildRequest(project=sample_project()))
    assert r['ok'] is True
    assert r['project']['variableCount'] == 2
    assert r['project']['objectCount'] == 2
    assert r['project']['studioCounts']['mathematics'] == 1
    assert r['project']['studioCounts']['graph-mathematics'] == 1
    assert len(r['projectHash']) == 64


def test_project_build_reports_missing_variable_reference():
    p = sample_project()
    p.objects[0].variableInputs.append('missing')
    r = build_project(ProjectBuildRequest(project=p))
    assert r['ok'] is False
    assert any(i['code'] == 'missing-variable' for i in r['project']['integrityIssues'])


def test_project_build_reports_missing_object_dependency():
    p = sample_project()
    p.objects[1].dependencyObjectIds = ['does-not-exist']
    r = build_project(ProjectBuildRequest(project=p))
    assert r['ok'] is False
    assert any(i['code'] == 'missing-object-dependency' for i in r['project']['integrityIssues'])


def test_shared_variable_override_is_deterministic():
    r = resolve_variables(VariableSetRequest(variables=[SharedVariable(name='x', value=1)], overrides={'x': 3}))
    assert r['ok'] is True
    assert r['result']['variables'][0]['value'] == 3
    assert r['result']['variables'][0]['overridden'] is True
    assert len(r['variableSetHash']) == 64


def test_locked_shared_variable_refuses_override():
    r = resolve_variables(VariableSetRequest(variables=[SharedVariable(name='x', value=1, locked=True)], overrides={'x': 3}))
    assert r['ok'] is False
    assert r['result']['variables'][0]['value'] == 1
    assert r['result']['lockedOverrideAttempts'] == ['x']


def test_variable_names_are_restricted_identifiers():
    with pytest.raises(ValueError):
        SharedVariable(name='x;import os', value=1)


def test_link_graph_topological_order_for_acyclic_project():
    p = sample_project()
    r = build_link_graph(LinkGraphRequest(objects=p.objects, links=[ObjectLink(fromObjectId='math-model', toObjectId='graph-view', relation='feeds', variableNames=['a'])]))
    assert r['ok'] is True
    assert r['result']['cycleDetected'] is False
    assert r['result']['topologicalOrder'] == ['math-model', 'graph-view']
    assert len(r['graphHash']) == 64


def test_link_graph_detects_cycle():
    p = sample_project()
    r = build_link_graph(LinkGraphRequest(objects=p.objects, links=[ObjectLink(fromObjectId='math-model', toObjectId='graph-view'), ObjectLink(fromObjectId='graph-view', toObjectId='math-model')]))
    assert r['ok'] is False
    assert r['result']['cycleDetected'] is True
    assert set(r['result']['cycleObjectIds']) == {'math-model','graph-view'}


def test_provenance_builds_hash_chain():
    p = sample_project()
    r = build_provenance(ProvenanceRequest(projectId=p.projectId, projectHash='abc', objects=p.objects, operations=[
        ProvenanceOperation(objectId='math-model', action='created', method='CAS'),
        ProvenanceOperation(objectId='graph-view', action='derived', inputs=['math-model'], method='graph render'),
    ], sources=[{'sourceId':'source-1','title':'Example source'}]))
    assert r['ok'] is True
    ops = r['result']['operations']
    assert ops[1]['parentHash'] == ops[0]['operationHash']
    assert r['result']['chainHeadHash'] == ops[-1]['operationHash']
    assert len(r['provenanceHash']) == 64


def test_history_is_append_only_hash_chain():
    r = build_history(HistoryRequest(projectId='study-one', baseProjectHash='basehash', events=[
        HistoryEvent(action='created', summary='Initial project'),
        HistoryEvent(action='updated', objectId='math-model', summary='Changed a'),
    ]))
    events = r['result']['events']
    assert events[0]['revision'] == 1 and events[1]['revision'] == 2
    assert events[1]['parentHash'] == events[0]['eventHash']
    assert r['result']['appendOnlyModel'] is True


def test_export_can_strip_payloads_and_metadata():
    p = sample_project()
    p.metadata = {'privateNote': 'not included'}
    p.objects[0].metadata = {'note':'x'}
    r = build_export(ExportRequest(project=p, includePayloads=False, includeMetadata=False, format='manifest'))
    assert r['ok'] is True
    assert r['result']['project']['metadata'] == {}
    assert all(obj['payload'] == {} and obj['metadata'] == {} for obj in r['result']['project']['objects'])
    assert r['result']['automaticPublicationAuthorized'] is False


def test_handoff_selects_requested_objects_and_requires_confirmation():
    p = sample_project()
    r = build_handoff(HandoffRequest(project=p, targetSurface='lab', objectIds=['graph-view'], purpose='continue-analysis'))
    assert r['ok'] is True
    assert r['result']['objectIds'] == ['graph-view']
    assert r['result']['targetSurface'] == 'lab'
    assert r['result']['requiresTargetImportConfirmation'] is True
    assert r['result']['automaticRemoteActionAuthorized'] is False


def test_handoff_reports_missing_object():
    r = build_handoff(HandoffRequest(project=sample_project(), targetSurface='decision-studio', objectIds=['missing']))
    assert r['ok'] is False
    assert r['result']['missingObjectIds'] == ['missing']


def test_payload_rejects_unsupported_python_objects():
    with pytest.raises(ValueError):
        build_project(ProjectBuildRequest(project=ProjectInput(projectId='x', objects=[ComputationalObject(objectId='o', kind='x', payload={'bad': {1,2,3}})])))
