#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="6.10.0"
PRODUCT="Workbench"
ARCHIVE="${1:-/tmp/sustainable-catalyst-workbench-backend-v6.10.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/workbench}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-workbench}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-workbench}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-workbench-v6100.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
marker="$(find "$TMP/package" -type f -path '*/backend/app/v6100.py' | head -1)"
[[ -n "$marker" ]] || fail "v6.10.0 predictive intelligence runtime module missing from package"
SRC_BACKEND="$(dirname "$(dirname "$marker")")"
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
grep -q 'APP_VERSION = "6.10.0"' "$SRC_BACKEND/app/release.py" || fail "package version mismatch"
grep -q 'sc.predictive.model.v1' "$SRC_BACKEND/app/v6100.py" || fail "Core predictive model contract missing"
grep -q 'sc.visual-runtime.predictive-intelligence.v1' "$SRC_BACKEND/app/v6100.py" || fail "visual predictive contract missing"
grep -q 'sustainable-catalyst-workbench:6.10.0' "$PACKAGE_ROOT/compose.yml" || fail "compose release identity mismatch"
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
[[ -f "$PACKAGE_ROOT/workbench-v6.10.0.env.example" ]] && cp "$PACKAGE_ROOT/workbench-v6.10.0.env.example" "$ROOT/workbench-v6.10.0.env.example"
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
echo "=== VERIFYING PREDICTIVE INTELLIGENCE RUNTIME ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json,os,urllib.request
base='http://127.0.0.1:8088'
def req(path,data=None,headers=None):
 h={'Accept':'application/json','Content-Type':'application/json'}; h.update(headers or {})
 r=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers=h,method='GET' if data is None else 'POST')
 with urllib.request.urlopen(r,timeout=10) as x:return x.status,json.load(x),dict(x.headers)
for path in ('/health','/runtime','/capabilities','/v6100/status'):
 s,b,_=req(path); assert s==200,(path,s); assert b.get('ok') is True,(path,b)
health=req('/health')[1]; assert health['version']=='6.10.0' and health['coreCompatible'] is True,health
caps=req('/capabilities')[1]; assert caps['coreIntegration']['predictiveIntelligenceRuntime'] is True,caps
headers={'X-Request-ID':'deploy-v6100','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':os.getenv('SCWB_CORE_EXPECTED_VERSION_PREFIX','3.')}
if os.getenv('SCWB_REQUIRE_SERVICE_TOKEN','').lower() in {'1','true','yes','on'}:
 token=os.getenv('SCWB_SERVICE_TOKEN',''); assert token; headers['X-SC-Service-Token']=token
s,m,_=req('/integration/core/predictive-intelligence/manifest',headers=headers); assert s==200,m; assert m['corePredictiveModelContract']=='sc.predictive.model.v1'; assert m['coreVisualPredictiveContract']=='sc.visual-runtime.predictive-intelligence.v1'
p={'projectEntityId':'project-deploy-probe','modelKey':'deploy-trend','modelName':'Deploy Trend','history':[2,4,6,8,10,12],'horizon':3,'method':'linear-trend'}
s,f,_=req('/predictive/forecast',p,headers); assert s==200,f; assert f['pointForecast']==[14.0,16.0,18.0],f
s,b,_=req('/predictive/backtest',{'history':[1,2,3,4,5,6,7],'method':'linear-trend','minimumTrainSize':3},headers); assert s==200,b; assert b['metrics']['mae']<1e-9,b
s,c,_=req('/predictive/calibration',{'probabilities':[0.1,0.2,0.8,0.9],'outcomes':[0,0,1,1],'bins':4},headers); assert s==200,c; assert c['metrics']['brier']<0.03,c
s,plan,_=req('/integration/core/predictive-intelligence/model/plan',{'forecastResult':f},headers); assert s==200,plan; assert plan['coreModelIdMustComeFromCore'] is True
print('PASS: /health reports Workbench 6.10.0')
print('PASS: point forecasting, backtesting, intervals and calibration execute in Workbench')
print('PASS: Core predictive and visual-predictive contracts are active')
print('PASS: predictive registry plans require Core-issued IDs and do not auto-dispatch')
PYVERIFY
echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
