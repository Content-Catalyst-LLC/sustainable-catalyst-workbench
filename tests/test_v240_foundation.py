"""Marker tests for Workbench v2.4.0 release artifacts."""
from pathlib import Path


def test_v240_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    required = [
        root / "backend/app/v240.py",
        root / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v240-instrumentation.php",
        root / "wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v240.js",
        root / "wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v240.css",
    ]
    assert all(path.exists() for path in required)
