#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.0.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.0.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v700.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v700.py' | head -1)"
[[ -n "$marker" ]] || fail "v7.0.0 Unified Scientific & Engineering Execution Runtime module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.0.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-unified-scientific-engineering-execution-runtime/1.0' "$SRC_BACKEND/app/v700.py" || fail "unified execution contract missing"
grep -q 'sc.research.computation-analysis-execution-lineage.v1' "$SRC_BACKEND/app/v700.py" || fail "Core computation lineage contract missing"
grep -q 'sustainable-catalyst-workbench:7.0.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
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
[[ -f "$PACKAGE_ROOT/workbench-v7.0.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.0.0.env.example" "$ROOT/workbench-v7.0.0.env.example"
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
echo "=== VERIFYING UNIFIED SCIENTIFIC & ENGINEERING EXECUTION RUNTIME ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {})
 r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=15) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v700/status','/execution/runtime/manifest','/execution/runtime/catalog'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.0.0' and health['coreCompatible'] is True,health
status=req('/v700/status')[1]; assert status['operationCount']>=60 and status['workflowExecution'] is True and status['arbitraryCodeExecution'] is False,status
caps=req('/capabilities')[1]; assert caps['coreIntegration']['unifiedScientificEngineeringExecutionRuntime'] is True,caps
s,math,_=req('/execution/runtime/execute',{'operation':'math.compute','payload':{'expression':'6*7'}}); assert s==200 and math['result']['result']['exactText']=='42',math
s,num,_=req('/execution/runtime/execute',{'operation':'numerical.integrate','payload':{'expression':'x**2','lower':0,'upper':1,'samples':101}}); assert s==200 and abs(num['result']['result']['value']-1/3)<1e-10,num
s,elec,_=req('/execution/runtime/execute',{'operation':'electronics.resistor-network','payload':{'topology':'series','resistancesOhm':[100,220],'sourceVoltageV':5}}); assert s==200 and elec['result']['result']['equivalentResistanceOhm']==320.0,elec
s,pred,_=req('/execution/runtime/execute',{'operation':'predictive.forecast','payload':{'projectEntityId':'deploy','modelKey':'linear','modelName':'Linear','history':[1,2,3,4,5,6],'horizon':2,'method':'linear-trend'}}); assert s==200 and pred['result']['pointForecast']==[7.0,8.0],pred
s,wf,_=req('/execution/runtime/workflow/run',{'workflowKey':'deploy','steps':[{'stepId':'a','operation':'math.compute','payload':{'expression':'10+5'}},{'stepId':'b','operation':'electronics.resistor-network','dependsOn':['a'],'payload':{'resistancesOhm':[10,20],'sourceVoltageV':3}}]}); assert s==200 and wf['dependencyOrder']==['a','b'] and wf['automaticOutputSubstitutionPerformed'] is False,wf
headers={'X-Request-ID':'deploy-v700','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
 token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,plan,_=req('/integration/core/unified-execution/lineage/plan',{'executionResult':num},headers); assert s==200 and plan['coreExecutionIdMustComeFromCore'] is True and plan['automaticCoreDispatchAuthorized'] is False,plan
print('PASS: /health reports Workbench 7.0.0')
print('PASS: unified operation catalog exposes bounded scientific and engineering specialist engines')
print('PASS: canonical execution envelopes, deterministic identities and dependency workflows are active')
print('PASS: representative math, numerical, electronics and predictive execution completed')
print('PASS: Platform Core lineage planning remains two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
