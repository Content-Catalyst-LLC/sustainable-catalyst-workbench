#!/usr/bin/env bash
set -Eeuo pipefail
ARCHIVE="${1:?Usage: $0 /tmp/sustainable-catalyst-workbench-backend-v8.12.0.zip}"; APP_DIR="${SCWB_APP_DIR:-/opt/sustainable-catalyst/workbench}"; BACKUP="${APP_DIR}.backup-v8.12.0-$(date +%Y%m%d%H%M%S)"; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
echo "=== BACKING UP WORKBENCH ==="; sudo cp -a "$APP_DIR" "$BACKUP"; echo "=== EXTRACTING v8.12.0 ==="; unzip -q "$ARCHIVE" -d "$TMP"; SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"; [[ -d "$SRC/backend" ]] || SRC="$TMP"; sudo rsync -a --delete --exclude='data/' "$SRC/" "$APP_DIR/"; cd "$APP_DIR"; sudo docker compose build --pull=false; sudo docker compose up -d
echo "=== VERIFYING UNIFIED WORKBENCH PRODUCTION CERTIFICATION ==="; for i in {1..30}; do if curl -fsS http://127.0.0.1:8088/health >/tmp/scwb-v8120-health.json 2>/dev/null; then break; fi; sleep 2; done
python3 - <<'PYVERIFY'
import json,urllib.request
base='http://127.0.0.1:8088'
def get(p): return json.load(urllib.request.urlopen(base+p,timeout=10))
h=get('/health'); assert h['version']=='8.12.0',h
m=get('/production-certification/manifest'); assert m['version']=='8.12.0' and m['capabilities']['retainedMilestoneAudit'] is True,m
s=get('/v8120/status'); assert s['productionCertification'] and s['automaticRemediation'] is False,s
print('PASS: Workbench v8.12.0 backend deployed and verified.')
PYVERIFY'
import json,urllib.request
base='http://127.0.0.1:8088'
def get(p): return json.load(urllib.request.urlopen(base+p,timeout=10))
h=get('/health'); assert h['version']=='8.12.0',h
m=get('/publication-handoff/manifest'); assert m['version']=='8.12.0' and m['capabilities']['evidenceManifestGeneration'] is True,m
s=get('/v8120/status'); assert s['immutableAnalysisSnapshotHandoff'] and s['automaticPublication'] is False,s
print('PASS: Workbench v8.12.0 backend deployed and verified.')
PYVERIFY
echo "Backend backup: $BACKUP"
