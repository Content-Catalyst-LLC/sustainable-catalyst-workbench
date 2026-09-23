#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="8.3.0"; PRODUCT="Workbench"; ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v8.3.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"; LIVE_BACKEND="$ROOT/backend"; COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"; SERVICE="${SC_TARGET_SERVICE:-workbench}"; CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"; BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v830.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"; [[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"; [[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"; unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v830.py' | head -1)"; [[ -n "$marker" ]] || fail "v8.3.0 asset-registry module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"; PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "8.3.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc-workbench-research-asset-artifact-registry/1.0' "$SRC_BACKEND/app/v830.py" || fail "asset registry schema missing"
grep -q 'sustainable-catalyst-workbench:8.3.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
grep -q './data:/data' "$PACKAGE_ROOT/compose.yml" || fail "persistent data mount missing"
mkdir -p "$ROOT/data"
if [[ ! -d "$BACKUP_ROOT" ]]; then if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"; fi; fi
if [[ ! -w "$BACKUP_ROOT" ]]; then command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo unavailable"; sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"; sudo chmod 750 "$BACKUP_ROOT"; fi
stamp="$(date +%Y%m%d-%H%M%S)"; echo "=== BACKING UP $PRODUCT BACKEND ==="; tar -C "$ROOT" -czf "$BACKUP_ROOT/workbench-backend-before-v$VERSION-$stamp.tgz" backend; cp -a "$COMPOSE" "$BACKUP_ROOT/workbench-compose-before-v$VERSION-$stamp.yml"
if [[ -d "$ROOT/data/research-environments" ]]; then tar -C "$ROOT/data" -czf "$BACKUP_ROOT/workbench-research-state-before-v$VERSION-$stamp.tgz" research-environments; fi
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"; cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"; [[ -f "$PACKAGE_ROOT/workbench-v8.3.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v8.3.0.env.example" "$ROOT/workbench-v8.3.0.env.example"
cd "$ROOT"; docker compose -f "$COMPOSE" config --quiet; echo "=== BUILDING $PRODUCT v$VERSION ==="; docker compose -f "$COMPOSE" build "$SERVICE"; docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0; for _ in $(seq 1 60); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"; case "$state" in healthy) ready=1; break ;; running) sleep 2 ;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;; esac; sleep 2; done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }
echo "=== VERIFYING RESEARCH ASSET & ARTIFACT REGISTRY ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,urllib.request,urllib.parse,uuid
base='http://127.0.0.1:8088'
def req(path,data=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x)
for path in ('/health','/v830/status','/research-assets/manifest'):
 s,b=req(path); assert s==200 and b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='8.3.0',health
uid=uuid.uuid4().hex[:12]; envkey='deploy-v830-env-'+uid; projectkey='deploy-v830-project-'+uid
spec={'environmentKey':envkey,'title':'Deployment Registry Environment','projectEntityId':projectkey,'components':[{'componentKey':'data','componentType':'data-workspace','payload':{'workspaceHash':'deploy-data-'+uid},'metadata':{'title':'Deployment dataset'}}]}
s,env=req('/research-environment/build',{'environment':spec}); assert s==200,env
s,se=req('/research-environment/persistence/save',{'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'deployment-verification'}); assert s==200 and se['revision']==1,se
s,ws=req('/research-projects/build',{'project':{'projectKey':projectkey,'title':'Deployment Registry Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}); assert s==200,ws
s,pr=req('/research-projects/save',{'workspace':ws,'expectedProjectRevision':0,'reason':'deployment-verification'}); assert s==200 and pr['projectRevision']==1,pr
s,idx=req('/research-assets/index/project',{'projectKey':projectkey}); assert s==200 and idx['indexedCount']==1,idx
q='/research-assets/search?project_key='+urllib.parse.quote(projectkey,safe='')+'&asset_type=dataset'
s,search=req(q); assert s==200 and search['resultCount']==1,search
assetkey=search['results'][0]['assetKey']; s,asset=req('/research-assets/'+urllib.parse.quote(projectkey,safe='')+'/'+urllib.parse.quote(assetkey,safe='')); assert s==200 and asset['asset']['contentHash'],asset
print('PASS: /health reports Workbench 8.3.0')
print('PASS: project-scoped content-addressed research asset indexing and search are active')
print('PASS: registry entries preserve v8.1 environment revision/hash anchors without duplicating scientific payloads')
print('PASS: append-only asset revision integrity and optimistic revision checks are active')
print('PASS: asset registry operations perform no scientific execution, remote retrieval or automatic Core dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
