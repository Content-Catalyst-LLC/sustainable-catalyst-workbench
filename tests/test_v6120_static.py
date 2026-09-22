from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_and_router_registration():
    assert 'APP_VERSION = "7.4.0"' in (ROOT/'backend/app/release.py').read_text()
    main = (ROOT/'backend/app/main.py').read_text()
    assert 'version="7.4.0"' in main
    assert 'from app.v6120 import router as v6120_router' in main
    compose = (ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:7.4.0' in compose
    assert "d.get('version')=='7.4.0'" in compose


def test_core_contracts_are_exact():
    src = (ROOT/'backend/app/v6120.py').read_text()
    for contract in (
        'sc.research.project-state-versioning-reproducibility.v1',
        'sc.research.reproducible-package.v1',
        'sc.research.cross-product-context-handoff.v1',
    ):
        assert contract in src


def test_state_restore_and_replay_guardrails_present():
    src = (ROOT/'backend/app/v6120.py').read_text()
    for marker in (
        'automaticStateRestoreAuthorized',
        'automaticExecutionReplayAuthorized',
        'coreInfersReproducibility',
        'workbenchCertifiesReproducibility',
        'truthDeterminationAuthorized',
    ):
        assert marker in src


def test_wordpress_identity_safe_bootstrap_and_module_include():
    main = (ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 7.4.0' in main
    assert "define('SCWB_VERSION', '7.4.0')" in main
    assert "require_once __DIR__ . '/includes/scwb-v6100-predictive-intelligence-runtime.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6110-forensic-quantitative-reconstruction.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6120-research-state-reproduction-snapshot.php';" in main
    assert 'SCWB_DIR' not in main


def test_release_artifacts_declared():
    for rel in (
        'RELEASE_NOTES_6.12.0_RESEARCH_STATE_REPRODUCTION_SNAPSHOT_INTEGRATION.md',
        'docs/V6120_RESEARCH_STATE_REPRODUCTION_SNAPSHOT_INTEGRATION.md',
        'docs/V6120_CORE_RESEARCH_STATE_FIELD_MAP.md',
        'workbench-v6.12.0.env.example',
    ):
        assert (ROOT/rel).exists(), rel
