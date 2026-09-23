#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.12.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.12.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v7120.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v7120.py' | head -1)"; [[ -n "$marker" ]] || fail "v7.12.0 reproducible package module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.12.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-reproducible-experiment-engineering-package/1.0' "$SRC_BACKEND/app/v7120.py" || fail "reproducible package schema missing"
grep -q 'sc.research.reproducible-package.v1' "$SRC_BACKEND/app/v7120.py" || fail "Platform Core reproducible package contract missing"
grep -q 'sustainable-catalyst-workbench:7.12.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v7.12.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.12.0.env.example" "$ROOT/workbench-v7.12.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING REPRODUCIBLE EXPERIMENT & ENGINEERING PACKAGE ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {}); r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v7120/status','/repro-package/manifest'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.12.0' and health['coreCompatible'] is True,health
spec={'packageKey':'deploy-v7120','title':'Deploy Reproducible Package','projectEntityId':'project:deploy','packageKind':'mixed','components':[
 {'componentKey':'notebook','componentType':'notebook-run','componentRef':'sc://workbench/notebook/deploy','payload':{'notebookRunHash':'deploy-nb','cells':[]}},
 {'componentKey':'dataset','componentType':'dataset','componentRef':'sc://dataset/deploy','contentHash':'a'*64,'required':True}
], 'environments':[{'environmentKey':'workbench','environmentType':'workbench','environmentRef':'sc://workbench/runtime/7.12.0','versionRef':'7.12.0'}]}
s,p,_=req('/repro-package/build',{'package':spec}); assert s==200,p; assert p['integrityManifest']['allRequiredComponentsHashed'] is True and p['boundaries']['automaticReplayAuthorized'] is False,p
s,v,_=req('/repro-package/validate',{'reproduciblePackage':p}); assert s==200 and v['valid'] is True,v
s,rp,_=req('/repro-package/replay/plan',{'reproduciblePackage':p,'mode':'replay'}); assert s==200 and rp['replayPerformed'] is False and rp['automaticExecutionReplayAuthorized'] is False,rp
s,ep,_=req('/repro-package/export/plan',{'reproduciblePackage':p}); assert s==200 and ep['archiveWritePerformed'] is False,ep
headers={'X-Request-ID':'deploy-v7120','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}: token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,plan,_=req('/integration/core/repro-package/plan',{'reproduciblePackage':p,'coreProjectEntityId':'core-project-v7120'},headers); assert s==200,plan; assert plan['coreContract']=='sc.research.reproducible-package.v1' and plan['corePackageIdMustComeFromCore'] is True and plan['automaticCoreDispatchAuthorized'] is False,plan
print('PASS: /health reports Workbench 7.12.0')
print('PASS: content-addressed experiment/engineering package manifests and integrity validation are active')
print('PASS: explicit replay/export planning is active without automatic execution or filesystem writes')
print('PASS: Workbench state assembly and required external-reference hashing are active')
print('PASS: Platform Core reproducible-package planning remains two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
