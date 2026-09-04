#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"

echo "Testing Sustainable Catalyst Workbench v5.5.0"
grep -q 'Version: 5.5.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '5.5.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v550-dynamic-geometry.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'data-scwb-version="5.5.0"' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'version="5.5.0"' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:5.5.0' "$ROOT/compose.yml"
grep -q 'from app.v550 import router as v550_router' "$ROOT/backend/app/main.py"
grep -q '"version": "5.5.0"' "$ROOT/offline/package-manifest.json"

find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done

php "$ROOT/tests/test_v550_plugin_activation.php"
php "$ROOT/tests/test_v540_plugin_activation.php"
for v in 550 540 533 532 531 530 520 510 500; do php "$ROOT/tests/test_v${v}_wordpress_runtime.php"; done

node "$ROOT/tests/test_v550_browser.js"
for v in 540 533 532 531 530 520 510 500; do node "$ROOT/tests/test_v${v}_browser.js"; done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"

for required in \
  "$ROOT/backend/app/v550.py" \
  "$PLUGIN/includes/scwb-v550-dynamic-geometry.php" \
  "$PLUGIN/assets/css/sc-workbench-v550.css" \
  "$PLUGIN/assets/js/sc-workbench-v550.js" \
  "$ROOT/docs/V550_DYNAMIC_GEOMETRY_INTERACTIVE_MATHEMATICS.md" \
  "$ROOT/docs/V550_SECURITY_BOUNDARY.md" \
  "$ROOT/examples/v550-dynamic-geometry-fixture.json" \
  "$ROOT/V550_RELEASE_NOTES.md"; do
  [[ -s "$required" ]] || { echo "Missing v5.5.0 artifact: $required" >&2; exit 1; }
done

if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v550.py"; then echo 'Unsafe eval/exec detected in v550 backend.' >&2; exit 1; fi
if grep -nE 'new Function\(|window\.scrollTo\(|scrollIntoView\(' "$PLUGIN/assets/js/sc-workbench-v550.js"; then echo 'Unsafe browser execution/viewport primitive detected in v550.' >&2; exit 1; fi

grep -q "'/v550/status'" "$PLUGIN/includes/scwb-v531-settings-backend-repair.php"
grep -q 'dynamicGeometry' "$PLUGIN/assets/js/sc-workbench-v531-admin.js"
grep -q 'draggable-points' "$ROOT/backend/app/v550.py"
grep -q 'affine-transformations' "$ROOT/backend/app/v550.py"
grep -q 'expression-linked-loci' "$ROOT/backend/app/v550.py"
grep -q 'canonical-geometry-objects' "$ROOT/backend/app/v550.py"

find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi

echo "Workbench v5.5.0 release checks passed."
