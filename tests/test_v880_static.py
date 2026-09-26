from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_v880_release_identity_and_routes():
 assert 'APP_VERSION = "9.8.0"' in (ROOT/'backend/app/release.py').read_text()
 main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.8.0"' in main and 'from app.v880 import router as v880_router' in main
 compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.8.0' in compose and "d.get('version')=='9.8.0'" in compose
def test_v880_artifacts_and_wp():
 for p in ['backend/app/v880.py','backend/tests/test_comparative_experiment_model_analysis_v880.py','RELEASE_NOTES_8.8.0_COMPARATIVE_EXPERIMENT_MODEL_ANALYSIS.md','V880_COMPARATIVE_EXPERIMENT_MODEL_ANALYSIS_MAP.md','docs/V880_COMPARATIVE_EXPERIMENT_MODEL_ANALYSIS.md','scripts/test_v880_release.sh','deploy/contabo/upgrade_workbench_backend_v8_8_0_contabo.sh','installers/apply_and_push_workbench_v8_8_0_macos.sh','wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v880-comparative-experiment-model-analysis.php']: assert (ROOT/p).exists(),p
 main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.8.0' in main and "define('SCWB_VERSION', '9.8.0')" in main and 'scwb-v880-comparative-experiment-model-analysis.php' in main and 'SCWB_DIR' not in main
def test_v880_neutrality_contract():
 s=(ROOT/'backend/app/v880.py').read_text(); assert 'automaticWinnerSelectionPerformed' in s and 'scientificValidityInferred' in s and 'pairwiseComparisons' in s and 'comparisonHash' in s
