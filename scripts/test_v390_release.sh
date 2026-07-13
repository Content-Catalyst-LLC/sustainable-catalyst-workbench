#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
echo "Testing Sustainable Catalyst Workbench v3.9.0"
grep -q 'Version: 3.9.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '3.9.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'version="3.9.0"' "$ROOT/backend/app/main.py"
grep -q 'from app.v390 import router as v390_router' "$ROOT/backend/app/main.py"
find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
node --check "$ROOT/offline/web/app.js" >/dev/null
node --check "$ROOT/offline/web/service-worker.js" >/dev/null
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done
php "$ROOT/tests/test_v390_plugin_activation.php"
php "$ROOT/tests/test_v390_wordpress_runtime.php"
php "$ROOT/tests/test_v380_wordpress_runtime.php"
php "$ROOT/tests/test_v370_wordpress_runtime.php"
php "$ROOT/tests/test_v331_embedded_suite_suppression.php"
node "$ROOT/tests/test_v390_browser.js"
node "$ROOT/tests/test_v380_browser.js"
node "$ROOT/tests/test_v370_browser.js"
node "$ROOT/tests/test_v360_browser.js"
node "$ROOT/tests/test_v350_browser.js"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" python3 -m pytest -q -p no:cacheprovider "$ROOT/tests"
python3 -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"
if command -v go >/dev/null 2>&1; then (cd "$ROOT/runner-go" && go test ./... && go vet ./...); fi
for required in "$PLUGIN/includes/scwb-v390-production-hardening.php" "$PLUGIN/assets/js/sc-workbench-v390.js" "$PLUGIN/assets/css/sc-workbench-v390.css" "$ROOT/docs/V390_SECURITY_BOUNDARY.md" "$ROOT/offline/package-manifest.json"; do [[ -s "$required" ]] || { echo "Missing v3.9.0 artifact: $required" >&2; exit 1; }; done
grep -q 'humanReleaseApprovalRequired' "$ROOT/backend/app/v390.py"
grep -q 'automaticPublicationAuthorized.*False' "$ROOT/backend/app/v390.py"
grep -q 'remoteShellAllowed.*False' "$ROOT/backend/app/v390.py"
find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi
echo "Workbench v3.9.0 release checks passed."
