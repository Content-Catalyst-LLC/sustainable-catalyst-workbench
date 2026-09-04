from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'wordpress-plugin'/'sustainable-catalyst-workbench'
def test_v531_settings_and_homepage_markers():
    settings=(PLUGIN/'includes'/'scwb-v531-settings-backend-repair.php').read_text()
    assert "const VERSION = '5.3.1'" in settings
    assert "const OPTION_BACKEND_URL = 'scwb_workbench_backend_url'" in settings
    assert "SCWB_WORKBENCH_BACKEND_URL" in settings
    assert "wp_ajax_scwb_v531_test_backend" in settings
    assert "/v510/status" in settings and "/v520/status" in settings and "/v530/status" in settings
    home=(PLUGIN/'includes'/'scwb-v530-blackboard-creative-prototyping.php').read_text()
    assert 'scwb-v531-home__capabilities' in home
    assert 'Equation → graph → sound → form → physical system' in home

def test_backend_runtime_unchanged_for_patch():
    main=(ROOT/'backend'/'app'/'main.py').read_text()
    assert 'version="5.3.0"' in main
    assert 'from app.v530 import router as v530_router' in main
