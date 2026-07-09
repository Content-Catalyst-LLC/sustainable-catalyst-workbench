from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_engineering_calculator_catalog_available():
    res = client.get('/engineering/calculators')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    ids = [item['id'] for item in data['calculators']]
    assert 'normal-stress' in ids
    assert 'beam-deflection' in ids
    assert 'pump-power' in ids


def test_normal_stress_calculator():
    res = client.post('/engineering/calculate', json={
        'calculator_id': 'normal-stress',
        'inputs': {'force_N': 1000, 'area_m2': 0.02}
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['values']['results']['stress_Pa'] == 50000
    assert data['graphs']


def test_beam_deflection_calculator_returns_mm():
    res = client.post('/engineering/calculate', json={
        'calculator_id': 'beam-deflection',
        'inputs': {'beam_case':'simply_supported_center','load_N':500,'length_m':2,'elastic_modulus_GPa':200,'second_moment_m4':0.000008}
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['values']['results']['deflection_mm'] > 0
    assert data['values']['calculator_id'] == 'beam-deflection'


def test_rc_calculator_response():
    res = client.post('/engineering/calculate', json={
        'calculator_id': 'rc-time-constant',
        'inputs': {'resistance_ohm': 10000, 'capacitance_F': 0.000001, 'initial_voltage_V': 0, 'final_voltage_V': 5, 'time_s': 0.01}
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert round(data['values']['results']['tau_s'], 6) == 0.01
    assert data['values']['results']['voltage_at_time_V'] > 3.0


def test_unknown_engineering_calculator_fails_cleanly():
    res = client.post('/engineering/calculate', json={'calculator_id':'missing-tool','inputs':{}})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is False
    assert 'available_calculators' in data
