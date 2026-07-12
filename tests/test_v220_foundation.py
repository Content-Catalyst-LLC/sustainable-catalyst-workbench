"""Static release-contract tests for Workbench v2.2.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v220_files_exist() -> None:
    required = [
        ROOT / "backend/app/v220.py",
        ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v220-hardware-validation.php",
        ROOT / "wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v220.js",
        ROOT / "runner-go/internal/runner/version.go",
    ]
    assert all(path.exists() for path in required)


def test_v220_routes_and_shortcodes_are_declared() -> None:
    backend = (ROOT / "backend/app/v220.py").read_text(encoding="utf-8")
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v220-hardware-validation.php").read_text(encoding="utf-8")
    for route in ["/fpga/projects", "/electronics/review", "/schematic/validate", "/bom/validate", "/pcb/review", "/validation/evaluate"]:
        assert route in backend
    for shortcode in ["sc_workbench_fpga_studio", "sc_workbench_electronics_design", "sc_workbench_schematic_editor", "sc_workbench_bom_validation", "sc_workbench_pcb_studio", "sc_workbench_hardware_validation"]:
        assert shortcode in plugin
