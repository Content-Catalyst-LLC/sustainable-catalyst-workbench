from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v7100_identity_router_compose():
    assert 'APP_VERSION = "9.6.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.6.0"' in main
    assert 'from app.v7100 import router as v7100_router' in main and 'app.include_router(v7100_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.6.0' in compose and "d.get('version')=='9.6.0'" in compose

def test_v7100_surfaces_boundaries():
    src=(ROOT/'backend/app/v7100.py').read_text()
    for literal in ('/notebooks/manifest','/notebooks/validate','/notebooks/run','/notebooks/run/validate','/notebooks/replay/plan','/notebooks/workflow-graph/plan','/integration/core/notebook-workflow/plan','/v7100/status','sc.research.workflow-orchestration.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('hiddenInterpreterStateAllowed','automaticCoreDispatchAuthorized','scientificValidityCertified'): assert boundary in src

def test_v7100_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.6.0' in main and "define('SCWB_VERSION', '9.6.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v7100-interactive-computational-notebook.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7100-interactive-computational-notebook.php').read_text()
    assert '/v7100/status' in inc and 'sc_workbench_notebook_runtime_status' in inc and '/notebook-runtime/status' in inc

def test_v7100_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'interactive-computational-notebook-runtime' in cap and 'interactiveComputationalNotebookRuntime' in cap
    assert (ROOT/'RELEASE_NOTES_7.10.0_INTERACTIVE_COMPUTATIONAL_NOTEBOOK_RUNTIME.md').exists()
    assert (ROOT/'V7100_INTERACTIVE_COMPUTATIONAL_NOTEBOOK_MAP.md').exists()
    assert (ROOT/'workbench-v7.10.0.env.example').exists()
