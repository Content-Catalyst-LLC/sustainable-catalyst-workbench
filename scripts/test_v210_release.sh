#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
V200="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v200-foundation.php"
V210="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v210-embedded-studio.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v210.js"
CSS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v210.css"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v210.py"
RUNNER="$ROOT/runner-go/cmd/workbench-runner/main.go"
RUNNER_VERSION="$ROOT/runner-go/internal/runner/version.go"

required=("$PLUGIN" "$V200" "$V210" "$JS" "$CSS" "$BACKEND" "$ROUTES" "$RUNNER" "$RUNNER_VERSION")
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "Missing required file: $path"; exit 1; }
done

grep -q 'Plugin Name: Sustainable Catalyst Prototyping Workbench' "$PLUGIN"
grep -q 'Version: 2.1.0' "$PLUGIN"
grep -q 'scwb-v200-foundation.php' "$PLUGIN"
grep -q 'scwb-v210-embedded-studio.php' "$PLUGIN"
grep -q 'v210_router' "$BACKEND"
grep -q 'const Version = "2.1.0"' "$RUNNER_VERSION"
grep -q 'mux.HandleFunc("/devices"' "$RUNNER"
grep -q 'mux.HandleFunc("/device-task"' "$RUNNER"

for marker in \
  sc_workbench_embedded_device_studio \
  sc_workbench_raspberry_pi \
  sc_workbench_tinyml \
  sc_workbench_sensor_calibration \
  sc_workbench_device_logs \
  sc_workbench_embedded_board_catalog; do
  grep -q "$marker" "$V210" || { echo "Missing shortcode marker: $marker"; exit 1; }
done

command -v php >/dev/null 2>&1 && php -l "$PLUGIN" >/dev/null
command -v php >/dev/null 2>&1 && php -l "$V200" >/dev/null
command -v php >/dev/null 2>&1 && php -l "$V210" >/dev/null
command -v node >/dev/null 2>&1 && node --check "$JS"
python3 -m py_compile "$BACKEND" "$ROUTES"

if command -v go >/dev/null 2>&1; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
  [[ "$(cd "$ROOT/runner-go" && go run ./cmd/workbench-runner version)" == "2.1.0" ]]
  (cd "$ROOT/runner-go" && go run ./cmd/workbench-runner devices >/dev/null)
fi

python3 - "$ROOT" <<'PY'
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
patterns = [
    re.compile(r'AIza[0-9A-Za-z_-]{20,}'),
    re.compile(r'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}'),
    re.compile(r'BEGIN (RSA|OPENSSH|EC) PRIVATE KEY'),
    re.compile(r'(?i)(password|api[_-]?key|secret)\s*[:=]\s*["\'][^"\']{12,}["\']'),
]
for path in root.rglob('*'):
    if not path.is_file() or any(part in {'.git', '.venv', '__pycache__', '.pytest_cache'} for part in path.parts):
        continue
    if path.suffix.lower() in {'.zip', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.pyc'}:
        continue
    text = path.read_text(errors='ignore')
    for pattern in patterns:
        if pattern.search(text):
            raise SystemExit(f'Potential secret found in {path}')
print('Push-safe secret scan passed.')
PY

echo "Workbench v2.1.0 release checks passed."
