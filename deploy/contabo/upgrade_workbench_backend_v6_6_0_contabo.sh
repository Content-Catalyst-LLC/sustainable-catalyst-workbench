#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="6.6.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v6.6.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v660.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v660.py' | head -1)"
[[ -n "$marker" ]] || fail "v6.6.0 unified session bridge module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "6.6.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sustainable-catalyst-workbench:6.6.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
grep -q 'httpx2>=2,<3' "$SRC_BACKEND/requirements.txt" || fail "httpx2 dependency missing"
if [[ ! -d "$BACKUP_ROOT" ]]; then
  if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi
fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"
echo "=== BACKING UP $PRODUCT BACKEND ==="
tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"
cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"
[[ -f "$PACKAGE_ROOT/workbench-v6.6.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v6.6.0.env.example" "$ROOT/workbench-v6.6.0.env.example"
cd "$ROOT"
docker compose -f "$COMPOSE" config --quiet
echo "=== BUILDING $PRODUCT v$VERSION ==="
docker compose -f "$COMPOSE" build "$SERVICE"
docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0
for _ in $(seq 1 60); do
 state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
 case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac
 sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING UNIFIED RESEARCH SESSION BRIDGE ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json, os, urllib.request, urllib.error
base='http://127.0.0.1:8088'
def req(path, data=None, headers=None):
    h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {})
    r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
    with urllib.request.urlopen(r,timeout=6) as x: return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v660/status'):
    status,body,_=req(path); assert status==200,(path,status); assert body.get('ok') is True,(path,body)
health=req('/health')[1]; assert health['version']=='6.6.0' and health['coreCompatible'] is True,health
caps=req('/capabilities')[1]; assert caps['coreIntegration']['unifiedResearchSessionBinding'] is True,caps
headers={'X-Request-ID':'deploy-v660','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
    token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token,'SCWB_REQUIRE_SERVICE_TOKEN=true but token empty'; headers['X-SC-Service-Token']=token
status,m,_=req('/integration/core/unified-runtime/manifest',headers=headers); assert status==200,m
assert m['version']=='6.6.0' and m['runtimeContractRef']=='sc.research.unified-runtime-contract.v1',m
assert m['coreUnifiedRuntimeContract']=='sc.research.unified-research-scientific-investigation-runtime.v1',m
sample={'project':{'projectId':'deploy-v660','title':'Deployment Verification','variables':[],'objects':[]}}
status,draft,_=req('/integration/core/unified-runtime/sessions/build',sample,headers); assert status==200,draft
assert draft['phase']=='prepare-session' and draft['coreRequest']['path']=='/v1/research/unified-runtime/sessions',draft
assert draft['automaticCorePersistenceAuthorized'] is False,draft
print('PASS: /health reports Workbench 6.6.0')
print('PASS: Core 3.0 unified research session bridge is active')
print('PASS: phase-one session request builds without automatic dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
