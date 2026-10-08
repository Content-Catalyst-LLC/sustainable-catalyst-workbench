import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_release_router():
    assert 'APP_VERSION = "14.0.0"' in (ROOT/'backend/app/release.py').read_text()
    m=(ROOT/'backend/app/main.py').read_text()
    assert '# Static release identity marker: version="14.0.0"' in m
    assert 'from app.v1400 import router as v1400_router' in m
    assert 'app.include_router(v1400_router)' in m


def test_backend_contract():
    p=(ROOT/'backend/app/v1400.py').read_text()
    for x in ['computationalWorkflowComposerReady','multiStepComposition','cycleDetection','deterministicTopologicalOrdering','${stepId.result}','workflowIsNotMathAuthority']:
        assert x in p


def test_frontend_workflow_surface():
    p=(ROOT/'standalone-app/app-shell.js').read_text()
    for x in ['workflowDraft','workflowView','composeWorkflow','executeWorkflow','data-workflow-add-step']:
        assert x in p


def test_manifest():
    d=json.loads((ROOT/'standalone-app/version.json').read_text())
    assert d['version']=='14.0.0'
    assert d['interface']=='computational-workflow-composer'


def test_client():
    p=(ROOT/'standalone-client/workflows.js').read_text()
    assert 'ComputationalWorkflowClient' in p
    assert 'execute(workflow)' in p


def test_wp_optional():
    p=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 14.0.0' in p
    assert 'scwb-v1400-computational-workflow-composer.php' in p
