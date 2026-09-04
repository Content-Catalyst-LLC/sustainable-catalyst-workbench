#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
echo "Testing Sustainable Catalyst Workbench v5.2.0"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
grep -q 'Version: 5.2.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '5.2.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'version="5.2.0"' "$ROOT/backend/app/main.py"
grep -q 'from app.v520 import router as v520_router' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:5.2.0' "$ROOT/compose.yml"
find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done
php "$ROOT/tests/test_v520_plugin_activation.php"
php "$ROOT/tests/test_v520_wordpress_runtime.php"
php "$ROOT/tests/test_v510_wordpress_runtime.php"
php "$ROOT/tests/test_v500_wordpress_runtime.php"
node "$ROOT/tests/test_v520_browser.js"
node "$ROOT/tests/test_v510_browser.js"
node "$ROOT/tests/test_v500_browser.js"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"
for required in "$ROOT/backend/app/v520.py" "$PLUGIN/includes/scwb-v520-graph-mathematics.php" "$PLUGIN/assets/js/sc-workbench-v520.js" "$PLUGIN/assets/css/sc-workbench-v520.css" "$ROOT/docs/V520_INTERACTIVE_GRAPH_MATHEMATICS.md" "$ROOT/docs/V520_SECURITY_BOUNDARY.md" "$ROOT/examples/v520-interactive-graph-fixture.json"; do [[ -s "$required" ]] || { echo "Missing v5.2.0 artifact: $required" >&2; exit 1; }; done
grep -q 'arbitraryCodeExecutionAuthorized.*False' "$ROOT/backend/app/v520.py"
grep -q 'pythonEvalAuthorized.*False' "$ROOT/backend/app/v520.py"
if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v520.py"; then echo 'Unsafe eval/exec detected in v520 backend.' >&2; exit 1; fi
grep -q '"version": "5.2.0"' "$ROOT/offline/package-manifest.json"
grep -q 'backend/app/v520.py' "$ROOT/offline/package-manifest.json"
find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi
echo "Workbench v5.2.0 release checks passed."
