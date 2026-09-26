from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v8120_release_identity_and_routes():
    assert 'APP_VERSION = "9.12.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.12.0"' in main and 'from app.v8120 import router as v8120_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.12.0' in compose and "d.get('version')=='9.12.0'" in compose and '127.0.0.1:8088:8088' in compose

def test_v8120_artifacts_and_capability_registry():
    for p in ['backend/app/v8120.py','backend/tests/test_unified_workbench_production_certification_v8120.py','RELEASE_NOTES_8.12.0_UNIFIED_WORKBENCH_PRODUCTION_CERTIFICATION.md','V8120_UNIFIED_WORKBENCH_PRODUCTION_CERTIFICATION_MAP.md','docs/V8120_UNIFIED_WORKBENCH_PRODUCTION_CERTIFICATION.md','scripts/test_v8120_release.sh','deploy/contabo/upgrade_workbench_backend_v8_12_0_contabo.sh','installers/apply_and_push_workbench_v8_12_0_macos.sh','wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v8120-unified-production-certification.php','workbench-v8.12.0.env.example']:
        assert (ROOT/p).exists(),p
    caps=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('unifiedWorkbenchProductionCertification','productionCertificationReleaseIdentity','productionCertificationPersistenceReadiness','productionCertificationCoreCompatibility','productionCertificationPublicationHandoff','productionCertificationWordPressIntegrity','productionCertificationDeploymentInvariants'):
        assert flag in caps

def test_v8120_wordpress_and_boundary_contract():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.12.0' in main and "define('SCWB_VERSION', '9.12.0')" in main and 'SCWB_DIR' not in main
    assert 'scwb-v8120-unified-production-certification.php' in main
    src=(ROOT/'backend/app/v8120.py').read_text()
    for literal in ('/production-certification/manifest','/production-certification/run','/v8120/status'):
        assert literal in src
    for boundary in ('scientificCorrectnessCertified','evidenceValidityCertified','causalClaimsCertified','statisticalSignificanceCertified','automaticRemediationAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src

def test_v8120_deployer_uses_correct_workbench_port():
    deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v8_12_0_contabo.sh').read_text(); assert '127.0.0.1:8088' in deploy and '127.0.0.1:8000' not in deploy


def test_v8120_installer_uses_checksum_aware_rsync():
    installer=(ROOT/'installers/apply_and_push_workbench_v8_12_0_macos.sh').read_text(); assert 'rsync -a --checksum' in installer
