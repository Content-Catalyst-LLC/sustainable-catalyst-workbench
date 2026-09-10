#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
export GIT_PAGER=cat
export PAGER=cat

echo "Testing Sustainable Catalyst Workbench v5.9.0"
grep -q 'Version: 5.9.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '5.9.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v590-fpga-pynq-digital-logic.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'data-scwb-version="5.9.0"' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'version="5.9.0"' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:5.9.0' "$ROOT/compose.yml"
grep -q 'from app.v590 import router as v590_router' "$ROOT/backend/app/main.py"
grep -q '"version": "5.9.0"' "$ROOT/offline/package-manifest.json"

find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done

for v in 590 580 570 560 550 540; do php "$ROOT/tests/test_v${v}_plugin_activation.php"; done
for v in 590 580 570 560 550 540 533 532 531 530 520 510 500; do php "$ROOT/tests/test_v${v}_wordpress_runtime.php"; done
for v in 590 580 570 560 550 540 533 532 531 530 520 510 500; do node "$ROOT/tests/test_v${v}_browser.js"; done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"

for required in \
  "$ROOT/backend/app/v590.py" \
  "$PLUGIN/includes/scwb-v590-fpga-pynq-digital-logic.php" \
  "$PLUGIN/assets/css/sc-workbench-v590.css" \
  "$PLUGIN/assets/js/sc-workbench-v590.js" \
  "$ROOT/docs/V590_FPGA_PYNQ_DIGITAL_LOGIC.md" \
  "$ROOT/docs/V590_SECURITY_BOUNDARY.md" \
  "$ROOT/examples/v590-digital-logic-fixture.json" \
  "$ROOT/V590_RELEASE_NOTES.md"; do
  [[ -s "$required" ]] || { echo "Missing v5.9.0 artifact: $required" >&2; exit 1; }
done

if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v590.py"; then echo 'Unsafe eval/exec detected in v590 backend.' >&2; exit 1; fi
if grep -nE 'subprocess\.|os\.system\(|serial\.Serial|/dev/tty|jtag|openocd' "$ROOT/backend/app/v590.py" | grep -vE 'jtagAccessAuthorized|JTAG'; then echo 'Unauthorized device/shell primitive detected in v590 backend.' >&2; exit 1; fi
if grep -nE 'new Function\(|window\.scrollTo\(|scrollIntoView\(' "$PLUGIN/assets/js/sc-workbench-v590.js"; then echo 'Unsafe browser execution/viewport primitive detected in v590.' >&2; exit 1; fi

grep -q "'/v590/status'" "$PLUGIN/includes/scwb-v531-settings-backend-repair.php"
grep -q 'digitalLogic' "$PLUGIN/assets/js/sc-workbench-v531-admin.js"
grep -q 'restricted-boolean-expression-parser' "$ROOT/backend/app/v590.py"
grep -q 'boolean-minimization' "$ROOT/backend/app/v590.py"
grep -q 'karnaugh-maps' "$ROOT/backend/app/v590.py"
grep -q 'finite-state-machine-validation' "$ROOT/backend/app/v590.py"
grep -q 'digital-timing-waveforms' "$ROOT/backend/app/v590.py"
grep -q 'verilog-scaffolds' "$ROOT/backend/app/v590.py"
grep -q 'pynq-overlay-scaffolds' "$ROOT/backend/app/v590.py"
grep -q 'canonical-digital-logic-objects' "$ROOT/backend/app/v590.py"

# Direct assembled-route and deterministic-function smoke checks. Deliberately
# avoids FastAPI TestClient so the release gate does not depend on httpx extras.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from app.main import app
from app.v590 import (
    BooleanExpressionInput, KarnaughInput, FSMInput, FSMTransition, TimingInput, TimingSignal,
    HDLScaffoldInput, PYNQOverlayInput, truth_table_object, minimize_object, karnaugh_object,
    fsm_object, timing_object, hdl_scaffold_object, pynq_overlay_object, status_record,
)
paths=set(app.openapi().get('paths', {}).keys())
for path in ['/v590/status','/v590/truth-table','/v590/minimize','/v590/karnaugh','/v590/fsm','/v590/timing','/v590/hdl-scaffold','/v590/resource-estimate','/v590/pynq-overlay']:
    assert path in paths, path
assert status_record()['version']=='5.9.0'
t=truth_table_object(BooleanExpressionInput(expression='A ^ B')); assert [r['output'] for r in t['result']['rows']]==[0,1,1,0]
m=minimize_object(BooleanExpressionInput(expression='(A & B) | (A & !B)')); assert m['result']['sumOfProducts']=='A'
k=karnaugh_object(KarnaughInput(expression='(!A & B) | (A & !B)')); assert k['result']['grid']==[[0,1],[1,0]]
f=fsm_object(FSMInput(states=['IDLE','RUN'],initialState='IDLE',transitions=[FSMTransition(fromState='IDLE',input='1',toState='RUN'),FSMTransition(fromState='RUN',input='0',toState='IDLE')])); assert f['result']['deterministic'] is True
w=timing_object(TimingInput(expression='A ^ B',signals=[TimingSignal(name='A',values=[0,0,1,1]),TimingSignal(name='B',values=[0,1,0,1])])); assert w['result']['output']==[0,1,1,0]
h=hdl_scaffold_object(HDLScaffoldInput(language='verilog',moduleName='demo_logic',expression='A ^ B')); assert h['result']['synthesisPerformed'] is False
p=pynq_overlay_object(PYNQOverlayInput(projectName='demo_overlay',moduleName='demo_logic',expression='A ^ B')); assert p['result']['bitstreamGenerated'] is False and p['result']['overlayLoaded'] is False
print('Workbench v5.9.0 assembled-route and digital-logic smoke tests passed.')
PY

find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi

echo "Workbench v5.9.0 release checks passed."
