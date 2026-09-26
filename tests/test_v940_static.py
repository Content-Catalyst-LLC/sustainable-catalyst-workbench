from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_v940_identity_and_registration():
    assert 'APP_VERSION = "9.4.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.4.0"' in main and 'from app.v940 import router as v940_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.4.0' in compose and "d.get('version')=='9.4.0'" in compose
def test_v940_contract():
    s=(ROOT/'backend/app/v940.py').read_text()
    for k in ('monteCarloSampling','latinHypercubeSampling','sobolSampling','campaignResultSensitivityAnalysis','standardizedRegressionSensitivity','contentAddressedStudies','platformCoreUncertaintyPlanning'): assert k in s
    for k in ('automaticDistributionSelection','automaticParameterImportanceRanking','automaticCausalImportanceInference','automaticConvergenceDeclaration','automaticScientificValidityInference','automaticCoreDispatch'): assert k in s
def test_v940_routes():
    s=(ROOT/'backend/app/v940.py').read_text()
    for p in ('/uncertainty-sensitivity/manifest','/uncertainty-sensitivity/source-catalog/{project_key}','/uncertainty-sensitivity/compose','/uncertainty-sensitivity/studies','/uncertainty-sensitivity/analyze','/integration/core/uncertainty-sensitivity/plan','/v940/status'): assert p in s
def test_v940_wordpress():
    plugin=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v940-uncertainty-sensitivity-study-composer.php').read_text()
    assert 'Version: 9.4.0' in plugin and "define('SCWB_VERSION', '9.4.0')" in plugin and 'scwb-v940-uncertainty-sensitivity-study-composer.php' in plugin
    assert "add_shortcode('sc_workbench_uncertainty_sensitivity_study'" in inc and "add_shortcode('sc_workbench_uncertainty_sensitivity_status'" in inc
def test_v940_deployment_and_installer_hardening():
    dep=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_4_0_contabo.sh').read_text(); inst=(ROOT/'installers/apply_and_push_workbench_v9_4_0_macos.sh').read_text()
    assert 'rsync -a --checksum' in dep and '127.0.0.1:8088' in dep and 'sustainable-catalyst-workbench:9.4.0' in dep and 'APP_VERSION = "9.4.0"' in dep
    assert 'rsync -a --checksum' in inst and "r.APP_VERSION=='9.4.0'" in inst and '__pycache__' in inst
