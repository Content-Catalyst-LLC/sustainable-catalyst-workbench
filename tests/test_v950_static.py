from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v950_identity_and_registration():
    assert 'APP_VERSION = "9.7.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.7.0"' in main and 'from app.v950 import router as v950_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.7.0' in compose and "d.get('version')=='9.7.0'" in compose

def test_v950_contract():
    s=(ROOT/'backend/app/v950.py').read_text()
    for k in ('researcherAuthoredCalibrationProblems','campaignCandidateObjectiveScoring','boundedParameterEstimation','weightedLeastSquaresCalibration','robustHuberCalibration','identifiabilityDiagnostics','approximateParameterIntervals','platformCoreCalibrationPlanning'): assert k in s
    for k in ('automaticModelValidityInference','automaticScientificAcceptance','automaticPreferredModelSelection','automaticCausalInference','automaticPriorSelection','automaticJobExecution','automaticCoreDispatch'): assert k in s

def test_v950_routes():
    s=(ROOT/'backend/app/v950.py').read_text()
    for p in ('/model-calibration/manifest','/model-calibration/source-catalog/{project_key}','/model-calibration/compose','/model-calibration/estimate','/model-calibration/calibrations','/model-calibration/analysis-plan','/integration/core/model-calibration/plan','/v950/status'): assert p in s

def test_v950_wordpress():
    plugin=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v950-model-calibration-parameter-estimation.php').read_text()
    assert 'Version: 9.7.0' in plugin and "define('SCWB_VERSION', '9.7.0')" in plugin and 'scwb-v950-model-calibration-parameter-estimation.php' in plugin
    assert "add_shortcode('sc_workbench_model_calibration'" in inc and "add_shortcode('sc_workbench_model_calibration_status'" in inc

def test_v950_deployment_and_installer_hardening():
    dep=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_5_0_contabo.sh').read_text(); inst=(ROOT/'installers/apply_and_push_workbench_v9_5_0_macos.sh').read_text()
    assert 'rsync -a --checksum' in dep and '127.0.0.1:8088' in dep and 'sustainable-catalyst-workbench:9.5.0' in dep and 'APP_VERSION = "9.5.0"' in dep
    assert 'rsync -a --checksum' in inst and "r.APP_VERSION=='9.5.0'" in inst and '__pycache__' in inst and '.pytest_cache' in inst
