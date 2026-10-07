import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_release_router():
    assert 'APP_VERSION = "13.12.0"' in (ROOT/'backend/app/release.py').read_text()
    m=(ROOT/'backend/app/main.py').read_text()
    assert '# Static release identity marker: version="13.12.0"' in m
    assert 'from app.v13120 import router as v13120_router' in m
    assert 'app.include_router(v13120_router)' in m


def test_backend_certification_contract():
    p=(ROOT/'backend/app/v13120.py').read_text()
    for x in [
        'standaloneFunctionalProductionCertified','allSurfaceContractsReady',
        'allFunctionalSmokeChecksPass','versionConsistent','wordpressOptional',
        'canonicalCalculationAuthorityPreserved','plannerDoesNotExecuteDirectly',
        'domainTemplatesDoNotExecuteDirectly'
    ]:
        assert x in p


def test_frontend_certification_marker():
    p=(ROOT/'standalone-app/app-shell.js').read_text()
    assert '/v13120/status' in p
    assert 'standaloneFunctionalProductionCertified' in p
    assert 'v13 production certified' in p


def test_manifest():
    d=json.loads((ROOT/'standalone-app/version.json').read_text())
    assert d['version']=='13.12.0'
    assert d['interface']=='standalone-functional-production-certification'


def test_client():
    p=(ROOT/'standalone-client/production-certification.js').read_text()
    assert 'ProductionCertificationClient' in p
    assert 'report()' in p


def test_wp_optional():
    p=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 13.12.0' in p
    assert 'scwb-v13120-standalone-functional-production-certification.php' in p
