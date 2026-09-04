#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo "Testing Sustainable Catalyst Workbench v5.3.1"
grep -q 'Version: 5.3.1' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '5.3.1')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v531-settings-backend-repair.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'data-scwb-version="5.3.1"' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'version="5.3.0"' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:5.3.0' "$ROOT/compose.yml"
grep -q '"version": "5.3.1"' "$ROOT/offline/package-manifest.json"
find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done
php "$ROOT/tests/test_v531_plugin_activation.php"
php "$ROOT/tests/test_v531_wordpress_runtime.php"
php "$ROOT/tests/test_v530_wordpress_runtime.php"
php "$ROOT/tests/test_v520_wordpress_runtime.php"
php "$ROOT/tests/test_v510_wordpress_runtime.php"
php "$ROOT/tests/test_v500_wordpress_runtime.php"
node "$ROOT/tests/test_v531_browser.js"
node "$ROOT/tests/test_v530_browser.js"
node "$ROOT/tests/test_v520_browser.js"
node "$ROOT/tests/test_v510_browser.js"
node "$ROOT/tests/test_v500_browser.js"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"
for required in \
  "$PLUGIN/includes/scwb-v531-settings-backend-repair.php" \
  "$PLUGIN/assets/css/sc-workbench-v531-admin.css" \
  "$PLUGIN/assets/js/sc-workbench-v531-admin.js" \
  "$ROOT/docs/V531_SETTINGS_BACKEND_CONNECTION_REPAIR.md" \
  "$ROOT/docs/V531_HOMEPAGE_INSTRUMENT_REFINEMENT.md" \
  "$ROOT/V531_RELEASE_NOTES.md" \
  "$ROOT/NO_BACKEND_REDEPLOY_REQUIRED_v5.3.1.md"; do
  [[ -s "$required" ]] || { echo "Missing v5.3.1 artifact: $required" >&2; exit 1; }
done
grep -q 'automaticDeviceProgrammingAuthorized.*False' "$ROOT/backend/app/v530.py"
if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v530.py"; then echo 'Unsafe eval/exec detected in v530 backend.' >&2; exit 1; fi
find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi
echo "Workbench v5.3.1 release checks passed."
