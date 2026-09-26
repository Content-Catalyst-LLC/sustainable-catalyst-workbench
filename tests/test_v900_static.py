from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v900_release_identity_and_routes():
    assert 'APP_VERSION = "9.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.3.0"' in main and 'from app.v900 import router as v900_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.3.0' in compose and "d.get('version')=='9.3.0'" in compose and '127.0.0.1:8088:8088' in compose

def test_v900_artifacts_and_capability_registry():
    for p in ['backend/app/v900.py','backend/tests/test_unified_scientific_study_composer_v900.py','RELEASE_NOTES_9.0.0_UNIFIED_SCIENTIFIC_STUDY_COMPOSER.md','V900_UNIFIED_SCIENTIFIC_STUDY_COMPOSER_MAP.md','docs/V900_UNIFIED_SCIENTIFIC_STUDY_COMPOSER.md','scripts/test_v900_release.sh','deploy/contabo/upgrade_workbench_backend_v9_0_0_contabo.sh','installers/apply_and_push_workbench_v9_0_0_macos.sh','wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v900-unified-scientific-study-composer.php','workbench-v9.0.0.env.example']:
        assert (ROOT/p).exists(),p
    caps=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('unifiedScientificStudyComposer','scientificStudyStageReadiness','scientificStudyContentAddressedRecords','scientificStudyAnalysisSnapshotBinding','scientificStudyPublicationPackageBinding','scientificStudyCorePlanning'):
        assert flag in caps

def test_v900_wordpress_and_boundary_contract():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.3.0' in main and "define('SCWB_VERSION', '9.3.0')" in main and 'SCWB_DIR' not in main and 'scwb-v900-unified-scientific-study-composer.php' in main
    src=(ROOT/'backend/app/v900.py').read_text()
    for literal in ('/study-composer/manifest','/study-composer/source-catalog/{project_key}','/study-composer/compose','/study-composer/studies','/integration/core/study-composer/plan','/v900/status'):
        assert literal in src
    for boundary in ('stageReadinessIsScientificValidity','automaticHypothesisAcceptance','automaticFindingGeneration','automaticPreferredModelSelection','automaticCausalInference','automaticStatisticalSignificanceInference','automaticPublication','automaticCoreDispatch','platformCoreGovernanceReplaced'):
        assert boundary in src

def test_v900_deployer_and_installer_are_hardened():
    deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_0_0_contabo.sh').read_text(); assert '127.0.0.1:8088' in deploy and '127.0.0.1:8000' not in deploy and 'rsync -a --checksum' in deploy and '__pycache__' in deploy
    installer=(ROOT/'installers/apply_and_push_workbench_v9_0_0_macos.sh').read_text(); assert 'rsync -a --checksum' in installer and '__pycache__' in installer and 'APP_VERSION' in installer
