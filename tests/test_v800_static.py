from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v800_identity_router_compose():
    assert 'APP_VERSION = "9.5.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.5.0"' in main
    assert 'from app.v800 import router as v800_router' in main and 'app.include_router(v800_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.5.0' in compose and "d.get('version')=='9.5.0'" in compose


def test_v800_surfaces_boundaries():
    src=(ROOT/'backend/app/v800.py').read_text()
    for literal in ('/research-environment/manifest','/research-environment/build','/research-environment/validate','/research-environment/surface/plan','/research-environment/session/plan','/research-environment/snapshot/plan','/integration/core/research-environment/plan','/v800/status','sc.research.unified-research-scientific-investigation-runtime.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('automaticExecutionAuthorized','automaticReplayAuthorized','automaticCoreDispatchAuthorized','scientificValidityCertified','engineeringSafetyCertified'):
        assert boundary in src


def test_v800_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.5.0' in main and "define('SCWB_VERSION', '9.5.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v800-unified-computational-research-environment.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v800-unified-computational-research-environment.php').read_text()
    assert '/v800/status' in inc and 'sc_workbench_research_environment_status' in inc and '/research-environment/status' in inc


def test_v800_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'unified-computational-research-environment' in cap and 'unifiedComputationalResearchEnvironment' in cap
    assert (ROOT/'RELEASE_NOTES_8.0.0_UNIFIED_COMPUTATIONAL_RESEARCH_ENVIRONMENT.md').exists()
    assert (ROOT/'V800_UNIFIED_COMPUTATIONAL_RESEARCH_ENVIRONMENT_MAP.md').exists()
    assert (ROOT/'workbench-v8.0.0.env.example').exists()
