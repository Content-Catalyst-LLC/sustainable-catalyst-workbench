#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT:$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v6.12.0 release validation ==="
"$PY" -m pytest -q \
  "$ROOT/backend/tests/test_platform_core_connectivity_v640.py" \
  "$ROOT/backend/tests/test_unified_runtime_contract_adapter_v650.py" \
  "$ROOT/backend/tests/test_unified_research_session_bridge_v660.py" \
  "$ROOT/backend/tests/test_computation_execution_lineage_bridge_v670.py" \
  "$ROOT/backend/tests/test_scenario_uncertainty_runtime_v680.py" \
  "$ROOT/backend/tests/test_visual_reasoning_runtime_adapter_v690.py" \
  "$ROOT/backend/tests/test_predictive_intelligence_runtime_v6100.py" \
  "$ROOT/backend/tests/test_forensic_quantitative_reconstruction_v6110.py" \
  "$ROOT/backend/tests/test_research_state_reproduction_snapshot_v6120.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6100-predictive-intelligence-runtime.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6110-forensic-quantitative-reconstruction.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6120-research-state-reproduction-snapshot.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then
  echo "ERROR: unsafe SCWB_DIR bootstrap reference detected" >&2
  exit 1
fi
SCWB_REQUIRE_SERVICE_TOKEN=false "$PY" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
m=c.get('/integration/core/research-state/manifest'); assert m.status_code==200 and m.json()['version']=='6.12.0'
s=c.post('/research-state/snapshot/build',json={'snapshotKey':'release-probe','projectRef':'sc://workbench/project/release','title':'Release probe','bindings':[{'bindingKey':'out','objectType':'output','objectRef':'sc://workbench/output/release','contentHash':'sha256:out'}],'environments':[{'environmentKey':'wb','environmentType':'workbench','environmentRef':'sc://workbench/runtime/6.12.0'}]}); assert s.status_code==200,s.text
snap=s.json(); assert len(snap['snapshotHash'])==64
p=c.post('/integration/core/research-state/project-state/version/plan',json={'coreStateId':'state-probe','snapshot':snap}); assert p.status_code==200,p.text; assert p.json()['automaticStateRestoreAuthorized'] is False
r=c.post('/integration/core/research-state/reproduction/prepare',json={'coreProjectEntityId':'project-probe','snapshot':snap}); assert r.status_code==200,r.text; assert r.json()['corePackageIdMustComeFromCore'] is True
ctx=c.post('/integration/core/research-state/context/prepare',json={'snapshot':snap}); assert ctx.status_code==200,ctx.text; assert ctx.json()['coreContextIdMustComeFromCore'] is True
print('PASS: Workbench v6.12.0 research state, reproduction and snapshot endpoints assembled')
PY
echo 'PASS: Workbench v6.12.0 release checks passed.'
