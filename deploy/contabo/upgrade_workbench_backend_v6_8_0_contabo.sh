#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="6.8.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v6.8.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v680.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v680.py' | head -1)"
[[ -n "$marker" ]] || fail "v6.8.0 scenario/uncertainty runtime module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "6.8.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'scenario-compute-input-manifest-v1' "$SRC_BACKEND/app/v680.py" || fail "Core scenario manifest compatibility missing"
grep -q '/v1/uncertainty-compute/sampling/design' "$SRC_BACKEND/app/v680.py" || fail "Core uncertainty runtime compatibility missing"
grep -q 'sustainable-catalyst-workbench:6.8.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
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
[[ -f "$PACKAGE_ROOT/workbench-v6.8.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v6.8.0.env.example" "$ROOT/workbench-v6.8.0.env.example"
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
echo "=== VERIFYING SCENARIO & UNCERTAINTY COMPUTE RUNTIME ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json, os, urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
    h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {})
    r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
    with urllib.request.urlopen(r,timeout=10) as x: return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v680/status'):
    status,body,_=req(path); assert status==200,(path,status); assert body.get('ok') is True,(path,body)
health=req('/health')[1]; assert health['version']=='6.8.0' and health['coreCompatible'] is True,health
caps=req('/capabilities')[1]; assert caps['coreIntegration']['scenarioUncertaintyRuntime'] is True,caps
headers={'X-Request-ID':'deploy-v680','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
    token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token,'SCWB_REQUIRE_SERVICE_TOKEN=true but token empty'; headers['X-SC-Service-Token']=token
status,m,_=req('/integration/core/scenario-uncertainty/manifest',headers=headers); assert status==200,m
assert m['version']=='6.8.0' and m['coreScenarioInputManifestSchema']=='scenario-compute-input-manifest-v1',m
status,d,_=req('/integration/core/scenario-uncertainty/sampling/design/run',{'method':'latin-hypercube','sampleCount':8,'seed':42,'factors':[{'key':'x','distribution':'uniform','lowerBound':0,'upperBound':1}]},headers); assert status==200,d
assert len(d['samples'])==8 and d['calculated_by_workbench'] is True and d['calculated_by_core'] is False,d
scenario={'schema':'scenario-compute-input-manifest-v1','project_entity_id':'p','model_entity_id':'m','model_version_entity_id':'mv','scenario_entity_id':'s','execution_product':'workbench','parameter_values':{'x':2,'y':3},'expected_outputs':['z'],'execution_contract':{},'output_contract':{},'case_hash':'deploy','core_execution':False}
status,d,_=req('/integration/core/scenario-uncertainty/scenario/affine/run',{'coreRequestId':'deploy-v680','inputManifest':scenario,'outputs':{'z':{'intercept':1,'coefficients':{'x':2,'y':3}}}},headers); assert status==200,d
assert d['outputs'][0]['value']==14 and d['executionRegistrationPlan']['coreExecutionIdMustComeFromCore'] is True,d
print('PASS: /health reports Workbench 6.8.0')
print('PASS: Core scenario and uncertainty compatibility manifest is active')
print('PASS: LHS sampling and affine scenario computation execute in Workbench')
print('PASS: v6.7 lineage registration plan builds without automatic Core dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
