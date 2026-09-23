#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="8.0.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v8.0.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v800.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v800.py' | head -1)"; [[ -n "$marker" ]] || fail "v8.0.0 unified research environment module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "8.0.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-unified-computational-research-environment/1.0' "$SRC_BACKEND/app/v800.py" || fail "research environment schema missing"
grep -q 'sc.research.unified-research-scientific-investigation-runtime.v1' "$SRC_BACKEND/app/v800.py" || fail "Platform Core unified research contract missing"
grep -q 'sustainable-catalyst-workbench:8.0.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v8.0.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v8.0.0.env.example" "$ROOT/workbench-v8.0.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING UNIFIED COMPUTATIONAL RESEARCH ENVIRONMENT ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {}); r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v800/status','/research-environment/manifest'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='8.0.0' and health['coreCompatible'] is True,health
spec={'environmentKey':'deploy-v800','title':'Unified Research Environment','projectEntityId':'project:deploy','activeSurface':'notebook','components':[
 {'componentKey':'notebook','componentType':'notebook-run','payload':{'notebookRunHash':'deploy-nb','cellRuns':[]}},
 {'componentKey':'visual','componentType':'visual-workspace','componentRef':'sc://workbench/visual/deploy','contentHash':'a'*64},
 {'componentKey':'package','componentType':'reproducible-package','componentRef':'sc://workbench/package/deploy','contentHash':'b'*64}
]}
s,env,_=req('/research-environment/build',{'environment':spec}); assert s==200,env; assert env['state']['componentCount']==3 and env['boundaries']['automaticExecutionAuthorized'] is False,env
s,v,_=req('/research-environment/validate',{'researchEnvironment':env}); assert s==200 and v['valid'] is True,v
s,surf,_=req('/research-environment/surface/plan',{'researchEnvironment':env,'surface':'simulation','action':'prepare-run','requestPayload':{'simulationKind':'scalar-dynamic'}}); assert s==200 and surf['executionPerformed'] is False and surf['automaticDispatchAuthorized'] is False,surf
s,snap,_=req('/research-environment/snapshot/plan',{'researchEnvironment':env}); assert s==200 and snap['packageBuildPerformed'] is False and snap['targetPath']=='/repro-package/build',snap
headers={'X-Request-ID':'deploy-v800','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}: token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,plan,_=req('/integration/core/research-environment/plan',{'researchEnvironment':env,'coreProjectEntityId':'core-project-v800'},headers); assert s==200,plan; assert plan['phase']=='prepare-session' and plan['coreSessionIdMustComeFromCore'] is True and plan['automaticCoreDispatchAuthorized'] is False,plan
print('PASS: /health reports Workbench 8.0.0')
print('PASS: content-addressed unified research environment state and integrity validation are active')
print('PASS: explicit surface/session/snapshot planning is active without hidden execution or replay')
print('PASS: completed v7 scientific, engineering, notebook, visual and reproducibility surfaces are integrated')
print('PASS: Platform Core unified research-session planning remains two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
