#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"

export GIT_PAGER=cat
export PAGER=cat

echo "Testing Sustainable Catalyst Workbench v5.8.0"
grep -q 'Version: 5.8.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '5.8.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v580-electronics-embedded-systems.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'data-scwb-version="5.8.0"' "$PLUGIN/includes/scwb-primary-shortcode.php"
grep -q 'version="5.8.0"' "$ROOT/backend/app/main.py"
grep -q 'sustainable-catalyst-workbench:5.8.0' "$ROOT/compose.yml"
grep -q 'from app.v580 import router as v580_router' "$ROOT/backend/app/main.py"
grep -q '"version": "5.8.0"' "$ROOT/offline/package-manifest.json"

find "$PLUGIN" -type f -name '*.php' -print0 | while IFS= read -r -d '' file; do php -l "$file" >/dev/null; done
find "$PLUGIN/assets/js" -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done
find "$ROOT/installers" "$ROOT/scripts" -type f \( -name '*.sh' -o -name '*.command' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done

for v in 580 570 560 550 540; do php "$ROOT/tests/test_v${v}_plugin_activation.php"; done
for v in 580 570 560 550 540 533 532 531 530 520 510 500; do php "$ROOT/tests/test_v${v}_wordpress_runtime.php"; done

for v in 580 570 560 550 540 533 532 531 530 520 510 500; do node "$ROOT/tests/test_v${v}_browser.js"; done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider "$ROOT/tests"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app"/*.py "$ROOT/offline/start_local_workbench.py"

for required in \
  "$ROOT/backend/app/v580.py" \
  "$PLUGIN/includes/scwb-v580-electronics-embedded-systems.php" \
  "$PLUGIN/assets/css/sc-workbench-v580.css" \
  "$PLUGIN/assets/js/sc-workbench-v580.js" \
  "$ROOT/docs/V580_ELECTRONICS_EMBEDDED_SYSTEMS.md" \
  "$ROOT/docs/V580_SECURITY_BOUNDARY.md" \
  "$ROOT/examples/v580-electronics-embedded-fixture.json" \
  "$ROOT/V580_RELEASE_NOTES.md"; do
  [[ -s "$required" ]] || { echo "Missing v5.8.0 artifact: $required" >&2; exit 1; }
done

if grep -nE '\beval\(|\bexec\(' "$ROOT/backend/app/v580.py"; then echo 'Unsafe eval/exec detected in v580 backend.' >&2; exit 1; fi
if grep -nE 'serial\.Serial|/dev/tty|subprocess\.|os\.system\(' "$ROOT/backend/app/v580.py"; then echo 'Unauthorized device/shell primitive detected in v580 backend.' >&2; exit 1; fi
if grep -nE 'new Function\(|window\.scrollTo\(|scrollIntoView\(' "$PLUGIN/assets/js/sc-workbench-v580.js"; then echo 'Unsafe browser execution/viewport primitive detected in v580.' >&2; exit 1; fi

grep -q "'/v580/status'" "$PLUGIN/includes/scwb-v531-settings-backend-repair.php"
grep -q 'electronicsEmbedded' "$PLUGIN/assets/js/sc-workbench-v531-admin.js"
grep -q 'resistor-network-analysis' "$ROOT/backend/app/v580.py"
grep -q 'adc-dac-quantization' "$ROOT/backend/app/v580.py"
grep -q 'pwm-timer-planning' "$ROOT/backend/app/v580.py"
grep -q 'i2c-spi-uart-planning' "$ROOT/backend/app/v580.py"
grep -q 'gpio-allocation-planning' "$ROOT/backend/app/v580.py"
grep -q 'export-only-embedded-scaffolds' "$ROOT/backend/app/v580.py"
grep -q 'canonical-electronics-embedded-objects' "$ROOT/backend/app/v580.py"

# FastAPI route smoke tests through the assembled application.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT:$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient
from backend.app.main import app
c=TestClient(app)
r=c.get('/v580/status'); assert r.status_code==200 and r.json()['version']=='5.8.0'
r=c.post('/v580/resistor-network',json={'topology':'series','resistancesOhm':[100,200],'sourceVoltageV':6}); assert r.status_code==200 and abs(r.json()['result']['equivalentResistanceOhm']-300)<1e-12
r=c.post('/v580/adc-dac',json={'bits':12,'referenceVoltageV':3.3,'inputVoltageV':1.65,'dacCode':2048}); assert r.status_code==200 and r.json()['result']['maxCode']==4095
r=c.post('/v580/pwm-timer',json={'clockHz':16000000,'desiredFrequencyHz':1000,'dutyCyclePercent':50,'counterBits':16,'alignment':'edge','availablePrescalers':[1,8,64,256,1024]}); assert r.status_code==200 and abs(r.json()['result']['selected']['actualFrequencyHz']-1000)<1e-9
r=c.post('/v580/prototype-scaffold',json={'target':'arduino','projectName':'demo_project','interface':'pwm','sampleRateHz':1000}); assert r.status_code==200 and r.json()['result']['exportOnly'] is True
print('Workbench v5.8.0 FastAPI electronics/embedded smoke tests passed.')
PY

find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='.venv*' --exclude-dir='venv' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' --exclude='*.pyc' '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then echo 'Potential secret detected.' >&2; exit 1; fi

echo "Workbench v5.8.0 release checks passed."
