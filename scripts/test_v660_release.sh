#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo '=== Workbench v6.6.0 release validation ==='
grep -q 'APP_VERSION = "6.6.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v660 import router as v660_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.6.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.6.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.6.0' "$ROOT/compose.yml"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/v650.py" "$ROOT/backend/app/v660.py" "$ROOT/backend/app/main.py"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q tests/test_unified_research_session_bridge_v660.py tests/test_unified_runtime_contract_adapter_v650.py tests/test_platform_core_connectivity_v640.py)
(cd "$ROOT" && PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q tests/test_v660_static.py tests/test_v650_static.py tests/test_v640_static.py)
if command -v php >/dev/null 2>&1; then php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null; php -l "$PLUGIN/includes/scwb-v660-unified-research-session-bridge.php" >/dev/null; fi
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY_VALIDATOR'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v650/status','/v660/status','/integration/core/unified-runtime/manifest'):
 r=c.get(path); assert r.status_code==200,(path,r.status_code,r.text)
health=c.get('/health').json(); assert health['ok'] is True and health['version']=='6.6.0' and health['coreCompatible'] is True
caps=c.get('/capabilities').json(); assert caps['coreIntegration']['unifiedResearchSessionBinding'] is True
manifest=c.get('/integration/core/unified-runtime/manifest').json(); assert manifest['version']=='6.6.0'; assert manifest['runtimeContractRef']=='sc.research.unified-runtime-contract.v1'; assert manifest['coreUnifiedRuntimeContract']=='sc.research.unified-research-scientific-investigation-runtime.v1'
for path in ('/integration/core/unified-runtime/sessions/build','/integration/core/unified-runtime/projects/bind','/integration/core/unified-runtime/executions/bind','/integration/core/unified-runtime/visuals/bind','/integration/core/unified-runtime/validations/bind','/integration/core/unified-runtime/packages/bind','/integration/core/unified-runtime/handoffs/bind','/integration/core/unified-runtime/bundles/consume'):
 r=c.post(path,json={}); assert r.status_code != 404,(path,r.status_code,r.text)
print('PASS: Workbench v6.6.0 unified research session bridge endpoints assembled')
PY_VALIDATOR
)
echo 'PASS: Workbench v6.6.0 release checks passed.'
