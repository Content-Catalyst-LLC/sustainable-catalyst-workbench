from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release():
    assert 'APP_VERSION = "12.8.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.8.0"' in m
    assert "from app.v1280 import router as v1280_router" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1280.py").read_text()
    assert "/standalone/v1/state-authority" in p
    assert "/standalone/v1/state-dependency/certification" in p
    assert "wordpressMayOwnCanonicalV12State" in p
    assert "historicalWordPressModulesMayRemainLoaded" in p

def test_standalone_client():
    p=(ROOT/"standalone-client/state-authority.js").read_text()
    assert "StandaloneStateAuthorityClient" in p
    assert "certification" in p
    assert "sessionProbe" in p

def test_app_has_state_authority_check():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert "loadStateCertification" in p
    assert "WORDPRESS STATE: ELIMINATED" in p
    assert "stateCertification" in p

def test_v1280_wordpress_adapter_has_no_state_writes():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1280-wordpress-state-dependency-elimination.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress compatibility adapter only" in p
    forbidden=[
      "update_option(","add_option(","delete_option(",
      "update_user_meta(","add_user_meta(","delete_user_meta(",
      "set_transient(","delete_transient("
    ]
    for term in forbidden:
        assert term not in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.8.0" in c
    assert "d.get('version')=='12.8.0'" in c
