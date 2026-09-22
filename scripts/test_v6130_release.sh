#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT:$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v6.13.0 release validation ==="
"$PY" -m pytest -q \
  "$ROOT/backend/tests/test_platform_core_connectivity_v640.py" \
  "$ROOT/backend/tests/test_unified_runtime_contract_adapter_v650.py" \
  "$ROOT/backend/tests/test_unified_research_session_bridge_v660.py" \
  "$ROOT/backend/tests/test_computation_execution_lineage_bridge_v670.py" \
  "$ROOT/backend/tests/test_scenario_uncertainty_runtime_v680.py" \
  "$ROOT/backend/tests/test_visual_reasoning_runtime_adapter_v690.py" \
  "$ROOT/backend/tests/test_predictive_intelligence_runtime_v6100.py" \
  "$ROOT/backend/tests/test_forensic_quantitative_reconstruction_v6110.py" \
  "$ROOT/backend/tests/test_research_state_reproduction_snapshot_v6120.py" \
  "$ROOT/backend/tests/test_core_aware_experience_v6130.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6100-predictive-intelligence-runtime.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6110-forensic-quantitative-reconstruction.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6120-research-state-reproduction-snapshot.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6130-core-aware-experience.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then
  echo "ERROR: unsafe SCWB_DIR bootstrap reference detected" >&2
  exit 1
fi
SCWB_REQUIRE_SERVICE_TOKEN=false "$PY" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
m=c.get('/integration/core/experience/manifest'); assert m.status_code==200 and m.json()['version']=='6.13.0'
ctx=c.post('/integration/core/experience/context/assemble',json={'projectRef':'sc://workbench/project/release','coreProjectRef':'core-project:release','coreSessionId':'session:release'}); assert ctx.status_code==200,ctx.text
body=ctx.json(); assert 'coreExecutionId' in body['missingCoreIds']; assert body['automaticDispatchAuthorized'] is False
compat=c.post('/integration/core/experience/compatibility/evaluate',json={'coreReachable':True,'coreVersion':'3.0.0'}); assert compat.status_code==200 and compat.json()['compatible'] is True
plan=c.post('/integration/core/experience/actions/plan',json={'action':'register-execution-lineage','context':{'projectRef':'sc://workbench/project/release','coreSessionId':'session:release'}}); assert plan.status_code==200 and plan.json()['ready'] is True and plan.json()['automaticDispatchAuthorized'] is False
print('PASS: Workbench v6.13.0 Core-aware experience endpoints assembled')
PY
echo 'PASS: Workbench v6.13.0 release checks passed.'
