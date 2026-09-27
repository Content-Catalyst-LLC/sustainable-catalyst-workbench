from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v1020_identity_and_registration():
    assert 'APP_VERSION = "10.2.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.2.0"' in main and 'from app.v1020 import router as v1020_router' in main
    assert 'sustainable-catalyst-workbench:10.2.0' in (ROOT/'compose.yml').read_text()

def test_v1020_backend_contract_surface():
    t=(ROOT/'backend/app/v1020.py').read_text()
    for s in ('/ai-training/manifest','/ai-training/compose','/ai-training/runs','/ai-training/execution-plan','/ai-training/events','/ai-training/results','/ai-training/derived-model-plan','/integration/core/ai-training/plan','/v1020/status'): assert s in t
    for s in ('registryBackedTrainingRuns','fullAndParameterEfficientFineTuning','loraAndQloraConfiguration','deterministicTrainingManifests','trainingResourceBudgets','checkpointLineage','appendOnlyTrainingProgressEvents','immutableTrainingResults','derivedModelRegistrationPlanning'): assert s in t
    for s in ('automaticTrainingExecution','arbitraryCodeExecution','automaticRegistryPromotion','automaticCheckpointPromotion','automaticPreferredModelSelection','scientificValidityInferred','automaticCoreDispatch'): assert s in t

def test_v1020_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1020-training-finetuning-experiment-runtime.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_ai_training'" in t and "add_shortcode('sc_workbench_ai_training_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.2.0' in main and "define('SCWB_VERSION', '10.2.0');" in main and 'scwb-v1020-training-finetuning-experiment-runtime.php' in main

def test_v1020_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v10_2_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v10_2_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='10.2.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='10.2.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_10.2.0_TRAINING_FINE_TUNING_EXPERIMENT_RUNTIME.md').exists()
    assert (ROOT/'V1020_TRAINING_FINE_TUNING_EXPERIMENT_RUNTIME_MAP.md').exists()
    assert (ROOT/'workbench-v10.2.0.env.example').exists()

def test_v1020_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('trainingFineTuningExperimentRuntime','aiTrainingRegistryBackedRuns','aiTrainingFineTuningMethods','aiTrainingDeterministicManifests','aiTrainingResourceBudgets','aiTrainingCheckpointLineage','aiTrainingAppendOnlyProgress','aiTrainingImmutableResults','aiTrainingDerivedModelPlanning','aiTrainingCorePlanning'): assert s in t
