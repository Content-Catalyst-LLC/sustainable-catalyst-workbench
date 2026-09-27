from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v1030_identity_and_registration():
    assert 'APP_VERSION = "10.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.3.0"' in main and 'from app.v1030 import router as v1030_router' in main
    assert 'sustainable-catalyst-workbench:10.3.0' in (ROOT/'compose.yml').read_text()

def test_v1030_backend_contract_surface():
    t=(ROOT/'backend/app/v1030.py').read_text()
    for s in ('/ai-evaluation/manifest','/ai-evaluation/benchmarks/compose','/ai-evaluation/benchmarks','/ai-evaluation/execution-plan','/ai-evaluation/results','/ai-evaluation/compare','/integration/core/ai-evaluation/plan','/v1030/status'): assert s in t
    for s in ('registryBackedBenchmarkSuites','researcherDefinedMetrics','diagnosticSlices','immutableEvaluationResults','baselineRelativeRegressionDiagnostics','multiModelComparison'): assert s in t
    for s in ('automaticInferenceExecution','automaticCompositeRanking','automaticWinnerSelection','automaticPreferredModelPromotion','automaticProductionApproval','scientificValidityInferred'): assert s in t

def test_v1030_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1030-ai-evaluation-benchmark-workspace.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_ai_evaluation'" in t and "add_shortcode('sc_workbench_ai_evaluation_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.3.0' in main and "define('SCWB_VERSION', '10.3.0');" in main and 'scwb-v1030-ai-evaluation-benchmark-workspace.php' in main

def test_v1030_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v10_3_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v10_3_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='10.3.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='10.3.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_10.3.0_AI_EVALUATION_BENCHMARK_WORKSPACE.md').exists()
    assert (ROOT/'V1030_AI_EVALUATION_BENCHMARK_WORKSPACE_MAP.md').exists()
    assert (ROOT/'workbench-v10.3.0.env.example').exists()

def test_v1030_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('aiEvaluationBenchmarkWorkspace','aiEvaluationRegistryBackedBenchmarks','aiEvaluationResearcherDefinedMetrics','aiEvaluationDatasetBindings','aiEvaluationDiagnosticSlices','aiEvaluationDeterministicManifests','aiEvaluationImmutableResults','aiEvaluationRegressionDiagnostics','aiEvaluationMultiModelComparison','aiEvaluationCorePlanning'): assert s in t
