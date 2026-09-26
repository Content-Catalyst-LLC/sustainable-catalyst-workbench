from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v920_backend_registration_and_identity():
    assert 'APP_VERSION = "9.7.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v920 import router as v920_router' in main and 'version="9.7.0"' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.7.0' in compose and "d.get('version')=='9.7.0'" in compose

def test_v920_campaign_contract_and_boundaries():
    s=(ROOT/'backend/app/v920.py').read_text()
    for x in ('deterministicCartesianParameterSweeps','resumableCampaignState','executionConsoleJobMaterialization','neutralAnalysisHandoffPlanning','platformCoreCampaignPlanning'):
        assert x in s
    for x in ('automaticJobExecution','automaticBestResultSelection','automaticScientificValidityInference','automaticCoreDispatch'):
        assert x in s

def test_v920_routes_exist():
    s=(ROOT/'backend/app/v920.py').read_text()
    for path in ('/campaign-manager/manifest','/campaign-manager/compose','/campaign-manager/campaigns','/campaign-manager/materialize','/campaign-manager/refresh','/campaign-manager/analysis-plan','/integration/core/campaign-manager/plan','/v920/status'):
        assert path in s

def test_v920_wordpress_surface_and_version():
    plugin=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v920-batch-experiment-computational-campaign-manager.php').read_text()
    assert 'Version: 9.7.0' in plugin and "define('SCWB_VERSION', '9.7.0')" in plugin
    assert 'scwb-v920-batch-experiment-computational-campaign-manager.php' in plugin
    assert "add_shortcode('sc_workbench_batch_campaign_manager'" in inc
    assert "add_shortcode('sc_workbench_batch_campaign_manager_status'" in inc

def test_v920_capabilities_registered():
    s=(ROOT/'backend/app/v640.py').read_text()
    for key in ('batchExperimentComputationalCampaignManager','computationalCampaignDeterministicSweeps','computationalCampaignResumableState','computationalCampaignExecutionMaterialization','computationalCampaignAnalysisPlanning','computationalCampaignCorePlanning'):
        assert f'"{key}": True' in s
