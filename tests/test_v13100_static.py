import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_router():
    assert 'APP_VERSION = "13.10.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.10.0"' in m
    assert "from app.v13100 import router as v13100_router" in m
    assert "app.include_router(v13100_router)" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v13100.py").read_text()
    for x in ["intentPlanningReady","explicitPlanObject","deterministicAlternatives",
              "preExecutionValidation","postExecutionExplanation",
              "calculationObjectRemainsResultAuthority"]:
        assert x in p

def test_frontend_planning():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["intentPlan","planNaturalLanguage","applyIntentPlan",
              "explainLastExecution","Intent-to-calculation plan",
              "plan-interpret","plan-apply"]:
        assert x in p

def test_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.10.0"
    assert d["interface"]=="intent-to-calculation-planning-explainable-execution"

def test_client():
    p=(ROOT/"standalone-client/intent-planning.js").read_text()
    assert "IntentPlanningClient" in p
    assert "validate(plan)" in p
    assert "explain(plan,calculationObject)" in p

def test_wp_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.10.0" in p
    assert "scwb-v13100-intent-planning-explainable-execution.php" in p
