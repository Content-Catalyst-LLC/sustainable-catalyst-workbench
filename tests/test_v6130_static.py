from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_and_router_registration():
    assert 'APP_VERSION = "8.7.0"' in (ROOT/'backend/app/release.py').read_text()
    main = (ROOT/'backend/app/main.py').read_text()
    assert 'version="8.7.0"' in main
    assert 'from app.v6130 import router as v6130_router' in main
    compose = (ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:8.7.0' in compose
    assert "d.get('version')=='8.7.0'" in compose


def test_experience_contract_and_boundaries_present():
    src = (ROOT/'backend/app/v6130.py').read_text()
    for marker in (
        'sc-workbench-core-aware-experience/1.0',
        'single-core-aware-context-view',
        'core-id-presence-and-gap-detection',
        'automaticCoreDispatchAuthorized',
        'automaticCorePersistenceAuthorized',
        'automaticStateRestoreAuthorized',
        'automaticExecutionReplayAuthorized',
        'truthDeterminationAuthorized',
    ):
        assert marker in src


def test_wordpress_identity_safe_bootstrap_and_module_include():
    main = (ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.7.0' in main
    assert "define('SCWB_VERSION', '8.7.0')" in main
    assert "require_once __DIR__ . '/includes/scwb-v6100-predictive-intelligence-runtime.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6110-forensic-quantitative-reconstruction.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6120-research-state-reproduction-snapshot.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6130-core-aware-experience.php';" in main
    assert 'SCWB_DIR' not in main


def test_release_artifacts_declared():
    for rel in (
        'RELEASE_NOTES_6.13.0_CORE_AWARE_WORKBENCH_EXPERIENCE.md',
        'docs/V6130_CORE_AWARE_WORKBENCH_EXPERIENCE.md',
        'docs/V6130_CORE_AWARE_EXPERIENCE_FIELD_MAP.md',
        'workbench-v6.13.0.env.example',
    ):
        assert (ROOT/rel).exists(), rel
