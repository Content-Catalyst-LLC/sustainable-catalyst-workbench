from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v9120_identity_and_registration():
    assert 'APP_VERSION = "10.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.0.0"' in main and 'from app.v9120 import router as v9120_router' in main
    assert 'sustainable-catalyst-workbench:10.0.0' in (ROOT/'compose.yml').read_text()

def test_v9120_backend_contract_surface():
    t=(ROOT/'backend/app/v9120.py').read_text()
    for s in ('/v9-production-certification/manifest','/v9-production-certification/run','/v9-production-certification/certifications','/integration/core/v9-production-certification/plan','/v9120/status'): assert s in t
    for s in ('canonical-release-identity','runtime-health-readiness','retained-v9-milestones','research-package-portability','platform-wide-handoff','research-study-certification'): assert s in t
    for s in ('productionCertificationIsScientificValidity','scientificCorrectnessCertified','automaticRemediation','automaticCoreDispatch','governedCoreObjectCreated'): assert s in t

def test_v9120_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v9120-workbench-v9-production-certification.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_v9_production_certification'" in t and "add_shortcode('sc_workbench_v9_production_certification_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.0.0' in main and "define('SCWB_VERSION', '10.0.0');" in main and 'scwb-v9120-workbench-v9-production-certification.php' in main

def test_v9120_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_12_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_12_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.12.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.12.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.12.0_WORKBENCH_V9_PRODUCTION_CERTIFICATION.md').exists()
    assert (ROOT/'V9120_WORKBENCH_V9_PRODUCTION_CERTIFICATION_MAP.md').exists()
    assert (ROOT/'workbench-v9.12.0.env.example').exists()

def test_v9120_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('workbenchV9ProductionCertification','v9ProductionCertificationReleaseIdentity','v9ProductionCertificationRuntimeReadiness','v9ProductionCertificationPersistenceReadiness','v9ProductionCertificationRetainedMilestones','v9ProductionCertificationPortabilityHandoff','v9ProductionCertificationDeploymentInvariants','v9ProductionCertificationContentAddressedRecords','v9ProductionCertificationCorePlanning'): assert s in t
