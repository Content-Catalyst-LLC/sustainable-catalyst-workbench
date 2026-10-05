import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_and_router():
    assert 'APP_VERSION = "13.1.0"' in (ROOT/'backend/app/release.py').read_text()
    m=(ROOT/'backend/app/main.py').read_text(); assert 'version="13.1.0"' in m; assert 'from app.v1310 import router as v1310_router' in m; assert 'app.include_router(v1310_router)' in m

def test_frontend_version_manifest():
    d=json.loads((ROOT/'standalone-app/version.json').read_text()); assert d['version']=='13.1.0'; assert d['wordpressRequired'] is False

def test_config_version(): assert 'version:"13.1.0"' in (ROOT/'standalone-app/config.js').read_text()

def test_deployment_health_client():
    p=(ROOT/'standalone-client/deployment-health.js').read_text(); assert 'compareVersions' in p; assert '/standalone/v1/interface/hardening-readiness' in p
