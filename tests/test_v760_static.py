from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v760_release_identity_router_compose():
    assert 'APP_VERSION = "8.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.11.0"' in main
    assert 'from app.v760 import router as v760_router' in main and 'app.include_router(v760_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.11.0' in compose and "d.get('version')=='8.11.0'" in compose


def test_v760_engineering_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v760.py').read_text()
    for literal in ('/engineering/manifest','/engineering/catalog','/engineering/analyze','/engineering/validate','/engineering/system/run','/engineering/workspace-binding/plan','/integration/core/engineering-lineage/plan','/v760/status','sc.research.computation-analysis-execution-lineage.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    assert 'licensedEngineeringCertificationAuthorized' in src and 'codeComplianceCertificationAuthorized' in src and 'physicalSafetyCertificationAuthorized' in src


def test_v760_wordpress_identity_and_status_surface():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.11.0' in main and "define('SCWB_VERSION', '8.11.0')" in main
    assert 'includes/scwb-v760-engineering-systems-runtime.php' in main and 'SCWB_DIR' not in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v760-engineering-systems-runtime.php').read_text()
    assert '/v760/status' in inc and 'sc_workbench_engineering_systems_status' in inc and '/engineering-systems/status' in inc


def test_v760_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'engineering-systems-runtime' in cap and 'engineeringSystemsRuntime' in cap
    assert (ROOT/'RELEASE_NOTES_7.6.0_ENGINEERING_SYSTEMS_RUNTIME.md').exists()
    assert (ROOT/'V760_ENGINEERING_SYSTEMS_MAP.md').exists()
    assert (ROOT/'workbench-v7.6.0.env.example').exists()
