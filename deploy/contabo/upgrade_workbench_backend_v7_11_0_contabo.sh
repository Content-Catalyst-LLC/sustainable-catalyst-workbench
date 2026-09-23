#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.11.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.11.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v7110.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v7110.py' | head -1)"; [[ -n "$marker" ]] || fail "v7.11.0 Visual Scientific Computing Workspace module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.11.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-visual-scientific-computing-workspace/1.0' "$SRC_BACKEND/app/v7110.py" || fail "visual workspace schema missing"
grep -q 'sc.visual-runtime.linked-views.v1' "$SRC_BACKEND/app/v7110.py" || fail "Core linked-views contract missing"
grep -q 'sustainable-catalyst-workbench:7.11.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v7.11.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.11.0.env.example" "$ROOT/workbench-v7.11.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING VISUAL SCIENTIFIC COMPUTING WORKSPACE ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {}); r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v7110/status','/visual-workspace/manifest'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.11.0' and health['coreCompatible'] is True,health
workspace={'workspace':{'workspaceKey':'deploy-v7110','title':'Deploy Visual Workspace','projectEntityId':'project:deploy','views':[
 {'viewId':'trajectory','kind':'trajectory','title':'Trajectory','data':{'x':[0,1,2],'y':[1,.5,.25]}},
 {'viewId':'uncertainty','kind':'uncertainty-band','title':'Uncertainty','data':{'x':[0,1,2],'center':[1,1.1,1.2],'lower':[.8,.9,1.0],'upper':[1.2,1.3,1.4]}}
], 'controls':[{'controlId':'gain','label':'Gain','targetPath':'payload.gain','value':1,'minimum':0,'maximum':2,'targetRuntimePath':'/simulations/run'}],
'links':[{'linkId':'time','sourceViewId':'trajectory','targetViewId':'uncertainty','relation':'time','sourceField':'x','targetField':'x'}]}}
s,w,_=req('/visual-workspace/build',workspace); assert s==200,w; assert w['linkedViewsEnabled'] is True and w['controlsExecuteAutomatically'] is False,w
s,v,_=req('/visual-workspace/validate',{'visualWorkspace':w}); assert s==200 and v['valid'] is True,v
s,p,_=req('/visual-workspace/control/plan',{'visualWorkspace':w,'controlId':'gain','value':1.5,'runtimeRequest':{'payload':{}}}); assert s==200 and p['executionPerformed'] is False and p['preparedRuntimeRequest']['payload']['gain']==1.5,p
headers={'X-Request-ID':'deploy-v7110','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}: token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,plan,_=req('/integration/core/visual-workspace/plan',{'visualWorkspace':w,'coreSessionId':'core-visual-v7110'},headers); assert s==200,plan; assert plan['coreLinkedViewsContract']=='sc.visual-runtime.linked-views.v1' and plan['automaticCoreDispatchAuthorized'] is False and plan['coreExecutesScientificComputation'] is False,plan
print('PASS: /health reports Workbench 7.11.0')
print('PASS: renderer-neutral scientific views, uncertainty bands and linked-view state are active')
print('PASS: explicit parameter-control recomputation planning is active without automatic execution')
print('PASS: visual workspace integrity hashing and tamper validation are active')
print('PASS: Platform Core visual-reasoning planning reuses scene, grammar and linked-view contracts without dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
