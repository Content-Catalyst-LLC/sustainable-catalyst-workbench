import os
from fastapi.testclient import TestClient
from app.main import app
from app.v760 import SCHEMA, RESULT, CORE_COMPUTATION_LINEAGE_CONTRACT


def client(): return TestClient(app)


def test_manifest_catalog_status_and_capabilities():
    c=client(); m=c.get('/engineering/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='8.7.0' and len(d['analysisKeys'])==9
    assert {'mechanical','thermal','fluids','civil-infrastructure','electrical','controls-mechatronics','energy-systems'}.issubset(set(d['domains']))
    cat=c.get('/engineering/catalog').json(); assert cat['analysisCount']==9
    s=c.get('/v760/status').json(); assert s['ok'] and s['engineeringSystemBundles'] and s['licensedEngineeringCertification'] is False
    caps=c.get('/capabilities').json(); assert caps['version']=='8.7.0' and caps['coreIntegration']['engineeringSystemsRuntime'] is True


def test_mechanical_axial_member_and_execution_object():
    c=client(); r=c.post('/engineering/analyze',json={'analysisKey':'mechanical.axial-member','inputs':{'force_n':10000,'area_m2':0.001,'length_m':2,'elongation_m':0.001,'yield_strength_pa':250e6}})
    assert r.status_code==200,r.text; d=r.json(); assert d['schema']==RESULT and abs(d['result']['stressMPa']-10)<1e-9
    assert d['result']['factorOfSafetyToYield']==25
    assert d['executionObject']['objectKind']=='single_execution' and d['engineeringRunHash']


def test_beam_and_thermal_formulas():
    c=client(); beam=c.post('/engineering/analyze',json={'analysisKey':'mechanical.simply-supported-beam','inputs':{'span_m':2,'elastic_modulus_pa':200e9,'second_moment_m4':1e-6,'center_point_load_n':1000}}).json()
    assert abs(beam['result']['maximumMomentNm']-500)<1e-9 and beam['result']['maximumDeflectionM']>0
    cond=c.post('/engineering/analyze',json={'analysisKey':'thermal.conduction','inputs':{'conductivity_w_mk':10,'area_m2':2,'thickness_m':0.1,'hot_temp_c':100,'cold_temp_c':20}}).json()
    assert abs(cond['result']['heatRateW']-16000)<1e-9
    conv=c.post('/engineering/analyze',json={'analysisKey':'thermal.convection','inputs':{'coefficient_w_m2k':25,'area_m2':2,'surface_temp_c':60,'fluid_temp_c':20}}).json()
    assert abs(conv['result']['heatRateW']-2000)<1e-9


def test_pipe_flow_and_civil_capacity_are_bounded():
    c=client(); pipe=c.post('/engineering/analyze',json={'analysisKey':'fluids.pipe-flow','inputs':{'diameter_m':0.05,'length_m':10,'density_kg_m3':998,'dynamic_viscosity_pa_s':0.001,'volumetric_flow_m3_s':0.001,'roughness_m':1e-5}})
    assert pipe.status_code==200,pipe.text; p=pipe.json()['result']; assert p['reynoldsNumber']>0 and p['pressureDropPa']>=0 and p['flowRegime'] in {'laminar','transition','turbulent','no-flow'}
    civil=c.post('/engineering/analyze',json={'analysisKey':'civil.axial-capacity','inputs':{'axial_load_n':100000,'area_m2':0.01,'allowable_stress_pa':20e6}}).json()
    assert civil['result']['utilization']==0.5 and civil['result']['declaredCapacityStatus']=='within-declared-capacity' and civil['result']['codeComplianceDetermined'] is False


def test_electrical_dc_and_actuator_adapter():
    c=client(); dc=c.post('/engineering/analyze',json={'analysisKey':'electrical.dc-circuit','inputs':{'voltage_v':12,'resistance_ohm':6,'duration_s':60}})
    assert dc.status_code==200,dc.text; r=dc.json()['result']; assert r['currentA']==2 and r['powerW']==24 and r['energyJ']==1440
    act=c.post('/engineering/analyze',json={'analysisKey':'controls.actuator-sizing','inputs':{'actuator_type':'dc-motor','mass_kg':5,'radius_m':0.05,'acceleration':1,'friction':0.1,'safety_factor':2,'target_rpm':100,'voltage':24,'efficiency':0.8}})
    assert act.status_code==200,act.text; assert act.json()['result']['torqueNm']>0 and act.json()['domain']=='controls-mechatronics'


def test_validation_detects_tampering():
    c=client(); d=c.post('/engineering/analyze',json={'analysisKey':'electrical.dc-circuit','inputs':{'voltage_v':10,'current_a':2}}).json()
    assert c.post('/engineering/validate',json=d).json()['valid'] is True
    d['result']['powerW']=999
    bad=c.post('/engineering/validate',json=d).json(); assert bad['valid'] is False and 'engineering-run-hash-mismatch' in bad['reasons']


def test_system_bundle_runs_multiple_domains_without_hidden_coupling():
    c=client(); r=c.post('/engineering/system/run',json={'systemKey':'demo','analyses':[{'itemKey':'electrical','analysisKey':'electrical.dc-circuit','inputs':{'voltage_v':12,'current_a':2}},{'itemKey':'thermal','analysisKey':'thermal.convection','inputs':{'coefficient_w_m2k':10,'area_m2':1,'surface_temp_c':50,'fluid_temp_c':20}}]})
    assert r.status_code==200,r.text; d=r.json(); assert d['analysisCount']==2 and d['automaticCrossDomainCouplingPerformed'] is False and d['hiddenOutputSubstitutionPerformed'] is False


def _workspace(c):
    r=c.post('/data-workspace/build',json={'workspaceKey':'eng-ws','variables':[],'parameterSets':[{'parameterSetKey':'beam','parameters':[{'parameterKey':'load','value':1500,'unit':'N'}]}],'datasets':[],'assumptions':[]}); assert r.status_code==200,r.text; return r.json()


def test_workspace_binding_materializes_parameter_without_execution():
    c=client(); ws=_workspace(c)
    r=c.post('/engineering/workspace-binding/plan',json={'workspace':ws,'analysisKey':'mechanical.simply-supported-beam','inputs':{'span_m':2,'elastic_modulus_pa':200e9,'second_moment_m4':1e-6,'center_point_load_n':1000},'bindings':[{'sourceKind':'parameter','parameterSetKey':'beam','sourceKey':'load','targetField':'center_point_load_n'}]})
    assert r.status_code==200,r.text; d=r.json(); assert d['engineeringRequest']['inputs']['center_point_load_n']==1500 and d['executionPerformed'] is False


def test_core_lineage_plan_is_two_phase_and_token_bounded(monkeypatch):
    c=client(); result=c.post('/engineering/analyze',json={'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.01}}).json()
    first=c.post('/integration/core/engineering-lineage/plan',json={'engineeringResult':result}); assert first.status_code==200,first.text
    d=first.json(); assert d['coreComputationLineageContract']==CORE_COMPUTATION_LINEAGE_CONTRACT and d['coreExecutionIdMustComeFromCore'] is True and d['outputRegistrations']==[]
    second=c.post('/integration/core/engineering-lineage/plan',json={'engineeringResult':result,'coreExecutionId':'core-exec-760'}); assert second.status_code==200 and second.json()['outputRegistrations'][0]['path'].endswith('/outputs')
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret760')
    assert c.post('/integration/core/engineering-lineage/plan',json={'engineeringResult':result}).status_code==401
    ok=c.post('/integration/core/engineering-lineage/plan',headers={'X-SC-Service-Token':'secret760'},json={'engineeringResult':result}); assert ok.status_code==200 and ok.json()['automaticCoreDispatchAuthorized'] is False


def test_invalid_engineering_input_is_rejected():
    c=client(); r=c.post('/engineering/analyze',json={'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0}})
    assert r.status_code==422
