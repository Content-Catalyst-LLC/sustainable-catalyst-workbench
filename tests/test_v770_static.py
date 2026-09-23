from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v770_identity_router_compose():
    assert 'APP_VERSION = "7.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="7.11.0"' in main
    assert 'from app.v770 import router as v770_router' in main and 'app.include_router(v770_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:7.11.0' in compose and "d.get('version')=='7.11.0'" in compose

def test_v770_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v770.py').read_text()
    for literal in ('/design-space/manifest','/design-space/evaluate','/design-space/explore','/design-space/pareto','/design-space/optimize','/design-space/workspace-binding/plan','/design-space/candidate-handoff/plan','/integration/core/design-space-lineage/plan','/v770/status','sc.research.computation-analysis-execution-lineage.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    assert 'automaticWinnerSelectionAuthorized' in src and 'engineeringSafetyCertificationAuthorized' in src and 'codeComplianceCertificationAuthorized' in src

def test_v770_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 7.11.0' in main and "define('SCWB_VERSION', '7.11.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v770-optimization-design-space.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v770-optimization-design-space.php').read_text()
    assert '/v770/status' in inc and 'sc_workbench_design_space_status' in inc and '/design-space/status' in inc

def test_v770_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'optimization-design-space-runtime' in cap and 'optimizationDesignSpaceRuntime' in cap
    assert (ROOT/'RELEASE_NOTES_7.7.0_OPTIMIZATION_DESIGN_SPACE_EXPLORATION.md').exists()
    assert (ROOT/'V770_OPTIMIZATION_DESIGN_SPACE_MAP.md').exists()
    assert (ROOT/'workbench-v7.7.0.env.example').exists()
