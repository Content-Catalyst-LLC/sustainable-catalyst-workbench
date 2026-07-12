#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
V200="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v200-foundation.php"
V210="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v210-embedded-studio.php"
V220="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v220-hardware-validation.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v220.js"
CSS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v220.css"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v220.py"
RUNNER="$ROOT/runner-go/cmd/workbench-runner/main.go"
RUNNER_VERSION="$ROOT/runner-go/internal/runner/version.go"

required=("$PLUGIN" "$V200" "$V210" "$V220" "$JS" "$CSS" "$BACKEND" "$ROUTES" "$RUNNER" "$RUNNER_VERSION")
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "Missing required file: $path"; exit 1; }
done

grep -q 'Plugin Name: Sustainable Catalyst Prototyping Workbench' "$PLUGIN"
grep -q 'Version: 2.2.0' "$PLUGIN"
grep -q 'scwb-v200-foundation.php' "$PLUGIN"
grep -q 'scwb-v210-embedded-studio.php' "$PLUGIN"
grep -q 'scwb-v220-hardware-validation.php' "$PLUGIN"
grep -q 'v220_router' "$BACKEND"
grep -q 'const Version = "2.2.0"' "$RUNNER_VERSION"
grep -q 'mux.HandleFunc("/hardware-tools"' "$RUNNER"
grep -q 'mux.HandleFunc("/hardware-task"' "$RUNNER"

for marker in \
  sc_workbench_fpga_studio \
  sc_workbench_electronics_design \
  sc_workbench_schematic_editor \
  sc_workbench_bom_validation \
  sc_workbench_pcb_studio \
  sc_workbench_hardware_validation; do
  grep -q "$marker" "$V220" || { echo "Missing shortcode marker: $marker"; exit 1; }
done

for route in \
  '/fpga/projects' \
  '/electronics/review' \
  '/schematic/validate' \
  '/bom/validate' \
  '/pcb/review' \
  '/validation/evaluate'; do
  grep -q "$route" "$ROUTES" || { echo "Missing API route marker: $route"; exit 1; }
done

command -v php >/dev/null 2>&1 && php -l "$PLUGIN" >/dev/null
command -v php >/dev/null 2>&1 && php -l "$V200" >/dev/null
command -v php >/dev/null 2>&1 && php -l "$V210" >/dev/null
command -v php >/dev/null 2>&1 && php -l "$V220" >/dev/null
command -v node >/dev/null 2>&1 && node --check "$JS"
python3 - "$BACKEND" "$ROUTES" <<'PYCODE'
from pathlib import Path
import sys
for filename in sys.argv[1:]:
    path = Path(filename)
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
PYCODE

if command -v go >/dev/null 2>&1; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
  [[ "$(cd "$ROOT/runner-go" && go run ./cmd/workbench-runner version)" == "2.2.0" ]]
  (cd "$ROOT/runner-go" && go run ./cmd/workbench-runner hardware-tools >/dev/null)
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

echo "Workbench v2.2.0 release checks passed."
