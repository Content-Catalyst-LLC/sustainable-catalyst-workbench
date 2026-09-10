#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
export GIT_PAGER=cat
export PAGER=cat

echo "Testing Sustainable Catalyst Workbench v6.0.0"
grep -q 'Version: 6.0.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.0.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v600-unified-computational-workbench.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'data-scwb-version="6.0.0"' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'version="6.0.0"' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:6.0.0' "$ROOT/compose.yml"
grep -q 'from app.v600 import router as v600_router' "$ROOT/backend/app/main.py"
grep -q '"version": "6.0.0"' "$ROOT/offline/package-manifest.json"

find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done

for v in 600 590 580 570 560 550 540; do php "$ROOT/tests/test_v${v}_plugin_activation.php"; done
for v in 600 590 580 570 560 550 540 533 532 531 530 520 510 500; do php "$ROOT/tests/test_v${v}_wordpress_runtime.php"; done
for v in 600 590 580 570 560 550 540 533 532 531 530 520 510 500; do node "$ROOT/tests/test_v${v}_browser.js"; done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"

for required in \
  "$ROOT/backend/app/v600.py" \
  "$PLUGIN/includes/scwb-v600-unified-computational-workbench.php" \
  "$PLUGIN/assets/css/sc-workbench-v600.css" \
  "$PLUGIN/assets/js/sc-workbench-v600.js" \
  "$ROOT/docs/V600_UNIFIED_COMPUTATIONAL_WORKBENCH.md" \
  "$ROOT/docs/V600_SECURITY_BOUNDARY.md" \
  "$ROOT/examples/v600-unified-computational-project-fixture.json" \
  "$ROOT/V600_RELEASE_NOTES.md"; do
  [[ -s "$required" ]] || { echo "Missing v6.0.0 artifact: $required" >&2; exit 1; }
done

if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v600.py"; then echo 'Unsafe eval/exec detected in v600 backend.' >&2; exit 1; fi
if grep -nE 'subprocess\.|os\.system\(|serial\.Serial|/dev/tty|openocd' "$ROOT/backend/app/v600.py"; then echo 'Unauthorized device/shell primitive detected in v600 backend.' >&2; exit 1; fi
if grep -nE 'new Function\(|window\.scrollTo\(|scrollIntoView\(' "$PLUGIN/assets/js/sc-workbench-v600.js"; then echo 'Unsafe browser execution/viewport primitive detected in v600.' >&2; exit 1; fi

grep -q "'/v600/status'" "$PLUGIN/includes/scwb-v531-settings-backend-repair.php"
grep -q 'unifiedComputational' "$PLUGIN/assets/js/sc-workbench-v531-admin.js"
grep -q 'canonical-computational-projects' "$ROOT/backend/app/v600.py"
grep -q 'shared-project-variables' "$ROOT/backend/app/v600.py"
grep -q 'linked-computational-objects' "$ROOT/backend/app/v600.py"
grep -q 'computational-provenance' "$ROOT/backend/app/v600.py"
grep -q 'append-only-project-history' "$ROOT/backend/app/v600.py"
grep -q 'portable-computational-exports' "$ROOT/backend/app/v600.py"
grep -q 'cross-platform-handoff-packets' "$ROOT/backend/app/v600.py"

# Direct assembled-route and deterministic project smoke checks. Avoid TestClient
# so the release gate does not depend on optional HTTP client extras.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from app.main import app
from app.v600 import (
    ComputationalObject, HandoffRequest, LinkGraphRequest, ObjectLink,
    ProjectBuildRequest, ProjectInput, SharedVariable, VariableSetRequest,
    build_handoff, build_link_graph, build_project, resolve_variables, status_record,
)
paths=set(app.openapi().get('paths', {}).keys())
for path in ['/v600/status','/v600/project/build','/v600/variables/resolve','/v600/links/validate','/v600/provenance/build','/v600/history/build','/v600/export/build','/v600/handoff/build']:
    assert path in paths, path
assert status_record()['version']=='6.0.0'
p=ProjectInput(projectId='smoke',title='Smoke',variables=[SharedVariable(name='a',value=2)],objects=[
    ComputationalObject(objectId='math',kind='expression',studio='mathematics',variableInputs=['a']),
    ComputationalObject(objectId='graph',kind='graph',studio='graph-mathematics',variableInputs=['a'],dependencyObjectIds=['math']),
])
r=build_project(ProjectBuildRequest(project=p)); assert r['ok'] and len(r['projectHash'])==64
v=resolve_variables(VariableSetRequest(variables=p.variables,overrides={'a':3})); assert v['result']['variables'][0]['value']==3
l=build_link_graph(LinkGraphRequest(objects=p.objects,links=[ObjectLink(fromObjectId='math',toObjectId='graph')])); assert l['ok'] and l['result']['topologicalOrder']==['math','graph']
h=build_handoff(HandoffRequest(project=p,targetSurface='lab',objectIds=['graph'])); assert h['ok'] and h['result']['automaticRemoteActionAuthorized'] is False
print('Workbench v6.0.0 assembled-route and unified-project smoke tests passed.')
PY

find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi

echo "Workbench v6.0.0 release checks passed."
