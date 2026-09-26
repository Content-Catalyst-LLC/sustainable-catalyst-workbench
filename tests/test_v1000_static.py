from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v1000_identity_and_registration():
    assert 'APP_VERSION = "10.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.0.0"' in main and 'from app.v1000 import router as v1000_router' in main
    assert 'sustainable-catalyst-workbench:10.0.0' in (ROOT/'compose.yml').read_text()

def test_v1000_backend_contract_surface():
    t=(ROOT/'backend/app/v1000.py').read_text()
    for s in ('/ai-engineering/manifest','/ai-engineering/runtime-contracts','/ai-engineering/compose','/ai-engineering/experiments','/ai-engineering/execution-plan','/integration/core/ai-engineering/plan','/v1000/status'): assert s in t
    for s in ('scientificAIEngineeringRuntimeFoundation','contentAddressedAIExperimentSpecifications','deterministicSeedConfiguration','resourceBudgetContracts','neutralAIExecutionPlanning','platformCoreAIExperimentPlanning'): assert s in t
    for s in ('automaticModelDownload','automaticTrainingExecution','automaticInferenceExecution','hiddenAgentExecutionAuthorized','automaticModelSelection','scientificValidityInferred','automaticCoreDispatch','governedCoreObjectCreated'): assert s in t

def test_v1000_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1000-scientific-ai-engineering-runtime-foundation.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_ai_engineering'" in t and "add_shortcode('sc_workbench_ai_engineering_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.0.0' in main and "define('SCWB_VERSION', '10.0.0');" in main and 'scwb-v1000-scientific-ai-engineering-runtime-foundation.php' in main

def test_v1000_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v10_0_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v10_0_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='10.0.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='10.0.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_10.0.0_SCIENTIFIC_AI_ENGINEERING_RUNTIME_FOUNDATION.md').exists()
    assert (ROOT/'V1000_SCIENTIFIC_AI_ENGINEERING_RUNTIME_FOUNDATION_MAP.md').exists()
    assert (ROOT/'workbench-v10.0.0.env.example').exists()

def test_v1000_capability_registry_and_execution_console():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('scientificAIEngineeringRuntimeFoundation','aiEngineeringContentAddressedExperiments','aiEngineeringModelProviderContracts','aiEngineeringDatasetLineage','aiEngineeringDeterministicConfiguration','aiEngineeringResourceBudgets','aiEngineeringNeutralExecutionPlanning','aiEngineeringCorePlanning'): assert s in t
    assert '"ai-engineering"' in (ROOT/'backend/app/v840.py').read_text()
