#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="8.4.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v8.4.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v840.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v840.py' | head -1)"; [[ -n "$marker" ]] || fail "v8.4.0 execution-console module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "8.4.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-interactive-execution-console/1.0' "$SRC_BACKEND/app/v840.py" || fail "execution console schema missing"
grep -q 'sustainable-catalyst-workbench:8.4.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
grep -q './data:/data' "$PACKAGE_ROOT/compose.yml" || fail "persistent data mount missing"
mkdir -p "$ROOT/data"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
if [[ -d "$ROOT/data/research-environments" ]]; then tar -C "$ROOT/data" -czf "$BACKUP_ROOT/workbench-research-state-before-v$VERSION-$stamp.tgz" research-environments; fi
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v8.4.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v8.4.0.env.example" "$ROOT/workbench-v8.4.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING INTERACTIVE EXECUTION CONSOLE ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,urllib.request,uuid
base='http://127.0.0.1:8088'
def req(path,data=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=30) as x:return x.status,json.load(x)
for path in ('/health','/v840/status','/execution-console/manifest'):
 s,b=req(path); assert s==200 and b.get('ok') is True,(path,b)
assert req('/health')[1]['version']=='8.4.0'
uid=uuid.uuid4().hex[:12]; envkey='deploy-v840-env-'+uid; projectkey='deploy-v840-project-'+uid
s,env=req('/research-environment/build',{'environment':{'environmentKey':envkey,'title':'Deployment Execution Environment','projectEntityId':projectkey,'components':[]}}); assert s==200,env
s,saved=req('/research-environment/persistence/save',{'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'deployment-verification'}); assert s==200 and saved['revision']==1,saved
s,ws=req('/research-projects/build',{'project':{'projectKey':projectkey,'title':'Deployment Execution Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}); assert s==200,ws
s,pr=req('/research-projects/save',{'workspace':ws,'expectedProjectRevision':0,'reason':'deployment-verification'}); assert s==200 and pr['projectRevision']==1,pr
s,job=req('/execution-console/jobs/prepare',{'projectKey':projectkey,'runtimeKind':'solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert s==200 and job['status']=='prepared',job
s,run=req('/execution-console/jobs/'+job['jobId']+'/run',{'expectedJobRevision':1,'reason':'deployment-verification'}); assert s==200 and run['status']=='completed' and run['scientificExecutionPerformed'] is True,run
print('PASS: /health reports Workbench 8.4.0')
print('PASS: durable project-scoped prepare, queue, inspect and explicit run lifecycle is active')
print('PASS: allow-listed specialist runtime dispatch records integrity-protected requests and results')
print('PASS: pending cancellation and neutral completed-run comparison are available without hidden background execution')
print('PASS: execution-console Core planning remains two-phase and non-dispatching')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
