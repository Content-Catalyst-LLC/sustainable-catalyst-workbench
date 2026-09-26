from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v930_current_release_identity_and_registration():
    assert 'APP_VERSION = "9.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.3.0"' in main and 'from app.v930 import router as v930_router' in main and 'app.include_router(v930_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.3.0' in compose and "d.get('version')=='9.3.0'" in compose and '127.0.0.1:8088:8088' in compose

def test_v930_statistical_contract_and_boundaries():
    s=(ROOT/'backend/app/v930.py').read_text()
    for key in ('descriptiveStatistics','confidenceIntervals','distributionDiagnostics','normalityDiagnostics','varianceDiagnostics','explicitHypothesisTestStatistics','correlationAnalysis','linearRegressionDiagnostics','contentAddressedAnalysisRecords','platformCoreStatisticalAnalysisPlanning'):
        assert key in s
    for key in ('automaticMethodSelection','automaticSignificanceDecision','automaticHypothesisAcceptanceOrRejection','automaticCausalInference','automaticScientificValidityInference','automaticPreferredModelSelection','automaticResearchInterpretation','automaticCoreDispatch'):
        assert key in s

def test_v930_routes_exist():
    s=(ROOT/'backend/app/v930.py').read_text()
    for path in ('/statistical-workspace/manifest','/statistical-workspace/source-catalog/{project_key}','/statistical-workspace/analyze','/statistical-workspace/analyses','/integration/core/statistical-workspace/plan','/v930/status'):
        assert path in s

def test_v930_capabilities_registered():
    s=(ROOT/'backend/app/v640.py').read_text()
    for key in ('statisticalAnalysisDiagnosticWorkspace','statisticalAnalysisDescriptiveStatistics','statisticalAnalysisDiagnostics','statisticalAnalysisHypothesisStatistics','statisticalAnalysisRegressionDiagnostics','statisticalAnalysisContentAddressedRecords','statisticalAnalysisCorePlanning'):
        assert f'"{key}": True' in s

def test_v930_wordpress_surface_and_identity():
    plugin=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v930-statistical-analysis-diagnostic-workspace.php').read_text()
    assert 'Version: 9.3.0' in plugin and "define('SCWB_VERSION', '9.3.0')" in plugin and 'scwb-v930-statistical-analysis-diagnostic-workspace.php' in plugin
    assert "add_shortcode('sc_workbench_statistical_analysis_workspace'" in inc and "add_shortcode('sc_workbench_statistical_analysis_status'" in inc

def test_v930_deployment_and_installer_hardening():
    dep=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_3_0_contabo.sh').read_text(); inst=(ROOT/'installers/apply_and_push_workbench_v9_3_0_macos.sh').read_text()
    assert 'rsync -a --checksum' in dep and '127.0.0.1:8088' in dep and 'sustainable-catalyst-workbench:9.3.0' in dep and "APP_VERSION = \"9.3.0\"" in dep
    assert 'rsync -a --checksum' in inst and "r.APP_VERSION=='9.3.0'" in inst and '__pycache__' in inst
