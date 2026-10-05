import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_router():
    assert 'APP_VERSION = "13.7.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.7.0"' in m
    assert "from app.v1370 import router as v1370_router" in m
    assert "app.include_router(v1370_router)" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1370.py").read_text()
    for x in ["packageWorkspaceReady","sideBySideReplayComparison","integrity_status",
              "/replay","/verify","/export","canonicalV1117ReplayEnginePreserved"]:
        assert x in p

def test_frontend_workspace():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["activePackageId","activePackage","packageComparison",
              "loadPackageWorkspace","activatePackage","replayActivePackage",
              "Reproducibility Package Workspace"]:
        assert x in p

def test_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.7.0"
    assert d["interface"]=="reproducibility-package-workspace"

def test_client():
    p=(ROOT/"standalone-client/reproducibility-workspace.js").read_text()
    assert "ReproducibilityWorkspaceClient" in p
    assert "verify(id)" in p
    assert "replay(id" in p

def test_wp_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.7.0" in p
    assert "scwb-v1370-reproducibility-package-workspace.php" in p
