#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
export GIT_PAGER=cat
export PAGER=cat

echo "Testing Sustainable Catalyst Workbench v6.0.1"
grep -q 'Version: 6.0.1' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.0.1')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v601-unified-experience-hardening.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'data-scwb-version="6.0.1"' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'version="6.0.1"' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:6.0.1' "$ROOT/compose.yml"
grep -q 'from app.v601 import router as v601_router' "$ROOT/backend/app/main.py"

find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done

for v in 601 600 590 580 570 560 550 540; do php "$ROOT/tests/test_v${v}_plugin_activation.php"; done
for v in 601 600 590 580 570 560 550 540 533 532 531 530 520 510 500; do php "$ROOT/tests/test_v${v}_wordpress_runtime.php"; done
for v in 601 600 590 580 570 560 550 540 533 532 531 530 520 510 500; do node "$ROOT/tests/test_v${v}_browser.js"; done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"

for required in \
  "$ROOT/backend/app/v601.py" \
  "$PLUGIN/includes/scwb-v601-unified-experience-hardening.php" \
  "$PLUGIN/assets/css/sc-workbench-v601.css" \
  "$PLUGIN/assets/js/sc-workbench-v601.js" \
  "$ROOT/docs/V601_UNIFIED_EXPERIENCE_RUNTIME_HARDENING.md" \
  "$ROOT/docs/V601_SECURITY_BOUNDARY.md" \
  "$ROOT/examples/v601-interface-status-fixture.json" \
  "$ROOT/V601_RELEASE_NOTES.md"; do
  [[ -s "$required" ]] || { echo "Missing v6.0.1 artifact: $required" >&2; exit 1; }
done

if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v601.py"; then echo 'Unsafe eval/exec detected in v601 backend.' >&2; exit 1; fi
if grep -nE 'subprocess\.|os\.system\(|serial\.Serial|/dev/tty|openocd' "$ROOT/backend/app/v601.py"; then echo 'Unauthorized device/shell primitive detected in v601 backend.' >&2; exit 1; fi
if grep -nE 'new Function\(|window\.scrollTo\(|scrollIntoView\(' "$PLUGIN/assets/js/sc-workbench-v601.js" "$PLUGIN/assets/js/scwb-primary-repair.js" "$PLUGIN/assets/js/sc-workbench-v540.js"; then echo 'Unsafe browser execution/viewport primitive detected in v601 interface line.' >&2; exit 1; fi
if grep -q 'sc_workbench_homepage_instrument' "$PLUGIN/includes/scwb-v601-unified-experience-hardening.php"; then echo 'Homepage instrument leaked into v6.0.1 Workbench experience.' >&2; exit 1; fi

grep -q "'/v601/status'" "$PLUGIN/includes/scwb-v531-settings-backend-repair.php"
grep -q 'UNIFIED EXPERIENCE' "$PLUGIN/includes/scwb-v531-settings-backend-repair.php"
grep -q 'ResizeObserver' "$PLUGIN/assets/js/sc-workbench-v540.js"
grep -q 'data-scwb-studio-filter' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'favoritesKey' "$PLUGIN/assets/js/scwb-primary-repair.js"
grep -q 'recentsKey' "$PLUGIN/assets/js/scwb-primary-repair.js"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from app.main import app
from app.v601 import status_record
from app.v600 import ProjectBuildRequest, ProjectInput, SharedVariable, ComputationalObject, build_project, status_record as v600_status
paths=set(app.openapi().get('paths',{}).keys())
for path in ['/v601/status','/v600/status','/v600/project/build','/v540/status']:
    assert path in paths, path
s=status_record(); assert s['ok'] and s['version']=='6.0.1' and s['homepageInstrumentOnWorkbenchPage'] is False
assert v600_status()['version']=='6.0.1'
p=ProjectInput(projectId='v601-smoke',title='v6.0.1 smoke',variables=[SharedVariable(name='a',value=2)],objects=[ComputationalObject(objectId='math',kind='expression',studio='mathematics',variableInputs=['a'])])
r=build_project(ProjectBuildRequest(project=p)); assert r['ok'] and len(r['projectHash'])==64
print('Workbench v6.0.1 assembled-route and identity smoke tests passed.')
PY

find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi

echo "Workbench v6.0.1 release checks passed."
