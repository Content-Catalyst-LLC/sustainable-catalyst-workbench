from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v6100_release_identity_and_routes():
    assert 'APP_VERSION = "8.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v6100 import router as v6100_router' in main and 'app.include_router(v6100_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.3.0' in compose and "d.get('version')=='8.3.0'" in compose

def test_v6100_core_predictive_contracts_present():
    t=(ROOT/'backend/app/v6100.py').read_text()
    for s in ('sc.predictive.model.v1','sc.predictive.probabilistic-forecast.v1','sc.predictive.calibration-study.v1','sc.visual-runtime.predictive-intelligence.v1','/v1/predictive-intelligence/models','/v1/visual-runtime/predictive'):
        assert s in t
    assert 'automaticCoreDispatchAuthorized' in t and 'coreExecutesPredictiveModels' in t

def test_v6100_wordpress_bridge():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench'; main=(p/'sustainable-catalyst-workbench.php').read_text(); inc=(p/'includes/scwb-v6100-predictive-intelligence-runtime.php').read_text()
    assert 'Version: 8.3.0' in main and "define('SCWB_VERSION', '8.3.0')" in main
    assert 'scwb-v6100-predictive-intelligence-runtime.php' in main
    assert '/v6100/status' in inc and 'sc_workbench_predictive_intelligence_status' in inc

def test_v6100_release_assets_exist():
    for rel in ('RELEASE_NOTES_6.10.0_PREDICTIVE_INTELLIGENCE_RUNTIME.md','BUILD_VALIDATION_6.10.0.txt','WORKBENCH_V6100_TERMINAL_COMMANDS.txt','docs/V6100_PREDICTIVE_INTELLIGENCE_RUNTIME.md','docs/V6100_CORE_PREDICTIVE_FIELD_MAP.md','scripts/test_v6100_release.sh','deploy/contabo/upgrade_workbench_backend_v6_10_0_contabo.sh','workbench-v6.10.0.env.example'):
        assert (ROOT/rel).exists(), rel
