from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v680_release_identity_and_routes():
    assert 'APP_VERSION = "8.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v680 import router as v680_router' in main and 'app.include_router(v680_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.0.0' in compose and "d.get('version')=='8.0.0'" in compose

def test_v680_bridge_contract_and_core_paths_present():
    t=(ROOT/'backend/app/v680.py').read_text()
    for s in ('scenario-compute-input-manifest-v1','/v1/scenario-compute/requests/{request_id}/attempts','/v1/uncertainty-compute/sampling/design','/v1/uncertainty-compute/sensitivity/sobol','/v1/uncertainty-compute/sensitivity/morris'):
        assert s in t
    assert 'arbitraryCodeFromCoreAuthorized' in t and 'False' in t

def test_v680_wordpress_bridge_and_shortcode():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench'; main=(p/'sustainable-catalyst-workbench.php').read_text(); inc=(p/'includes/scwb-v680-scenario-uncertainty-runtime.php').read_text()
    assert 'Version: 8.0.0' in main and "define('SCWB_VERSION', '8.0.0')" in main
    assert 'scwb-v680-scenario-uncertainty-runtime.php' in main
    assert '/v680/status' in inc and 'sc_workbench_scenario_uncertainty_status' in inc

def test_v680_release_assets_exist():
    for rel in ('RELEASE_NOTES_6.8.0_SCENARIO_UNCERTAINTY_COMPUTE_RUNTIME.md','BUILD_VALIDATION_6.8.0.txt','WORKBENCH_V680_TERMINAL_COMMANDS.txt','docs/V680_SCENARIO_UNCERTAINTY_COMPUTE_RUNTIME.md','scripts/test_v680_release.sh','deploy/contabo/upgrade_workbench_backend_v6_8_0_contabo.sh','workbench-v6.8.0.env.example'):
        assert (ROOT/rel).exists(), rel
