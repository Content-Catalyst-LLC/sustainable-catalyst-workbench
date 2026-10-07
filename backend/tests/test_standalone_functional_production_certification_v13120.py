from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def test_status_certified():
    r=client.get('/v13120/status')
    assert r.status_code==200
    d=r.json()
    assert d['version']=='13.12.0'
    assert d['standaloneFunctionalProductionCertified'] is True
    assert all(d['checks'].values())


def test_report_surface_matrix_and_smoke():
    r=client.get('/standalone/v1/certification/v13/report')
    assert r.status_code==200
    c=r.json()['certification']
    assert c['certified'] is True
    expected={
        'calculator','project-research-sessions','graph-studio',
        'notebook-history-timeline','reproducibility-packages',
        'unified-workbench','natural-language','intent-planning','domain-calculators'
    }
    assert expected <= set(c['surfaceChecks'])
    assert all(c['surfaceChecks'].values())
    assert all(c['smokeChecks'].values())
    assert c['wordpressRequired'] is False
    assert c['productionTopology']['wordpressRole']=='optional compatibility/embed layer'


def test_certification_smoke_contains_lineage():
    c=client.get('/standalone/v1/certification/v13/report').json()['certification']
    assert c['smoke']['natural-language-interpretation']['interpretationHash']
    assert c['smoke']['intent-plan']['planHash']
    assert c['smoke']['intent-plan']['validationHash']
    assert c['smoke']['domain-template']['instanceHash']
    assert c['smoke']['domain-registry']['registryHash']
    assert c['certificationHash']
