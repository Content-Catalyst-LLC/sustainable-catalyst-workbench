from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_status():
    d=client.get('/v13110/status').json(); assert d['version']=='13.11.0'; assert d['domainCalculatorRegistryReady'] is True; assert d['templateCount']>=7; assert all(d['checks'].values())

def test_registry_and_domains():
    reg=client.get('/standalone/v1/domain-calculators/registry').json()['registry']; assert reg['totalTemplateCount']>=7 and reg['registryHash']
    domains={d['id'] for d in reg['domains']}; assert {'mathematics','physics','electrical-engineering','energy','sustainability','finance','statistics'} <= domains
    filtered=client.get('/standalone/v1/domain-calculators/registry?domain=energy').json()['registry']; assert filtered['templateCount']==1; assert filtered['templates'][0]['id']=='energy.capacity-factor'

def test_template_instantiation():
    t=client.get('/standalone/v1/domain-calculators/templates/physics.kinetic-energy').json()['template']; assert t['templateExecutesMathematics'] is False and t['templateHash']
    inst=client.post('/standalone/v1/domain-calculators/templates/physics.kinetic-energy/instantiate',json={'values':{'mass':2,'velocity':3},'metadata':{'source':'test'}}).json()['instance']
    assert inst['calculationRequest']['calculation']['operation']=='evaluate'; assert inst['calculationRequest']['requireVerification'] is True; assert inst['calculationRequest']['requireProvenance'] is True; assert inst['policy']['canonicalCalculatorRequired'] is True; assert inst['instanceHash']

def test_constraints_and_unknown_parameters():
    assert client.post('/standalone/v1/domain-calculators/templates/statistics.z-score/instantiate',json={'values':{'standard_deviation':0}}).status_code==422
    assert client.post('/standalone/v1/domain-calculators/templates/mathematics.circle-area/instantiate',json={'values':{'radius':2,'bogus':3}}).status_code==422

def test_contract_preserves_planning():
    c=client.get('/standalone/v1/domain-calculators/contract').json()['domainCalculators']; assert c['features']['v13100PlanningPreserved'] is True; assert c['features']['canonicalExecutionOnly'] is True; assert c['features']['deterministicInstantiation'] is True
