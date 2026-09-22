#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo '=== Workbench v6.8.0 release validation ==='
grep -q 'APP_VERSION = "6.8.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v680 import router as v680_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.8.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.8.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.8.0' "$ROOT/compose.yml"
grep -q 'scenario-compute-input-manifest-v1' "$ROOT/backend/app/v680.py"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/v650.py" "$ROOT/backend/app/v660.py" "$ROOT/backend/app/v670.py" "$ROOT/backend/app/v680.py" "$ROOT/backend/app/main.py"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q tests/test_scenario_uncertainty_runtime_v680.py tests/test_computation_execution_lineage_bridge_v670.py tests/test_unified_research_session_bridge_v660.py tests/test_unified_runtime_contract_adapter_v650.py tests/test_platform_core_connectivity_v640.py)
(cd "$ROOT" && PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q tests/test_v680_static.py tests/test_v670_static.py tests/test_v660_static.py tests/test_v650_static.py tests/test_v640_static.py)
if command -v php >/dev/null 2>&1; then php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null; php -l "$PLUGIN/includes/scwb-v680-scenario-uncertainty-runtime.php" >/dev/null; fi
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY_VALIDATOR'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v670/status','/v680/status','/integration/core/scenario-uncertainty/manifest'):
 r=c.get(path); assert r.status_code==200,(path,r.status_code,r.text)
health=c.get('/health').json(); assert health['ok'] is True and health['version']=='6.8.0' and health['coreCompatible'] is True
caps=c.get('/capabilities').json(); assert caps['coreIntegration']['scenarioUncertaintyRuntime'] is True
manifest=c.get('/integration/core/scenario-uncertainty/manifest').json(); assert manifest['version']=='6.8.0'; assert manifest['coreScenarioInputManifestSchema']=='scenario-compute-input-manifest-v1'
for path in ('/integration/core/scenario-uncertainty/scenario/request/consume','/integration/core/scenario-uncertainty/scenario/affine/run','/integration/core/scenario-uncertainty/scenario/callbacks/build','/integration/core/scenario-uncertainty/sampling/design/run','/integration/core/scenario-uncertainty/sensitivity/sobol/run','/integration/core/scenario-uncertainty/sensitivity/morris/run','/integration/core/scenario-uncertainty/ensembles/statistics/run','/integration/core/scenario-uncertainty/probabilities/exceedance/run'):
 r=c.post(path,json={}); assert r.status_code != 404,(path,r.status_code,r.text)
r=c.post('/integration/core/scenario-uncertainty/sampling/design/run',json={'method':'monte-carlo','sampleCount':4,'seed':42,'factors':[{'key':'x','distribution':'uniform','lowerBound':0,'upperBound':1}]}); assert r.status_code==200,r.text; d=r.json(); assert len(d['samples'])==4 and d['calculated_by_workbench'] is True
scenario={'schema':'scenario-compute-input-manifest-v1','project_entity_id':'p','model_entity_id':'m','model_version_entity_id':'mv','scenario_entity_id':'s','execution_product':'workbench','parameter_values':{'x':2,'y':3},'expected_outputs':['z'],'execution_contract':{},'output_contract':{},'case_hash':'h','core_execution':False}
r=c.post('/integration/core/scenario-uncertainty/scenario/affine/run',json={'coreRequestId':'release-probe','inputManifest':scenario,'outputs':{'z':{'intercept':1,'coefficients':{'x':2,'y':3}}}}); assert r.status_code==200,r.text; d=r.json(); assert d['outputs'][0]['value']==14 and d['automaticCorePersistenceAuthorized'] is False
print('PASS: Workbench v6.8.0 scenario and uncertainty runtime endpoints assembled')
PY_VALIDATOR
)
echo 'PASS: Workbench v6.8.0 release checks passed.'
