from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _normal_stress_result():
    res = client.post('/engineering/calculate', json={
        'calculator_id': 'normal-stress',
        'inputs': {'force_N': 1000, 'area_m2': 0.02}
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    return data


def test_calculation_report_endpoint_generates_markdown_and_html():
    source = _normal_stress_result()
    res = client.post('/reports/calculation', json={
        'source_result': source,
        'include_graphs': True,
        'report_type': 'engineering_calculation_note'
    })
    assert res.status_code == 200
    report = res.json()
    assert report['ok'] is True
    assert report['version'] == '1.5.0'
    assert report['report_title'] == 'Normal stress from axial force and area'
    assert 'markdown' in report['formats']
    assert 'html' in report['formats']
    assert 'σ = F / A' in report['formats']['markdown']
    assert 'force' in report['formats']['markdown'].lower()
    assert '<html' in report['formats']['html'].lower()
    assert report['filename_base'].startswith('normal-stress')


def test_calculation_report_endpoint_handles_minimal_result():
    res = client.post('/reports/calculation', json={
        'source_result': {
            'ok': True,
            'tool': 'Example Calculator',
            'summary': 'Example summary',
            'values': {'inputs': {'x': 2}, 'results': {'y': 4}, 'formula': 'y = x^2'},
            'warnings': ['Check inputs.']
        },
        'include_graphs': False
    })
    assert res.status_code == 200
    report = res.json()
    assert report['ok'] is True
    assert 'Example summary' in report['formats']['markdown']
    assert 'y = x^2' in report['formats']['markdown']
    assert 'Check inputs.' in report['formats']['markdown']
