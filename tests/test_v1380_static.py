import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_router():
    assert 'APP_VERSION = "13.8.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.8.0"' in m
    assert "from app.v1380 import router as v1380_router" in m
    assert "app.include_router(v1380_router)" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1380.py").read_text()
    for x in ["unifiedWorkspaceReady","crossSurfaceHandoffs","continuationCards",
              "unifiedCounts","recentActivity","backendAuthoritiesPreserved"]:
        assert x in p

def test_frontend_unified_workspace():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["unifiedWorkspace","loadUnifiedWorkspace","Unified Workbench Workspace",
              "data-workspace-route","unifiedContinuation","unifiedActivity"]:
        assert x in p

def test_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.8.0"
    assert d["interface"]=="unified-workbench-workspace"

def test_client():
    p=(ROOT/"standalone-client/unified-workspace.js").read_text()
    assert "UnifiedWorkspaceClient" in p
    assert "handoff(projectId" in p

def test_wp_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.8.0" in p
    assert "scwb-v1380-unified-workbench-workspace.php" in p
