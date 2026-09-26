#!/usr/bin/env bash
set -Eeuo pipefail
ARCHIVE="${1:?Usage: $0 /tmp/sustainable-catalyst-workbench-backend-v9.6.0.zip}"
APP_DIR="${SCWB_APP_DIR:-/opt/sustainable-catalyst/workbench}"
BACKUP="${APP_DIR}.backup-v9.6.0-$(date +%Y%m%d%H%M%S)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
echo "=== BACKING UP WORKBENCH ==="; sudo cp -a "$APP_DIR" "$BACKUP"
echo "=== EXTRACTING v9.6.0 ==="; unzip -q "$ARCHIVE" -d "$TMP"
PKG_ROOT="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
[[ -f "$PKG_ROOT/compose.yml" && -d "$PKG_ROOT/backend" ]] || { echo "ERROR: v9.6 package root not found" >&2; exit 1; }
sudo rsync -a --checksum --delete --exclude='data/' "$PKG_ROOT/" "$APP_DIR/"
sudo find "$APP_DIR/backend" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
sudo find "$APP_DIR/backend" -type f -name '*.pyc' -delete 2>/dev/null || true
cd "$APP_DIR"
python3 - <<'PYIDENT'
from pathlib import Path
r=Path('backend/app/release.py').read_text(); c=Path('compose.yml').read_text(); m=Path('backend/app/main.py').read_text()
assert 'APP_VERSION = "9.6.0"' in r,r
assert 'sustainable-catalyst-workbench:9.6.0' in c,c
assert 'version="9.6.0"' in m,m
print('PASS: installed source identity and compose image are v9.6.0')
PYIDENT
sudo docker compose build --pull=false
sudo docker compose up -d
echo "=== VERIFYING SCIENTIFIC RESULTS & NARRATIVE SYNTHESIS ==="
for i in {1..30}; do if curl -fsS http://127.0.0.1:8088/health >/tmp/scwb-v960-health.json 2>/dev/null; then break; fi; sleep 2; done
python3 - <<'PYVERIFY'
import json,urllib.request
base='http://127.0.0.1:8088'
def get(path): return json.load(urllib.request.urlopen(base+path,timeout=10))
h=get('/health'); assert h['version']=='9.6.0' and h.get('readiness')=='ready',h
m=get('/results-synthesis/manifest'); assert m['version']=='9.6.0' and m['capabilities']['statementSourceTraceability'] is True,m
s=get('/v960/status'); assert s['scientificResultsNarrativeSynthesis'] and s['automaticNarrativeGeneration'] is False,s
print('PASS: Workbench v9.6.0 backend deployed and verified.')
PYVERIFY
echo "Backend backup: $BACKUP"
