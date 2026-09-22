#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT:$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.0.0 release validation ==="
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
  "$ROOT/backend/tests/test_core_aware_experience_v6130.py" \
  "$ROOT/backend/tests/test_platform_integration_certification_v6140.py" \
  "$ROOT/backend/tests/test_unified_execution_runtime_v700.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6100-predictive-intelligence-runtime.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6110-forensic-quantitative-reconstruction.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6120-research-state-reproduction-snapshot.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6130-core-aware-experience.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6140-platform-integration-certification.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v700-unified-execution-runtime.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then
  echo "ERROR: unsafe SCWB_DIR bootstrap reference detected" >&2
  exit 1
fi
SCWB_REQUIRE_SERVICE_TOKEN=false "$PY" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/v700/status'); assert s.status_code==200 and s.json()['version']=='7.0.0' and s.json()['operationCount']>=60
m=c.get('/execution/runtime/manifest'); assert m.status_code==200 and m.json()['capabilities']['canonicalExecutionEnvelope'] is True
r=c.post('/execution/runtime/execute',json={'operation':'numerical.integrate','payload':{'expression':'x**2','lower':0,'upper':1,'samples':101}}); assert r.status_code==200; d=r.json(); assert abs(d['result']['result']['value']-1/3)<1e-10
f=c.post('/execution/runtime/execute',json={'operation':'predictive.forecast','payload':{'projectEntityId':'release','modelKey':'linear','modelName':'Linear','history':[1,2,3,4,5,6],'horizon':2,'method':'linear-trend'}}); assert f.status_code==200 and f.json()['result']['pointForecast']==[7.0,8.0]
w=c.post('/execution/runtime/workflow/run',json={'workflowKey':'release','steps':[{'stepId':'a','operation':'math.compute','payload':{'expression':'6*7'}},{'stepId':'b','operation':'electronics.resistor-network','dependsOn':['a'],'payload':{'resistancesOhm':[100,220],'sourceVoltageV':5}}]}); assert w.status_code==200 and w.json()['dependencyOrder']==['a','b'] and w.json()['automaticOutputSubstitutionPerformed'] is False
p=c.post('/integration/core/unified-execution/lineage/plan',json={'executionResult':r.json()}); assert p.status_code==200 and p.json()['coreExecutionIdMustComeFromCore'] is True and p.json()['automaticCoreDispatchAuthorized'] is False
print('PASS: Workbench v7.0.0 unified scientific and engineering execution endpoints assembled')
PY
echo 'PASS: Workbench v7.0.0 release checks passed.'
