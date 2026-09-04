from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'wordpress-plugin'/'sustainable-catalyst-workbench'
def test_v532_homepage_and_experience_markers():
    php=(PLUGIN/'includes'/'scwb-v532-compact-showcase-experience.php').read_text()
    assert "const VERSION = '5.3.2'" in php
    assert 'sc_workbench_homepage_instrument' in php
    assert 'sc_workbench_experience' in php
    assert 'Open Workbench →' in php
    assert 'data-scwb-v532-mode="4"' in php
    assert 'one object · multiple representations' in php

def test_v532_graph_presentation_markers():
    js=(PLUGIN/'assets'/'js'/'sc-workbench-v520.js').read_text()
    for marker in ['sampledMarkers','drawTrace','requestFullscreen','wheel','drag to rotate','surfaceState']:
        assert marker in js
    css=(PLUGIN/'assets'/'css'/'sc-workbench-v520.css').read_text()
    assert 'v5.3.2 advanced graph presentation' in css

def test_v532_backend_runtime_unchanged():
    assert 'version="5.3.0"' in (ROOT/'backend'/'app'/'main.py').read_text()
    assert 'sustainable-catalyst-workbench:5.3.0' in (ROOT/'compose.yml').read_text()
