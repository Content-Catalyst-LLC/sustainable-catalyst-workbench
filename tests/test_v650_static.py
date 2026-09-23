from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v650_release_identity_and_routes_are_registered():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    compose = (ROOT / "compose.yml").read_text()
    assert 'APP_VERSION = "6.5.0"' in release or 'APP_VERSION = "6.6.0"' in release or 'APP_VERSION = "6.7.0"' in release or 'APP_VERSION = "6.8.0"' in release or 'APP_VERSION = "8.4.0"' in release
    assert 'from app.v650 import router as v650_router' in main
    assert 'app.include_router(v650_router)' in main
    assert 'sustainable-catalyst-workbench:6.5.0' in compose or 'sustainable-catalyst-workbench:6.6.0' in compose or 'sustainable-catalyst-workbench:6.7.0' in compose or 'sustainable-catalyst-workbench:6.8.0' in compose or 'sustainable-catalyst-workbench:8.4.0' in compose
    assert "d.get('version')=='6.5.0'" in compose or "d.get('version')=='6.6.0'" in compose or "d.get('version')=='6.7.0'" in compose or "d.get('version')=='6.8.0'" in compose or "d.get('version')=='8.4.0'" in compose


def test_v650_adapter_declares_core_contract_and_non_dispatch_boundary():
    source = (ROOT / "backend/app/v650.py").read_text()
    assert 'sc.research.unified-runtime-contract.v1' not in source or 'CORE_RUNTIME_CONTRACT' in source
    assert 'automaticDispatchAuthorized' in source
    assert 'automaticCorePersistenceAuthorized' in source
    assert '/integration/core/runtime-contract/manifest' in source
    assert '/integration/core/runtime-contract/exchanges/consume' in source
    assert '/integration/core/runtime-contract/invocations/build' in source
    assert '/integration/core/runtime-contract/results/build' in source


def test_wordpress_release_identity_and_adapter_bridge():
    plugin = ROOT / "wordpress-plugin/sustainable-catalyst-workbench"
    main = (plugin / "sustainable-catalyst-workbench.php").read_text()
    include = (plugin / "includes/scwb-v650-unified-runtime-contract-adapter.php").read_text()
    assert 'Version: 6.5.0' in main or 'Version: 6.6.0' in main or 'Version: 6.7.0' in main or 'Version: 6.8.0' in main or 'Version: 8.4.0' in main
    assert "define('SCWB_VERSION', '6.5.0')" in main or "define('SCWB_VERSION', '6.6.0')" in main or "define('SCWB_VERSION', '6.7.0')" in main or "define('SCWB_VERSION', '6.8.0')" in main or "define('SCWB_VERSION', '8.4.0')" in main
    assert 'scwb-v650-unified-runtime-contract-adapter.php' in main
    assert '/v650/status' in include
    assert 'sc_workbench_runtime_contract_status' in include
