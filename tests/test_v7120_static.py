from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v7120_identity_router_compose():
    assert 'APP_VERSION = "8.7.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.7.0"' in main
    assert 'from app.v7120 import router as v7120_router' in main and 'app.include_router(v7120_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.7.0' in compose and "d.get('version')=='8.7.0'" in compose


def test_v7120_surfaces_boundaries():
    src=(ROOT/'backend/app/v7120.py').read_text()
    for literal in ('/repro-package/manifest','/repro-package/build','/repro-package/assemble','/repro-package/validate','/repro-package/replay/plan','/repro-package/export/plan','/integration/core/repro-package/plan','/v7120/status','sc.research.reproducible-package.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('automaticReplayAuthorized','automaticCoreDispatchAuthorized','reproducibilityCertified','scientificValidityCertified','engineeringSafetyCertified'):
        assert boundary in src


def test_v7120_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.7.0' in main and "define('SCWB_VERSION', '8.7.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v7120-reproducible-experiment-engineering-package.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7120-reproducible-experiment-engineering-package.php').read_text()
    assert '/v7120/status' in inc and 'sc_workbench_reproducible_package_status' in inc and '/reproducible-package/status' in inc


def test_v7120_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'reproducible-experiment-engineering-package' in cap and 'reproducibleExperimentEngineeringPackage' in cap
    assert (ROOT/'RELEASE_NOTES_7.12.0_REPRODUCIBLE_EXPERIMENT_ENGINEERING_PACKAGE.md').exists()
    assert (ROOT/'V7120_REPRODUCIBLE_EXPERIMENT_ENGINEERING_PACKAGE_MAP.md').exists()
    assert (ROOT/'workbench-v7.12.0.env.example').exists()
