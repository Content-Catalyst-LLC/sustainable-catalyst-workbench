#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo '=== Workbench v6.7.0 release validation ==='
grep -q 'APP_VERSION = "6.7.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v670 import router as v670_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.7.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.7.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.7.0' "$ROOT/compose.yml"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/v650.py" "$ROOT/backend/app/v660.py" "$ROOT/backend/app/v670.py" "$ROOT/backend/app/main.py"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q tests/test_computation_execution_lineage_bridge_v670.py tests/test_unified_research_session_bridge_v660.py tests/test_unified_runtime_contract_adapter_v650.py tests/test_platform_core_connectivity_v640.py)
(cd "$ROOT" && PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q tests/test_v670_static.py tests/test_v660_static.py tests/test_v650_static.py tests/test_v640_static.py)
if command -v php >/dev/null 2>&1; then php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null; php -l "$PLUGIN/includes/scwb-v670-computation-execution-lineage.php" >/dev/null; fi
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY_VALIDATOR'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v660/status','/v670/status','/integration/core/computation-lineage/manifest'):
 r=c.get(path); assert r.status_code==200,(path,r.status_code,r.text)
health=c.get('/health').json(); assert health['ok'] is True and health['version']=='6.7.0' and health['coreCompatible'] is True
caps=c.get('/capabilities').json(); assert caps['coreIntegration']['executionLineageBridge'] is True
manifest=c.get('/integration/core/computation-lineage/manifest').json(); assert manifest['version']=='6.7.0'; assert manifest['coreComputationLineageContract']=='sc.research.computation-analysis-execution-lineage.v1'
for path in ('/integration/core/computation-lineage/executions/build','/integration/core/computation-lineage/executions/components/build','/integration/core/computation-lineage/executions/session-binding/build','/integration/core/computation-lineage/executions/lifecycle/build','/integration/core/computation-lineage/bundles/consume'):
 r=c.post(path,json={}); assert r.status_code != 404,(path,r.status_code,r.text)
r=c.post('/integration/core/computation-lineage/executions/build',json={'executionKey':'release-probe','title':'Release Probe'}); assert r.status_code==200,r.text; assert r.json()['coreExecutionIdMustComeFromCore'] is True
r=c.post('/integration/core/computation-lineage/executions/components/build',json={'coreExecutionId':'core-probe','inputs':[],'outputs':[]}); assert r.status_code==200,r.text; assert r.json()['automaticCorePersistenceAuthorized'] is False
print('PASS: Workbench v6.7.0 computation lineage endpoints assembled')
PY_VALIDATOR
)
echo 'PASS: Workbench v6.7.0 release checks passed.'
