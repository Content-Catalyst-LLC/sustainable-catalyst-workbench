from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_release():
    assert 'APP_VERSION = "11.9.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.9.0"' in m and "v1190_router" in m
def test_routes():
    p=(ROOT/"backend/app/v1190.py").read_text()
    assert "/calculation-engine/v1/precision" in p
    assert "intervalArithmetic" in p
def test_requirement():
    assert "mpmath>=1.3,<2" in (ROOT/"backend/requirements.txt").read_text()
def test_wp():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1190-arbitrary-precision-interval.php").read_text()
    assert "wordpressRequired = false" in p and "/calculation-engine/v1/precision" in p
def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.9.0" in c and "d.get('version')=='11.9.0'" in c
