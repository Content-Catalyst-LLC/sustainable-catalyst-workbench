#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
FOUNDATION="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v200-foundation.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v200.js"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v200.py"
RUNNER_VERSION="$ROOT/runner-go/internal/runner/version.go"

required=("$PLUGIN" "$FOUNDATION" "$JS" "$BACKEND" "$ROUTES" "$RUNNER_VERSION")
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "Missing required file: $path"; exit 1; }
done

grep -q 'Plugin Name: Sustainable Catalyst Prototyping Workbench' "$PLUGIN"
grep -q 'Version: 2.0.0' "$PLUGIN"
grep -q 'scwb-v200-foundation.php' "$PLUGIN"
grep -Eq "version=['\"]2\.0\.0['\"]" "$BACKEND"
grep -q 'Version = "2.0.0"' "$RUNNER_VERSION"

for marker in \
  sc_workbench_lab_canvas \
  sc_workbench_notebook \
  sc_workbench_documentation_studio \
  sc_workbench_hardware_studio \
  sc_workbench_arduino \
  sc_workbench_schematic \
  sc_workbench_bom \
  sc_workbench_pcb \
  sc_workbench_assembly \
  sc_workbench_fpga \
  sc_workbench_local_runner; do
  grep -q "$marker" "$FOUNDATION" || { echo "Missing shortcode marker: $marker"; exit 1; }
done

command -v php >/dev/null 2>&1 && php -l "$PLUGIN" >/dev/null
command -v php >/dev/null 2>&1 && php -l "$FOUNDATION" >/dev/null
command -v node >/dev/null 2>&1 && node --check "$JS"
python3 -m py_compile "$BACKEND" "$ROUTES"

if command -v go >/dev/null 2>&1; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
fi

python3 - "$ROOT" <<'__SECRET_SCAN__'
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
pattern = re.compile(r'(?i)(api[_-]?key|secret|password)\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']')
for path in root.rglob('*'):
    if not path.is_file() or any(part in {'.git', '.venv', '__pycache__', '.pytest_cache'} for part in path.parts):
        continue
    if path.suffix.lower() in {'.zip', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.pyc'}:
        continue
    text = path.read_text(errors='ignore')
    if pattern.search(text):
        raise SystemExit(f'Potential secret assignment found in {path}')
print('Push-safe secret scan passed.')
__SECRET_SCAN__

echo "Workbench v2.0.0 release checks passed."
