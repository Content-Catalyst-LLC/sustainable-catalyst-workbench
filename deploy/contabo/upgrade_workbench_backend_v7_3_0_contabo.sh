#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.3.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.3.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v730.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v730.py' | head -1)"; [[ -n "$marker" ]] || fail "v7.3.0 Dataset, Variable & Parameter Workspace module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.3.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-data-variable-parameter-workspace/1.0' "$SRC_BACKEND/app/v730.py" || fail "data workspace schema missing"
grep -q 'sc.research.computation-analysis-execution-lineage.v1' "$SRC_BACKEND/app/v730.py" || fail "Core lineage contract missing"
grep -q 'sustainable-catalyst-workbench:7.3.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
grep -q 'httpx2>=2,<3' "$SRC_BACKEND/requirements.txt" || fail "httpx2 dependency missing"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v7.3.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.3.0.env.example" "$ROOT/workbench-v7.3.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING DATASET, VARIABLE & PARAMETER WORKSPACE ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {}); r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=15) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v730/status','/data-workspace/manifest'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.3.0' and health['coreCompatible'] is True,health
ws={'workspaceKey':'deploy','variables':[{'variableKey':'a','value':6},{'variableKey':'b','value':7},{'variableKey':'c','kind':'derived','expression':'a*b','dependsOn':['a','b']}],'parameterSets':[{'parameterSetKey':'p','parameters':[{'parameterKey':'gain','value':2}]}],'datasets':[{'datasetKey':'d','columns':[{'name':'x'}],'rows':[{'x':1},{'x':2}]}],'assumptions':[{'assumptionKey':'declared','statement':'Deployment verification assumption.'}]}
s,w,_=req('/data-workspace/build',ws); assert s==200,w; assert next(x for x in w['variables'] if x['variableKey']=='c')['derivedValue']==42.0,w
s,u,_=req('/data-workspace/units/convert',{'value':1,'fromUnit':'kW','toUnit':'W'}); assert s==200 and u['convertedValue']==1000.0,u
s,p,_=req('/data-workspace/execution-binding/plan',{'workspace':w,'operation':'math.compute','payload':{'expression':'1+1'},'bindings':[{'sourceKind':'parameter','parameterSetKey':'p','sourceKey':'gain','targetField':'precision'}]}); assert s==200 and p['executionPerformed'] is False,p
headers={'X-Request-ID':'deploy-v730','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}: token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,cplan,_=req('/integration/core/data-workspace/lineage/plan',{'workspace':w,'coreExecutionId':'core-exec-deploy'},headers); assert s==200,cplan
assert cplan['coreComputationLineageContract']=='sc.research.computation-analysis-execution-lineage.v1' and cplan['datasetInputRegistrations'][0]['path'].endswith('/inputs'),cplan
assert cplan['automaticCoreDispatchAuthorized'] is False,cplan
print('PASS: /health reports Workbench 7.3.0')
print('PASS: content-addressed datasets, variables, parameter sets and assumptions are active')
print('PASS: unit conversion and restricted derived scalar values are active')
print('PASS: workspace-to-orchestrator execution binding plans are explicit and non-dispatching')
print('PASS: Platform Core computation-lineage plans register datasets/parameters/assumptions only against Core-issued execution ids')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
