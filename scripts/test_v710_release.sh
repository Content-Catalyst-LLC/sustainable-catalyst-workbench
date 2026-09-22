#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT:$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.1.0 release validation ==="
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
  "$ROOT/backend/tests/test_unified_execution_runtime_v700.py" \
  "$ROOT/backend/tests/test_unified_execution_object_model_v710.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v700-unified-execution-runtime.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v710-unified-execution-object-model.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then
  echo "ERROR: unsafe SCWB_DIR bootstrap reference detected" >&2
  exit 1
fi
SCWB_REQUIRE_SERVICE_TOKEN=false "$PY" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/v710/status'); assert s.status_code==200 and s.json()['version']=='7.1.0' and s.json()['contentAddressedIntegrity'] is True
m=c.get('/execution/objects/manifest'); assert m.status_code==200 and m.json()['objectSchema']=='sc-workbench-execution-object/1.0'
x=c.post('/execution/objects/execute',json={'operation':'math.compute','payload':{'expression':'6*7'},'projectRef':'project:release','requestKey':'release-math'}); assert x.status_code==200; obj=x.json()['executionObject']; assert obj['outputs'][0]['inlineResult']['result']['exactText']=='42'
v=c.post('/execution/objects/validate',json={'executionObject':obj}); assert v.status_code==200 and v.json()['valid'] is True
r=c.post('/execution/objects/revise',json={'executionObject':obj,'reason':'release validation','metadataPatch':{'reviewed':True}}); assert r.status_code==200 and r.json()['revision']==2 and r.json()['outputs']==obj['outputs']
w=c.post('/execution/objects/workflow/run',json={'workflowKey':'release-flow','steps':[{'stepId':'a','operation':'math.compute','payload':{'expression':'10+5'}},{'stepId':'b','operation':'electronics.resistor-network','dependsOn':['a'],'payload':{'resistancesOhm':[10,20],'sourceVoltageV':3}}]}); assert w.status_code==200; wo=w.json()['executionObject']; assert wo['objectKind']=='workflow_execution' and len(wo['dependencies']['edges'])==1
p=c.post('/integration/core/execution-objects/binding/plan',json={'executionObject':obj,'coreRuntimeSessionId':'core-session-release','coreRuntimeContractId':'core-contract-release'}); assert p.status_code==200; d=p.json(); assert d['scientificRuntimeExecutionBinding']['path']=='/v1/research/unified-runtime/execution-bindings' and d['runtimeInvocationRegistration']['path']=='/v1/research/runtime-contract/invocations' and d['automaticCoreDispatchAuthorized'] is False
print('PASS: Workbench v7.1.0 unified execution object endpoints assembled')
PY
echo 'PASS: Workbench v7.1.0 release checks passed.'
