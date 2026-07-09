from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _run(calculator_id, inputs=None):
    res = client.post('/engineering/calculate', json={'calculator_id': calculator_id, 'inputs': inputs or {}})
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data.get('graphs')
    return data


def test_v170_catalog_contains_advanced_domains():
    data = client.get('/engineering/calculators').json()
    ids = {item['id'] for item in data['calculators']}
    for cid in [
        'econometrics-simple-ols',
        'psychometrics-cronbach-alpha',
        'computational-biology-michaelis-menten',
        'computational-chemistry-arrhenius',
        'computational-physics-harmonic-oscillator',
        'architecture-floor-area-efficiency',
        'infrastructure-rational-runoff',
        'pattern-recognition-cosine-similarity',
        'astrophysics-kepler-orbit',
    ]:
        assert cid in ids


def test_econometrics_ols_runs():
    data = _run('econometrics-simple-ols', {'x_values':'1,2,3,4', 'y_values':'2,4,6,8'})
    assert abs(data['values']['results']['slope_beta1'] - 2.0) < 1e-6


def test_psychometrics_alpha_runs():
    data = _run('psychometrics-cronbach-alpha')
    assert 'cronbach_alpha' in data['values']['results']


def test_biology_chemistry_physics_architecture_infrastructure_pattern_astrophysics_run():
    checks = {
        'computational-biology-logistic-growth': 'N_t',
        'computational-chemistry-nernst': 'cell_potential_V',
        'computational-physics-projectile-motion': 'range_m',
        'architecture-daylight-aperture': 'effective_aperture',
        'infrastructure-peak-water-demand': 'peak_demand_m3_day',
        'pattern-recognition-harmonic-centroid': 'spectral_centroid_hz',
        'astrophysics-luminosity-flux': 'flux_W_m2',
    }
    for cid, key in checks.items():
        data = _run(cid)
        assert key in data['values']['results']
