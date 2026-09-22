#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"

printf '%s\n' '=== Workbench v6.5.0 release validation ==='
grep -q 'APP_VERSION = "6.5.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v650 import router as v650_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.5.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.5.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.5.0' "$ROOT/compose.yml"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"

"$PYTHON_BIN" -m py_compile \
  "$ROOT/backend/app/release.py" \
  "$ROOT/backend/app/v640.py" \
  "$ROOT/backend/app/v650.py" \
  "$ROOT/backend/app/main.py"

(
  cd "$ROOT/backend"
  PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q \
    tests/test_unified_runtime_contract_adapter_v650.py \
    tests/test_platform_core_connectivity_v640.py
)

(
  cd "$ROOT"
  PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q \
    tests/test_v650_static.py \
    tests/test_v640_static.py
)

if command -v php >/dev/null 2>&1; then
  php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null
  php -l "$PLUGIN/includes/scwb-v640-platform-core-connectivity.php" >/dev/null
  php -l "$PLUGIN/includes/scwb-v650-unified-runtime-contract-adapter.php" >/dev/null
fi

(
  cd "$ROOT/backend"
  PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v640/status','/v650/status'):
    r=c.get(path)
    assert r.status_code==200,(path,r.status_code,r.text)
health=c.get('/health').json()
assert health['ok'] is True and health['version']=='6.5.0' and health['coreCompatible'] is True
caps=c.get('/capabilities').json()
assert caps['coreIntegration']['connectivityFoundation'] is True
assert caps['coreIntegration']['unifiedRuntimeContractAdapter'] is True
manifest=c.get('/integration/core/runtime-contract/manifest')
assert manifest.status_code==200,manifest.text
m=manifest.json()
assert m['version']=='6.5.0'
assert m['contract']=='sc.research.unified-runtime-contract.v1'
assert m['boundaries']['automaticCoreDispatchAuthorized'] is False
# Probe every v6.5 route through the ASGI app instead of relying on
# FastAPI/Starlette internal route-object shapes. Current FastAPI versions may
# retain included routers as _IncludedRouter objects, while TestClient still
# resolves their child routes correctly. A non-404 validation response proves
# the route is registered; successful GETs above verify the public read paths.
for required in (
    '/integration/core/runtime-contract/validate',
    '/integration/core/runtime-contract/product-binding',
    '/integration/core/runtime-contract/project/map',
    '/integration/core/runtime-contract/exchanges/consume',
    '/integration/core/runtime-contract/exchanges/build',
    '/integration/core/runtime-contract/invocations/build',
    '/integration/core/runtime-contract/results/build',
):
    probe=c.post(required,json={})
    assert probe.status_code != 404,(required,probe.status_code,probe.text)
print('PASS: Workbench v6.5.0 unified runtime adapter endpoints assembled')
PY
)

printf '%s\n' 'PASS: Workbench v6.5.0 release checks passed.'
