from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "wordpress-plugin" / "sustainable-catalyst-workbench"


def test_v640_release_identity_and_files():
    main = (ROOT / "backend/app/main.py").read_text()
    release = (ROOT / "backend/app/release.py").read_text()
    plugin = (PLUGIN / "sustainable-catalyst-workbench.php").read_text()
    compose = (ROOT / "compose.yml").read_text()
    assert 'APP_VERSION = "6.4.0"' in release or 'APP_VERSION = "6.5.0"' in release or 'APP_VERSION = "6.6.0"' in release or 'APP_VERSION = "6.7.0"' in release or 'APP_VERSION = "6.8.0"' in release or 'APP_VERSION = "6.11.0"' in release
    assert "from app.v640 import router as v640_router" in main
    assert "app.include_router(v640_router)" in main
    assert "Version: 6.4.0" in plugin or "Version: 6.5.0" in plugin or 'Version: 6.6.0' in plugin or 'Version: 6.7.0' in plugin or 'Version: 6.8.0' in plugin or 'Version: 6.11.0' in plugin
    assert "define('SCWB_VERSION', '6.4.0')" in plugin or "define('SCWB_VERSION', '6.5.0')" in plugin or "define('SCWB_VERSION', '6.6.0')" in plugin or "define('SCWB_VERSION', '6.7.0')" in plugin or "define('SCWB_VERSION', '6.8.0')" in plugin or "define('SCWB_VERSION', '6.11.0')" in plugin
    assert "scwb-v640-platform-core-connectivity.php" in plugin
    assert "sustainable-catalyst-workbench:6.4.0" in compose or "sustainable-catalyst-workbench:6.5.0" in compose or 'sustainable-catalyst-workbench:6.6.0' in compose or 'sustainable-catalyst-workbench:6.7.0' in compose or 'sustainable-catalyst-workbench:6.8.0' in compose or 'sustainable-catalyst-workbench:6.11.0' in compose
    assert "/health" in compose


def test_v640_security_and_core_contract_are_explicit():
    code = (ROOT / "backend/app/v640.py").read_text()
    assert "sc.research.unified-runtime-contract.v1" in code
    assert "X-SC-Service-Token" in code
    assert "hmac.compare_digest" in code
    assert "outboundDispatchEnabled" in code
    assert "secretsReturned" in code
