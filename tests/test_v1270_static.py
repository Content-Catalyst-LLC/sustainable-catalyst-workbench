from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release():
    assert 'APP_VERSION = "12.7.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.7.0"' in m
    assert "from app.v1270 import router as v1270_router" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1270.py").read_text()
    assert "/standalone/v1/launch/config" in p
    assert "/standalone/v1/launch/validate" in p
    assert "authenticationEmbedded" in p
    assert "SCWB_STANDALONE_APP_URL" in p

def test_client():
    p=(ROOT/"standalone-client/deep-link.js").read_text()
    assert "StandaloneDeepLinkClient" in p
    assert "parseLaunchToken" in p
    assert "validateLaunch" in p

def test_app_launch_resolution():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert "resolveLaunch" in p
    assert 'searchParams.get("launch")' in p
    assert "targetType" in p

def test_wordpress_embed_shortcode():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1270-wordpress-embed-deep-link.php").read_text()
    assert "add_shortcode('sc_workbench_embed'" in p
    assert "sc_workbench_embed" in p
    assert "iframe" in p
    assert "wordpressRequired = false" in p
    assert "authentication credentials" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.7.0" in c
    assert "d.get('version')=='12.7.0'" in c
    assert "SCWB_STANDALONE_APP_URL" in c
    assert "SCWB_DEEP_LINK_SECRET" in c
