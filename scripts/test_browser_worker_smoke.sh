#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if ! command -v chromium >/dev/null 2>&1; then
  echo "Chromium unavailable; skipping browser worker smoke test."
  exit 0
fi
PORT="${SCWB_SMOKE_PORT:-8769}"
LOG="${TMPDIR:-/tmp}/scwb-v190-http.log"
python3 -m http.server "$PORT" --directory "$ROOT" >"$LOG" 2>&1 &
PID=$!
trap 'kill "$PID" >/dev/null 2>&1 || true' EXIT
sleep 1
DOM=$(timeout 20s chromium --headless --no-sandbox --disable-gpu --disable-dev-shm-usage --virtual-time-budget=6000 --dump-dom "http://127.0.0.1:$PORT/tests/browser/javascript_worker_smoke.html" 2>/dev/null)
printf '%s' "$DOM" | grep -q 'data-status="passed"'
echo "JavaScript browser worker smoke test passed."
