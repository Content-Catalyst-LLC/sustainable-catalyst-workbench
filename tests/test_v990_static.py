from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v990_identity_and_registration():
    assert 'APP_VERSION = "9.12.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.12.0"' in main and 'from app.v990 import router as v990_router' in main
    assert 'sustainable-catalyst-workbench:9.12.0' in (ROOT/'compose.yml').read_text()

def test_v990_backend_contract_surface():
    t=(ROOT/'backend/app/v990.py').read_text()
    for s in ('/research-package-exchange/manifest','/research-package-exchange/source-catalog/{project_key}','/research-package-exchange/packages','/research-package-exchange/import/validate','/research-package-exchange/import/stage','/research-package-exchange/imports/{target_project_key}','/integration/core/research-package-exchange/plan','/v990/status'): assert s in t
    for s in ('automaticNativeObjectOverwrite','automaticImportedObjectActivation','automaticScientificValidityInference','automaticEvidencePromotion','automaticCoreDispatch','archiveExecutionAllowed'): assert s in t

def test_v990_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v990-research-package-exchange-portability.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_research_package_exchange'" in t and "add_shortcode('sc_workbench_research_package_exchange_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.12.0' in main and "define('SCWB_VERSION', '9.12.0');" in main and 'scwb-v990-research-package-exchange-portability.php' in main

def test_v990_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_9_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_9_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.9.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.9.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.9.0_RESEARCH_PACKAGE_EXCHANGE_PORTABILITY.md').exists()
    assert (ROOT/'V990_RESEARCH_PACKAGE_EXCHANGE_PORTABILITY_MAP.md').exists()
    assert (ROOT/'workbench-v9.9.0.env.example').exists()

def test_v990_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('researchPackageExchangePortability','researchPackageContentAddressedExport','researchPackageZipArchiveExport','researchPackageIntegrityVerification','researchPackageDependencyInventory','researchPackageCompatibilityAssessment','researchPackageImportStaging','researchPackageCorePlanning'): assert s in t
