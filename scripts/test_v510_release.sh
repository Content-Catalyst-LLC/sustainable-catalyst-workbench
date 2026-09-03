#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
echo "Testing Sustainable Catalyst Workbench v5.1.0"
grep -q 'Version: 5.1.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '5.1.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'version="5.1.0"' "$ROOT/backend/app/main.py"
grep -q 'from app.v510 import router as v510_router' "$ROOT/backend/app/main.py"
find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done
php "$ROOT/tests/test_v510_plugin_activation.php"
php "$ROOT/tests/test_v510_wordpress_runtime.php"
php "$ROOT/tests/test_v500_wordpress_runtime.php"
node "$ROOT/tests/test_v510_browser.js"
node "$ROOT/tests/test_v500_browser.js"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" python3 -m pytest -q -p no:cacheprovider "$ROOT/tests"
python3 -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"
for required in "$ROOT/backend/app/v510.py" "$PLUGIN/includes/scwb-v510-mathematics.php" "$PLUGIN/assets/js/sc-workbench-v510.js" "$PLUGIN/assets/css/sc-workbench-v510.css" "$ROOT/docs/V510_UNIVERSAL_MATHEMATICS.md" "$ROOT/docs/V510_SECURITY_BOUNDARY.md" "$ROOT/examples/v510-mathematics-fixture.json"; do [[ -s "$required" ]] || { echo "Missing v5.1.0 artifact: $required" >&2; exit 1; }; done
grep -q 'pythonEvalAuthorized.*False' "$ROOT/backend/app/v510.py"
grep -q 'arbitraryCodeExecutionAuthorized.*False' "$ROOT/backend/app/v510.py"
if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v510.py"; then echo 'Unsafe eval/exec detected in v510 backend.' >&2; exit 1; fi
grep -q '"version": "5.1.0"' "$ROOT/offline/package-manifest.json"
grep -q 'backend/app/v510.py' "$ROOT/offline/package-manifest.json"
find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi
echo "Workbench v5.1.0 release checks passed."
