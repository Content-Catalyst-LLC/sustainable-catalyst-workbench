#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo '=== Workbench v6.10.0 release validation ==='
grep -q 'APP_VERSION = "6.10.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v6100 import router as v6100_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.10.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.10.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.10.0' "$ROOT/compose.yml"
grep -q 'sc.predictive.model.v1' "$ROOT/backend/app/v6100.py"
grep -q 'sc.predictive.probabilistic-forecast.v1' "$ROOT/backend/app/v6100.py"
grep -q 'sc.visual-runtime.predictive-intelligence.v1' "$ROOT/backend/app/v6100.py"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/v650.py" "$ROOT/backend/app/v660.py" "$ROOT/backend/app/v670.py" "$ROOT/backend/app/v680.py" "$ROOT/backend/app/v690.py" "$ROOT/backend/app/v6100.py" "$ROOT/backend/app/main.py"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q tests/test_predictive_intelligence_runtime_v6100.py tests/test_visual_reasoning_runtime_adapter_v690.py tests/test_scenario_uncertainty_runtime_v680.py tests/test_computation_execution_lineage_bridge_v670.py tests/test_unified_research_session_bridge_v660.py tests/test_unified_runtime_contract_adapter_v650.py tests/test_platform_core_connectivity_v640.py)
(cd "$ROOT" && PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q tests/test_v6100_static.py tests/test_v690_static.py tests/test_v680_static.py tests/test_v670_static.py tests/test_v660_static.py tests/test_v650_static.py tests/test_v640_static.py)
if command -v php >/dev/null 2>&1; then php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null; php -l "$PLUGIN/includes/scwb-v6100-predictive-intelligence-runtime.php" >/dev/null; fi
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v690/status','/v6100/status','/integration/core/predictive-intelligence/manifest'):
 r=c.get(path); assert r.status_code==200,(path,r.status_code,r.text)
health=c.get('/health').json(); assert health['version']=='6.10.0' and health['coreCompatible'] is True
caps=c.get('/capabilities').json(); assert caps['coreIntegration']['predictiveIntelligenceRuntime'] is True
m=c.get('/integration/core/predictive-intelligence/manifest').json(); assert m['corePredictiveModelContract']=='sc.predictive.model.v1'; assert m['coreVisualPredictiveContract']=='sc.visual-runtime.predictive-intelligence.v1'
p={'projectEntityId':'project-release-probe','modelKey':'release-trend','modelName':'Release Trend','history':[1,2,3,4,5,6],'horizon':3,'method':'linear-trend'}
r=c.post('/predictive/forecast',json=p); assert r.status_code==200,r.text; f=r.json(); assert f['pointForecast']==[7.0,8.0,9.0]
r=c.post('/integration/core/predictive-intelligence/model/plan',json={'forecastResult':f}); assert r.status_code==200,r.text; assert r.json()['coreModelIdMustComeFromCore'] is True
r=c.post('/integration/core/predictive-intelligence/forecast/plan',json={'forecastResult':f,'coreModelId':'model-release-probe','coreTargetId':'target-release-probe'}); assert r.status_code==200,r.text; assert r.json()['coreProbabilisticForecastIdMustComeFromCore'] is True
print('PASS: Workbench v6.10.0 predictive intelligence runtime endpoints assembled')
PY
)
echo 'PASS: Workbench v6.10.0 release checks passed.'
