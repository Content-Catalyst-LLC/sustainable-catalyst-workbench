import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_release_router():
    assert 'APP_VERSION = "13.11.0"' in (ROOT/'backend/app/release.py').read_text(); m=(ROOT/'backend/app/main.py').read_text(); assert '# Static release identity marker: version="13.11.0"' in m; assert 'from app.v13110 import router as v13110_router' in m; assert 'app.include_router(v13110_router)' in m
def test_backend_contract():
    p=(ROOT/'backend/app/v13110.py').read_text();
    for x in ['domainCalculatorRegistryReady','governedDomainRegistry','deterministicInstantiation','parameterLineage','canonicalExecutionOnly','energy.capacity-factor','sustainability.emissions-intensity']: assert x in p
def test_frontend_domain_templates():
    p=(ROOT/'standalone-app/app-shell.js').read_text();
    for x in ['domainCalculatorRegistry','loadDomainCalculatorRegistry','domainCalculatorPanel','instantiateDomainTemplate','applyDomainTemplate','domain-template-select']: assert x in p
def test_manifest():
    d=json.loads((ROOT/'standalone-app/version.json').read_text()); assert d['version']=='13.11.0'; assert d['interface']=='domain-calculator-registry-templates'
def test_client():
    p=(ROOT/'standalone-client/domain-calculators.js').read_text(); assert 'DomainCalculatorClient' in p; assert 'instantiate(id,values' in p
def test_wp_optional():
    p=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 13.11.0' in p; assert 'scwb-v13110-domain-calculator-registry-templates.php' in p
