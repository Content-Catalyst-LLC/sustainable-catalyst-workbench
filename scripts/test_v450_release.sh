#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
echo "Testing Sustainable Catalyst Workbench v4.5.0"
grep -q 'Version: 4.5.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '4.5.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'version="4.5.0"' "$ROOT/backend/app/main.py"
find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
node --check "$ROOT/offline/web/app.js" >/dev/null
node --check "$ROOT/offline/web/service-worker.js" >/dev/null
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done
php "$ROOT/tests/test_v450_plugin_activation.php"
php "$ROOT/tests/test_v450_wordpress_runtime.php"
php "$ROOT/tests/test_v440_wordpress_runtime.php"
php "$ROOT/tests/test_v430_wordpress_runtime.php"
php "$ROOT/tests/test_v420_wordpress_runtime.php"
php "$ROOT/tests/test_v410_wordpress_runtime.php"
php "$ROOT/tests/test_v402_wordpress_runtime.php"
php "$ROOT/tests/test_v401_wordpress_runtime.php"
php "$ROOT/tests/test_v400_wordpress_runtime.php"
php "$ROOT/tests/test_v390_wordpress_runtime.php"
php "$ROOT/tests/test_v380_wordpress_runtime.php"
php "$ROOT/tests/test_v370_wordpress_runtime.php"
php "$ROOT/tests/test_v331_embedded_suite_suppression.php"
node "$ROOT/tests/test_v450_browser.js"
node "$ROOT/tests/test_v440_browser.js"
node "$ROOT/tests/test_v430_browser.js"
node "$ROOT/tests/test_v420_browser.js"
node "$ROOT/tests/test_v410_browser.js"
node "$ROOT/tests/test_v402_browser.js"
node "$ROOT/tests/test_v401_browser.js"
node "$ROOT/tests/test_v400_browser.js"
node "$ROOT/tests/test_v390_browser.js"
node "$ROOT/tests/test_v380_browser.js"
node "$ROOT/tests/test_v370_browser.js"
node "$ROOT/tests/test_v360_browser.js"
node "$ROOT/tests/test_v350_browser.js"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" python3 -m pytest -q -p no:cacheprovider "$ROOT/tests"
python3 -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"
if [[ "${SCWB_SKIP_GO_TESTS:-0}" != "1" ]] && command -v go >/dev/null 2>&1; then
  (cd "$ROOT/runner-go" && GOTOOLCHAIN=local go test ./... && GOTOOLCHAIN=local go vet ./...)
elif [[ "${SCWB_SKIP_GO_TESTS:-0}" == "1" ]]; then echo "Go compatibility checks skipped by SCWB_SKIP_GO_TESTS=1."; fi
for required in "$PLUGIN/includes/scwb-v450-extension-framework.php" "$PLUGIN/assets/js/sc-workbench-v450.js" "$PLUGIN/assets/css/sc-workbench-v450.css" "$ROOT/backend/app/v450.py" "$ROOT/docs/V450_SECURITY_BOUNDARY.md" "$ROOT/docs/V450_EXTENSION_SDK.md" "$ROOT/examples/v450-extension-sdk-fixture.json" "$ROOT/offline/package-manifest.json"; do [[ -s "$required" ]] || { echo "Missing v4.5.0 artifact: $required" >&2; exit 1; }; done
grep -q 'automaticExtensionInstallationAuthorized.*False' "$ROOT/backend/app/v450.py"
grep -q 'automaticExtensionActivationAuthorized.*False' "$ROOT/backend/app/v450.py"
grep -q 'automaticPrivilegeEscalationAuthorized.*False' "$ROOT/backend/app/v450.py"
grep -q 'arbitraryCodeExecutionAuthorized.*False' "$ROOT/backend/app/v450.py"
grep -q 'remoteShellAuthorized.*False' "$ROOT/backend/app/v450.py"
grep -q '"version": "4.5.0"' "$ROOT/offline/package-manifest.json"
grep -q 'backend/app/v450.py' "$ROOT/offline/package-manifest.json"
find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi
echo "Workbench v4.5.0 release checks passed."
