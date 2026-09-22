import os
from fastapi.testclient import TestClient
from app.main import app
from app.v730 import SCHEMA, CORE_COMPUTATION_LINEAGE_CONTRACT


def client(): return TestClient(app)


def workspace_payload():
    return {
      'workspaceKey':'energy-model','title':'Energy Model','projectRef':'project:v730','coreSessionId':'session:v730',
      'datasets':[{'datasetKey':'weather','columns':[{'name':'hour','dataType':'integer','role':'index'},{'name':'load_kw','unit':'kW','role':'target'}],'rows':[{'hour':1,'load_kw':3.2},{'hour':2,'load_kw':4.1}]}],
      'variables':[{'variableKey':'base','symbol':'base','value':10,'unit':'kW'},{'variableKey':'factor','symbol':'factor','value':2},{'variableKey':'scaled','kind':'derived','expression':'base*factor','dependsOn':['base','factor'],'unit':'kW'}],
      'parameterSets':[{'parameterSetKey':'scenario','parameters':[{'parameterKey':'efficiency','value':0.9,'lowerBound':0,'upperBound':1},{'parameterKey':'years','value':20,'dataType':'integer'}]}],
      'assumptions':[{'assumptionKey':'constant-efficiency','statement':'Efficiency remains constant during the declared run.'}]
    }


def test_manifest_status_capabilities_current_identity():
    c=client(); m=c.get('/data-workspace/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='7.4.0' and d['contentAddressedDatasets'] if 'contentAddressedDatasets' in d else d['capabilities']['contentAddressedDatasets']
    s=c.get('/v730/status').json(); assert s['ok'] and s['version']=='7.4.0' and s['unitAware'] is True
    caps=c.get('/capabilities').json(); assert caps['version']=='7.4.0'; assert caps['coreIntegration']['datasetVariableParameterWorkspace'] is True


def test_workspace_build_is_content_addressed_and_derived_values_are_safe():
    c=client(); a=c.post('/data-workspace/build',json=workspace_payload()); b=c.post('/data-workspace/build',json=workspace_payload())
    assert a.status_code==200,a.text; x=a.json(); y=b.json(); assert x['workspaceHash']==y['workspaceHash'] and x['workspaceRef']==y['workspaceRef']
    assert x['datasets'][0]['rowCount']==2 and x['datasets'][0]['datasetRef'].startswith('sc://workbench/dataset/')
    scaled=next(v for v in x['variables'] if v['variableKey']=='scaled'); assert scaled['derivedValue']==20.0 and scaled['variableHash']
    assert x['counts']=={'datasets':1,'variables':3,'parameterSets':1,'parameters':2,'assumptions':1}


def test_unit_conversion_and_incompatible_units_rejected():
    c=client(); r=c.post('/data-workspace/units/convert',json={'value':1,'fromUnit':'kW','toUnit':'W'}); assert r.status_code==200 and r.json()['convertedValue']==1000.0
    bad=c.post('/data-workspace/units/convert',json={'value':1,'fromUnit':'kW','toUnit':'second'}); assert bad.status_code==422


def test_derived_expression_uses_restricted_parser_not_python_eval():
    c=client(); r=c.post('/data-workspace/derive',json={'expression':'a*b+2','values':{'a':3,'b':4}}); assert r.status_code==200 and r.json()['value']==14.0
    bad=c.post('/data-workspace/derive',json={'expression':'__import__("os")','values':{}}); assert bad.status_code==422


def built(c): return c.post('/data-workspace/build',json=workspace_payload()).json()


def test_execution_binding_plan_materializes_only_declared_scalar_bindings_and_dataset_refs():
    c=client(); ws=built(c); r=c.post('/data-workspace/execution-binding/plan',json={'workspace':ws,'operation':'electronics.resistor-network','payload':{'topology':'series','resistancesOhm':[10,20]},'bindings':[{'sourceKind':'parameter','parameterSetKey':'scenario','sourceKey':'efficiency','targetField':'sourceVoltageV'},{'sourceKind':'dataset','sourceKey':'weather'}],'requestKey':'bound-run'})
    assert r.status_code==200,r.text; d=r.json(); q=d['orchestratorRequest']; assert q['payload']['sourceVoltageV']==0.9
    assert len(q['datasetRefs'])==1 and q['metadata']['workspaceHash']==ws['workspaceHash']
    assert d['executionPerformed'] is False and d['automaticDispatchAuthorized'] is False


def test_workspace_integrity_tampering_is_rejected():
    c=client(); ws=built(c); ws['title']='tampered'; r=c.post('/data-workspace/execution-binding/plan',json={'workspace':ws,'operation':'math.compute'}); assert r.status_code==422


def test_core_lineage_plan_is_two_phase_exact_contract_and_non_dispatching():
    c=client(); ws=built(c)
    first=c.post('/integration/core/data-workspace/lineage/plan',json={'workspace':ws}); assert first.status_code==200,first.text
    a=first.json(); assert a['coreComputationLineageContract']==CORE_COMPUTATION_LINEAGE_CONTRACT and a['coreExecutionIdMustComeFromCore'] is True
    assert a['datasetInputRegistrations']==[] and a['parameterRegistrations']==[] and a['assumptionRegistrations']==[]
    second=c.post('/integration/core/data-workspace/lineage/plan',json={'workspace':ws,'coreExecutionId':'core-exec-730'}); assert second.status_code==200,second.text
    d=second.json(); assert d['datasetInputRegistrations'][0]['path']=='/v1/research/computation-lineage/executions/core-exec-730/inputs'
    assert d['datasetInputRegistrations'][0]['data']['input_type']=='dataset'
    assert len(d['parameterRegistrations'])==2 and d['assumptionRegistrations'][0]['data']['assumption_key']=='constant-efficiency'
    assert d['automaticCoreDispatchAuthorized'] is False and d['coreExecutesSpecialistWork'] is False


def test_core_route_token_boundary(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret730')
    c=client(); ws=built(c); denied=c.post('/integration/core/data-workspace/lineage/plan',json={'workspace':ws}); assert denied.status_code==401
    ok=c.post('/integration/core/data-workspace/lineage/plan',headers={'X-SC-Service-Token':'secret730'},json={'workspace':ws}); assert ok.status_code==200 and ok.json()['version']=='7.4.0'
