#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="7.4.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v7.4.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v740.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v740.py' | head -1)"; [[ -n "$marker" ]] || fail "v7.4.0 Numerical Methods & Solver Runtime module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "7.4.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-numerical-methods-solver-runtime/1.0' "$SRC_BACKEND/app/v740.py" || fail "solver runtime schema missing"
grep -q 'sc.research.computation-analysis-execution-lineage.v1' "$SRC_BACKEND/app/v740.py" || fail "Core lineage contract missing"
grep -q 'sustainable-catalyst-workbench:7.4.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v7.4.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v7.4.0.env.example" "$ROOT/workbench-v7.4.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING NUMERICAL METHODS & SOLVER RUNTIME ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {}); r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v740/status','/solvers/manifest','/solvers/catalog'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='7.4.0' and health['coreCompatible'] is True,health
s,root,_=req('/solvers/solve',{'problemKind':'root','solverKey':'root.brentq','problem':{'expression':'x**2-2','bracket':[0,2],'tolerance':1e-10},'requestKey':'deploy-root'}); assert s==200,root; assert root['diagnostics']['converged'] is True and abs(root['diagnostics']['residual'])<1e-8,root
s,lin,_=req('/solvers/solve',{'problemKind':'linear-algebra','solverKey':'linear.solve','problem':{'matrix':[[3,1],[1,2]],'vector':[9,8]},'requestKey':'deploy-linear'}); assert s==200,lin; assert lin['diagnostics']['residualNorm']<1e-10,lin
s,study,_=req('/solvers/convergence-study',{'problemKind':'integration','solverKey':'integration.simpson','problem':{'expression':'sin(x)','lower':0,'upper':3.141592653589793,'samples':21},'levels':3}); assert s==200 and len(study['levels'])==3,study
ws={'workspaceKey':'solver-deploy','variables':[],'parameterSets':[{'parameterSetKey':'solver','parameters':[{'parameterKey':'tol','value':1e-9}]}],'datasets':[],'assumptions':[]}
s,w,_=req('/data-workspace/build',ws); assert s==200,w
s,p,_=req('/solvers/workspace-binding/plan',{'workspace':w,'problemKind':'root','problem':{'expression':'x-1','bracket':[0,2]},'bindings':[{'sourceKind':'parameter','parameterSetKey':'solver','sourceKey':'tol','targetField':'tolerance'}]}); assert s==200 and p['executionPerformed'] is False,p
headers={'X-Request-ID':'deploy-v740','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}: token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,cp,_=req('/integration/core/solver-lineage/plan',{'solverResult':root,'coreExecutionId':'core-exec-v740'},headers); assert s==200,cp; assert cp['coreComputationLineageContract']=='sc.research.computation-analysis-execution-lineage.v1' and cp['outputRegistrations'][0]['path'].endswith('/outputs'),cp
assert cp['automaticCoreDispatchAuthorized'] is False,cp
print('PASS: /health reports Workbench 7.4.0')
print('PASS: canonical bounded numerical solver registry is active')
print('PASS: residual, conditioning, convergence and error diagnostics are active')
print('PASS: convergence studies and v7.3 workspace binding plans are active')
print('PASS: Platform Core numerical solver lineage planning remains two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
