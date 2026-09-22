#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.1.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.1.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v710.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v710.py' | head -1)"
[[ -n "$marker" ]] || fail "v7.1.0 Unified Execution Object Model module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.1.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-execution-object/1.0' "$SRC_BACKEND/app/v710.py" || fail "execution object schema missing"
grep -q 'sc.research.unified-research-scientific-investigation-runtime.v1' "$SRC_BACKEND/app/v710.py" || fail "Core unified research runtime contract missing"
grep -q 'sustainable-catalyst-workbench:7.1.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
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
[[ -f "$PACKAGE_ROOT/workbench-v7.1.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.1.0.env.example" "$ROOT/workbench-v7.1.0.env.example"
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
echo "=== VERIFYING UNIFIED EXECUTION OBJECT MODEL ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {})
 r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=15) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v710/status','/execution/objects/manifest'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.1.0' and health['coreCompatible'] is True,health
status=req('/v710/status')[1]; assert status['singleExecutionObjects'] is True and status['workflowExecutionObjects'] is True and status['contentAddressedIntegrity'] is True,status
caps=req('/capabilities')[1]; assert caps['coreIntegration']['unifiedExecutionObjectModel'] is True,caps
s,x,_=req('/execution/objects/execute',{'operation':'math.compute','payload':{'expression':'6*7'},'projectRef':'project:deploy','requestKey':'deploy-math'}); assert s==200,x
obj=x['executionObject']; assert obj['objectKind']=='single_execution' and obj['outputs'][0]['inlineResult']['result']['exactText']=='42',obj
s,v,_=req('/execution/objects/validate',{'executionObject':obj}); assert s==200 and v['valid'] is True,v
s,rev,_=req('/execution/objects/revise',{'executionObject':obj,'reason':'deployment verification','metadataPatch':{'verified':True}}); assert s==200 and rev['revision']==2 and rev['outputs']==obj['outputs'],rev
s,w,_=req('/execution/objects/workflow/run',{'workflowKey':'deploy-flow','steps':[{'stepId':'a','operation':'math.compute','payload':{'expression':'10+5'}},{'stepId':'b','operation':'electronics.resistor-network','dependsOn':['a'],'payload':{'resistancesOhm':[10,20],'sourceVoltageV':3}}]}); assert s==200,w
wo=w['executionObject']; assert wo['objectKind']=='workflow_execution' and len(wo['children'])==2 and len(wo['dependencies']['edges'])==1,wo
headers={'X-Request-ID':'deploy-v710','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
 token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,p,_=req('/integration/core/execution-objects/binding/plan',{'executionObject':obj,'coreRuntimeSessionId':'core-session-deploy','coreRuntimeContractId':'core-contract-deploy'},headers); assert s==200,p
assert p['scientificRuntimeExecutionBinding']['path']=='/v1/research/unified-runtime/execution-bindings' and p['runtimeInvocationRegistration']['path']=='/v1/research/runtime-contract/invocations',p
assert p['automaticCoreDispatchAuthorized'] is False and p['automaticCorePersistenceAuthorized'] is False,p
print('PASS: /health reports Workbench 7.1.0')
print('PASS: single and workflow execution objects are active and content-addressed')
print('PASS: object integrity validation and metadata-only revisioning are active')
print('PASS: workflow dependency edges and child execution objects are preserved')
print('PASS: Platform Core execution-object binding plans remain two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
