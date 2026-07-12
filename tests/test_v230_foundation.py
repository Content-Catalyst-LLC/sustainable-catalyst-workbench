from pathlib import Path

def test_v230_markers():
    root = Path(__file__).resolve().parents[1]
    assert 'VERSION = "2.3.0"' in (root / 'backend/app/v230.py').read_text()
    assert 'sc_workbench_robotics_studio' in (root / 'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v230-robotics-controls.php').read_text()
