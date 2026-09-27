from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v1040_identity_and_registration():
    assert 'APP_VERSION = "10.4.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.4.0"' in main and 'from app.v1040 import router as v1040_router' in main
    assert 'sustainable-catalyst-workbench:10.4.0' in (ROOT/'compose.yml').read_text()

def test_v1040_backend_contract_surface():
    t=(ROOT/'backend/app/v1040.py').read_text()
    for s in ('/ai-optimization/manifest','/ai-optimization/searches/compose','/ai-optimization/searches','/ai-optimization/trials/generate','/ai-optimization/execution-plan','/ai-optimization/trial-results','/ai-optimization/analyze','/integration/core/ai-optimization/plan','/v1040/status'): assert s in t
    for s in ('gridSearch','seededRandomSearch','latinHypercubeSearch','externalBayesianOptimizerContract','deterministicTrialManifests','immutableTrialResults','objectiveDiagnostics'): assert s in t
    for s in ('automaticTrainingExecution','automaticExternalOptimizerCall','automaticPreferredModelPromotion','automaticProductionApproval','scientificValidityInferred'): assert s in t

def test_v1040_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1040-hyperparameter-optimization-search-engine.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_ai_optimization'" in t and "add_shortcode('sc_workbench_ai_optimization_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.4.0' in main and "define('SCWB_VERSION', '10.4.0');" in main and 'scwb-v1040-hyperparameter-optimization-search-engine.php' in main

def test_v1040_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v10_4_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v10_4_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='10.4.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='10.4.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_10.4.0_HYPERPARAMETER_OPTIMIZATION_SEARCH_ENGINE.md').exists()
    assert (ROOT/'V1040_HYPERPARAMETER_OPTIMIZATION_SEARCH_ENGINE_MAP.md').exists()
    assert (ROOT/'workbench-v10.4.0.env.example').exists()

def test_v1040_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('aiOptimizationSearchEngine','aiOptimizationTrainingRunBinding','aiOptimizationBenchmarkObjectiveBinding','aiOptimizationTypedSearchSpaces','aiOptimizationDeterministicTrials','aiOptimizationSearchBudgets','aiOptimizationImmutableTrialResults','aiOptimizationObjectiveDiagnostics','aiOptimizationCorePlanning'): assert s in t
