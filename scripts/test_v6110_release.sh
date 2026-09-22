#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo '=== Workbench v6.11.0 release validation ==='
grep -q 'APP_VERSION = "6.11.0"' "$ROOT/backend/app/release.py"
grep -q 'version="6.11.0"' "$ROOT/backend/app/main.py"
grep -q 'from app.v6110 import router as v6110_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.11.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.11.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'scwb-v6110-forensic-quantitative-reconstruction.php' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -Fq "require_once __DIR__ . '/includes/scwb-v6100-predictive-intelligence-runtime.php';" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -Fq "require_once __DIR__ . '/includes/scwb-v6110-forensic-quantitative-reconstruction.php';" "$PLUGIN/sustainable-catalyst-workbench.php"
if grep -q 'SCWB_DIR' "$PLUGIN/sustainable-catalyst-workbench.php"; then echo 'FAIL: undefined SCWB_DIR bootstrap reference detected' >&2; exit 1; fi
grep -q 'sustainable-catalyst-workbench:6.11.0' "$ROOT/compose.yml"
grep -q 'sc.open-forensics.quantitative-reconstruction.v1' "$ROOT/backend/app/v6110.py"
grep -q 'sc.forensic-quantitative-handoff.v1' "$ROOT/backend/app/v6110.py"
grep -q 'sc.open-forensics.quantitative-reproduction-package.v1' "$ROOT/backend/app/v6110.py"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/v650.py" "$ROOT/backend/app/v660.py" "$ROOT/backend/app/v670.py" "$ROOT/backend/app/v680.py" "$ROOT/backend/app/v690.py" "$ROOT/backend/app/v6100.py" "$ROOT/backend/app/v6110.py" "$ROOT/backend/app/main.py"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q \
 tests/test_platform_core_connectivity_v640.py \
 tests/test_unified_runtime_contract_adapter_v650.py \
 tests/test_unified_research_session_bridge_v660.py \
 tests/test_computation_execution_lineage_bridge_v670.py \
 tests/test_scenario_uncertainty_runtime_v680.py \
 tests/test_visual_reasoning_runtime_adapter_v690.py \
 tests/test_predictive_intelligence_runtime_v6100.py \
 tests/test_forensic_quantitative_reconstruction_v6110.py)
(cd "$ROOT" && PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q \
 tests/test_v640_static.py tests/test_v650_static.py tests/test_v660_static.py tests/test_v670_static.py \
 tests/test_v680_static.py tests/test_v690_static.py tests/test_v6100_static.py tests/test_v6110_static.py)
if command -v php >/dev/null 2>&1; then
 php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null
 php -l "$PLUGIN/includes/scwb-v6110-forensic-quantitative-reconstruction.php" >/dev/null
fi
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='6.11.0'
s=c.get('/v6110/status'); assert s.status_code==200 and s.json()['truthDetermination'] is False
m=c.get('/integration/core/forensic-quantitative/manifest'); assert m.status_code==200 and m.json()['coreForensicHandoffContract']=='sc.forensic-quantitative-handoff.v1'
p={'reconstructionKey':'release-probe','points':[{'pointKey':'a','timeSeconds':0,'x':0,'y':0},{'pointKey':'b','timeSeconds':2,'x':3,'y':4}]}
r=c.post('/forensics/reconstruction/trajectory',json=p); assert r.status_code==200 and r.json()['segments'][0]['distance']==5.0
h=c.post('/forensics/reconstruction/hypothesis-metrics',json={'observations':[1,2],'hypotheses':[{'hypothesisRef':'h1','predictions':[1,2]},{'hypothesisRef':'h2','predictions':[2,3]}]}); assert h.status_code==200 and h.json()['ranked'] is False and h.json()['winner'] is None
print('PASS: Workbench v6.11.0 forensic quantitative reconstruction endpoints assembled')
PY
)
echo 'PASS: Workbench v6.11.0 release checks passed.'
