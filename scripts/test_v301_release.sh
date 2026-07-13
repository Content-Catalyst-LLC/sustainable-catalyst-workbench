#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"

echo "Testing Sustainable Catalyst Workbench v3.0.1"

grep -q 'Version: 3.0.1' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '3.0.1')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v301-production-reliability.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-primary-shortcode.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'from app.v301 import router as v301_router' "$ROOT/backend/app/main.py"
grep -q 'version="3.0.1"' "$ROOT/backend/app/main.py"

find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done

php "$ROOT/tests/test_v301_plugin_activation.php"
php "$ROOT/tests/test_v301_wordpress_runtime.php"
node "$ROOT/tests/test_v301_router.js"

PYTHONPATH="$ROOT/backend" python3 -m pytest -q "$ROOT/tests"
python3 -m py_compile "$ROOT/backend/app"/*.py

if command -v go >/dev/null 2>&1; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
fi

if grep -RInE --exclude-dir=.git --exclude='*.md' --exclude='*.txt' --exclude='*.zip' \
  '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,})' "$ROOT"; then
  echo 'Potential secret detected.' >&2
  exit 1
fi

echo "Workbench v3.0.1 release checks passed."
