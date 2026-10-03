from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "12.1.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.1.0"' in m
    assert "from app.v1210 import router as v1210_router" in m
    assert "app.include_router(v1210_router)" in m

def test_auth_routes_and_security_contract():
    p=(ROOT/"backend/app/v1210.py").read_text()
    assert "/standalone/v1/auth/config" in p
    assert "/standalone/v1/auth/session/anonymous" in p
    assert "/standalone/v1/auth/session/verify" in p
    assert "/standalone/v1/auth/session/refresh" in p
    assert "/standalone/v1/auth/session/me" in p
    assert "HMAC-SHA256" in p
    assert "compare_digest" in p

def test_standalone_client():
    p=(ROOT/"standalone-client/session.js").read_text()
    assert "StandaloneSessionClient" in p
    assert "createAnonymousSession" in p
    assert "refreshSession" in p
    assert "Authorization" in p

def test_app_shell_auth_bootstrap():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert "/standalone/v1/auth/config" in p
    assert "/standalone/v1/auth/session/anonymous" in p
    assert "session.subject.type" in p

def test_wordpress_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1210-standalone-authentication-session-foundation.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress does not own standalone session identity" in p
    assert "/standalone/v1/auth/config" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.1.0" in c
    assert "d.get('version')=='12.1.0'" in c
    assert "SCWB_SESSION_SECRET" in c
