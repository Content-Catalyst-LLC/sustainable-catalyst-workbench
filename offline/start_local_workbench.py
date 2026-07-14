#!/usr/bin/env python3
"""Launch Sustainable Catalyst Workbench v4.2.0 on the local loopback interface."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for path in (str(ROOT), str(BACKEND)):
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.main import app

WEB_ROOT = ROOT / "offline" / "web"
if WEB_ROOT.exists():
    app.mount("/offline", StaticFiles(directory=str(WEB_ROOT), html=True), name="offline")

@app.get("/", include_in_schema=False)
def local_root():
    return RedirectResponse(url="/offline/")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sustainable Catalyst Workbench locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Refusing public bind. Use 127.0.0.1, localhost, or ::1.")
    if not args.no_browser:
        webbrowser.open(f"http://127.0.0.1:{args.port}/offline/")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
