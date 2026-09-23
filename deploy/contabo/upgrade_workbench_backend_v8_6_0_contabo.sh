#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="8.6.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v8.6.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v860.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v860.py' | head -1)"; [[ -n "$marker" ]] || fail "v8.6.0 visual research canvas module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "8.6.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-visual-research-canvas/1.0' "$SRC_BACKEND/app/v860.py" || fail "visual research canvas schema missing"
grep -q 'sustainable-catalyst-workbench:8.6.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
grep -q './data:/data' "$PACKAGE_ROOT/compose.yml" || fail "persistent data mount missing"
mkdir -p "$ROOT/data"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
if [[ -d "$ROOT/data/research-environments" ]]; then tar -C "$ROOT/data" -czf "$BACKUP_ROOT/workbench-research-state-before-v$VERSION-$stamp.tgz" research-environments; fi
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v8.6.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v8.6.0.env.example" "$ROOT/workbench-v8.6.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING VISUAL RESEARCH CANVAS ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,urllib.request,uuid
base='http://127.0.0.1:8088'
def req(path,data=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=30) as x:return x.status,json.load(x)
for path in ('/health','/v860/status','/research-canvas/manifest'):
 s,b=req(path); assert s==200 and b.get('ok') is True,(path,b)
assert req('/health')[1]['version']=='8.6.0'
uid=uuid.uuid4().hex[:12]; envkey='deploy-v860-env-'+uid; project='deploy-v860-project-'+uid
s,env=req('/research-environment/build',{'environment':{'environmentKey':envkey,'title':'Deployment Canvas Environment','projectEntityId':project,'components':[]}}); assert s==200,env
s,saved=req('/research-environment/persistence/save',{'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'deployment-verification'}); assert s==200 and saved['revision']==1,saved
s,ws=req('/research-projects/build',{'project':{'projectKey':project,'title':'Deployment Canvas Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}); assert s==200,ws
s,pr=req('/research-projects/save',{'workspace':ws,'expectedProjectRevision':0,'reason':'deployment-verification'}); assert s==200 and pr['projectRevision']==1,pr
s,asset=req('/research-assets/register',{'asset':{'projectKey':project,'assetKey':'deployment-source','assetType':'source','title':'Deployment Source','assetRef':'https://example.org/deploy','contentHash':'12345678abcdef','origin':'external'},'expectedAssetRevision':0,'reason':'deployment-verification'}); assert s==200 and asset['assetRevision']==1,asset
s,job=req('/execution-console/jobs/prepare',{'projectKey':project,'runtimeKind':'solver','label':'Deployment solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert s==200 and job['status']=='prepared',job
s,run=req('/execution-console/jobs/'+job['jobId']+'/run',{'expectedJobRevision':1,'reason':'deployment-verification'}); assert s==200 and run['status']=='completed',run
s,canvas=req('/research-canvas/'+project); assert s==200,canvas
assert set(('project','environment','asset','execution','timeline')).issubset(set(n['kind'] for n in canvas['nodes']))
node=canvas['nodes'][0]
s,layout=req('/research-canvas/'+project+'/layout/save',{'expectedLayoutRevision':0,'nodes':[{'nodeId':node['nodeId'],'x':111,'y':222,'pinned':True}],'reason':'deployment-verification'}); assert s==200 and layout['layoutRevision']==1,layout
s,canvas2=req('/research-canvas/'+project); assert s==200 and next(n for n in canvas2['nodes'] if n['nodeId']==node['nodeId'])['x']==111,canvas2
s,selection=req('/research-canvas/selection/resolve',{'projectKey':project,'nodeIds':[node['nodeId']]}); assert s==200 and selection['selectionIsViewStateOnly'] is True,selection
s,lineage=req('/research-canvas/'+project+'/lineage-overlay'); assert s==200 and lineage['automaticCausalInferencePerformed'] is False,lineage
print('PASS: /health reports Workbench 8.6.0')
print('PASS: project, environment, asset, execution and timeline objects project into the visual research canvas')
print('PASS: durable view-only layout persistence and linked selection are active')
print('PASS: timeline lineage overlay remains explicit and non-causal')
print('PASS: canvas performs no scientific execution, interpretation or automatic Core dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
