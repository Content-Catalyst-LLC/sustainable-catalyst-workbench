from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v1010_identity_and_registration():
    assert 'APP_VERSION = "10.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.3.0"' in main and 'from app.v1010 import router as v1010_router' in main
    assert 'sustainable-catalyst-workbench:10.3.0' in (ROOT/'compose.yml').read_text()

def test_v1010_backend_contract_surface():
    t=(ROOT/'backend/app/v1010.py').read_text()
    for s in ('/ai-registry/manifest','/ai-registry/models','/ai-registry/datasets','/ai-registry/search','/ai-registry/experiment-binding-plan','/ai-registry/experiment-bindings','/integration/core/ai-registry/plan','/v1010/status'): assert s in t
    for s in ('immutableVersionedModelRecords','immutableVersionedDatasetRecords','contentAddressedRegistryRecords','licenseAndProvenanceMetadata','compatibilityMetadata','neutralEvaluationState','registrySearchAndListing','immutableAIExperimentRegistryBindings','versionCollisionProtection'): assert s in t
    for s in ('automaticModelDownload','automaticDatasetDownload','automaticRegistryReplacement','automaticLatestVersionSelection','automaticPreferredModelSelection','automaticPreferredDatasetSelection','automaticExperimentMutation','scientificValidityInferred','automaticCoreDispatch'): assert s in t

def test_v1010_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1010-model-dataset-registry.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_model_dataset_registry'" in t and "add_shortcode('sc_workbench_model_dataset_registry_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.3.0' in main and "define('SCWB_VERSION', '10.3.0');" in main and 'scwb-v1010-model-dataset-registry.php' in main

def test_v1010_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v10_1_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v10_1_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='10.1.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='10.1.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_10.1.0_MODEL_DATASET_REGISTRY.md').exists()
    assert (ROOT/'V1010_MODEL_DATASET_REGISTRY_MAP.md').exists()
    assert (ROOT/'workbench-v10.1.0.env.example').exists()

def test_v1010_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('modelDatasetRegistry','aiRegistryImmutableModelVersions','aiRegistryImmutableDatasetVersions','aiRegistryContentAddressedRecords','aiRegistryLicenseProvenance','aiRegistryCompatibilityMetadata','aiRegistryNeutralEvaluationState','aiRegistrySearch','aiRegistryExperimentBindings','aiRegistryCorePlanning'): assert s in t
