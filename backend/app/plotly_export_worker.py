"""FIG-02A isolated static export worker (PNG/SVG/PDF) for compiled Plotly figures.

Run only as ``python -I plotly_export_worker.py`` by ``plotly_figure_adapter.run_static_export``.
Reads one JSON request on stdin and writes one JSON result on stdout. It imports nothing from
the Workbench application, receives a minimal environment without service credentials, loads
plotly.js from the installed plotly.py package (never a CDN) and disables MathJax so the
headless Chrome page has no remote script dependencies.
"""
import base64
import json
import math
import os
import subprocess
import sys
from pathlib import Path

FORMATS = {"png", "svg", "pdf"}
MAX_FIGURE_CHARS = 5_000_000


def _fail(error):
    sys.stdout.write(json.dumps({"ok": False, "error": error}))
    return 0


def _reject_nonfinite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite")
    if isinstance(value, dict):
        for item in value.values():
            _reject_nonfinite(item)
    elif isinstance(value, list):
        for item in value:
            _reject_nonfinite(item)


def _chrome_version(path):
    if not path:
        return None
    try:
        out = subprocess.run([path, "--version"], capture_output=True, timeout=15, check=False)
        return out.stdout.decode("utf-8", "replace").strip()[:120] or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def main():
    raw = sys.stdin.read(MAX_FIGURE_CHARS + 1)
    if len(raw) > MAX_FIGURE_CHARS:
        return _fail("figure-too-large")
    try:
        request = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        figure = request["figure"]
        formats = list(request["formats"])
        width, height = int(request["width"]), int(request["height"])
        _reject_nonfinite(figure)
    except (ValueError, KeyError, TypeError):
        return _fail("invalid-request")
    if not formats or not set(formats) <= FORMATS:
        return _fail("unsupported-format")
    try:
        import kaleido
        import plotly
        from choreographer.browsers.chromium import Chromium
    except ImportError:
        return _fail("plotly-or-kaleido-not-installed")
    # Never download a browser: only an explicitly configured or system-installed Chrome is used.
    browser = os.environ.get("BROWSER_PATH") or Chromium.find_browser(skip_local=True)
    if not browser or not os.path.exists(browser):
        return _fail("chrome-unavailable")
    plotly_js = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
    if not plotly_js.is_file():
        return _fail("local-plotlyjs-missing")
    kopts = {"plotlyjs": str(plotly_js), "mathjax": False, "path": browser}
    outputs = {}
    try:
        for fmt in formats:
            data = kaleido.calc_fig_sync(figure, opts={"format": fmt, "width": width, "height": height}, kopts=kopts)
            outputs[fmt] = base64.b64encode(data).decode("ascii")
    except Exception as exc:  # noqa: BLE001 - classified, never echoed with paths or environment
        text = f"{type(exc).__name__} {exc}".lower()
        if "browser" in text or "chrome" in text or "chromium" in text:
            return _fail("chrome-unavailable")
        return _fail("render-failed")
    sys.stdout.write(json.dumps({"ok": True, "outputs": outputs, "chromeVersion": _chrome_version(browser)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
