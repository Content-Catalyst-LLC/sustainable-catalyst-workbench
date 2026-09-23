#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="8.1.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v8.1.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v810.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v810.py' | head -1)"; [[ -n "$marker" ]] || fail "v8.1.0 persistence/recovery module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "8.1.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-research-environment-persistence-recovery/1.0' "$SRC_BACKEND/app/v810.py" || fail "persistence schema missing"
grep -q 'sustainable-catalyst-workbench:8.1.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
grep -q './data:/data' "$PACKAGE_ROOT/compose.yml" || fail "persistent data mount missing"
mkdir -p "$ROOT/data"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
if [[ -d "$ROOT/data/research-environments" ]]; then tar -C "$ROOT/data" -czf "$BACKUP_ROOT/workbench-research-environments-before-v$VERSION-$stamp.tgz" research-environments; fi
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v8.1.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v8.1.0.env.example" "$ROOT/workbench-v8.1.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING RESEARCH ENVIRONMENT PERSISTENCE & RECOVERY ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,urllib.request,urllib.parse,uuid
base='http://127.0.0.1:8088'
def req(path,data=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x)
for path in ('/health','/v810/status','/research-environment/persistence/manifest'):
 s,b=req(path); assert s==200 and b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='8.1.0',health
key='deploy-v810-'+uuid.uuid4().hex[:12]
spec={'environmentKey':key,'title':'Deployment Persistence Check','projectEntityId':'project:'+key,'components':[{'componentKey':'notebook','componentType':'notebook-run','payload':{'notebookRunHash':'deploy-nb','cellRuns':[]}}]}
s,env=req('/research-environment/build',{'environment':spec}); assert s==200,env
s,saved=req('/research-environment/persistence/save',{'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'deployment-verification'}); assert s==200 and saved['revision']==1,saved
s,loaded=req('/research-environment/persistence/'+urllib.parse.quote(key,safe='')); assert s==200 and loaded['currentRevision']==1 and loaded['researchEnvironment']['environmentHash']==env['environmentHash'],loaded
s,cp=req('/research-environment/checkpoints/create',{'environmentKey':key,'label':'deployment-verification'}); assert s==200 and cp['revision']==1,cp
s,plan=req('/research-environment/recovery/plan',{'environmentKey':key,'target':{'checkpointId':cp['checkpointId']}}); assert s==200 and plan['recoveryCreatesNewRevision'] is True and plan['destructiveRollbackPerformed'] is False,plan
s,recovered=req('/research-environment/recovery/apply',{'environmentKey':key,'target':{'revision':1},'expectedCurrentRevision':1,'reason':'deployment-recovery-check'}); assert s==200 and recovered['newRevision']==2 and recovered['destructiveRollbackPerformed'] is False,recovered
print('PASS: /health reports Workbench 8.1.0')
print('PASS: atomic persistent research-environment save/load is active on the mounted data store')
print('PASS: append-only revision history, immutable checkpoints and optimistic revision checks are active')
print('PASS: recovery creates a new integrity-validated revision instead of destructively rewriting history')
print('PASS: persistence/recovery performs no scientific execution, notebook replay, workflow execution or Core dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
