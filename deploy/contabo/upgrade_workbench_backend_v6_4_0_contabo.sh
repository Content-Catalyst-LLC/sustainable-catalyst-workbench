#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="6.4.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v6.4.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v640.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v640.py' | head -1)"
[[ -n "$marker" ]] || fail "v6.4.0 connectivity module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "6.4.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sustainable-catalyst-workbench:6.4.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"

if [[ ! -d "$BACKUP_ROOT" ]]; then
  if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else
    command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo is unavailable"
    sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"
  fi
fi
if [[ ! -w "$BACKUP_ROOT" ]]; then
  command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo is unavailable"
  sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"
  sudo chmod 750 "$BACKUP_ROOT"
fi

stamp="$(date +%Y%m%d-%H%M%S)"
echo "=== BACKING UP $PRODUCT BACKEND ==="
tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"

rsync -a \
  --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' \
  --exclude='.env' --exclude='.env.*' \
  "$SRC_BACKEND/" "$LIVE_BACKEND/"
cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"
[[ -f "$PACKAGE_ROOT/workbench-v6.4.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v6.4.0.env.example" "$ROOT/workbench-v6.4.0.env.example"

cd "$ROOT"
docker compose -f "$COMPOSE" config --quiet
echo "=== BUILDING $PRODUCT v$VERSION ==="
docker compose -f "$COMPOSE" build "$SERVICE"
docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"

ready=0
for _ in $(seq 1 60); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
  case "$state" in
    healthy) ready=1; break ;;
    running) sleep 2 ;;
    unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;;
  esac
  sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }

echo "=== VERIFYING PLATFORM CORE CONNECTIVITY FOUNDATION ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json, os, urllib.request, urllib.error
base='http://127.0.0.1:8088'
def get(path, headers=None):
    req=urllib.request.Request(base+path,headers=headers or {'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=5) as r:
        return r.status, json.load(r), dict(r.headers)
for path in ('/health','/runtime','/capabilities','/v640/status'):
    status, body, headers=get(path)
    assert status==200,(path,status)
    assert body.get('ok') is True,(path,body)
health=get('/health')[1]
assert health['version']=='6.4.0',health
assert health['product']=='workbench',health
assert health['coreCompatible'] is True,health
headers={'Accept':'application/json','X-Request-ID':'deploy-v640','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
    token=os.getenv('SCWB_SERVICE_TOKEN','')
    assert token,'SCWB_REQUIRE_SERVICE_TOKEN=true but SCWB_SERVICE_TOKEN is empty'
    headers['X-SC-Service-Token']=token
status, core, response_headers=get('/integration/core/status',headers)
assert status==200,core
assert core['version']=='6.4.0',core
assert core['security']['secretsReturned'] is False,core
assert core['execution']['coreDispatchPerformed'] is False,core
print('PASS: /health reports Workbench 6.4.0 and Core compatibility')
print('PASS: runtime/capability surfaces are active')
print('PASS: Core integration status is reachable with configured token policy')
PYVERIFY

echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
