#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"

printf '%s\n' '=== Workbench v6.4.0 release validation ==='
grep -q 'APP_VERSION = "6.4.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v640 import router as v640_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.4.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.4.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.4.0' "$ROOT/compose.yml"
grep -q 'SCWB_CORE_EXPECTED_VERSION_PREFIX' "$ROOT/compose.yml"
grep -q 'healthcheck:' "$ROOT/compose.yml"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"

"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/main.py"
"$PYTHON_BIN" -c 'import httpx2'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q -p no:cacheprovider \
  "$ROOT/backend/tests/test_platform_core_connectivity_v640.py" \
  "$ROOT/tests/test_v640_static.py" \
  "$ROOT/backend/tests/test_energy_grid_storage_reliability_v630.py"

if command -v php >/dev/null 2>&1; then
  php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null
  php -l "$PLUGIN/includes/scwb-v640-platform-core-connectivity.php" >/dev/null
fi
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose -f "$ROOT/compose.yml" config --quiet
fi

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v640/status'):
    r=c.get(path); assert r.status_code==200,(path,r.status_code,r.text)
h=c.get('/health').json(); assert h['ok'] and h['version']=='6.4.0' and h['coreCompatible'] is True
paths=set(app.openapi()['paths'])
for required in ('/health','/runtime','/capabilities','/integration/core/status','/v640/status'):
    assert required in paths, required
print('PASS: Workbench v6.4.0 Core connectivity endpoints assembled')
PY

if grep -RInE --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir='__pycache__' --exclude='*.md' --exclude='*.txt' --exclude='*.zip' \
  '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})' "$ROOT"; then
  echo 'Potential secret detected.' >&2
  exit 1
fi

find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$ROOT" -type f -name '*.pyc' -delete
printf '%s\n' 'PASS: Workbench v6.4.0 release checks passed.'
