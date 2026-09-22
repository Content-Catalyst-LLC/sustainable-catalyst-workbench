#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="6.12.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v6.12.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v6120.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v6120.py' | head -1)"
[[ -n "$marker" ]] || fail "v6.12.0 research-state module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "6.12.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc.research.project-state-versioning-reproducibility.v1' "$SRC_BACKEND/app/v6120.py" || fail "Core project-state contract missing"
grep -q 'sc.research.reproducible-package.v1' "$SRC_BACKEND/app/v6120.py" || fail "Core reproducible package contract missing"
grep -q 'sc.research.cross-product-context-handoff.v1' "$SRC_BACKEND/app/v6120.py" || fail "Core context handoff contract missing"
grep -q 'sustainable-catalyst-workbench:6.12.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
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
[[ -f "$PACKAGE_ROOT/workbench-v6.12.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v6.12.0.env.example" "$ROOT/workbench-v6.12.0.env.example"
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
echo "=== VERIFYING RESEARCH STATE, REPRODUCTION & SNAPSHOT INTEGRATION ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {})
 r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=10) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v6120/status'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='6.12.0' and health['coreCompatible'] is True,health
caps=req('/capabilities')[1]; assert caps['coreIntegration']['researchStateReproductionSnapshotIntegration'] is True,caps
headers={'X-Request-ID':'deploy-v6120','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
 token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,m,_=req('/integration/core/research-state/manifest',headers=headers); assert s==200,m; assert m['coreProjectStateContract']=='sc.research.project-state-versioning-reproducibility.v1'; assert m['boundaries']['automaticStateRestoreAuthorized'] is False
snapshot_payload={'snapshotKey':'deploy-probe','projectRef':'sc://workbench/project/deploy','title':'Deployment probe','bindings':[{'bindingKey':'dataset','objectType':'dataset','objectRef':'sc://workbench/dataset/deploy','contentHash':'sha256:data'},{'bindingKey':'output','objectType':'output','objectRef':'sc://workbench/output/deploy','contentHash':'sha256:out'}],'dependencies':[{'dependencyKey':'dep','fromBindingKey':'dataset','toBindingKey':'output','relation':'produced'}],'environments':[{'environmentKey':'wb','environmentType':'workbench','environmentRef':'sc://workbench/runtime/6.12.0','versionRef':'6.12.0'}]}
s,snap,_=req('/research-state/snapshot/build',snapshot_payload,headers); assert s==200,snap; assert len(snap['snapshotHash'])==64
s,state,_=req('/integration/core/research-state/project-state/prepare',{'snapshot':snap},headers); assert s==200,state; assert state['coreStateIdMustComeFromCore'] is True
s,version_plan,_=req('/integration/core/research-state/project-state/version/plan',{'coreStateId':'state-deploy','snapshot':snap},headers); assert s==200,version_plan; assert version_plan['freezeMustFollowBindings'] is True and version_plan['automaticExecutionReplayAuthorized'] is False
s,repro,_=req('/integration/core/research-state/reproduction/prepare',{'coreProjectEntityId':'project-deploy','snapshot':snap},headers); assert s==200,repro; assert repro['corePackageIdMustComeFromCore'] is True
s,ctx,_=req('/integration/core/research-state/context/prepare',{'snapshot':snap},headers); assert s==200,ctx; assert ctx['coreContextIdMustComeFromCore'] is True
s,resume,_=req('/integration/core/research-state/resume/consume',{'bundle':{'state':{'project_ref':'project-deploy'},'version':{'version':1,'status':'frozen'},'bindings':[{'object_ref':'sc://workbench/output/deploy','content_hash':'sha256:out'}],'dependencies':[],'environments':[{'environment_ref':'sc://workbench/runtime/6.12.0'}]}},headers); assert s==200,resume; assert resume['automaticRestoreAuthorized'] is False and resume['automaticExecutionReplayAuthorized'] is False
print('PASS: /health reports Workbench 6.12.0')
print('PASS: deterministic Workbench research-state snapshot capture is active')
print('PASS: Core project-state, reproducible-package and context contracts are active')
print('PASS: resume/reconstruction plans do not auto-restore or replay executions')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
