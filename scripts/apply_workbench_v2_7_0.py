#!/usr/bin/env python3
"""Merge Workbench v2.7.0 into an existing v2.6.0 repository checkout."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

VERSION = "2.7.0"
RELEASE_TITLE = "Scientific Visualization and Engineering Dashboard Studio"


def copy_tree(source: Path, target: Path) -> None:
    for item in source.rglob("*"):
        if "__pycache__" in item.parts or item.suffix == ".pyc":
            continue
        destination = target / item.relative_to(source)
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def inject_php(text: str, block: str) -> str:
    if text.rstrip().endswith("?>"):
        index = text.rfind("?>")
        return text[:index].rstrip() + "\n\n" + block.rstrip() + "\n"
    return text.rstrip() + "\n\n" + block.rstrip() + "\n"


def patch(repo: Path, overlay: Path) -> None:
    plugin = repo / "wordpress-plugin/sustainable-catalyst-workbench"
    main_plugin = plugin / "sustainable-catalyst-workbench.php"
    prerequisite = plugin / "includes/scwb-v260-multilanguage-runtime.php"
    if not prerequisite.exists():
        raise SystemExit("Workbench v2.6.0 is required before v2.7.0.")

    copy_tree(overlay / "wordpress-plugin/sustainable-catalyst-workbench", plugin)
    plugin_text = main_plugin.read_text()
    plugin_text = re.sub(r"(?m)^(\s*\*\s*Version:\s*)[^\r\n]+$", rf"\g<1>{VERSION}", plugin_text, count=1)
    plugin_text = re.sub(r"define\('SCWB_VERSION',\s*'[^']+'\);", f"define('SCWB_VERSION', '{VERSION}');", plugin_text, count=1)
    if "SCWB_V270_PLUGIN_FILE" not in plugin_text:
        plugin_text = inject_php(plugin_text, """// Workbench v2.7.0 — Scientific Visualization and Engineering Dashboard Studio.
if (!defined('SCWB_V270_PLUGIN_FILE')) { define('SCWB_V270_PLUGIN_FILE', __FILE__); }
require_once __DIR__ . '/includes/scwb-v270-visualization-dashboard.php';""")
    main_plugin.write_text(plugin_text)

    app = repo / "backend/app"
    copy_tree(overlay / "backend/app", app)
    backend_main = app / "main.py"
    backend_text = re.sub(r'version="[^"]+"', f'version="{VERSION}"', backend_main.read_text(), count=1)
    backend_text = re.sub(r'(?m)^version="[^"]+"$', f'version="{VERSION}"', backend_text, count=1)
    if "v270_router" not in backend_text:
        backend_text = backend_text.rstrip() + "\n\n# Workbench v2.7.0 scientific visualization and engineering dashboard routes.\nfrom app.v270 import router as v270_router\napp.include_router(v270_router)\n"
    backend_main.write_text(backend_text)

    copy_tree(overlay / "runner-go", repo / "runner-go")
    copy_tree(overlay / "docs", repo / "docs")
    copy_tree(overlay / "tests", repo / "tests")
    release_test = repo / "scripts/test_v270_release.sh"
    release_test.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(overlay / "scripts/test_v270_release.sh", release_test)
    release_test.chmod(0o755)

    readme = repo / "README.md"
    if readme.exists():
        readme_text = re.sub(r"(?m)^# Sustainable Catalyst(?: Prototyping)? Workbench v[^\s]+", "# Sustainable Catalyst Prototyping Workbench v2.7.0", readme.read_text(), count=1)
        heading = "## Version 2.7.0 — Scientific Visualization and Engineering Dashboard Studio"
        if heading not in readme_text:
            readme_text = readme_text.rstrip() + "\n\n" + heading + "\n\nAdds browser-local scientific figures, threshold-aware engineering dashboards, interactive parameter charts, validation overlays, system-state views, accessible descriptions, and report-ready visual exports.\n"
        readme.write_text(readme_text)

    shutil.copy2(overlay / "docs/V270_RELEASE_NOTES.md", repo / "V270_RELEASE_NOTES.md")
    required = [
        plugin / "includes/scwb-v270-visualization-dashboard.php",
        plugin / "assets/js/sc-workbench-v270.js",
        plugin / "assets/css/sc-workbench-v270.css",
        app / "v270.py",
        repo / "runner-go/internal/runner/version.go",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("v2.7.0 merge incomplete:\n" + "\n".join(missing))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--overlay", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    patch(args.repo.resolve(), args.overlay.resolve())
    print(f"Applied Workbench {VERSION} — {RELEASE_TITLE}")
    print(args.repo.resolve())


if __name__ == "__main__":
    main()
