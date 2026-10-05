import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_and_router():
    assert 'APP_VERSION = "13.5.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.5.0"' in m
    assert "from app.v1350 import router as v1350_router" in m
    assert "app.include_router(v1350_router)" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1350.py").read_text()
    for x in ["scwb_graph_studies","scwb_graph_annotations",
              "/standalone/v1/graph-studio/graphs",
              "multipleFunctionSeries","researchSessionBinding",
              "viewSpecAuthority"]:
        assert x in p

def test_frontend_graph_studio():
    s=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["Interactive Graph Studio","savedGraphs","activeGraphId",
              "createGraphStudy","renderSavedGraph","addGraphSeries",
              "graph-study-select"]:
        assert x in s

def test_renderer_supports_backend_view_shape():
    p=(ROOT/"standalone-app/math-renderer.js").read_text()
    assert "spec?.result?.views" in p
    assert "seriesPoints" in p
    assert "graphSeriesLabel" in p

def test_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.5.0"
    assert d["interface"]=="interactive-graph-studio"

def test_client_and_wp():
    assert "GraphStudioClient" in (ROOT/"standalone-client/graph-studio.js").read_text()
    wp=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.5.0" in wp
    assert "scwb-v1350-interactive-graph-studio.php" in wp
