#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.7.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.7.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v770.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v770.py' | head -1)"; [[ -n "$marker" ]] || fail "v7.7.0 Optimization & Design Space module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.7.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-optimization-design-space-runtime/1.0' "$SRC_BACKEND/app/v770.py" || fail "design-space runtime schema missing"
grep -q 'sc.research.computation-analysis-execution-lineage.v1' "$SRC_BACKEND/app/v770.py" || fail "Core lineage contract missing"
grep -q 'sustainable-catalyst-workbench:7.7.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v7.7.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.7.0.env.example" "$ROOT/workbench-v7.7.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING OPTIMIZATION & DESIGN SPACE RUNTIME ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {}); r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v770/status','/design-space/manifest'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.7.0' and health['coreCompatible'] is True,health
space={'designSpaceKey':'deploy-v770','variables':[{'variableKey':'x','lowerBound':0,'upperBound':4,'initial':1,'gridPoints':5},{'variableKey':'y','lowerBound':0,'upperBound':4,'initial':1,'gridPoints':5}],'objectives':[{'objectiveKey':'cost','expression':'x**2+y**2','goal':'minimize','weight':1},{'objectiveKey':'performance','expression':'x+2*y','goal':'maximize','weight':0.2}],'constraints':[{'constraintKey':'minimum','expression':'x+y','relation':'>=','rhs':1}]}
s,e,_=req('/design-space/explore',{'designSpace':space,'maxPoints':100}); assert s==200,e; assert e['pointCount']==25 and e['automaticBestDesignSelected'] is False,e
s,p,_=req('/design-space/pareto',e); assert s==200,p; assert p['frontierPointCount']>=1 and p['automaticWinnerSelected'] is False,p
s,d,_=req('/design-space/optimize',{'designSpace':space,'requestKey':'deploy-v770'}); assert s==200,d; assert d['result']['evaluation']['feasible'] is True and d['executionObject']['objectKind']=='single_execution',d
s,h,_=req('/design-space/candidate-handoff/plan',{'candidatePoint':{'x':1.2,'y':2},'targetKind':'engineering','targetRequest':{'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.1}},'bindings':[{'variableKey':'x','targetField':'inputs.area_m2'}]}); assert s==200,h; assert h['executionPerformed'] is False and h['preparedRequest']['inputs']['area_m2']==1.2,h
headers={'X-Request-ID':'deploy-v770','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}: token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,cp,_=req('/integration/core/design-space-lineage/plan',{'designResult':d,'coreExecutionId':'core-exec-v770'},headers); assert s==200,cp; assert cp['coreComputationLineageContract']=='sc.research.computation-analysis-execution-lineage.v1' and cp['outputRegistrations'][0]['path'].endswith('/outputs'),cp
assert cp['automaticCoreDispatchAuthorized'] is False,cp
print('PASS: /health reports Workbench 7.7.0')
print('PASS: bounded design variables, explicit objectives and constraints are active')
print('PASS: deterministic full-factorial exploration and Pareto-frontier extraction are active')
print('PASS: constrained weighted-sum optimization and explicit engineering/simulation candidate handoff plans are active')
print('PASS: Platform Core design-space lineage planning remains two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
