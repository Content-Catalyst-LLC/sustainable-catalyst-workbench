import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_router():
    assert 'APP_VERSION = "13.9.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.9.0"' in m
    assert "from app.v1390 import router as v1390_router" in m
    assert "app.include_router(v1390_router)" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1390.py").read_text()
    for x in ["naturalLanguageFoundationReady","directExecutionDisabled",
              "canonicalCalculationAuthorityPreserved","unrecognized-natural-language-intent",
              "/standalone/v1/natural-language/interpret"]:
        assert x in p

def test_frontend_nl_input():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["naturalLanguagePlan","interpretNaturalLanguage","applyNaturalLanguagePlan",
              "Natural-language computation","nl-interpret","nl-apply-plan"]:
        assert x in p

def test_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.9.0"
    assert d["interface"]=="natural-language-computation-foundation"

def test_client():
    p=(ROOT/"standalone-client/natural-language-computation.js").read_text()
    assert "NaturalLanguageComputationClient" in p
    assert "interpret(text)" in p

def test_wp_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.9.0" in p
    assert "scwb-v1390-natural-language-computation-foundation.php" in p
