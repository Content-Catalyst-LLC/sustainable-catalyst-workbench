from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v7110_identity_router_compose():
    assert 'APP_VERSION = "9.2.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.2.0"' in main
    assert 'from app.v7110 import router as v7110_router' in main and 'app.include_router(v7110_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.2.0' in compose and "d.get('version')=='9.2.0'" in compose

def test_v7110_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v7110.py').read_text()
    for literal in ('/visual-workspace/manifest','/visual-workspace/build','/visual-workspace/validate','/visual-workspace/linked-state/apply','/visual-workspace/control/plan','/visual-workspace/notebook/project','/integration/core/visual-workspace/plan','/v7110/status','sc.visual-runtime.linked-views.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('controlsExecuteAutomatically','automaticCoreDispatchAuthorized','scientificValidityCertified'): assert boundary in src

def test_v7110_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.2.0' in main and "define('SCWB_VERSION', '9.2.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v7110-visual-scientific-computing-workspace.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7110-visual-scientific-computing-workspace.php').read_text()
    assert '/v7110/status' in inc and 'sc_workbench_visual_scientific_status' in inc and '/visual-scientific/status' in inc

def test_v7110_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'visual-scientific-computing-workspace' in cap and 'visualScientificComputingWorkspace' in cap
    assert (ROOT/'RELEASE_NOTES_7.11.0_VISUAL_SCIENTIFIC_COMPUTING_WORKSPACE.md').exists()
    assert (ROOT/'V7110_VISUAL_SCIENTIFIC_COMPUTING_WORKSPACE_MAP.md').exists()
    assert (ROOT/'workbench-v7.11.0.env.example').exists()
