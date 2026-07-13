#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
echo "Testing Sustainable Catalyst Workbench v3.6.0"
grep -q 'Version: 3.6.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '3.6.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'version="3.6.0"' "$ROOT/backend/app/main.py"
find "$PLUGIN" -type f -name '*.php' -print0|while IFS= read -r -d '' file;do php -l "$file" >/dev/null;done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0|while IFS= read -r -d '' file;do node --check "$file" >/dev/null;done
php "$ROOT/tests/test_v360_plugin_activation.php"
php "$ROOT/tests/test_v360_wordpress_runtime.php"
php "$ROOT/tests/test_v350_wordpress_runtime.php"
php "$ROOT/tests/test_v331_embedded_suite_suppression.php"
node "$ROOT/tests/test_v360_browser.js"
node "$ROOT/tests/test_v350_browser.js"
node "$ROOT/tests/test_v340_browser.js"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" python3 -m pytest -q -p no:cacheprovider "$ROOT/tests"
python3 -m py_compile "$ROOT/backend/app"/*.py
if command -v go >/dev/null 2>&1;then(cd "$ROOT/runner-go"&&go test ./...&&go vet ./...);fi
find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT";then echo 'Potential secret detected.' >&2;exit 1;fi
echo "Workbench v3.6.0 release checks passed."
