from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_router_and_compose():
    assert 'APP_VERSION = "9.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main = (ROOT/'backend/app/main.py').read_text()
    assert 'version="9.11.0"' in main
    assert 'from app.v6140 import router as v6140_router' in main
    compose = (ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:9.11.0' in compose
    assert "d.get('version')=='9.11.0'" in compose


def test_core_certification_contract_and_boundaries_present():
    src = (ROOT/'backend/app/v6140.py').read_text()
    for marker in (
        'sc.research.platform-integration-certification.v1',
        'deterministic-local-conformance-report',
        'certificationMeansRuntimeContractConformanceOnly',
        'automaticCoreDispatchAuthorized',
        'automaticCorePersistenceAuthorized',
        'scientificValidityCertificationAuthorized',
        'productQualityCertificationAuthorized',
        'productRankingAuthorized',
        'reproducibilityInferenceAuthorized',
        'truthDeterminationAuthorized',
    ):
        assert marker in src


def test_wordpress_identity_bootstrap_and_no_scwb_dir_regression():
    main = (ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.11.0' in main
    assert "define('SCWB_VERSION', '9.11.0')" in main
    assert "require_once __DIR__ . '/includes/scwb-v6100-predictive-intelligence-runtime.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6110-forensic-quantitative-reconstruction.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6120-research-state-reproduction-snapshot.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6130-core-aware-experience.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6140-platform-integration-certification.php';" in main
    assert 'SCWB_DIR' not in main


def test_capabilities_and_release_artifacts_declared():
    v640=(ROOT/'backend/app/v640.py').read_text()
    assert '"platformIntegrationCertification": True' in v640
    assert 'platform-core-integration-certification' in v640
    for rel in (
        'RELEASE_NOTES_6.14.0_PLATFORM_INTEGRATION_CERTIFICATION.md',
        'docs/V6140_PLATFORM_INTEGRATION_CERTIFICATION.md',
        'docs/V6140_CORE_CERTIFICATION_FIELD_MAP.md',
        'workbench-v7.3.0.env.example',
    ):
        assert (ROOT/rel).exists(), rel
